"""Structure-aware fuzzer for flax.serialization.from_state_dict (structural layer).

Distinct surface from fuzz_msgpack_restore (which fuzzes bytes -> pytree through
numpy C code, weak coverage). from_state_dict(target, state) reconciles an
untrusted state dict against a target template, recursing through flax's own
Python handlers (dict, list, tuple, namedtuple, FrozenDict, dataclass). That
reconciliation is where structural confusion and recursion live, and it is
instrumented Python, so coverage guidance actually works here.

The trust boundary: from_bytes(target, untrusted_bytes) calls
msgpack_restore(bytes) then from_state_dict(target, restored). An application
restoring a checkpoint controls the target template but NOT the state. So we fix
a small set of realistic targets and fuzz the STATE against them.

Probes already show a soft spot: a non-dict state where a dict is expected raises
a raw AttributeError ('list'/'str' object has no attribute 'keys') rather than a
clean flax deserialization error, i.e. input validation is not uniform. This
harness treats flax's own SerializationError / ValueError as clean rejections and
flags anything else (unhandled types, recursion) for inspection.

Scope: robustness/DoS. Defect demonstration only.
"""

import sys

import atheris

with atheris.instrument_imports():
    import flax.serialization as fs
    from flax.core import FrozenDict


# Realistic target templates an application might restore into. The fuzzer picks
# one and fuzzes the state against it.
_TARGETS = [
    {"params": {"w": 0, "b": 0}, "step": 0},
    {"model": {"layers": [{"kernel": 0}, {"kernel": 0}]}, "opt": {"count": 0}},
    [0, 0, 0],
    (0, 0),
    FrozenDict({"a": 0, "nested": {"x": 0}}),
    {"scalar": 0.0, "flag": False, "name": ""},
]


def _make_state(fdp, depth):
    pick = fdp.ConsumeIntInRange(0, 9 if depth < 6 else 4)
    if pick == 0:
        return fdp.ConsumeInt(8)
    if pick == 1:
        return fdp.ConsumeFloat()
    if pick == 2:
        return fdp.ConsumeBool()
    if pick == 3:
        return fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 16))
    if pick == 4:
        return None
    if pick == 5:
        return [_make_state(fdp, depth + 1)
                for _ in range(fdp.ConsumeIntInRange(0, 5))]
    if pick == 6:
        return {fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 8)) or "k":
                _make_state(fdp, depth + 1)
                for _ in range(fdp.ConsumeIntInRange(0, 5))}
    if pick == 7:
        # dict with realistic-looking keys to actually match target structure
        # sometimes (drives the deeper reconciliation paths)
        keys = ["params", "step", "w", "b", "model", "layers", "kernel", "opt",
                "count", "a", "nested", "x", "scalar", "flag", "name", "0", "1"]
        n = fdp.ConsumeIntInRange(0, 5)
        return {keys[fdp.ConsumeIntInRange(0, len(keys) - 1)]:
                _make_state(fdp, depth + 1) for _ in range(n)}
    if pick == 8:
        # numeric string keys (list-handler path expects these)
        n = fdp.ConsumeIntInRange(0, 5)
        return {str(i): _make_state(fdp, depth + 1) for i in range(n)}
    # deliberately wrong container type at this position (type confusion)
    return fdp.ConsumeBytes(fdp.ConsumeIntInRange(0, 8))


# flax's own clean rejections. Anything else (AttributeError, RecursionError,
# etc.) is surfaced for inspection.
def _expected(exc):
    names = {"SerializationError", "ValueError", "KeyError", "TypeError"}
    return type(exc).__name__ in names or isinstance(exc, (ValueError, KeyError))


def TestOneInput(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    target = _TARGETS[fdp.ConsumeIntInRange(0, len(_TARGETS) - 1)]
    try:
        state = _make_state(fdp, 0)
    except Exception:
        return
    try:
        fs.from_state_dict(target, state)
    except RecursionError:
        raise
    except Exception as e:  # noqa: BLE001
        if not _expected(e):
            raise


def _selftest() -> int:
    # matching state restores
    t = {"params": {"w": 0, "b": 0}, "step": 0}
    r = fs.from_state_dict(t, {"params": {"w": 1, "b": 2}, "step": 5})
    print("SELFTEST match restores:", r["step"] == 5)
    # the known soft spot: non-dict state -> AttributeError (unhandled)
    try:
        fs.from_state_dict(t, "notadict")
        print("SELFTEST non-dict state: no error (?)")
    except Exception as e:  # noqa: BLE001
        flagged = not _expected(e)
        print(f"SELFTEST non-dict state raises {type(e).__name__}; "
              f"flagged-as-finding={flagged}")
    # generator reach
    import random
    ok = rej = flg = 0
    for _ in range(300):
        fdp = atheris.FuzzedDataProvider(random.randbytes(48))
        tgt = _TARGETS[fdp.ConsumeIntInRange(0, len(_TARGETS) - 1)]
        try:
            st = _make_state(fdp, 0)
        except Exception:
            continue
        try:
            fs.from_state_dict(tgt, st); ok += 1
        except Exception as e:  # noqa: BLE001
            if _expected(e):
                rej += 1
            else:
                flg += 1
    print(f"SELFTEST generator: {ok} restored, {rej} clean-rejected, "
          f"{flg} flagged (unhandled) of ~300")
    return 0


def main() -> None:
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
