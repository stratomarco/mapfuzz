"""Structure-aware fuzzer for flax checkpoint restore (JAX-ecosystem loader).

Trust boundary: restoring an untrusted JAX/flax checkpoint. flax serializes a
pytree to msgpack with custom extension types for array leaves; restoring calls
flax.serialization.msgpack_restore(bytes) -> pytree, which runs flax's own
ext_hook (_msgpack_ext_unpack) and _ndarray_from_bytes (np.frombuffer + reshape
on an untrusted shape/dtype/buffer triple). This is the JAX sibling of the
pytorch weights_only target, and none of flax/orbax/jax/msgpack are in OSS-Fuzz.

Entry point verified against flax 0.12.8 source. Scope: robustness/DoS on load
(crashes, hangs, unhandled exceptions, unbounded allocation). Defect
demonstration only; numpy blocks object-dtype arrays from buffers, so this is not
a code-execution surface.

Blind byte mutation dies in the msgpack framing. This harness builds a VALID
msgpack pytree and mutates the security-relevant fields: the array-ext triple
(shape, dtype_name, buffer) where declared shape/dtype meet actual bytes, plus
the surrounding pytree structure (nesting, key types, ext codes).
"""

import sys

import atheris

with atheris.instrument_imports():
    import msgpack
    import numpy as np
    import flax.serialization as fs


# flax ext type codes (verified from source): ndarray=1, native_complex=2,
# npscalar=3.
_EXT_NDARRAY = 1
_EXT_COMPLEX = 2
_EXT_NPSCALAR = 3

_DTYPES = [b"<f4", b"<f8", b"<i4", b"<i8", b"<u1", b"|b1", b"<f2",
           b"bfloat16", b"O", b"<M8[Y]", b"<c8", b"not_a_dtype", b""]


def _make_array_ext(fdp):
    # Build the [shape, dtype_name, buffer] triple that _ndarray_from_bytes reads.
    ndim = fdp.ConsumeIntInRange(0, 4)
    shape = [fdp.ConsumeIntInRange(-2, 2**20) for _ in range(ndim)]
    dtype = _DTYPES[fdp.ConsumeIntInRange(0, len(_DTYPES) - 1)]
    buf = fdp.ConsumeBytes(fdp.ConsumeIntInRange(0, 256))
    inner = msgpack.packb([shape, dtype, buf])
    code = fdp.ConsumeIntInRange(1, 3)   # ndarray / complex / npscalar
    return msgpack.ExtType(code, inner)


def _make_value(fdp, depth):
    pick = fdp.ConsumeIntInRange(0, 9 if depth < 4 else 5)
    if pick == 0:
        return fdp.ConsumeInt(8)
    if pick == 1:
        return fdp.ConsumeFloat()
    if pick == 2:
        return fdp.ConsumeBool()
    if pick == 3:
        return None
    if pick == 4:
        return fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 20))
    if pick == 5:
        return _make_array_ext(fdp)             # the interesting leaf
    if pick == 6:
        return [_make_value(fdp, depth + 1)
                for _ in range(fdp.ConsumeIntInRange(0, 4))]
    if pick == 7:
        return {fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 8)) or "k":
                _make_value(fdp, depth + 1)
                for _ in range(fdp.ConsumeIntInRange(0, 4))}
    if pick == 8:
        # non-string map key (strict_map_key=False allows these)
        return {fdp.ConsumeIntInRange(0, 999): _make_value(fdp, depth + 1)}
    # raw ext with an arbitrary code (exercises the ext_hook fallback)
    return msgpack.ExtType(fdp.ConsumeIntInRange(0, 127),
                           fdp.ConsumeBytes(fdp.ConsumeIntInRange(0, 32)))


_EXPECTED = (
    ValueError, TypeError, KeyError, IndexError, msgpack.exceptions.UnpackException,
    msgpack.exceptions.ExtraData, OverflowError, UnicodeDecodeError, OSError,
    NotImplementedError, AttributeError,
)


def TestOneInput(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    try:
        tree = _make_value(fdp, 0)
        blob = msgpack.packb(tree, default=msgpack.ExtType.__new__)
    except Exception:
        # fall back to packing without a default hook
        try:
            blob = msgpack.packb(tree)
        except Exception:
            return
    try:
        fs.msgpack_restore(blob)
    except _EXPECTED:
        return
    except RecursionError:
        raise
    except Exception:  # noqa: BLE001
        # numpy/flax may raise other exceptions on malformed arrays; those are
        # clean rejections unless they indicate a real defect. Let unexpected
        # types through to the fuzzer for inspection.
        raise


def _selftest() -> int:
    # a real checkpoint round-trips
    tree = {"params": {"w": np.zeros((2, 3), dtype=np.float32)}, "step": 1}
    blob = fs.msgpack_serialize(tree)
    back = fs.msgpack_restore(blob)
    print("SELFTEST round-trip OK:", back["step"] == 1)
    # the generator produces restorable-or-cleanly-rejected blobs
    import random
    ok = rej = 0
    for i in range(200):
        fdp = atheris.FuzzedDataProvider(random.randbytes(64))
        try:
            t = _make_value(fdp, 0)
            b = msgpack.packb(t)
        except Exception:
            continue
        try:
            fs.msgpack_restore(b); ok += 1
        except Exception:
            rej += 1
    print(f"SELFTEST generator: {ok} restored, {rej} cleanly rejected of ~200")
    print("flax", __import__("flax").__version__)
    return 0


def main() -> None:
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
