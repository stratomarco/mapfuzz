# GGUF structure-aware mutation notes

Byte-level mutation wastes most of its budget failing the magic and version checks. A structure-aware mutator keeps the envelope parseable while mutating the fields that drive the dangerous code paths. This file records the format layout and the mutation targets; a mutator module (custom libFuzzer mutator, or a protobuf-style grammar) is the next step.

## Wire layout (GGUF v3)

Header:
- magic: 4 bytes, `GGUF`.
- version: uint32.
- tensor_count: uint64.
- metadata_kv_count: uint64.

Metadata key/value section, repeated `metadata_kv_count` times:
- key: gguf string (uint64 length, then bytes).
- value_type: uint32 (a `gguf_type`).
- value: depends on type. For `ARRAY`: element_type (uint32), length (uint64), then elements.

Tensor info section, repeated `tensor_count` times:
- name: gguf string.
- n_dims: uint32.
- dims: n_dims x int64 (the `ne` array).
- type: uint32 (a `ggml_type`).
- offset: uint64.

Then alignment padding to `general.alignment`, then the tensor data blob.

## High-value mutation targets

These are the fields that reach the memory-safety and resource classes; a mutator should perturb them independently rather than uniformly:

- `general.alignment` value: unbounded or non-power-of-2 values drive the alignment and padding math.
- string lengths and array lengths: large declared lengths drive allocation and read sizes.
- `metadata_kv_count` and `tensor_count`: high counts against a short file drive read-past-end and allocation-count paths.
- `value_type` and array `element_type`: out-of-range enum values exercise the type-dispatch and size-lookup logic.
- tensor `n_dims` and the `ne` dimensions: zero, negative, and near-`INT64_MAX` dimensions drive the element-count overflow and division checks.
- tensor `type`: out-of-range values exercise the block-size lookup used in size computation.
- tensor `offset`: values that overlap, exceed the file, or wrap exercise the data-region bounds handling.

## Approach

Two options, in increasing order of effort:

1. Custom libFuzzer mutator (`LLVMFuzzerCustomMutator`) that parses the current input into the structure above, mutates one field class per call while keeping the rest valid, and re-serializes. Fast to write, no schema dependency.
2. A protobuf model of the GGUF structure driven by a protobuf-aware mutator, replaying the message into a serializer. Heavier, but reuses a mature mutation engine and composes with the ONNX and SavedModel targets that are already protobuf.

Start with option 1 for GGUF; it is self-contained and the format is small.
