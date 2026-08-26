# Related work and positioning

Honest positioning of mapfuzz against existing published work. Written after an
M0 on the project itself (2026-08-17): checking what already exists before
claiming novelty. The short version: the general "ML supply chain is an attack
surface" framing is established prior art and is NOT claimed here; the GGUF core
parser is a crowded, active CVE target and our result there is a deliberately
scoped negative, not a safety claim; the defensible contribution is active
fuzzing at the under-examined conversion/quantization/native-multimodal
boundaries, plus a reproducible, provenance-preserving methodology.

## Prior work this project does NOT claim to originate

### Supply-chain framing (SoK and precursors)
"SoK: Understanding Vulnerabilities in the LLM Supply Chain" (arXiv 2502.12497)
systematizes 529 already-reported CVEs across 75 projects and 13 lifecycle
stages, with a CWE-based root-cause taxonomy (improper resource control ~46%,
improper neutralization ~25%, access control ~12%). It establishes the
supply-chain-as-attack-surface agenda. mapfuzz does not claim to originate this
framing. Two facts from that SoK directly motivate mapfuzz instead:
- Its method is RETROSPECTIVE (crawling vulnerability databases and labeling
  known CVEs). It finds no new bugs. Active discovery by fuzzing is orthogonal
  and complementary.
- Its own data shows the Model Quantization and Model Inference stages are the
  least populated (about 1.3% each), and it explicitly notes that model files
  fetched from remote locations make taint sources hard for static analysis.
  Those are precisely the under-examined surfaces mapfuzz targets by fuzzing.

### GGUF core parser (active, crowded CVE target)
The GGUF container parser has a long and active memory-safety history. Fuzzing or
auditing the GGUF core is NOT novel and is well covered by others:
- Talos 2024 (TALOS-2024-1913/1914/1915): three heap buffer overflows in the
  GGUF parser (gguf_fread_str, the ne dimension field, the n_tensors counter),
  all arbitrary-code-execution class.
- CVE-2025-53630: integer overflow in gguf_init_from_file_impl, heap OOB R/W.
- CVE-2026-27940 (GHSA-3p4r-fq3f-q74v, CVSS 7.8): a bypass of the 2025 fix, same
  function, undersized heap allocation from unguarded size addition; patched b8146.
- oss-sec V-01..V-06 (2026-05-15): six more (GGML_PAD alignment integer overflow,
  string-length, n_dims, gguf_type bounds, zero blck_size division), all GGUF
  versions since v3 and gguf-py.
- Bleeding Llama (CVE-2026-7482, CVSS 9.1): heap OOB read in Ollama's GGUF loader.
- An SGLang GGUF load-path RCE.

mapfuzz's GGUF result is a NEGATIVE deliberately scoped to metadata/tensor-
descriptor parsing with no_alloc=true at commit 432d7ffe. That configuration
skips allocation and therefore does not exercise the allocation-size-computation
path where the entire CVE class above lives. The negative is accurate for its
surface and is explicitly NOT a claim that GGUF loading is memory-safe. See the
GGUF claim boundary in evidence/claims.yaml.

### Composition / config-as-code at the loader-runtime seam (active, disclosed)
A distinct and severe class lives at the seam between a component that validates a
model config as data and a later component that turns config-named classes into
running code. In 2026 a set of high-severity CVEs (the FaceHugger set:
CVE-2026-44513, CVE-2026-44827, CVE-2026-45804, plus the parallel transformers
config-injection CVE-2026-4372) disclosed exactly this: a config file names
component classes, one layer validates it as well-formed, a later layer loads and
runs it, and the trust check sat in a different phase than the code load (a TOCTOU
across the seam). CVE-2026-44827 is the DDUF case, a model package declaring a
standard-looking class name while achieving code execution. These are fixed in
diffusers 0.38.0.

mapfuzz does NOT claim this class. It is recorded here as prior art and as method
validation: an independent composition-angle pass on the DDUF-to-diffusers seam
reached the same import-from-config surface before the public disclosure was
found (evidence C-0047). That convergence corroborates the seam thesis but the
findings are not ours. The popular libraries in this class (diffusers,
transformers) are now actively researched, so novel work should target quieter
component pairs or a different bug class.

## What this project does claim as its contribution

### 1. Active fuzzing at the under-examined boundaries
The SoK's emptiest cells (quantization, conversion, inference/native runtime) and
the model-file loading boundary are where mapfuzz fuzzes. Concretely, findings at
newer / less-covered surfaces that are not in the crowded GGUF-core CVE set:
- tokenizers (HuggingFace, Rust): panic-on-load class, findings 0002/0003,
  reported.
- minja (llama.cpp C++ chat-template engine): unbounded-recursion stack overflow
  and integer div/mod by zero, findings 0004/0005, Google-validated, PR #92.
- clip/mmproj (llama.cpp multimodal projector loader): scalar type-confusion abort
  and block_count unbounded allocation, findings 0006/0007, PR to ggml-org with a
  regression test. The mmproj loader is not in the llama.cpp OSS-Fuzz target list.

### 2. The left half of the chain is unprobed by anyone, including us
Verified against the full OSS-Fuzz project list (1372 projects, 2026-08-17): none
of huggingface_hub, auto-gptq, autoawq, bitsandbytes, optimum are OSS-Fuzz
projects. Combined with the SoK's near-empty quantization/conversion cells, the
convert and quantize stages are an attacker-reachable, essentially unfuzzed
surface. This is the prioritized direction (see docs/THREAT-MODEL.md), and it is
NOT covered by the retrospective SoK or the GGUF-core fuzzing others have done.

### 3. The seam-checking pattern holds across layers, not just file loaders
Probing the serving layer (vLLM v1, 2026-08-19) extended the thesis beyond file
loading. The sampling-parameter token-id seam, where a request field becomes an
index into the logits or vocab, is defended by a model-aware validator that runs
once vocab size is known (evidence C-0049). This is the same pattern found in the
file loaders: the check lives where the needed context exists, not at the request
layer that cannot know it. The observation is that "valid for whose purpose" is a
cross-layer principle, demonstrated from GGUF metadata parsing up through
inference-server request handling, and that mature ML infrastructure defends
itself by deferring each check to the boundary where it can be made. This
reframes the contribution from a loader-specific result to a cross-layer one.

### 4. A reproducible, provenance-preserving methodology
Independent of any single finding: a deterministic evidence base (every claim
carries provenance, an explicit boundary, and a status; negatives must state
effort; a validator gates the schema), honest severity calibration (robustness
nits and UBSan-only UB are recorded as non-findings, not inflated), coordinated
disclosure discipline (reproducers embargoed until fixed), and a target-selection
technique (check a project's OSS-Fuzz build.sh target LIST, not just membership;
in-OSS-Fuzz projects with entry points absent from that list are the richest
vein, this is how clip/mmproj was found). Security research in this space is
mostly point-in-time CVE disclosure; a maintained, continuous, reproducible
fuzzing method with recorded negatives is the process contribution.

The community itself has independently articulated the motivation for a
continuous method: the public GGUF advisories note that a parser of this size
accretes overflow bugs, one fix rarely closes the class, and re-checking the
build you actually run is necessary. That is the argument for continuous fuzzing,
which is what this project is built to be.

## Honest limitations of the novelty claim
- The tool (harnesses on libFuzzer/Atheris/cargo-fuzz) is a competent application
  of standard fuzzers, not a new fuzzing engine.
- The supply-chain concept is not ours (see the SoK).
- The GGUF-core surface is crowded; our contribution there is a scoped negative.
- The novelty rests on WHERE we fuzz (under-examined boundaries), the SPECIFIC
  new findings at newer surfaces, and the METHODOLOGY, not on inventing a
  category. That is a narrower and defensible claim, and it is the one made here.
