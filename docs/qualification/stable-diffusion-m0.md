# stable-diffusion.cpp model-reconciliation M0 review packet

## Identity and scope

- Package ID and objective: R6-SD-M0-2026-09-09; determine whether a bounded
  target around stable-diffusion.cpp model metadata, tensor-name conversion and
  cross-artifact shape/type reconciliation has a defensible uncovered consumer
  boundary without duplicating generic container work.
- Author/model and independent reviewer: Codex performed the source and public
  coverage review. Independent review was not run. The same conclusions were
  checked twice against pinned source and separately retrieved official project
  records; that is corroboration, not independent reproduction.
- Date, base SHA, implementation SHA or working-diff identity: 2026-09-09;
  `4fbb4a58acb93cd9bc1f6059151062ab82745360`; this report-and-roadmap working
  diff.
- Worktree/branch and exact-head CI link/status:
  `/mnt/f/mapfuzz/audit-hardening-dev`, `daybreak-stable-diffusion-m0`; hosted CI
  unavailable because this local branch was not pushed. Local repository checks
  are recorded below.
- Disposition: **M0-STOP**
- What this disposition establishes and does not establish: current official
  source confirms a real multi-file consumer boundary spanning format dispatch,
  model-family detection, tensor-name normalization, model component
  registration and metadata validation. The complete public tree names no fuzz
  target and the project is absent from the inspected OSS-Fuzz revision.
  Official project records nevertheless document fuzz-derived malformed-model
  faults, including one open ASan-confirmed safetensors shape-product issue with
  an open fix, and public failures in the same name/shape reconciliation path.
  The existing fuzz harness, corpus and coverage are unavailable. This M0
  therefore cannot establish an uncovered boundary, duplication, novelty, a new
  defect or authorization to build or fuzz.

## M0 and novelty boundary

| Source | Immutable revision and link | Retrieved date | Relevant path/entry point | Observation |
|---|---|---|---|---|
| Loader and normalization | stable-diffusion.cpp [`d04e8950c1ec8d30248cbe996682b3182fb1adf6`](https://github.com/leejet/stable-diffusion.cpp/blob/d04e8950c1ec8d30248cbe996682b3182fb1adf6/src/model_io/model_loader.cpp#L171-L212) | 2026-09-09 | `ModelLoader::init_from_file`; `convert_tensors_name` | The loader dispatches directories, GGUF, safetensors indexes/files and Torch zip/legacy inputs. After prefixing companion artifacts, it converts names into one map keyed by the converted name. |
| Supported consumer | same revision | 2026-09-09 | [`init_model_loader`](https://github.com/leejet/stable-diffusion.cpp/blob/d04e8950c1ec8d30248cbe996682b3182fb1adf6/src/stable-diffusion.cpp#L719-L870); [`validate_registered_tensors`](https://github.com/leejet/stable-diffusion.cpp/blob/d04e8950c1ec8d30248cbe996682b3182fb1adf6/src/model_io/model_manager.cpp#L343-L356) | Caller-selected main, diffusion, text-encoder, VAE and other companion paths are prefixed and normalized together. Constructed model components register expected tensors, then `ModelManager` rejects missing or wrong-shape metadata before parameter loading. |
| Current source-tree inventory | complete Git tree for `d04e895`, tree `e75222091ea943c3f5d204f3d9642b4f1aee2ecc` | 2026-09-09 | 467 paths, API `truncated=false` | Zero path names contain `fuzz` or `fuzzer`, case-insensitive. This excludes only publicly named paths in this tree; it does not establish absence of private, ad hoc, generated or differently named fuzzing. |
| Public OSS-Fuzz | OSS-Fuzz [`3209d05c48ad1232ab0c5797f6ed31a1486c2a80`](https://github.com/google/oss-fuzz/tree/3209d05c48ad1232ab0c5797f6ed31a1486c2a80/projects) | 2026-09-09 | `projects/stable-diffusion.cpp/project.yaml`; positive control `projects/sentencepiece/project.yaml` | Direct immutable lookup returned HTTP 404 for stable-diffusion.cpp and 200 for SentencePiece. Absence from OSS-Fuzz alone is not a coverage or novelty claim. |
| Existing fuzz work and fixed prior art | [issue 1396](https://github.com/leejet/stable-diffusion.cpp/issues/1396), [issue 1749](https://github.com/leejet/stable-diffusion.cpp/issues/1749) | 2026-09-09 | malformed safetensors size metadata; duplicate-name imatrix loader | Issue 1396 explicitly reports a malformed-model abort found by fuzz testing; current pinned source returns an error on that size mismatch. Issue 1749 explicitly reports fuzzing a separate binary loader. Neither record exposes a reusable harness, seed corpus, sanitizer configuration or coverage map. |
| Current same-boundary prior art | open [issue 1876](https://github.com/leejet/stable-diffusion.cpp/issues/1876), open [PR 1875](https://github.com/leejet/stable-diffusion.cpp/pull/1875), open [issue 1812](https://github.com/leejet/stable-diffusion.cpp/issues/1812) | 2026-09-09 | safetensors dimension/product validation; companion-artifact name/shape validation | Issue 1876 and PR 1875 document an ASan-confirmed denial-of-service from a signed shape-product wrap. The fix remains open, and pinned source still performs unchecked signed products. Issue 1812 records real companion-layout name/shape mismatches rejected by `ModelManager`. These are public prior art, not mapfuzz findings. |
| Current name-path control | closed [issue 1949](https://github.com/leejet/stable-diffusion.cpp/issues/1949) | 2026-09-09 | long fully qualified LLM tensor name | The report initially appeared to implicate name construction, but the reporter resolved it by using a current release after maintainers identified a mismatched ggml build. It is a useful false-positive/control example, not evidence of a current loader defect. |

The application supplies local model and companion-artifact paths. Whether an
untrusted party controls those bytes is deployment-dependent; the CLI itself
does not establish a remote trust boundary. The proposed semantic sequence was:
format metadata accepted, artifact prefixes applied, model family detected,
names converted into the shared tensor map, a selected model component
registered, metadata shapes/types validated, and selected tensor bytes loaded.
Generic JSON, GGUF, safetensors, zip or pickle parsing without those later
stable-diffusion-specific milestones would duplicate container-level work.

The current source provides the intended later consumer. `init_model_loader`
combines many optional model artifacts before name conversion, and
`validate_registered_tensors` compares registered component tensors with the
normalized metadata map. The current safetensors reader, however, also retains
the exact public issue 1876 prerequisite: it reads signed dimensions without a
positive/range check and `TensorStorage::nelements()` multiplies them in signed
`int64_t`. Reproducing or rediscovering that already disclosed condition would
not satisfy novelty or target qualification.

Public tree and OSS-Fuzz absence cannot resolve the comparison. At least two
official issue bodies say fuzzing found loader faults, but they do not identify
the maintained harness call path or coverage. Consequently this M0 cannot tell
whether a new model-reconciliation harness would be complementary, overlapping
or merely a repackaging of existing ad hoc work. Per the roadmap, an uncertain
coverage boundary is an M0 stop.

## Reproduction environment

Source-only reconnaissance ran from Ubuntu 22.04.5 WSL2 on x86_64 with Linux
6.6.87.2 and Python 3.10.12. Official heads were resolved with `git ls-remote`;
raw source, complete-tree metadata and GitHub API responses were saved under
ignored `.runs/stable-diffusion-m0-2026-09-09/` and hashed with SHA-256.

The exact upstream head was
`d04e8950c1ec8d30248cbe996682b3182fb1adf6`, committed 2026-09-07 16:23:08Z.
The OSS-Fuzz head was `3209d05c48ad1232ab0c5797f6ed31a1486c2a80`.
No dependency, compiler, submodule, package, container, binary or model was
installed or built. No local upstream patch exists. Fresh-build reproduction,
toolchain selection, dependency locks, binary hashes and seed hashes are **not
run** because M0 stopped first.

## Semantic controls

| Benign/control input and hash | Expected milestone | Observed milestone/count | Source probe location | Exit/result | Local evidence |
|---|---|---|---|---|---|
| Valid synthetic multi-artifact model | name conversion, model-family detection, component registration, metadata validation and selected tensor-byte load | not run | not implemented | not run | M0 stopped before architecture/seed selection |
| Malformed metadata | reject before registration or allocation | not run | not implemented | not run | Public fixed and open prior art inspected only |
| Missing/truncated companion tensor | metadata accepted, then fail distinctly at registration validation or byte read | not run | not implemented | not run | M0 stopped before seed/build |

No harness, seed, probe or target directory was created. In particular, this
report does not claim that format recognition, a metadata descriptor, a
converted map key or a successful `init_from_file` return proves component
construction or tensor-byte consumption.

## Bounded runs and resource behavior

Qualification and mutation batches are **not run**. The shared one-worker,
4 GiB/no-swap, 5-second input, 60-second campaign and 90-second outer caps were
therefore not exercised. Attempts, accepted inputs, materialized inputs, new
states/functions, elapsed time and peak resident memory are all **unavailable**,
not zero.

| Batch | Duration/limits | Attempts | Accepted | Materialized | New states/functions | Result/log hash |
|---|---|---|---|---|---|---|
| 1 | not run; M0 stop | unavailable | unavailable | unavailable | unavailable | unavailable |
| 2 | not run; M0 stop | unavailable | unavailable | unavailable | unavailable | unavailable |
| 3 | not run; M0 stop | unavailable | unavailable | unavailable | unavailable | unavailable |

## Independent review

- Exact commands replayed by reviewer and environment differences: independent
  review was not run. The author repeated live upstream/OSS-Fuzz head checks,
  parsed saved official API responses, compared hashes, and re-read the pinned
  dispatch, normalization, reader, manager and consumer paths.
- Benign/control outcomes compared with the author's report: not applicable; no
  build, harness, seed or control ran because M0 stopped.
- Core tests, workflow results and changed-code tests: two complete Python 3.10
  passes each reported evidence 5/5, chassis 16/16 and triage 3/3; both resource
  oracle self-tests, evidence schema/render checks, repository checks and
  `git diff --check` passed. Python 3.12 resource tests passed 5/5 twice. Hosted
  CI is unavailable for this unpushed branch.
- Exception handling, resource cleanup and instrumentation diff checked: no
  target, build, model, patch, instrumentation or runtime resource exists; only
  this report and the roadmap changed.
- Private artifacts and accidental disclosures excluded from review diff: raw
  public source/API snapshots remain ignored under `.runs/`. No private model,
  reproducer or credential was created or added. No external action occurred.
- Claims/render synchronization and scope wording checked: no evidence claim is
  proposed. Public prior art is explicitly separated from mapfuzz observations.
- Unresolved contradictions or limitations: official issue bodies establish
  fuzz-derived faults, but the exact harness, corpus, sanitizer configuration,
  coverage and current operation remain unavailable. GitHub searches are not
  exhaustive. The open public shape-overflow report was not reproduced locally.

## Decision

**M0-STOP.** Current source establishes a meaningful stable-diffusion-specific
model-reconciliation consumer after generic container parsing. Official project
records also establish fuzz-derived malformed-model work and public failures on
the same shape/name boundary, including an unresolved, already disclosed
ASan-confirmed condition. Because the actual existing harness and coverage
cannot be compared, the proposed target is neither proved duplicate nor proved
uncovered. Building a new harness now would risk spending compute on public
prior art and cannot satisfy the roadmap's M0 gate.

Step 5 allocates **no build or fuzz compute**. The bounded next action is review
of this stop decision followed by explicit selection of the next roadmap M0,
currently the current llama.cpp Jinja candidate. Do not create a
stable-diffusion.cpp target directory, rediscover the public issue, contact
maintainers or silently switch targets in this package.

## Local evidence inventory

All paths are ignored and contain only public source or API responses:

- Complete source tree API response: `tree.json`, SHA-256
  `c84f37353e2ca1593eb139b4a78cb11da8198b1cde7b56233c26a0988e5f37c4`.
- Loader/consumer source: `model_loader.cpp`, SHA-256
  `c05404cc0fe6e4ba0a93c6a22bb03325f0154454201819b6b5408f9140630db1`;
  `model_manager.cpp`, SHA-256
  `55eb22938881605ab81dc02d4fee7c9f71fe90f6551e1ec18010d58acd3d48b5`;
  `stable-diffusion.cpp`, SHA-256
  `fb8b02948d26fa0d32d6c51a64c5b17795cb164a15b152a3e0622bad9c33d807`.
- Format and tensor source: `safetensors_io.cpp`, SHA-256
  `c9427ff41e446ae4f35a44fba04fd03864d969b201f67f117c595b967046f7dd`;
  `pickle_io.cpp`, SHA-256
  `4aea00c9450bed89c7ed5622e208268550538b8116e0c52090cee64f3c1a8a6a`;
  `torch_zip_io.cpp`, SHA-256
  `4cd613f63aab6b7465f9108703654a84df0582d2682551a2f69830963d88101c`;
  `tensor_storage.h`, SHA-256
  `aaf282fbf7b310fbaa3cf2e17e51ee13d63a75f88742b920b9b96e5eff32d9ce`.
- OSS-Fuzz negative/positive snapshots: `oss-fuzz-project.yaml`, SHA-256
  `d5558cd419c8d46bdc958064cb97f963d1ea793866414c025906ec15033512ed`;
  `oss-fuzz-sentencepiece.yaml`, SHA-256
  `ece9329c97dee5fe140103552399a71d65bffdc21841ed37ed107e30d899d5a4`.
- Selected official records are `issue-{1396,1749,1796,1812,1876,1949}.json`,
  their comment snapshots, and `pr-1875.json`. Search snapshots are retained as
  `issues-*.json` and `prs-model-loader.json`; they are not treated as exhaustive.

No external action was taken: no push, merge, publication, pull request, issue,
message or upstream contact.
