# ExecuTorch program-loading M0 review packet

## Identity and scope

- Package ID and objective: R6-ET-M0-2026-09-09; determine whether a bounded
  target around ExecuTorch `Program::load`, program segments and verification
  modes has a defensible uncovered consumer boundary.
- Author/model and independent reviewer: Codex performed the source review; a
  separate Codex reviewer independently checked live heads, saved source/API
  evidence, report wording and the stop decision on 2026-09-09.
- Date, base SHA, implementation SHA or working-diff identity: 2026-09-09;
  `33de4573ae6044059bf154c9c72850f538527b45`; this report-only working diff.
- Worktree/branch and exact-head CI link/status:
  `/mnt/f/mapfuzz/audit-hardening-dev`, `daybreak-clip-qualification`; hosted CI
  unavailable because the local branch was not pushed. Local repository checks
  are recorded below.
- Disposition: **M0-STOP**
- What this disposition establishes and does not establish: current official
  source confirms a real `.pte` parser, loader-backed segment paths and distinct
  Minimal/InternalConsistency verification behavior. The complete public source
  tree names no fuzz target and ExecuTorch is absent from the inspected OSS-Fuzz
  revision. Official project records nevertheless confirm internal fuzzing and
  later fuzzer planning whose harness and coverage are unavailable. Therefore
  this M0 cannot establish an uncovered boundary, duplication, novelty, a defect,
  or authorization to build or fuzz.

## M0 and novelty boundary

| Source | Immutable revision and link | Retrieved date | Relevant path/entry point | Observation |
|---|---|---|---|---|
| Loader | ExecuTorch [`78c85d7553df47fb38c89ee3923e7123af54ac71`](https://github.com/pytorch/executorch/blob/78c85d7553df47fb38c89ee3923e7123af54ac71/runtime/executor/program.cpp#L73-L224) | 2026-09-09 | `Program::load`; [`Verification`](https://github.com/pytorch/executorch/blob/78c85d7553df47fb38c89ee3923e7123af54ac71/runtime/executor/program.h#L53-L99) | The default is `Minimal`. It checks alignment, minimum size, identifier, root offset and schema/selected segment relationships. `InternalConsistency` additionally runs FlatBuffers verification and `validate_program` when compiled in. |
| Segment consumer | same revision | 2026-09-09 | [`Program::load` constant segment](https://github.com/pytorch/executorch/blob/78c85d7553df47fb38c89ee3923e7123af54ac71/runtime/executor/program.cpp#L244-L321); [`Program::LoadSegment`](https://github.com/pytorch/executorch/blob/78c85d7553df47fb38c89ee3923e7123af54ac71/runtime/executor/program.cpp#L587-L623) | Program loading may synchronously request constant bytes. Later backend/mutable segment paths continue through the caller-supplied `DataLoader`. Method loading is a deeper, separately observable consumer. |
| Current source-tree inventory | complete Git tree for `78c85d7`, tree `b51fea7723fb293daafc5982095f20099e4a9374` | 2026-09-09 | 10,949 paths, API `truncated=false` | Zero path names contain `fuzz` or `fuzzer`, case-insensitive. This excludes only publicly named paths in this tree; it does not establish absence of generated, differently named, private or internal fuzzing. |
| Public OSS-Fuzz | OSS-Fuzz [`3209d05c48ad1232ab0c5797f6ed31a1486c2a80`](https://github.com/google/oss-fuzz/tree/3209d05c48ad1232ab0c5797f6ed31a1486c2a80/projects) | 2026-09-09 | `projects/executorch/project.yaml`; positive control `projects/sentencepiece/project.yaml` | Direct immutable lookup returned HTTP 404 for ExecuTorch and 200 for SentencePiece. Absence from OSS-Fuzz alone is not a coverage or novelty claim. |
| Existing fuzz work | [PR 1519](https://github.com/pytorch/executorch/pull/1519), [PR 11217](https://github.com/pytorch/executorch/pull/11217), [issue 15466](https://github.com/pytorch/executorch/issues/15466), [issue 15559](https://github.com/pytorch/executorch/issues/15559) | 2026-09-09 | missing Program arrays; `calculate_nbytes`; fuzzer planning/tasks | PR 1519 says the Program-array issue was found by “lionhead fuzzing”; PR 11217 says an overflow came from a fuzzer error. The two later issues explicitly track fuzzer work, and 15559 points to a document described as internal; this M0 did not obtain its harness details. The exact harness, corpus, modes and coverage cannot be compared. |
| Current hardening/prior art | [issue 16810](https://github.com/pytorch/executorch/issues/16810), merged [PR 18662](https://github.com/pytorch/executorch/pull/18662), merged [PR 19916](https://github.com/pytorch/executorch/pull/19916) | 2026-09-09 | safe PTE deserialization; overflow-safe bounds; null segment guards | The public project is actively hardening this boundary. These records do not prove complete coverage, but they make an uncovered/novel boundary especially unsafe to infer from public harness absence. |

The format boundary is caller-supplied `.pte` bytes passed through a
`DataLoader` to the edge runtime. Whether those bytes are attacker-controlled is
application-dependent; the official tutorials commonly show a model file chosen
by the application, not an asserted hostile network input. The supported consumer
sequence is `Program::load`, optional constant/other segment reads, metadata and
method lookup, then `Program::load_method`. A future qualification would have to
name exactly where it stops and distinguish FlatBuffer parsing, segment byte
loading, method construction, backend delegate initialization and execution.

The two verification modes are not equivalent by contract. The current
[`program_validation_test.cpp`](https://github.com/pytorch/executorch/blob/78c85d7553df47fb38c89ee3923e7123af54ac71/runtime/executor/test/program_validation_test.cpp#L215-L244)
explicitly expects a static tensor numel overflow to fail under
`InternalConsistency` and load successfully under `Minimal`. That documented
difference is a seed/control design input, not a defect. Tests also cover
truncation, corruption, bad root offset, alignment and several segment failures;
this M0 did not equate unit tests with fuzz coverage.

## Reproduction environment

Source-only reconnaissance ran from Ubuntu 22.04 WSL2 on x86_64 using Git 2.34.1,
`curl`, PowerShell JSON parsing and SHA-256. `git ls-remote` resolved official
heads; all inspected raw source and API responses were saved under ignored
`.runs/executorch-m0-2026-09-09/`. No dependency, compiler, submodule, package,
container, binary or exported model was installed or built.

The exact upstream head was
`78c85d7553df47fb38c89ee3923e7123af54ac71`, committed 2026-09-09 10:57:07Z.
The OSS-Fuzz head was `3209d05c48ad1232ab0c5797f6ed31a1486c2a80`.
No local patch exists. Fresh-build reproduction, toolchain selection, dependency
lock, binary hashes and seed hashes are **not run** because M0 stopped first.

## Semantic controls

| Benign/control input and hash | Expected milestone | Observed milestone/count | Source probe location | Exit/result | Local evidence |
|---|---|---|---|---|---|
| Valid minimal `.pte` | `Program::load` plus named method metadata | not run | not implemented | not run | M0 stopped before seed/build |
| Truncated/bad-root control | reject before FlatBuffer consumer access | not run | not implemented | not run | Upstream unit coverage inspected only |
| Valid program with appended constant segment | prove loader-backed segment bytes requested | not run | not implemented | not run | M0 stopped before seed/build |

No probe, seed, harness or target directory was created. In particular, this
report does not claim that parsing an identifier, returning `Error::Ok`, or
observing a descriptor proves method or backend consumption.

## Bounded runs and resource behavior

Qualification and mutation batches are **not run**. The shared one-worker,
4 GiB/no-swap, 5-second input, 60-second campaign and 90-second outer caps were
therefore not exercised. Attempts, accepted inputs, materialized segments, new
states/functions, elapsed time and peak resident memory are all **unavailable**,
not zero.

| Batch | Duration/limits | Attempts | Accepted | Materialized | New states/functions | Result/log hash |
|---|---|---|---|---|---|---|
| 1 | not run; M0 stop | unavailable | unavailable | unavailable | unavailable | unavailable |
| 2 | not run; M0 stop | unavailable | unavailable | unavailable | unavailable | unavailable |
| 3 | not run; M0 stop | unavailable | unavailable | unavailable | unavailable | unavailable |

## Independent review

- Exact commands replayed and environment differences: the reviewer repeated
  live `git ls-remote --symref` checks for ExecuTorch and OSS-Fuzz, immutable
  raw/API SHA-256 comparisons, the 404/200 OSS-Fuzz negative/positive controls,
  and local tree/source/test/hash/ignore checks. The environment matched Ubuntu
  22.04.5 WSL2 x86_64 and Git 2.34.1; the reviewer additionally recorded curl
  7.81.0.
- Benign/control outcomes compared with the author's report: not applicable;
  no build, harness, seed or control ran because M0 stopped.
- Core tests, workflow results and changed-code tests: Python 3.10 evidence 5/5,
  chassis 16/16 and triage 3/3 passed; the resource-oracle self-test passed;
  Python 3.12 resource tests passed 5/5. Evidence schema/render, repository and
  `git diff --check` checks passed. Hosted CI is unavailable for this unpushed
  branch.
- Exception handling, resource cleanup and instrumentation diff checked: no
  ExecuTorch target, patch, instrumentation, model, binary, build or fuzz
  artifact exists; only this report and roadmap changed.
- Private artifacts and accidental disclosures excluded from review diff: all
  public-source/API snapshots remain ignored under `.runs/`; reported paths and
  hashes matched. No reproducer or private artifact exists, the branch has no
  upstream, and no push, contact or publication occurred.
- Claims/render synchronization and scope wording checked: live official heads
  matched `78c85d7` and `3209d05`; the complete 10,949-entry, non-truncated tree
  contained zero fuzz-named paths; loader/test and PR/issue statements matched.
  No evidence claim is proposed.
- Unresolved contradictions or limitations: historical internal fuzz activity
  is established, but exact target, configuration, corpus, coverage and current
  operation remain unavailable. Public issue searches are incomplete and do not
  prove the absence of other work.

## Decision

**M0-STOP.** Current source establishes a meaningful parser and segment consumer,
but M0 requires comparison with actual existing harness call paths and coverage.
Official project records show that fuzzing has already found Program and size
validation defects and that later fuzzer work was coordinated through an internal
document. The current public tree and OSS-Fuzz checks cannot reveal that harness.
The proposed work is therefore neither proved duplicate nor proved uncovered.

Step 5 allocates **no build or fuzz compute**. The bounded next action is
maintainer review of this stop decision and explicit selection of a different M0
candidate. Do not contact ExecuTorch maintainers merely to fill this coverage gap,
do not create a target directory, and do not silently switch targets in this
package.

## Local evidence inventory

All paths are ignored and contain only public source or API responses:

- M0 observation summary:
  `.runs/executorch-m0-2026-09-09/m0-observations.txt`, SHA-256
  `cea2b01b8ea8569df3d0e1c599edc6047c8dea999314717b0161f714b82e415c`.
- Complete source tree API response: `executorch-tree.json`, SHA-256
  `92aed2dc75600e9bcd6fde246c0a50315999955035ad8413084b6c1c3dfd5ceb`.
- Loader source: `program.cpp`, SHA-256
  `c39fb2659405e38c90351e4b33415d2ce0f51897d5c6337dcc8eed7c054ffbdb`;
  `program.h`, SHA-256
  `ea859452b6e30e8ea3f0fb4c83896dc9ca3ecf2a5c1c8bb4a857d761e4dab034`.
- Upstream tests: `program_test.cpp`, SHA-256
  `6bb60459c95f3f41f4cf2875f5f8a01c64b9ebce836ee93dee5ab0539ab2323d`;
  `program_validation_test.cpp`, SHA-256
  `659b780aba9deca24b955288513bab0aaa9dd0e768e7d518c7add752489aa0e5`.
- OSS-Fuzz negative/positive snapshots:
  `oss-fuzz-executorch-project.yaml`, SHA-256
  `d5558cd419c8d46bdc958064cb97f963d1ea793866414c025906ec15033512ed`;
  `oss-fuzz-sentencepiece-project.yaml`, SHA-256
  `ece9329c97dee5fe140103552399a71d65bffdc21841ed37ed107e30d899d5a4`.
- Selected project records are `item-{1519,11217,15466,15559,16810,18662,19916}.json`;
  their hashes were recorded locally before this report. Raw issue searches are
  retained as `issues-*.json` and are not treated as exhaustive.

No external action was taken: no push, merge, publication, pull request, issue,
message or upstream contact.
