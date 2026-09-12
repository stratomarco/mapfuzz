# Hugging Face Tokenizers current M0 review packet

## Identity and scope

- Package ID and objective: R9-TOKENIZERS-M0-2026-09-12; refresh the
  historical Rust Tokenizers target against current source and public records,
  then decide whether a bounded package can exercise a complementary
  tokenizer-construction state without rediscovering known load-time panics.
- Author/model and independent reviewer: Codex performed the source and public
  coverage review. Independent review was not run. The author checked the
  decision twice against pinned source, direct OSS-Fuzz path controls, official
  issues and pull requests, and the canonical local claims; this is
  corroboration, not independent replay.
- Date, base SHA, implementation SHA or working-diff identity: 2026-09-12;
  `e970cc5b3e1b23f5703355e735406be2d7b0cb19`; this report, roadmap, target
  inventory, target README and qualification-manifest working diff.
- Worktree/branch and exact-head CI link/status:
  `/mnt/f/mapfuzz/audit-hardening-dev`, `daybreak-tokenizers-m0`; hosted CI is
  unavailable because the local branch was not pushed. Local repository checks
  are recorded below.
- Disposition: **M0-STOP**
- What this disposition establishes and does not establish: current source
  confirms `Tokenizer::from_bytes` as the exact in-memory deserialization and
  construction consumer. No fuzz-named path was found in the complete current
  public tree, and the inspected OSS-Fuzz revision has no dedicated Tokenizers
  project. Those absences do not prove the boundary is unfuzzed. Two open
  official issues and three open fixes already cover a BPE construction panic
  at this load boundary, while canonical mapfuzz claims C-0001 through C-0003
  cover and bound the decoder/normalizer expect-on-deserialize class. The local
  harness is also pinned to 0.21.4 without a complete dependency lock. This M0
  therefore establishes no complementary current scope, no new finding, no
  complete-coverage claim and no authorization to build or fuzz.

## M0 and novelty boundary

| Source | Immutable revision and link | Retrieved date | Relevant path/entry point | Observation |
|---|---|---|---|---|
| Loader | Tokenizers [`6cfd9d385ca0ed91c10b49f0ce97d02cfde1b607`](https://github.com/huggingface/tokenizers/blob/6cfd9d385ca0ed91c10b49f0ce97d02cfde1b607/tokenizers/src/tokenizer/mod.rs#L468-L475) | 2026-09-12 | `Tokenizer::from_file`; `Tokenizer::from_bytes` | Both entry points deserialize the complete `Tokenizer`; `from_bytes` passes the supplied bytes directly to `serde_json::from_slice`. The current crate version is `0.23.2-dev.0`. |
| Current BPE construction | same revision, [`models/bpe/model.rs`](https://github.com/huggingface/tokenizers/blob/6cfd9d385ca0ed91c10b49f0ce97d02cfde1b607/tokenizers/src/models/bpe/model.rs#L251-L270) | 2026-09-12 | BPE builder merge-map construction | Construction sizes a scratch buffer from the longest vocab token, then copies the concatenated merge pieces into slices of that buffer. This is the current source path described by the public BPE panic reports. It was inspected, not executed. |
| Existing local component boundary | same revision, [`decoders/mod.rs`](https://github.com/huggingface/tokenizers/blob/6cfd9d385ca0ed91c10b49f0ce97d02cfde1b607/tokenizers/src/decoders/mod.rs#L84-L94) and [`normalizers/mod.rs`](https://github.com/huggingface/tokenizers/blob/6cfd9d385ca0ed91c10b49f0ce97d02cfde1b607/tokenizers/src/normalizers/mod.rs#L132-L146) | 2026-09-12 | decoder and Precompiled-normalizer deserialization | The two expect-on-deserialize sites represented by C-0001 and C-0002 remain in current source. C-0003 bounds the historically probed class to these component families; that bounded result is not a claim about all current code. |
| Current public source inventory | complete Git tree for `6cfd9d3`, tree response [`82844c0...`](https://api.github.com/repos/huggingface/tokenizers/git/trees/6cfd9d385ca0ed91c10b49f0ce97d02cfde1b607?recursive=1) | 2026-09-12 | 422 entries, API `truncated=false`; exact source archive, 336 files | No path name contains `fuzz`, `cargo-fuzz`, `afl`, `proptest` or `quickcheck`; the extracted archive has no `Cargo.lock`. This only excludes visibly named paths in the inspected public tree. |
| Public fuzz build and harness | OSS-Fuzz [`4e65aea32254fe988ac4b84dbb088d2d08d789e7`](https://github.com/google/oss-fuzz/tree/4e65aea32254fe988ac4b84dbb088d2d08d789e7/projects) | 2026-09-12 | `projects/tokenizers/project.yaml`; positive control `projects/sentencepiece/project.yaml` | Direct immutable lookup returned HTTP 404 for Tokenizers and 200 for SentencePiece. A second negative control, `projects/safetensors/project.yaml`, also returned 404, demonstrating why project absence alone cannot establish lack of in-repository fuzzing. |
| Public prior art/fix status | open [issue 2094](https://github.com/huggingface/tokenizers/issues/2094), open [issue 2198](https://github.com/huggingface/tokenizers/issues/2198) | 2026-09-12 | malicious/crafted `tokenizer.json`; BPE merge-map build | Both official reports describe a load-time process panic when merge concatenation exceeds the scratch buffer. They overlap the same consumer and low-severity denial-of-service class contemplated by a generic `from_bytes` target. |
| Public fixes | open [PR 2104](https://github.com/huggingface/tokenizers/pull/2104), open [PR 2219](https://github.com/huggingface/tokenizers/pull/2219), open [PR 2333](https://github.com/huggingface/tokenizers/pull/2333) | 2026-09-12 | BPE merge validation | Three unmerged official pull requests propose returning an error instead of panicking for the same malformed-merge condition. Their open state makes this an active public dedup boundary, not a mapfuzz finding. |
| Local harness and lock | tracked `targets/tokenizers/fuzz/Cargo.toml` and `fuzz_targets/from_bytes.rs` | 2026-09-12 | `tokenizers = "=0.21.4"`; one-call generic harness | The harness ignores the result of `Tokenizer::from_bytes`. It has no `fuzz/Cargo.lock`, is not pinned to current main, and records no named current component milestone. It remains historical regression material, not a current qualification environment. |

The defended boundary is a `tokenizer.json` supplied with a model or otherwise
selected by an application and parsed into a supported Rust `Tokenizer`. It is
data deserialization rather than an interface intended to execute arbitrary
code. The exact current consumer is `serde_json::from_slice` followed by the
component-specific `Deserialize` and builder paths needed to construct the
returned tokenizer. A JSON-accepted counter alone would not show which model,
normalizer, pre-tokenizer, processor or decoder was constructed.

There is a narrow public inventory gap: no fuzz-named path was found in the
complete current tree and the exact OSS-Fuzz project path is absent. That does
not establish a novelty or coverage gap. Public records already cover the
current BPE load-time panic and proposed fixes. The project evidence base
separately contains verified, reported decoder and Precompiled-normalizer
load-time panics plus a bounded component-family probe. A generic `from_bytes`
campaign would therefore be predisposed to rediscover known low-severity
denial-of-service behavior.

M0 found no narrower model or component state with an independently stated
consumer milestone, earlier-failing control and dedup rule. The stale direct
crate pin and missing transitive lock independently fail the current
reproducibility prerequisite. Per the package stop rules, source/public
inspection stops here before build or replay.

## Reproduction environment

Source-only reconnaissance ran on Ubuntu 22.04.5 WSL2 x86_64, Linux
6.6.87.2, with Git 2.34.1, Python 3.10.12 and curl 7.81.0. Official heads,
complete-tree metadata, exact source archive, direct OSS-Fuzz path responses,
and official issue/pull-request API responses were retained under ignored
`.runs/next-m0-2026-09-12/` and hashed with SHA-256.

The exact Tokenizers head was
`6cfd9d385ca0ed91c10b49f0ce97d02cfde1b607`, committed 2026-09-03
12:01:53Z. The source archive SHA-256 is
`4ab44da3ae45af06bcd2182d9abd8ae89eb80d3fd49f74ca1a69a475b1df3e96`.
The exact OSS-Fuzz head was
`4e65aea32254fe988ac4b84dbb088d2d08d789e7`, committed 2026-09-11
14:51:38Z. The current upstream files name the Rust channel only as `stable`;
the tracked local target has neither a dated toolchain nor a complete
`fuzz/Cargo.lock`.

No dependency, compiler, cargo-fuzz tool, package, container or binary was
installed or built. No local upstream patch exists. Fresh-directory replay,
sanitizer selection, binary and seed hashes, and dependency resolution are
**not run** because M0 stopped first. Historical target artifacts were not
treated as current replay evidence.

## Semantic controls

| Benign/control input and hash | Expected milestone | Observed milestone/count | Source probe location | Exit/result | Local evidence |
|---|---|---|---|---|---|
| Current valid tokenizer with a newly named complementary component | JSON accepted and named component constructed | not run | not implemented | not run | M0 found no complementary component/state |
| Malformed metadata for that component | distinct rejection before the component-construction milestone | not run | not implemented | not run | M0 stopped before seed or probe design |
| Structurally valid but incomplete component | JSON accepted, then a defined construction error distinct from known panic families | not run | not implemented | not run | M0 stopped before build/replay |

No current seed, control, probe, harness or target directory was created. The
six tracked synthetic seeds and the generic 0.21.4 harness are historical
regression inputs only. Source inspection does not claim they construct the
same component states on current main.

## Bounded runs and resource behavior

Qualification and mutation batches are **not run**. The shared one-worker,
4 GiB/no-swap, 5-second input, 60-second campaign and 90-second outer caps were
not exercised. Attempts, accepted inputs, materialized/constructed inputs, new
states/functions, elapsed time and peak resident memory are all
**unavailable**, not zero.

| Batch | Duration/limits | Attempts | Accepted | Materialized | New states/functions | Result/log hash |
|---|---|---|---|---|---|---|
| 1 | not run; M0 stop | unavailable | unavailable | unavailable | unavailable | unavailable |
| 2 | not run; M0 stop | unavailable | unavailable | unavailable | unavailable | unavailable |
| 3 | not run; M0 stop | unavailable | unavailable | unavailable | unavailable | unavailable |

## Independent review

- Exact commands replayed by reviewer and environment differences: independent
  review was not run. The author repeated the source-to-consumer comparison,
  checked the complete official tree and extracted archive, used direct
  OSS-Fuzz negative and positive path controls, and compared official current
  issues/fixes with the canonical local claim boundaries.
- Benign/control outcomes compared with the author's report: not applicable; no
  current build, seed or control ran because M0 stopped.
- Core tests, workflow results and changed-code tests: two complete Python 3.10
  passes each reported evidence 5/5, chassis 16/16 and triage 3/3; both resource
  oracle self-tests, evidence schema/render checks, repository/manifest checks
  and `git diff --check` passed. Python 3.12 resource tests passed 5/5 twice.
  Hosted CI is unavailable for this unpushed branch.
- Exception handling, resource cleanup and instrumentation diff checked: no
  target, build, patch, instrumentation or runtime resource exists; only the
  brief, report and portfolio status documentation changed.
- Private artifacts and accidental disclosures excluded from review diff: raw
  inputs are official public source and metadata retained under ignored
  `.runs/`. No private reproducer, report contents or credential was copied.
- Claims/render synchronization and scope wording checked: existing C-0001
  through C-0003 are cited only as the local dedup boundary; no claim update is
  proposed. OSS-Fuzz/public-tree absence is not presented as proof of no other
  fuzzing.
- Unresolved contradictions or limitations: search and path-name inventories
  are not exhaustive; private, differently named or external fuzz work may
  exist. The public BPE condition and current historical findings were not
  reproduced in this package. Current issues and pull requests may change after
  the retrieval date.

## Decision

**M0-STOP.** The current `Tokenizer::from_bytes` consumer and a realistic
model-supplied-data boundary are established, but a defensible complementary
scope is not. Active official BPE reports and fixes cover the current load-time
panic class, and the canonical mapfuzz evidence already covers and bounds the
decoder/normalizer expect-on-deserialize class. The generic local target is
stale and lacks the dependency lock needed for current reproduction.

Allocate **no build, replay or fuzz compute**. The bounded next action is to
keep the historical target in regression maintenance. Reopen qualification only
after the active BPE issue/fix state changes and a separate brief names a
non-BPE, non-decoder, non-Precompiled-normalizer component state, a current
locked environment, a valid positive seed, an earlier-failing control and an
independent dedup rationale. Do not reproduce public reports, contact
maintainers, create an external issue or pull request, or silently switch
targets in this package.

## Local evidence inventory

All paths are ignored and contain only public source or API responses:

- Tokenizers commit and complete tree responses: `tokenizers-commit.json`,
  SHA-256
  `794f3bef8ec5d55c1802de65276839db15078e371ab1c2b12a4feb91f2899cc3`;
  `tokenizers-tree.json`, SHA-256
  `82844c011677e879c4756547c8e54df4255a8be36246cc2c3cadc90a0e3576d7`.
- Exact source archive: `tokenizers-source.tar.gz`, SHA-256
  `4ab44da3ae45af06bcd2182d9abd8ae89eb80d3fd49f74ca1a69a475b1df3e96`.
  Exact inspected source hashes are
  `38e8a0755d0c1c627bf532a28d6030413ee719c855fb1a807e1d3a647b62d56c`
  (`tokenizer/mod.rs`),
  `550f2d0fa8f0ecd27013a0787d8343c961e83a724fc09f7d596c695220f72429`
  (`models/bpe/model.rs`),
  `9963dedcd9a965ae80888e72a7d83fbe2ee1c4f426b313cf1b7014c384419a08`
  (`decoders/mod.rs`) and
  `93bbbae1b8885989b0163ad4e4141aeb0676928e6754e6a3d010f205f712cdd2`
  (`normalizers/mod.rs`).
- OSS-Fuzz commit response: `oss-fuzz-commit.json`, SHA-256
  `7bbb320a5ffed8a43aaa171c676f8a9ca8a06ee6c157bf31d9586d85040779cc`.
  Direct negative/positive status and response snapshots are
  `oss-fuzz-direct-status.txt`, SHA-256
  `024ba79a41f4c60cffb33f024cf531522931bbeb41173bf4171ac483268c4b6d`,
  and `oss-fuzz-controls.txt`, SHA-256
  `a04caa0806972d0f81b7cea5f97273ade79471e6e535bc5485ac3b341789c35b`.
- Official public records: `issue-2094.json`, SHA-256
  `ae8a7bb1d34bb1711d076a060a534c452e69ed0ea3852a0c4d8ec52359cd54d7`;
  `issue-2198.json`, SHA-256
  `35abc25645febc525f3d080ea3876674bb1cc4ecf04cfb3b7c274f4827f3df33`;
  `pr-2104.json`, SHA-256
  `7ea606d26d93ae9b013be47499343c29e1fe1b6d668640980e4462fe1e51e633`;
  `pr-2219.json`, SHA-256
  `f4c02110fa642b3851169458e36058beddbc32b2d144ea6b7f5b588253cfbd13`;
  and `pr-2333.json`, SHA-256
  `b358dcf368131cc47138e1c3c2aa5252e35180461fd8e262a8195f9cca9f5762`.
  Timeline and search snapshots are retained but are not treated as exhaustive.

No external action was taken: no push, merge, publication, pull request, issue,
message or upstream contact.
