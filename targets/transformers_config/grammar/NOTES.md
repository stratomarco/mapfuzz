# Config-parsing structure-aware notes

The input is a config dict/JSON parsed into a PretrainedConfig. Blind byte
mutation of JSON mostly yields invalid JSON rejected before parsing. A
structure-aware generator (the harness already builds dicts from fuzzer entropy)
keeps the JSON valid and mutates the fields that drive the interesting paths.

## High-value fields (robustness, not code-exec)

- Numeric shape/size fields (hidden_size, num_hidden_layers, num_attention_heads,
  vocab_size): extreme, negative, zero, non-int values; consistency between them.
- id2label / label2id maps: huge maps, mismatched pairs, non-string keys.
- torch_dtype and other string-enum fields: invalid enum strings.
- Nested sub-config dicts: deep nesting to probe recursion / stack depth.
- Fields consumed by validation loops or cross-field checks.

## Scope guard (do not remove)

The forbidden-key set (auto_map, trust_remote_code, _attn_implementation_internal,
_experts_implementation_internal, attn_implementation, quantization_config,
custom_pipelines) is stripped from every generated input. These reach the
dynamic-module / kernel-dispatch code-execution path (the recent CVEs). Keeping
them out is what makes this a robustness target rather than an RCE-hunting one.

## Next levers

- Longer campaigns (the import graph makes each run heavy; low exec/s is normal).
- Target specific model config subclasses (BertConfig, etc.) whose __init__ does
  more validation than the base class.
- Exercise from_json_file with malformed JSON text to hit the JSON parse layer,
  distinct from the dict path.
