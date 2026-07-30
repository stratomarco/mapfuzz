# Model Artifact Parser Fuzzer: Requirements Specification (v1)

Working codename: `mapfuzz` (placeholder; rename in section 10).

Status: draft for review. Section 10 lists the decisions that must be confirmed before implementation begins.

---

## 1. Problem statement

Machine learning deployment introduced a new class of untrusted input that the classical security-engineering literature already tells us how to treat: the model artifact. A `.gguf`, `.safetensors`, `.onnx`, or `.pt` file downloaded from a public hub is attacker-controlled data fed into a parser, exactly like a PDF, a font, or a media container. The loaders that consume these files are large C, C++, and Rust codebases with the usual parser bug surface, plus a serialization-driven code-execution surface unique to the ML stack.

The area is under-fuzzed relative to its blast radius. In May 2026 a researcher disclosed six vulnerabilities in the llama.cpp GGUF parser to the oss-security list, found by manual review, none with a CVE at disclosure; the classes were textbook fuzzing targets (unbounded alignment value causing integer overflow, an enum deserialized without a bounds check, division by zero from a zero block size, gigabyte-scale unbounded allocations). That these were found by hand indicates no effective continuous, structure-aware fuzzer reaches those load paths. This mirrors the broader OSS-Fuzz picture, where mature projects still sit near 30% runtime coverage because harnesses fail to reach deep code, not because engines are weak.

Guiding thesis: ML security is an extension of classical security engineering. This project treats the model artifact as a file format, the loader as a parser, and the download-to-load transition as a trust boundary, then applies the established parser-fuzzing toolchain to the entire local-AI supply chain.

## 2. Goals and non-goals

### Goals

1. Provide a maintained, structure-aware, continuously running fuzzing suite for the parsers and loaders of the major model-artifact formats.
2. Reach the deep load paths that generic byte-level harnesses miss, using format-aware input generation.
3. Detect both memory-safety defects and the load-time code-execution class specific to model artifacts.
4. Produce reproducible, minimized crash artifacts suitable for coordinated disclosure and upstream fixes.
5. Be trivially adoptable by maintainers: standard engines, standard corpus formats, CI-native.

### Non-goals

1. Not a model-content scanner. Detecting a known-malicious pickle opcode signature is ModelScan/Fickling territory; this project fuzzes the loader for unknown defects rather than matching known-bad payloads.
2. Not a jailbreak or prompt-injection fuzzer. The target is the deserialization and parsing code, not model behavior.
3. Not a deep-learning compiler fuzzer. NNSmith, Tzer, OATest and related work already cover TVM, ONNXRuntime graph optimization, and TensorRT. This project targets the format loader, not the graph optimizer.
4. Not a training-pipeline or data-poisoning tool.

## 3. Target formats and loaders (scope)

Priority tiers govern implementation order. Tier 1 is the MVP surface.

| Tier | Format | Primary loader(s) | Language | Example entry point | Engine |
|------|--------|-------------------|----------|---------------------|--------|
| 1 | GGUF | llama.cpp / ggml; gguf-py | C/C++; Python | `gguf_init_from_file`; `GGUFReader` | libFuzzer / AFL++; Atheris |
| 1 | safetensors | safetensors (Rust core + Python binding) | Rust | `SafeTensors::deserialize` | cargo-fuzz (libFuzzer) |
| 2 | ONNX | onnx (protobuf); onnxruntime | C++/Python | `onnx.load`; ORT session init | libFuzzer + protobuf-aware mutator; Atheris |
| 2 | PyTorch | `torch.load` (zip + pickle) | Python/C++ | `torch.load`, incl. `weights_only` path | Atheris |
| 3 | TensorFlow SavedModel | `tf.saved_model.load` (protobuf) | C++/Python | `saved_model.pb` parse | protobuf-aware mutator |
| 3 | Keras | `.keras` / `.h5` (HDF5 + config) | Python/C | HDF5 parse; Lambda-layer config | Atheris; libFuzzer on libhdf5 |
| 2 | Tokenizer / vocab | HF tokenizers (Rust); SentencePiece; tiktoken | Rust/C++ | `Tokenizer::from_file`; SP model parse | cargo-fuzz; libFuzzer |

Entry-point symbols above are indicative and must be confirmed against current source during harness authoring (see REQ-F1). Vocabulary loading is explicitly in scope: the May 2026 advisory set included a buffer overflow reachable through vocab loading, so the tokenizer path is part of the artifact parser surface, not a separate concern.

## 4. Functional requirements

- **REQ-F1 Harness authoring.** For each in-scope loader, provide a fuzz harness that takes a raw byte buffer, writes it to the format's expected input channel (file path or memory buffer), and invokes the loader's real entry point with no pre-validation. Each harness must be verified to reach the parse routine (non-trivial edge coverage in a short smoke run) before it is accepted; a harness that only exercises argument checks is rejected.
- **REQ-F2 Structure-aware generation.** Where the format has an exploitable structure, the harness must use a format-aware mutator rather than raw byte flips:
  - ONNX and TensorFlow SavedModel are protobuf; use a protobuf-aware mutator (libprotobuf-mutator or equivalent) seeded from the schema so mutations survive the wire decoder and reach semantic handling.
  - safetensors has a JSON header followed by a binary blob; provide a grammar that keeps the header parseable while mutating declared shapes, dtypes, offsets, and the header-length prefix.
  - GGUF has a typed key/value metadata section followed by tensor descriptors; provide a grammar that mutates counts, type tags, string lengths, alignment, and offsets independently so single-field pathologies (the alignment-overflow class) are reachable.
- **REQ-F3 Seed corpus.** Ship a minimal valid artifact per format as a seed, plus a small set of structurally diverse valid samples. Seeds must contain no real proprietary weights; use tiny synthetic tensors.
- **REQ-F4 Sanitizer coverage.** Native harnesses (C/C++/Rust) must build and run under AddressSanitizer and UndefinedBehaviorSanitizer at minimum; MemorySanitizer where the toolchain permits. Rust targets additionally run under the default cargo-fuzz sanitizer set.
- **REQ-F5 Memory-safety oracle.** Detect out-of-bounds read and write, heap and stack overflow, use-after-free, integer overflow and underflow in size and offset computations, division by zero, and null-pointer dereference. These are delivered by the sanitizers plus engine crash detection.
- **REQ-F6 Resource-exhaustion oracle.** Detect unbounded or attacker-scaled allocations (allocation size taken from an untrusted field), decompression bombs on any compressed sub-stream, and pathological allocation counts. Enforce an allocation ceiling and a per-input timeout so these surface as findings rather than as fuzzer OOM kills.
- **REQ-F7 Type-confusion oracle.** Detect enum and tag values deserialized from the file and used without a bounds check, including downstream effects such as a size-lookup returning zero.
- **REQ-F8 Load-time code-execution oracle.** Detect the artifact-specific execution surface, treated as first-class findings distinct from memory bugs:
  - Pickle-based formats (`torch.load`, legacy checkpoints): flag any reachable `__reduce__` / opcode-driven callable invocation on the load path.
  - GGUF and other formats embedding chat templates: flag Jinja template evaluation that is not sandboxed, since template rendering at initialization is an execution primitive.
  - Path traversal via tensor names, external-data references, or archive member names that escape the intended directory on load.
- **REQ-F9 Crash triage.** Every finding must be automatically deduplicated (stack-hash based), minimized to the smallest reproducing input, and bucketed by bug class and crashing frame. Each bucket yields a standalone reproducer file plus a machine-readable record (format, loader, sanitizer report, minimized input hash).
- **REQ-F10 Continuous operation.** The suite must run as a continuous job (OSS-Fuzz or ClusterFuzzLite pattern): every target commit is fuzzed against the accumulated corpus, new crashes are deduplicated and bisected to a commit where feasible, and a fix is verified when the reproducer stops crashing.
- **REQ-F11 Corpus lifecycle.** Persist and version the corpus per target; support corpus minimization and cross-run merge so coverage compounds over time.

## 5. Non-functional requirements

- **REQ-N1 Reproducibility.** Any reported crash must reproduce deterministically from its minimized input on a pinned toolchain and target commit. Record all three (input, toolchain, commit) with every finding.
- **REQ-N2 Containment.** Fuzzing loaders that may execute embedded payloads is itself a code-execution risk. All runs execute in an isolated sandbox (container with no outbound network, non-root, read-only mounts except a scratch dir, seccomp where available). No harness may reach the public internet during a run.
- **REQ-N3 Portability and architecture coverage.** Primary platform is Linux x86_64. The suite must also support a 32-bit build target for classes that only manifest there; the GGUF alignment-overflow finding was 32-bit-specific, so dropping 32-bit would blind the suite to a confirmed real class.
- **REQ-N4 Licensing.** Project license must be permissive and OSS-Fuzz compatible; Apache-2.0 recommended for the patent grant. Confirm per-target license compatibility for any linked loader before shipping a harness (the tier-1 targets are MIT and Apache-2.0, which are compatible).
- **REQ-N5 No telemetry, no embedded metadata.** The tool emits no analytics and writes no tool-authorship or generator metadata into any output artifact or report.
- **REQ-N6 Reporting hygiene.** Findings intended for maintainers follow coordinated disclosure: private report first, embargo respected, public reproducer withheld until a fix ships or the embargo lapses.

## 6. Architecture requirements

- **REQ-A1 Engine per language.** Native C/C++ targets use libFuzzer or AFL++; Rust targets use cargo-fuzz; Python targets use Atheris. Structure-aware native targets pair the engine with a protobuf or custom-grammar mutator. Prefer engines already accepted by OSS-Fuzz so upstreaming is frictionless.
- **REQ-A2 Harness isolation.** Each loader gets its own harness binary and its own corpus; no shared global state across targets.
- **REQ-A3 Coverage collection.** Native builds instrument with the compiler's coverage feature (`-fsanitize=fuzzer` edge coverage); Python builds use Atheris coverage. Coverage per target is a tracked metric (REQ-M3).
- **REQ-A4 CI integration.** Provide a ClusterFuzzLite configuration so any adopting repo can run the suite in its own CI, plus an OSS-Fuzz project layout for the central continuous instance.
- **REQ-A5 Extensibility.** Adding a new format requires implementing a documented harness interface and, if structured, a grammar module; no changes to the core runner. Document this path so external contributors can add formats.

## 7. Bug classes targeted (summary)

Memory corruption: OOB read/write, heap/stack overflow, UAF, integer overflow/underflow on size and offset math, division by zero, null deref. Resource exhaustion: untrusted-field-driven allocation, decompression bombs, allocation-count blowups. Type confusion: unchecked enum/tag deserialization. Load-time execution: pickle reduce, unsandboxed template rendering, path traversal on load.

## 8. Deliverables and milestones

- **M0 Baseline audit.** Confirm, per tier-1 and tier-2 target, whether an OSS-Fuzz or ClusterFuzzLite integration already exists and what its current coverage and harness quality are. Output: a short matrix of target, existing coverage, and the specific load paths left unreached. This closes the open question in section 10 about positioning and prevents duplicated effort.
- **M1 MVP.** One format end to end: GGUF native loader, structure-aware grammar, ASan/UBSan, memory-safety and resource-exhaustion oracles, crash triage, local continuous run. Success gate: one independently reproducible finding, or a documented coverage result proving the load paths are exercised where prior fuzzing did not reach.
- **M2 Breadth.** safetensors and ONNX added, with the protobuf-aware path for ONNX and the header grammar for safetensors. Tokenizer/vocab loaders added.
- **M3 Execution oracles.** Pickle-reduce, template-render, and path-traversal oracles landed for the formats that carry those surfaces (PyTorch, GGUF, Keras).
- **M4 Continuous and adoptable.** ClusterFuzzLite config and OSS-Fuzz project layout published; corpus lifecycle and bisection automated; contributor docs for adding a format.

## 9. Success criteria and metrics

- **REQ-M1 First-blood.** A reproducible, previously-unknown finding in at least one tier-1 loader, minimized and disclosure-ready.
- **REQ-M2 Breadth.** Structure-aware harnesses for at least four formats across at least two implementation languages.
- **REQ-M3 Coverage.** Measured edge or line coverage per target, with a demonstrated increase over the pre-existing harness where one existed (ties directly to the ~30% baseline problem).
- **REQ-M4 Impact (north star).** Upstreamed fixes and assigned CVEs; number of accepted patches is the primary external success signal.
- **REQ-M5 Adoption.** At least one external repo running the ClusterFuzzLite config in its own CI.

## 10. Open decisions (confirm before build)

1. **Project name.** Codename `mapfuzz` is a placeholder.
2. **First target.** Recommended MVP target is GGUF native (highest confirmed bug density, clearest impact story). Confirm, or swap to safetensors if you prefer the Rust/cargo-fuzz path first.
3. **Central instance.** Upstream to Google OSS-Fuzz for free continuous compute, or run a self-hosted ClusterFuzzLite fleet for full control, or both. Recommendation: both, ClusterFuzzLite first for iteration speed, OSS-Fuzz for sustained compute.
4. **Load-time execution oracle in v1.** Recommendation: memory-safety and resource oracles in M1; defer the execution-oracle work to M3 so the MVP ships fast. Confirm this sequencing, or pull the pickle/template oracle forward if that class is the priority story.
5. **Differential-across-loaders oracle.** Out of scope for v1 here; slotted as the natural follow-on (the Option 4 idea). Confirm it stays deferred.

## 11. References

- Multiple vulnerabilities in the llama.cpp GGUF format parsers, oss-security advisory, 2026-05-15.
- GGML GGUF file format vulnerabilities, Databricks security research, 2024.
- Model poisoning and load-time execution surfaces (pickle, unsandboxed Jinja chat templates), Cloud Security Alliance research note, 2026.
- OSS-Fuzz continuous fuzzing program documentation and coverage baseline (~30% runtime coverage across integrated projects).
- libprotobuf-mutator (structure-aware protobuf fuzzing), Atheris (Python), cargo-fuzz (Rust), AFL++ and libFuzzer engines.
