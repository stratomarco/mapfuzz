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

## tokenizers (HuggingFace) [T1]

- Checked: OSS-Fuzz `projects/tokenizers/project.yaml` returns HTTP 404 (positive control `sentencepiece` returns 200), and a fresh clone of huggingface/tokenizers contains no `fuzz/` directory or fuzz target.
- Result: open ground. No in-repo harness, not in OSS-Fuzz, no published fuzzing surfaced.
- Entry point verified from source: `Tokenizer::from_bytes` at `tokenizer/mod.rs:473`.
- Caveat: absence of public evidence is not proof of no private or academic fuzzing.

## safetensors [audited, deferred]

- Result: not open. Ships its own fuzz target (`safetensors/fuzz/`), runs a per-commit automated security audit, and the core is deliberately minimal (~400 lines) with sequential offset validation. Deferred as already well-covered.

## SentencePiece [audited, deferred]

- Result: confirmed in OSS-Fuzz (`projects/sentencepiece/project.yaml` returns 200). Watched. Deferred.

## PyTorch weights_only unpickler [selected target]

- OSS-Fuzz: `projects/pytorch/project.yaml` returns 404 (not continuously fuzzed publicly).
- Active area: CVE-2025-32434 (legacy .tar bypass, fixed 2.6.0), CVE-2026-24747 (opcode/metadata memory corruption in weights_only unpickler, fixed 2.10.0). Both fixes verified present in current `main` source.
- Entry point verified: `torch._weights_only_unpickler.load` (line 592).
- Result: high-value, active, not continuously fuzzed. Target the current release to hunt the next gap. Scope limited to defect demonstration (crashes / unexpected failures in the restricted path), not weaponized exploits.

## ONNX [audited, deferred]

- `onnx` is in OSS-Fuzz (200) and ships a full `onnx/fuzz/` directory (fuzz_model_loader, fuzz_parser, fuzz_shape_inference, fuzz_checker, seed-corpus generator, CI workflow). Format loader already continuously fuzzed. Deferred.
- `onnxruntime` not in OSS-Fuzz (404), but its format-load path overlaps the already-fuzzed onnx protobuf parser; marginal open ground is narrow. Not selected.
