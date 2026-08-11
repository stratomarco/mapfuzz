"""Atheris harness for transformers config PARSING robustness.

Scope (read this, it is a hard boundary):
    This fuzzes the robustness of parsing a config dict/JSON into a
    PretrainedConfig object: crashes, unhandled exceptions, hangs, and memory
    blowups on malformed input. It is a denial-of-service / robustness target.

    It deliberately does NOT touch the code-execution surface. The recent
    transformers RCEs (CVE-2026-4372 _attn_implementation_internal kernel
    dispatch, CVE-2026-5241 auto_map/trust_remote_code, CVE-2026-1839 Trainer
    torch.load) all live in the dynamic-module / kernel path reached through the
    Auto classes, not in dict-to-object parsing. We target PretrainedConfig
    .from_dict / .from_json_file directly, never set trust_remote_code, and
    strip the code-exec-adjacent keys from every generated input so a mutation
    cannot wander onto that path. A finding here is a crash or hang, reported as
    a robustness/DoS defect, never a weaponized config.

Entry point verified against source: PretrainedConfig.from_dict(config_dict,
**kwargs) at configuration_utils.py:861; from_dict pops trust_remote_code and
warns it has no effect on this path.
"""

import io
import json
import sys

import atheris

with atheris.instrument_imports():
    import transformers
    from transformers import PretrainedConfig


# Keys tied to the code-execution / dynamic-module / kernel-dispatch surface.
# Stripped from every generated input so fuzzing cannot steer onto that path.
# This is a scope guard, not a security control.
_FORBIDDEN_KEYS = frozenset({
    "auto_map",
    "trust_remote_code",
    "_attn_implementation_internal",
    "_experts_implementation_internal",
    "attn_implementation",
    "quantization_config",       # can trigger optional-package dispatch
    "custom_pipelines",
})


def _scrub(obj):
    # Recursively drop forbidden keys anywhere in the structure.
    if isinstance(obj, dict):
        return {k: _scrub(v) for k, v in obj.items() if k not in _FORBIDDEN_KEYS}
    if isinstance(obj, list):
        return [_scrub(v) for v in obj]
    return obj


# A small valid config the fuzzer mutates around.
_TEMPLATE = {
    "model_type": "bert",
    "hidden_size": 16,
    "num_hidden_layers": 2,
    "num_attention_heads": 2,
    "vocab_size": 100,
    "id2label": {"0": "A", "1": "B"},
}


def _build_dict(fdp) -> dict:
    """Build a config dict from fuzzer entropy: start from the template, then
    add/override a handful of keys with fuzzer-chosen JSON-ish values."""
    d = dict(_TEMPLATE)
    n = fdp.ConsumeIntInRange(0, 8)
    for _ in range(n):
        key = fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(1, 24)) or "k"
        d[key] = _rand_value(fdp, depth=0)
    return _scrub(d)


def _rand_value(fdp, depth):
    pick = fdp.ConsumeIntInRange(0, 8 if depth < 4 else 5)
    if pick == 0:
        return fdp.ConsumeInt(8)
    if pick == 1:
        return fdp.ConsumeFloat()
    if pick == 2:
        return fdp.ConsumeBool()
    if pick == 3:
        return None
    if pick == 4:
        return fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 40))
    if pick == 5:
        return [_rand_value(fdp, depth + 1)
                for _ in range(fdp.ConsumeIntInRange(0, 5))]
    if pick == 6:
        return {str(i): _rand_value(fdp, depth + 1)
                for i in range(fdp.ConsumeIntInRange(0, 5))}
    if pick == 7:
        # very large int (allocation / range surface)
        return 10 ** fdp.ConsumeIntInRange(1, 12)
    # deep nesting (recursion surface), still bounded
    return {"n": _rand_value(fdp, depth + 1)}


_EXPECTED = (
    ValueError, TypeError, KeyError, AttributeError, OverflowError,
    json.JSONDecodeError, UnicodeError, OSError,
)


def TestOneInput(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    try:
        d = _build_dict(fdp)
    except Exception:
        return
    # Exercise both the dict path and the JSON-text path (from_json_file reads a
    # file; feed it via a round-trip through json to hit the JSON parse layer).
    try:
        PretrainedConfig.from_dict(dict(d))
    except _EXPECTED:
        pass
    except RecursionError:
        raise
    try:
        text = json.dumps(d)
    except (TypeError, ValueError):
        return
    try:
        PretrainedConfig.from_dict(json.loads(text))
    except _EXPECTED:
        return
    except RecursionError:
        raise


def _selftest() -> int:
    ok = PretrainedConfig.from_dict(dict(_TEMPLATE))
    print("SELFTEST baseline from_dict OK ->", type(ok).__name__)
    # confirm the scope guard strips forbidden keys
    dirty = dict(_TEMPLATE)
    dirty["auto_map"] = {"AutoConfig": "evil.module.Cls"}
    dirty["trust_remote_code"] = True
    dirty["_attn_implementation_internal"] = "evil"
    scrubbed = _scrub(dirty)
    leaked = _FORBIDDEN_KEYS & set(scrubbed)
    if leaked:
        print("SELFTEST FAILED: forbidden keys leaked:", leaked)
        return 1
    print("SELFTEST scope guard OK: forbidden keys stripped:",
          sorted(_FORBIDDEN_KEYS & set(dirty)))
    print("transformers", transformers.__version__)
    return 0


def main() -> None:
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
