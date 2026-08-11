# Target: transformers config parsing (robustness / DoS only)

## Scope boundary (hard)

This target fuzzes the ROBUSTNESS of parsing a config dict/JSON into a
`PretrainedConfig`: crashes, unhandled exceptions, hangs, and memory blowups on
malformed input. It is a denial-of-service / robustness target.

It deliberately excludes the code-execution surface. The recent transformers
RCEs live in the dynamic-module / kernel-dispatch path reached through the Auto
classes and specific config fields, not in dict-to-object parsing:

- CVE-2026-4372: `_attn_implementation_internal` kernel dispatch, bypasses
  `trust_remote_code=False` (patched 5.3.0).
- CVE-2026-5241: `auto_map` / `trust_remote_code` override (LightGlue).
- CVE-2026-1839: Trainer reaching unsafe `torch.load`.

We target `PretrainedConfig.from_dict` directly, never set `trust_remote_code`,
and strip the code-exec-adjacent keys (`auto_map`, `trust_remote_code`,
`_attn_implementation_internal`, `_experts_implementation_internal`,
`attn_implementation`, `quantization_config`, `custom_pipelines`) from every
generated input. This is a scope guard so fuzzing cannot wander onto that path,
not a security control. A finding is a crash or hang, disclosed as a
robustness/DoS defect, never a weaponized config.

## Loader under test

- Entry point: `PretrainedConfig.from_dict(config_dict, **kwargs)` (verified at
  `configuration_utils.py:861`). `from_dict` pops `trust_remote_code` and warns
  it has no effect on this path, confirming dict-to-object parsing does not
  execute remote code.
- `from_dict` iterates config keys, `setattr`s values onto the object, and
  recurses into nested `PreTrainedConfig` sub-configs (a recursion surface).

## M0 audit result

- transformers is not in OSS-Fuzz (`projects/transformers/project.yaml` 404;
  sentencepiece control 200) and the repo ships no fuzz targets.
- The config CODE-EXECUTION surface is heavily worked (multiple 2026 CVEs). The
  config-PARSING robustness surface is not separately fuzzed, and is what we
  target here.

## Bug classes targeted

- Unhandled exceptions on malformed values (wrong types, out-of-range, bad
  `torch_dtype` strings, malformed `id2label` maps).
- Recursion / stack exhaustion via deeply nested sub-config dicts.
- Unbounded allocation from attacker-scaled sizes.
- Hangs in any parsing/validation loop.

## Build and run

Python + pip. Installs transformers and atheris (no torch needed for config
parsing).

```
./build.sh
python3 harness/fuzz_config_from_dict.py --selftest
python3 harness/fuzz_config_from_dict.py -max_total_time=600 -rss_limit_mb=4096
```

## Status

Built and validated in-sandbox against transformers 5.15.0: self-test passes
(baseline parses, scope guard strips forbidden keys), and a 60-second campaign
ran clean with coverage growth (reached config parsing, 27k runs, no crash).
The shallow layer is robust, expected for heavily-scrutinized post-CVE code; a
longer campaign and a structure-aware generator (see grammar notes) are the next
levers. Note the low exec rate: config parsing pulls a large import graph, so
each iteration is heavy.
