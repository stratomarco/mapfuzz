# M0 baseline audit

Milestone M0 records, per target, whether upstream already runs continuous fuzzing and which load paths any existing harness leaves unreached. This prevents duplicated effort and fixes the project's positioning against evidence rather than assumption.

## GGUF (ggml / llama.cpp)

- Commit audited: `432d7ffe2c3b4e539f3d0d4ae0a4893090a018d6` (ggml 0.18.0, 2026-07-30).
- Existing fuzz targets in the repository: none. A tree search for any file matching `*fuzz*` at this commit returned nothing.
- Consequence: the GGUF loader has no in-repo continuous fuzzing. This is consistent with the 2026-05-15 oss-security advisory, whose six parser bugs were found by manual review.
- Positioning: greenfield. The value is both breadth (a harness where none exists) and depth (structure-aware mutation reaching the alignment, element-count, and size-computation paths).

Verification note: OSS-Fuzz integration is separate from in-repo harnesses. Confirm whether GGUF is fuzzed through any external OSS-Fuzz project before publishing a novelty claim. The in-repo finding above is verified; the external-coverage question is open.

## Other targets

Not yet audited. Repeat the same procedure for safetensors, ONNX, PyTorch/pickle, TensorFlow SavedModel, Keras, and the tokenizer loaders before implementing each harness:

1. Search the upstream repository for existing fuzz targets.
2. Check OSS-Fuzz and ClusterFuzzLite for an existing integration and its reported coverage.
3. Record which load paths remain unreached.
