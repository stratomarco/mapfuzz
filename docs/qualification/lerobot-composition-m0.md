# LeRobot dataset-composition M0 review packet

## Identity and scope

- Package ID and objective: R6-LEROBOT-COMPOSITION-M0-2026-09-10;
  determine whether a bounded target around LeRobot v3 metadata, episode maps,
  Parquet rows, tasks and video references has a defensible project-specific
  consumer boundary beyond delegated file-format fuzzing.
- Author/model and independent reviewer: Codex performed the source and public
  coverage review. Independent review was not run. The author checked the
  boundary twice against pinned source, the complete source tree, official
  OSS-Fuzz definitions and separately retrieved official project records; that
  is corroboration, not independent replay.
- Date, base SHA, implementation SHA or working-diff identity: 2026-09-10;
  `525d907569548c8c44a02fb58a150268d3b784d3`; this report, roadmap, target
  inventory, manifest record and documentation-only target directory.
- Worktree/branch and exact-head CI link/status:
  `/mnt/f/mapfuzz/audit-hardening-dev`, `daybreak-lerobot-m0`; hosted CI is
  unavailable because this local branch was not pushed. Local repository checks
  are recorded below.
- Disposition: **QUALIFIED for M0 only; compute paused**
- What this disposition establishes and does not establish: current official
  source confirms a supported composition path from `info.json`, tasks and
  episode metadata through metadata-derived Parquet schemas, row materialization,
  task lookup, optional timestamp-driven video decoding and a training
  `DataLoader`. The complete pinned tree contains no fuzz-named path or source
  reference, and LeRobot is absent from the pinned OSS-Fuzz project path. Arrow
  and FFmpeg fuzz their own formats, but not LeRobot's cross-file relationships.
  This establishes a useful candidate boundary for a separately approved
  build/seed package. It does not establish a defect, novelty, runtime
  reachability, security impact, or permission to build or fuzz now.

## M0 and novelty boundary

| Source | Immutable revision and link | Retrieved date | Relevant path/entry point | Observation |
|---|---|---|---|---|
| Metadata loader and schema | LeRobot [`71a11efe77f55e61f3ab2ce45b40da8cf626afa9`](https://github.com/huggingface/lerobot/blob/71a11efe77f55e61f3ab2ce45b40da8cf626afa9/src/lerobot/datasets/dataset_metadata.py#L64-L149) | 2026-09-10 | `LeRobotDatasetMetadata`; [`DatasetInfo`](https://github.com/huggingface/lerobot/blob/71a11efe77f55e61f3ab2ce45b40da8cf626afa9/src/lerobot/datasets/utils.py#L156-L241) | `info.json` becomes a typed dataset description. It supplies feature types/shapes, counts, storage format and data/video path templates; tasks and episode Parquet are then loaded. |
| Cross-file mapping | same revision | 2026-09-10 | [`get_data_file_path` / `get_video_file_path`](https://github.com/huggingface/lerobot/blob/71a11efe77f55e61f3ab2ce45b40da8cf626afa9/src/lerobot/datasets/dataset_metadata.py#L311-L359); [`load_episodes`](https://github.com/huggingface/lerobot/blob/71a11efe77f55e61f3ab2ce45b40da8cf626afa9/src/lerobot/datasets/io_utils.py#L212-L218) | Episode rows select chunk/file indices for data and each video key. This is LeRobot-specific reconciliation across independent metadata and payload files. |
| Parquet row consumer | same revision | 2026-09-10 | [`DatasetReader._load_hf_dataset`](https://github.com/huggingface/lerobot/blob/71a11efe77f55e61f3ab2ce45b40da8cf626afa9/src/lerobot/datasets/dataset_reader.py#L225-L254); [`get_hf_features_from_features`](https://github.com/huggingface/lerobot/blob/71a11efe77f55e61f3ab2ce45b40da8cf626afa9/src/lerobot/datasets/feature_utils.py#L39-L80) | Metadata features are converted to a Hugging Face schema and applied while loading nested Parquet shards. A row becomes tensors; its `episode_index`, frame index and `task_index` drive later composition. |
| Video/task consumer | same revision | 2026-09-10 | [`DatasetReader.get_item`](https://github.com/huggingface/lerobot/blob/71a11efe77f55e61f3ab2ce45b40da8cf626afa9/src/lerobot/datasets/dataset_reader.py#L418-L463); [`_query_videos`](https://github.com/huggingface/lerobot/blob/71a11efe77f55e61f3ab2ce45b40da8cf626afa9/src/lerobot/datasets/dataset_reader.py#L376-L416) | One sample combines a data row, episode bounds, delta indices, task-table lookup and optional frames decoded at metadata-derived timestamps. Successful Parquet parsing alone does not reach this milestone. |
| Supported training consumer | same revision | 2026-09-10 | [`make_dataset`](https://github.com/huggingface/lerobot/blob/71a11efe77f55e61f3ab2ce45b40da8cf626afa9/src/lerobot/datasets/factory.py#L105-L174); [`lerobot_train.py`](https://github.com/huggingface/lerobot/blob/71a11efe77f55e61f3ab2ce45b40da8cf626afa9/src/lerobot/scripts/lerobot_train.py#L441-L447) | The official training path creates the selected dataset and later wraps it in a PyTorch `DataLoader`. Dataset metadata also configures policy/reward-model construction. |
| Current source-tree inventory | complete tree for `71a11ef`, tree `15a6928b38e3693b1a35d6459f22e684abd7cc61` | 2026-09-10 | 1,277 paths, API `truncated=false` | Zero path names contain `fuzz`, `fuzzer`, `atheris` or `hypothesis`. A second full-source search found only ignored `.hypothesis/` directories, not a fuzz harness or property-based test. This does not exclude private, downstream or differently named work. |
| Public OSS-Fuzz | OSS-Fuzz [`3209d05c48ad1232ab0c5797f6ed31a1486c2a80`](https://github.com/google/oss-fuzz/tree/3209d05c48ad1232ab0c5797f6ed31a1486c2a80/projects) | 2026-09-10 | `projects/lerobot/project.yaml`; positive controls `projects/arrow` and `projects/ffmpeg` | Direct immutable lookup returned 404 for LeRobot and 200 for Arrow and FFmpeg. Project-list absence alone is not proof that LeRobot has never been fuzzed. |
| Delegated Parquet coverage | OSS-Fuzz `3209d05`; Arrow [`926885f1b1ede73badd24c2e6f63c9429441e99a`](https://github.com/apache/arrow/blob/926885f1b1ede73badd24c2e6f63c9429441e99a/cpp/src/parquet/arrow/fuzz.cc#L22-L25) | 2026-09-10 | [`projects/arrow/build.sh`](https://github.com/google/oss-fuzz/blob/3209d05c48ad1232ab0c5797f6ed31a1486c2a80/projects/arrow/build.sh#L79-L84); Parquet reader/encoding fuzzers | Arrow currently provides Parquet reader and encoding fuzz targets, and OSS-Fuzz copies its `*-fuzz` binaries. This covers format parsing/encoding, not LeRobot's metadata-derived schema, episode mapping, task lookup or multi-file agreement. |
| Delegated video coverage | OSS-Fuzz `3209d05` | 2026-09-10 | [`projects/ffmpeg/build.sh`](https://github.com/google/oss-fuzz/blob/3209d05c48ad1232ab0c5797f6ed31a1486c2a80/projects/ffmpeg/build.sh#L218-L386) | FFmpeg builds decoder, demuxer and IO-demuxer fuzzers. That does not exercise LeRobot's episode-to-video mapping, timestamp shifts, tolerance policy, task/data composition or training use. |
| Same-boundary project prior art | open [issue 4143](https://github.com/huggingface/lerobot/issues/4143), open [PR 4561](https://github.com/huggingface/lerobot/pull/4561), open/reopened [issue 3788](https://github.com/huggingface/lerobot/issues/3788) | 2026-09-10 | corrupted episode lengths; incomplete episode metadata/boundary drift; stale task statistics | Official records confirm that cross-file disagreement can silently misassign frames, leave datasets unloadable or desynchronize task statistics. These exact conditions are public prior art and must be controls/dedup exclusions, not future novelty claims. |
| Schema/video/revision prior art | completed [issue 3513](https://github.com/huggingface/lerobot/issues/3513), open [PR 3552](https://github.com/huggingface/lerobot/pull/3552), completed [issue 3224](https://github.com/huggingface/lerobot/issues/3224), merged [PR 3807](https://github.com/huggingface/lerobot/pull/3807), closed-unmerged [PR 3833](https://github.com/huggingface/lerobot/pull/3833) | 2026-09-10 | timestamp/frame index; nested arrays; revision safety; row groups; scalar/vector ambiguity | Current public work spans the proposed seam but exposes no maintained generative harness, corpus or coverage map. Known timestamp, nested-array, revision, row-group and scalar-shape cases are excluded from novelty. Their existence supports a reconciliation oracle; it does not itself prove a new target will find a defect. |

The conditional trust boundary is a third-party or locally supplied LeRobot v3
dataset that an operator explicitly selects for training, evaluation, editing or
visualization. Hub, bucket and local modes can supply the metadata and payloads.
This is not an unauthenticated network service boundary. Potential consequences
are initially limited to data-loader denial of service, wrong sample/task/video
composition and training-data integrity. No code execution, model compromise or
physical-robot impact is established.

The qualifying boundary begins after generic JSON/Parquet/MP4 recognition. The
named sequence is: `DatasetInfo` accepted; tasks and episodes loaded; episode
chunk/file references resolved; metadata features converted to the Parquet
schema; at least one row materialized to tensors; row and episode indices agree;
`task_index` resolves to the intended task; and, in the video phase, a referenced
frame is decoded within tolerance. Training consumption is shown by the same
sample reaching a one-worker `DataLoader`, not by policy execution.

This is complementary to the inspected public fuzzing because Arrow receives one
Parquet byte stream and FFmpeg receives codec/container bytes, while the proposed
driver mutates relationships among several otherwise valid files. LeRobot's
large deterministic test suite covers normal dataset operations and selected
regressions, but the current tree exposes no maintained generative driver for
malformed cross-artifact combinations. Absence from names and one public service
is not proof of total fuzzing absence, so novelty must still be checked per fault.

Public prior art narrows the work. A future corpus must label and deduplicate the
known corrupted-length, missing-finalize/boundary-drift, stale-task-stat,
timestamp-out-of-range, nested-array, revision-race, row-group and scalar/vector
cases. Reproducing any of them is a regression result, not a new finding.

## Reproduction environment

Source-only reconnaissance ran on Ubuntu 22.04.5 WSL2 x86_64, Linux
6.6.87.2, with Git 2.34.1, Python 3.10.12 and curl 7.81.0. LeRobot itself
requires Python 3.12 or newer. Official heads were resolved with
`git ls-remote`; exact source archives, complete-tree metadata, source/API
snapshots and OSS-Fuzz definitions were retained under ignored
`.runs/lerobot-m0-2026-09-10/` and hashed with SHA-256.

The exact LeRobot head was
`71a11efe77f55e61f3ab2ce45b40da8cf626afa9`, committed 2026-09-09 16:07:45Z.
Its complete tree contained 1,277 entries and was not truncated. The exact
OSS-Fuzz head was `3209d05c48ad1232ab0c5797f6ed31a1486c2a80`.
The Arrow comparison used current official head
`926885f1b1ede73badd24c2e6f63c9429441e99a` only to inventory delegated Parquet
fuzzers. No dependency, compiler, package, container, dataset or binary was
installed or built. No upstream patch exists. Fresh-environment resolution from
the tracked `uv.lock`, binary/package hashes and seed hashes are **not run**
because this package ends at M0.

## Semantic controls

| Benign/control input and hash | Expected milestone | Observed milestone/count | Source probe location | Exit/result | Local evidence |
|---|---|---|---|---|---|
| Minimal valid v3 bundle: `info.json`, one task row, one episode row and one data-Parquet row | metadata accepted; episode/data mapping resolved; row tensorized; task string resolved; one-worker DataLoader yields one sample | not run | not implemented | not run | M0 only; next package must generate and hash it |
| Invalid `info.json` or feature rank | reject in `DatasetInfo` or metadata-to-HF-schema conversion before payload materialization | not run | not implemented | not run | source guards inspected only |
| Missing/truncated episode or data shard | metadata acceptance remains distinguishable from episode/Parquet failure | not run | not implemented | not run | M0 only |
| Cross-file index/schema mismatch | fail distinctly for feature schema, episode bounds or task index; never count as a composed sample | not run | not implemented | not run | known public cases define regression exclusions |
| Valid one-frame video plus missing/out-of-tolerance control | valid reference decodes one frame; missing/truncated/timestamp failure remains distinct | not run | not implemented | not run | video is a second semantic phase, not required for the initial no-video seed |

No harness, probe, seed, dependency environment or executable target was
created. In particular, parsing metadata, opening a Parquet file or decoding an
MP4 alone does not satisfy the composition milestone.

## Bounded runs and resource behavior

Qualification and mutation batches are **not run**. The shared one-worker,
4 GiB/no-swap, 5-second input, 60-second campaign and 90-second outer caps were
not exercised. Attempts, accepted datasets, composed samples, decoded videos,
new states/functions, elapsed time and peak resident memory are all
**unavailable**, not zero.

| Batch | Duration/limits | Attempts | Accepted | Materialized | New states/functions | Result/log hash |
|---|---|---|---|---|---|---|
| 1 | not run; M0-only package | unavailable | unavailable | unavailable | unavailable | unavailable |
| 2 | not run; M0-only package | unavailable | unavailable | unavailable | unavailable | unavailable |
| 3 | not run; M0-only package | unavailable | unavailable | unavailable | unavailable | unavailable |

## Independent review

- Exact commands replayed by reviewer and environment differences: independent
  review was not run. The author repeated official head checks, source-to-test
  tracing and complete-tree fuzz-name searches, and separately compared official
  LeRobot, Arrow, FFmpeg and OSS-Fuzz sources.
- Benign/control outcomes compared with the author's report: not applicable; no
  environment, seed, harness or control ran in this M0-only package.
- Core tests, workflow results and changed-code tests: two complete Python 3.10
  passes each reported evidence 5/5, chassis 16/16 and triage 3/3; both resource
  oracle self-tests, evidence schema/render checks, 10-target repository/manifest
  checks and `git diff --check` passed. Python 3.12 resource tests passed 5/5
  twice. Hosted CI is unavailable for this unpushed branch.
- Exception handling, resource cleanup and instrumentation diff checked: no
  LeRobot code, instrumentation, parser, decoder or cleanup behavior changed.
- Private artifacts and accidental disclosures excluded from review diff: all
  retained inputs are official public source/API snapshots under ignored
  `.runs/`; no dataset, reproducer, token or credential was created or added.
- Claims/render synchronization and scope wording checked: no evidence-ledger
  claim is proposed. Public project issues are prior art, not mapfuzz findings.
- Unresolved contradictions or limitations: named public-tree and OSS-Fuzz
  absence does not exclude private or differently named fuzzing. The GitHub
  search endpoint rate-limited one final video query; selected video prior art
  was already present in the successful dataset/metadata searches. No public
  issue search is exhaustive, and no reported condition was reproduced.

## Decision

**QUALIFIED for M0 only; compute paused.** Current source establishes a
project-specific composition consumer after delegated JSON, Parquet and video
parsing. The complete pinned tree and OSS-Fuzz comparison expose no LeRobot
fuzzer, while Arrow and FFmpeg targets stop below the metadata/episode/data/task
relationships used by LeRobot training. Public same-boundary bugs make the
reconciliation oracle concrete and also define cases that must not be presented
as new.

The bounded next action is a separately reviewed build-and-seed brief. It must
use the pinned Python 3.12+ `uv.lock`, create a fresh local environment, generate
a tiny tracked no-video v3 bundle, prove the metadata→episode→data→task→one-worker
DataLoader milestone, and run the listed negative controls. Video is a second
phase only after that gate. This report authorizes **no dependency installation,
build, seed execution or fuzz campaign**. Do not contact maintainers, reproduce
public reports or infer a security finding from source alone.

## Local evidence inventory

All paths are ignored and contain only public source or API responses:

- LeRobot commit and complete tree responses: `commit.json`, SHA-256
  `15a35c71e68fd584a313102c91585bb0cb0e37317bac10ceacbc710ba5c7661a`;
  `tree.json`, SHA-256
  `207c001c8537c0ff9d7606d1578986df453b111544604f78afffcb51b4fd84f2`.
- Exact LeRobot archive: `lerobot-71a11ef.tar.gz`, SHA-256
  `b0bb1866b7879e7307221fb7822c54a41cf1234a754de878f4bf5de1e18136d5`.
- Dependency inputs: `pyproject.toml`, SHA-256
  `d67a60c007eeb4401b29818d99a6ad94aa28c1f10beabdcf77c4da5d97f8e326`;
  `uv.lock`, SHA-256
  `4a56d47d2edfdc159bd137c854d37033028f38c4d9d57ec98284d8fce9ea2ccc`.
- Core source hashes: `dataset_metadata.py`
  `6f521ae70b89874027cbd0029b62da14f77958f551ded643b996b9a7db2b66df`;
  `dataset_reader.py`
  `b3fae3e9974011e12346638cf89cb8af9b362088581051dd2f0c694e24046230`;
  `io_utils.py`
  `af08c7875f34f8469f80c4fd903af12971d6fa96c179be984887b93ef2f6f91c`;
  `feature_utils.py`
  `c73e79ec70d9bcf751b8604f709546219fa90fe7010ac9c4e882f863f18b41c2`.
- OSS-Fuzz definitions: `oss-fuzz-arrow-build.txt`
  `e88c1ec3be22fc0e33136b63fda81357a48174abe9cafc9027a18c24ac9bd4f9`;
  `oss-fuzz-ffmpeg-build.txt`
  `8bc4a619c6df6fb1833ad3169fcc189256a67faa8d7871e9f90dc517985ad8ae`;
  LeRobot 404 body `d5558cd419c8d46bdc958064cb97f963d1ea793866414c025906ec15033512ed`.
- Official search snapshots: `issues-fuzz.json`
  `c9938edecb99d754b2d039ac9eec320a94c769b6a6417921e2dcbef9e2fe01a0`;
  `issues-dataset-parquet.json`
  `e0845d4b6a71d89d3e683195b12495ba3a4462a609df77d18f217b557aca1ea6`;
  `issues-metadata-validation.json`
  `5e50403a271d2cfd764f366665a1dad924df05731cbbf04add65b9a1b0aff922`.
  Selected records are retained separately; searches are not treated as exhaustive.

No external action was taken: no push, merge, publication, pull request, issue,
message or upstream contact.
