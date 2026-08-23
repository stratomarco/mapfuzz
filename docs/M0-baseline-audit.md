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

- Result: not open. Ships its own in-repo cargo-fuzz target (verified 2026-08-19: safetensors/fuzz/fuzz_targets/fuzz_target_1.rs), and the core is deliberately minimal (~400 lines) with sequential offset validation. Deferred as well-covered by its own fuzzer. CORRECTION (2026-08-19): safetensors is NOT a dedicated OSS-Fuzz project (verified against the full 1372-project list); the coverage basis is its in-repo fuzzer, not an OSS-Fuzz project. Absence from the project list does not prove it is never exercised inside another harness.

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

## transformers config parsing [selected target, robustness scope]

- transformers not in OSS-Fuzz (404; sentencepiece control 200); repo ships no fuzz targets.
- Config CODE-EXECUTION surface heavily worked (CVE-2026-4372 _attn_implementation_internal, CVE-2026-5241 auto_map/trust_remote_code, CVE-2026-1839 Trainer torch.load). Config-PARSING robustness surface not separately fuzzed.
- Scope limited to robustness/DoS (crashes/hangs in dict-to-object parsing). Code-exec fields stripped from every input by a scope guard; trust_remote_code never set. Entry point PretrainedConfig.from_dict verified (configuration_utils.py:861), confirmed inert re remote code.
- Validated in-sandbox against transformers 5.15.0: self-test passes, 60s campaign clean with coverage growth.

## numpy .npy/.npz [RULED OUT - already fuzzed]

- numpy IS in OSS-Fuzz (project.yaml present, vendor AdaLogics). Definitive check
  of projects/numpy/ shows harnesses that cover our exact intended surface:
  fuzz_binary_loader.py (imports zipfile+tempfile = .npy/.npz load path),
  fuzz_fromfile_loader.py, fuzz_dtype.py (dtype descriptor parsing), fuzz_loader.py.
- The .npy/.npz format parser and the dtype-string surface are continuously
  fuzzed. RULED OUT, same as safetensors and ONNX. Do not build.

## HDF5 / Keras / h5py [RULED OUT - already fuzzed, including the RCE surface]

- hdf5, h5py, keras, tensorflow ALL in OSS-Fuzz (all project.yaml 200).
- keras fuzzes the exact promising surfaces: fuzz_model.py (h5py + keras .h5
  model load) AND fuzz_serialization.py (deserialize_keras_object = the config
  deserialization / RCE surface). h5py fuzzes the HDF5 file layer (h5f).
- Both the binary format and the model-deserialization path are covered. RULED OUT.

## Strategic note: mainstream ML formats are saturated in OSS-Fuzz

Audit finding across this session: numpy, hdf5, h5py, keras, tensorflow, onnx,
sentencepiece and others are in OSS-Fuzz (largely via AdaLogics). NOTE (2026-08-19): safetensors is covered by its own in-repo cargo-fuzz target rather than a dedicated OSS-Fuzz project (see the safetensors entry above); the numpy/hdf5/onnx saturation claims below should each be re-verified against the current OSS-Fuzz project list rather than assumed. The
obvious format-parser targets are taken. mapfuzz's defensible niche is therefore
NOT "fuzz another mainstream format parser" but the surfaces OSS-Fuzz does not
cover: (1) newer/smaller-ecosystem loaders not yet onboarded (llama.cpp GGUF was
one; tokenizers Rust internals were another - both yielded); (2) cross-cutting
bug CLASSES that per-project fuzzers miss (resource exhaustion / decompression
bombs, cross-implementation divergence, the download-to-load trust-boundary
composition); (3) the integration layer where a model file crosses between a
parser and a consumer. Breadth-by-format is largely exhausted; depth-by-class and
newer-loaders are where the open ground is.

## flax/orbax JAX checkpoint restore [SELECTED - open]

- flax, orbax, jax, msgpack all NOT in OSS-Fuzz (404; pyyaml/sentencepiece 200 controls).
  The raw YAML/sentencepiece parse layers are covered; the JAX checkpoint-restore
  path is not.
- Entry point verified: flax.serialization.msgpack_restore(bytes) -> pytree (and
  from_bytes -> from_state_dict). Custom ext_hook (_msgpack_ext_unpack) and
  _ndarray_from_bytes (np.frombuffer + reshape on untrusted shape/dtype/buffer)
  are flax's own deserialization logic, distinct from raw msgpack.
- Trust boundary: restoring an untrusted JAX/flax checkpoint (download-to-load),
  the JAX-ecosystem sibling of the pytorch weights_only target. Used by DreamerV3
  and most JAX world models (dreamerv3/lerobot also 404, not fuzzed).
- Shallow probes: array reconstruction mostly robust (shape/buffer mismatch, huge
  shape, object-dtype all reject cleanly), but shape/dtype fields are loosely
  typed (string shapes interpreted byte-wise, exotic dtypes pass). A structure-
  aware fuzzer is warranted. Validated in-sandbox (flax 0.12.8 installed).

## minja chat-template parser (llama.cpp C++ Jinja) [SELECTED - open, promising]

- jinja2 (Python engine) IS in OSS-Fuzz, but minja (llama.cpp's from-scratch C++
  reimplementation) is NOT, nor are consumers (llama-cpp-python/ollama/vllm/
  transformers all 404). No fuzzer in the minja repo. Open ground.
- Entry point: minja::Parser::parse(std::string, Options) (header-only, verified).
  Trust boundary: chat templates ship inside model tokenizer configs and are
  parsed+executed at inference (download-to-load-to-execute).
- Built in-sandbox (clang 18, libFuzzer+ASan+UBSan). One low-severity real finding:
  minja::Options has uninitialized bool members; `Options opts;` reads garbage
  bools during parse (UBSan minja.hpp:2604). Fix = one line of defaults. Low sev,
  caller-dependent reachability.
- With Options initialized, parse is clean over 93k runs BUT with RICH growing
  coverage (cov 2709, ft 8158), unlike other targets' shallow corridors. Genuinely
  deep C++ parser worth a long campaign. Most promising open surface in the project.

## clip/mmproj loader (llama.cpp multimodal projector) [SELECTED - open, yielded 2 findings]

- llama.cpp IS in OSS-Fuzz, but its target list (fuzz_grammar, fuzz_json_to_grammar,
  fuzz_apply_template, fuzz_load_model, fuzz_inference, fuzz_structured) does NOT
  cover the mmproj/CLIP loader (tools/mtmd/clip.cpp). GBNF grammar parsing was
  declined as saturated (fuzz_grammar exists); the mmproj loader was the open gap.
- Entry point: clip_init(const char*, clip_context_params) -> clip_model_loader,
  reached via a synthetic minimal mmproj GGUF (has_vision_encoder + mlp projector +
  vision hparams). Trust boundary: mmproj files are downloaded model artifacts.
- Built in-tree (clang 18, libFuzzer+ASan+UBSan, coverage instrumentation in the
  library via -fsanitize=fuzzer-no-link). Two real findings: 0006 (scalar getter
  type-confusion abort, SIGABRT) and 0007 (block_count unbounded allocation,
  std::bad_alloc). Both confirmed in release, both fixed and submitted upstream.
- After neutralizing both as fuzz-blockers, 22.8M runs clean on the hparam surface
  (C-0035). A maintainer security-audit branch (xsn/security_audit_0) was
  concurrently active on the same file, independently validating target selection.

## LeRobot dataset-metadata loader (HuggingFace robotics) [EVALUATED - boundary exists, robust]

- Not in OSS-Fuzz (404). Real download-to-load boundary: LeRobotDatasetMetadata
  parses meta/info.json from a downloaded dataset via DatasetInfo.from_dict.
- Probed in-venv (Python 3.12, lerobot[dataset]). from_dict raises raw
  AttributeError/TypeError on malformed metadata (flax-tier robustness nit,
  C-0022), and total_episodes flows into list(range(...)) unbounded (C-0023) BUT
  the reachable site is dead on its only caller. No crash-tier finding. The
  "download DoS" hypothesis was raised and retracted after caller analysis.
- Outcome: largely robust (delegates to mature libs, guards the obvious cases).
  Two non-findings recorded; no report warranted.

## jax pickle_util [DECLINED - no defended boundary]

- jax/jaxlib/cloudpickle all 404 in OSS-Fuzz (unfuzzed), but jax._src.pickle_util
  .loads is a thin cloudpickle.loads passthrough for internal host callbacks.
  Pickle executes code by design; there is no safe-parse intent to violate.
- Declined (C-0042). Refines the target filter: "unfuzzed" is insufficient; a
  target needs a DEFENDED trust boundary where a crash/divergence is a genuine
  defect. minja and clip had one; raw pickle does not.

## gguf-py GGUFReader (llama.cpp Python GGUF reference reader) [SELECTED - yielded finding 0008]

- Not a dedicated OSS-Fuzz target (llamacpp's targets cover C++ loaders, not the
  Python gguf-py reader). gguf-py was named affected in the 2026-05-15 oss-sec GGUF
  advisory (V-01..V-06), confirming the component is an active class.
- Entry point: GGUFReader(path) which mmaps and parses an untrusted .gguf with its
  own offset/count/recursion logic. Trust boundary: GGUF files are downloaded.
- Fuzzed with Atheris (Python 3.12 venv; deps numpy, pyyaml). One finding: 0008,
  unbounded array-length loop (DoS), minimized to 49 bytes, confirmed via 5s
  timeout, and cross-impl grounded (C++ reader guards it, Python does not; C-0044).
- This is the Python-reader surface the project's C++ GGUF harness (no_alloc,
  gguf_init_from_buffer) did not and could not exercise, directly extending the
  re-scoped GGUF negative (see docs/RELATED-WORK.md).

### gguf-py reader: surface fully characterized (2026-08-19)

After finding 0008, the surface was mapped to completion: (1) a 2.2M-run negative
past 0008 with the width bound applied (C-0036); (2) a nested-array recursion
robustness gap (C-0024): the Python reader recurses per nesting level with no
depth guard and raises an uncaught RecursionError beyond Python's default limit
(~1000 levels), while the C++ reader rejects nested arrays as an invalid type and
does not recurse. The recursion gap is caller-catchable and fast-failing, a low
robustness nit, not a DoS. Net: one real finding (0008), one robustness
non-finding (C-0024), otherwise robust on the parsing surface. Tensor-data
materialization untested.

## huggingface_hub download/cache path-traversal [EVALUATED - defended boundary, negative]

- Not an OSS-Fuzz project, and the download boundary (repo-controlled filename ->
  local cache path) is the classic path-traversal surface. Real threat model:
  a malicious repo ships a crafted filename.
- Result: properly defended. _validate_relative_filename (_local_folder.py:199)
  rejects '..' segments, absolute/root, Windows drive, drive-relative, and UNC
  paths, checked under BOTH POSIX and Windows rules cross-OS (the docstring even
  addresses the UNC NetNTLMv2 hash-leak). Independently, _get_pointer_path
  (file_download.py:2056) containment-checks the final joined path against the
  snapshot dir. Two correct, independent layers.
- Deliberate design note: the containment check uses lexical abspath, not
  symlink-resolving resolve(); a symlink escape would need pre-existing attacker
  write access to the cache (out of threat model).
- Outcome: defended-boundary negative (C-0045). Not a productive input-fuzz target.
  Documented as a mapping of what is solid, and as good defensive work by the
  maintainers. Pivot to a softer surface (the quantize stage).

### gguf-py tensor path: hardened (2026-08-19)

Probed the tensor path (untested by the 0008 KV-focused harness). Huge declared
dims (2^32 x 2^32) fail cleanly with a numpy reshape ValueError (no hang/OOM);
the quant type is validated via an enum cast (unknown type -> ValueError); all 35
quant types have nonzero block_size and are present in GGML_QUANT_SIZES (no
div-by-zero at :338, no KeyError at :337); n_elems uses Python ints by design to
avoid uint64 overflow. Net on gguf-py: one finding (0008, KV array-length loop),
one recursion nit (C-0024), tensor path hardened (C-0037). Component thoroughly
mapped; pivoting to third-party quantizers where the SoK's empty cell likely is.
