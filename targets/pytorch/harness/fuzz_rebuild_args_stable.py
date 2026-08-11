"""Coverage-guided, structure-STABLE generator for the pytorch meta-tensor path.

The problem with the first generator (fuzz_rebuild_args.py): it draws a variable
number of values from FuzzedDataProvider in an order that depends on earlier
draws (ndim is chosen first, then that many values; _draw_int consumes one or two
bytes depending on the branch). So a one-byte mutation by libFuzzer can shift
every downstream field, and coverage feedback cannot home in on a single field.
The byte-to-structure mapping is unstable under mutation, which fights the fuzzer.

This generator fixes that with a FIXED-LAYOUT decode: every structural choice and
every value is read from a fixed byte offset with fixed width. Mutating byte N
changes exactly one field and nothing else. That makes libFuzzer's coverage-
guided byte mutations behave as coverage-guided STRUCTURAL mutations: the fuzzer
learns which fields drive new coverage and steers toward them, for free.

Layout (all fixed width, consumed in constant order):
    [0]      function/dtype selector byte
    [1]      ndim_size   (0..MAXDIM)
    [2]      ndim_stride (0..MAXDIM)
    [3]      requires_grad + offset-mode flags
    [4]      storage_offset value-class selector
    [5..]    MAXDIM size value-classes, then MAXDIM stride value-classes,
             each one byte selecting a boundary value class
Unused slots (ndim < MAXDIM) are still consumed, so positions never shift.

Target: _rebuild_meta_tensor_no_storage (allowlisted, no storage), reaching
empty_strided in the C++ backend. Scope: defect demonstration only.
"""

import io
import struct
import sys

import atheris

with atheris.instrument_imports():
    import torch  # noqa: F401
    from torch import _weights_only_unpickler as wou


_DTYPES = [
    "float32", "float64", "float16", "bfloat16",
    "int64", "int32", "int16", "int8", "uint8", "bool",
    "complex64", "complex128",
]
_MAXDIM = 6
# Fixed header width, then 2*_MAXDIM value slots.
_HEADER = 5
_LAYOUT_LEN = _HEADER + 2 * _MAXDIM


# --- pickle opcode assembly (legacy GLOBAL, LONG1 ints, TUPLE) ----------------
def _int(n: int) -> bytes:
    if n == 0:
        return b"\x8a\x00"
    length = (n.bit_length() + 8) // 8
    return b"\x8a" + bytes([length]) + n.to_bytes(length, "little", signed=True)


def _tuple(items) -> bytes:
    return b"(" + b"".join(items) + b"t"


def _bool(v: bool) -> bytes:
    return b"\x88" if v else b"\x89"


def _global(module: str, name: str) -> bytes:
    return b"c" + module.encode() + b"\n" + name.encode() + b"\n"


# --- fixed-width value-class decode (stable under mutation) --------------------
# Each value slot is one byte selecting a boundary-biased integer. Stable: the
# same byte always yields the same value, independent of neighbours.
def _value_from_byte(b: int) -> int:
    cls = b & 0x0F                      # low nibble selects class
    payload = (b >> 4) & 0x0F           # high nibble is a small payload
    if cls == 0:
        return 0
    if cls == 1:
        return -1
    if cls == 2:
        return payload                  # small non-negative 0..15
    if cls == 3:
        return -payload                 # small non-positive
    if cls == 4:
        return 2**31 - 1
    if cls == 5:
        return 2**63 - 1
    if cls == 6:
        return -(2**63)
    if cls == 7:
        return 2**31
    if cls == 8:
        return 1 << (payload % 63)      # power-of-two, spreads magnitude
    if cls == 9:
        return -(1 << (payload % 63))
    if cls == 10:
        return 255 * (payload + 1)
    # remaining classes: mid-range values keyed by payload
    return (payload + 1) * 4096


def _fixed_bytes(data: bytes) -> bytes:
    # Pad/truncate the raw input to exactly _LAYOUT_LEN so offsets are stable.
    if len(data) >= _LAYOUT_LEN:
        return data[:_LAYOUT_LEN]
    return data + b"\x00" * (_LAYOUT_LEN - len(data))


def _build_stream(data: bytes) -> bytes:
    b = _fixed_bytes(data)
    sel = b[0]
    dtype_name = _DTYPES[sel % len(_DTYPES)]
    ndim_size = b[1] % (_MAXDIM + 1)
    ndim_stride = b[2] % (_MAXDIM + 1)
    requires_grad = bool(b[3] & 1)
    offset = _value_from_byte(b[4])

    size_slots = b[_HEADER:_HEADER + _MAXDIM]
    stride_slots = b[_HEADER + _MAXDIM:_HEADER + 2 * _MAXDIM]
    size = [_value_from_byte(size_slots[i]) for i in range(ndim_size)]
    stride = [_value_from_byte(stride_slots[i]) for i in range(ndim_stride)]

    parts = [b"\x80\x02"]
    parts.append(_global("torch._utils", "_rebuild_meta_tensor_no_storage"))
    args = [
        _global("torch", dtype_name),
        _tuple([_int(x) for x in size]),
        _tuple([_int(x) for x in stride]),
        _bool(requires_grad),
    ]
    # storage_offset is not an arg to this rebuild fn; kept for parity with the
    # storage-backed generator and to consume the byte (stable layout).
    _ = offset
    parts.append(_tuple(args))
    parts.append(b"R.")
    return b"".join(parts)


_EXPECTED = (
    wou.UnpicklingError, EOFError, ValueError, KeyError, IndexError,
    TypeError, AttributeError, ImportError, struct.error, RuntimeError,
)


def TestOneInput(data: bytes) -> None:
    try:
        stream = _build_stream(data)
    except Exception:
        return
    try:
        wou.load(io.BytesIO(stream))
    except _EXPECTED:
        return
    except RecursionError:
        raise


def _selftest() -> int:
    # Stability check: flipping one byte changes at most one decoded field.
    import copy  # noqa: F401
    base = bytes(range(_LAYOUT_LEN))

    def decode_fields(data):
        b = _fixed_bytes(data)
        ns = b[1] % (_MAXDIM + 1)
        nst = b[2] % (_MAXDIM + 1)
        size = [_value_from_byte(b[_HEADER + i]) for i in range(ns)]
        stride = [_value_from_byte(b[_HEADER + _MAXDIM + i]) for i in range(nst)]
        return (b[0] % len(_DTYPES), ns, nst, bool(b[3] & 1), tuple(size), tuple(stride))

    f0 = decode_fields(base)
    # flip a single size-slot byte; only the size tuple should change
    mut = bytearray(base); mut[_HEADER] ^= 0xFF
    f1 = decode_fields(bytes(mut))
    changed = [i for i in range(len(f0)) if f0[i] != f1[i]]
    print("baseline fields:", f0)
    print("after flipping one size-slot byte, changed field indices:", changed)
    ok = changed in ([4], [])  # only the size tuple (index 4), or no-op
    print("STABILITY", "OK" if ok else "FAILED",
          "(a one-byte flip perturbs a local field, not the whole structure)")
    # and confirm a stream builds + is well-formed
    s = _build_stream(base)
    print("stream builds, len:", len(s))
    return 0 if ok else 1


def main() -> None:
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
