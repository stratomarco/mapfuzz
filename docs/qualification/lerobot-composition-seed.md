# LeRobot dataset-composition R7 review packet

## Identity and scope

- Package ID and objective: `R7-LEROBOT-COMPOSITION-SEED-2026-09-11`; build a
  fresh locked LeRobot environment and prove one deterministic no-video v3
  sample through metadata, episode metadata, Parquet row materialization, task
  lookup and a one-worker `DataLoader`.
- Author/model and independent reviewer: Codex implemented and replayed the
  package. Independent review was **not run**. Two fresh author replays and two
  focused-test passes are corroboration, not independent review.
- Date, base SHA, implementation SHA or working-diff identity: work executed
  2026-09-10 through 2026-09-11; M0 base
  `3d723e46508cc25a16a6ceacb957042616faa304`; brief checkpoints `4d5f4ce`,
  `f9a0b48` and `a62521b`; implementation
  `f6818dba3707e194926827691dea6912cc2cbd11`. This report and status updates
  are the following documentation diff.
- Worktree/branch and exact-head CI link/status:
  `/mnt/f/mapfuzz/audit-hardening-dev`, `daybreak-lerobot-r7`. Hosted CI is
  unavailable because the branch remains local and unpushed. Local checks are
  recorded below.
- Disposition: **QUALIFIED for the no-video R7 seed; COMPUTE PAUSED before video**
- What this disposition establishes and does not establish: the pinned public
  API and lock reproducibly generate a one-frame dataset whose returned
  PyTorch tensors, indices, task string and one-worker batch match fixed values.
  Four malformed relationship controls stop at their expected earlier stages.
  This does not establish a vulnerability, novelty, broad dataset compatibility,
  safe video handling, policy/training execution or permission to fuzz.

## M0 and novelty boundary

| Source | Immutable revision and link | Retrieved date | Relevant path/entry point | Observation |
|---|---|---|---|---|
| Loader and writer | LeRobot [`71a11efe77f55e61f3ab2ce45b40da8cf626afa9`](https://github.com/huggingface/lerobot/blob/71a11efe77f55e61f3ab2ce45b40da8cf626afa9/src/lerobot/datasets/lerobot_dataset.py#L475-L532) | 2026-09-10 | `LeRobotDataset.create`, `add_frame`, `save_episode`, `finalize` | The official writer produced the seed. The official constructor and reader reopened it locally. No upstream patch was applied. |
| Metadata and schema | same revision | 2026-09-10 | [`LeRobotDatasetMetadata`](https://github.com/huggingface/lerobot/blob/71a11efe77f55e61f3ab2ce45b40da8cf626afa9/src/lerobot/datasets/dataset_metadata.py#L64-L149); [`DatasetInfo`](https://github.com/huggingface/lerobot/blob/71a11efe77f55e61f3ab2ce45b40da8cf626afa9/src/lerobot/datasets/utils.py#L156-L241) | `info.json`, tasks and episode metadata are accepted before the probe asks the dataset reader for a Parquet row. |
| Row/task consumer | same revision | 2026-09-10 | [`DatasetReader.get_item`](https://github.com/huggingface/lerobot/blob/71a11efe77f55e61f3ab2ce45b40da8cf626afa9/src/lerobot/datasets/dataset_reader.py#L418-L463) | The row's episode/frame/task indices drive composition; `task_index` is resolved only after the row is returned as tensors. |
| Supported downstream consumer | same revision | 2026-09-10 | [`lerobot_train.py`](https://github.com/huggingface/lerobot/blob/71a11efe77f55e61f3ab2ce45b40da8cf626afa9/src/lerobot/scripts/lerobot_train.py#L335-L352) | The qualification uses the same PyTorch `DataLoader` class with one worker, but does not create a policy or run training. |
| Public fuzz build and harness | OSS-Fuzz [`3209d05c48ad1232ab0c5797f6ed31a1486c2a80`](https://github.com/google/oss-fuzz/tree/3209d05c48ad1232ab0c5797f6ed31a1486c2a80/projects) | 2026-09-10 | LeRobot absent; Arrow and FFmpeg positive controls | R6 found no public LeRobot target at the pinned path. Arrow/FFmpeg cover their formats, not these cross-file relationships. This is absence of observed coverage, not proof no other fuzzing exists. |
| Public same-boundary cases | LeRobot issues/PRs catalogued in the [R6 packet](lerobot-composition-m0.md) | 2026-09-10 | episode lengths, incomplete metadata, task stats, timestamps, nested arrays, revision, row groups and scalar/vector shape | These remain regression/dedup exclusions. R7 did not reproduce them or identify a new fault. |

The trust boundary is a third-party or local LeRobot v3 dataset that an operator
explicitly selects for training, evaluation, editing or visualization. It is not
an unauthenticated service boundary. R7 starts with individually valid JSON and
Parquet artifacts, then tests their LeRobot-specific agreement. Hub access was
disabled during replay. A missing local shard caused LeRobot's Hub fallback to
raise `OfflineModeIsEnabled`; that is a control outcome, not a finding.

## Reproduction environment

The final environment was Ubuntu 22.04.5 WSL2 x86_64, Linux
6.6.87.2-microsoft-standard-WSL2, Python 3.12.13 and upstream-pinned
`uv 0.11.30`. The `uv` executable SHA-256 was
`9a4299a0c3bcc01012acbcdae7b5655e5087e0e5d87459306736a1420a902b81`.
The exact LeRobot archive SHA-256 was
`b0bb1866b7879e7307221fb7822c54a41cf1234a754de878f4bf5de1e18136d5`;
`pyproject.toml` was
`d67a60c007eeb4401b29818d99a6ad94aa28c1f10beabdcf77c4da5d97f8e326`;
and `uv.lock` was
`4a56d47d2edfdc159bd137c854d37033028f38c4d9d57ec98284d8fce9ea2ccc`.

The resolved core packages were LeRobot 0.6.2 from the fresh source,
PyTorch 2.11.0+cu128, TorchVision 0.26.0+cu128, TorchCodec 0.11.1,
PyArrow 25.0.1, datasets 4.8.5, pandas 2.3.3, NumPy 2.2.6 and PyAV 15.1.0.
The official Linux lock includes CUDA packages; execution set
`CUDA_VISIBLE_DEVICES=''`, and the positive probe reported CUDA unavailable.
No GPU was used. The explicit `pyav` selection avoids irrelevant TorchCodec
probing in this no-video phase; no frame was decoded.

The first environment was extracted fresh from the retained verified archive
and resolved with:

```bash
env UV_PROJECT_ENVIRONMENT=/mnt/f/mapfuzz/audit-hardening-dev/.runs/lerobot-r7-2026-09-10/env \
  UV_CACHE_DIR=/mnt/f/mapfuzz/audit-hardening-dev/.runs/lerobot-r7-2026-09-10/uv-cache \
  ../uv-bootstrap/bin/uv sync --locked --extra dataset --extra test --no-dev
```

The tracked bootstrap was then replayed into a second empty source, cache and
environment root under a 600-second host timeout. It exited zero in 154.74
seconds. Raw package manifests differ only in the expected editable source path;
after replacing that path with `<fresh-source>`, both manifests were byte
identical with SHA-256
`7c486f14cd5ec680c1a996c8915bf248dc9a9ec74da4eb3a89a0cb8c92415178`.
The second `UV_CACHE_DIR` was empty and did not reuse the first dependency
cache. Possible host pip-cache reuse for the `uv` bootstrap wheel was not
instrumented.

The valid bundle is generated, not tracked. Both fresh generations were byte
identical in this locked environment:

| File | Bytes | SHA-256 |
|---|---:|---|
| `data/chunk-000/file-000.parquet` | 3,775 | `68223838485fc3ff9dd1581d9109ea7f22b84efb051253876a9193a249caa5fa` |
| `meta/episodes/chunk-000/file-000.parquet` | 34,688 | `4d1f641e50c96941e86b880eb23a264c2ac8ea144e1111bfa4fa0271606eb513` |
| `meta/info.json` | 1,446 | `1a47dadadda2f3c5493ff218d5cd1749e66e278cc57e94b4e8b216f4a40e0dcc` |
| `meta/stats.json` | 3,586 | `49da8356a343194679b5d7f46f5a06e5b3f9a6f34ffecaab5ab0179dc25df183` |
| `meta/tasks.parquet` | 2,070 | `ee79c6f7d46e6c0a74f8148266a5b39d1761987ef615a3205c16bf5cc8ded584` |

The frame values are float32 `observation.state=[1.0, 2.0]` and
`action=[0.25, -0.25]`, with task `move test object`, FPS 10, one frame and one
episode. Cross-version byte identity is not claimed.

## Semantic controls

| Benign/control input and hash | Expected milestone | Observed milestone/count | Source probe location | Exit/result | Local evidence |
|---|---|---|---|---|---|
| Valid bundle; data hash `682238…a5fa` | all six milestones and one worker batch | 1 metadata dataset, 1 episode, 1 Parquet row, 1 materialized row, 1 task, 1 batch | `qualification.py:125-201` | 0 / qualified twice | `controls-pass1b.json`, `controls-pass2.json` |
| FPS-zero `info.json`; `6d7c9e…e9c1` | reject before metadata acceptance | last stage `start`; 0 accepted datasets | `qualification.py:129-148` | 2 / `ValueError` twice | same logs |
| Missing data shard; valid info `1a47da…0dcc` | metadata/tables accepted; no row | last stage `metadata_tables_loaded`; 0 materialized rows | `qualification.py:150-171` | 2 / `OfflineModeIsEnabled` twice | same logs; offline mode blocked Hub fallback |
| 32-byte data shard; `6dd135…f620` | metadata/tables accepted; Parquet rejected | last stage `metadata_tables_loaded`; 0 materialized rows | `qualification.py:150-171` | 2 / `ArrowInvalid` twice | same logs |
| Valid Parquet with `task_index=1`; `283d37…21e6` | row materializes; task lookup fails | last stage `row_materialized`; 1 materialized row, 0 tasks/batches | `qualification.py:162-184` | 2 / `IndexError` twice | same logs |

The probe first invokes the real metadata object, then the real dataset and its
Hugging Face dataset, then `dataset[0]`, and finally PyTorch's one-worker
`DataLoader`. It observes returned objects and does not patch upstream. Here,
materialization means the public reader returned float32 `torch.Tensor` objects
with verified values and indices. Whether Arrow copied, mapped or deferred the
underlying pages was not instrumented and is not claimed.

`MemoryError` is re-raised. Per-replay timeout raises a non-success orchestration
error. Negative return codes are reported as signals. Other exceptions produce
a rejected JSON result and CLI exit 2, never exit-zero acceptance. A focused
forced-timeout test and `MemoryError` test passed twice. No sanitizer was used in
this Python-only package.

## Bounded runs and resource behavior

Each matrix used a new root, five generated datasets, CPU-only execution, one
frame per dataset, one `DataLoader` worker, a 60-second Python child timeout and
a 360-second GNU `timeout` around the full suite. Each pass attempted five
datasets; four reached accepted metadata, two materialized a row, one resolved a
task and one yielded a batch. These are dataset-case denominators, not fuzz
executions. No mutation attempt occurred.

GNU `time` observed peak RSS but did not enforce a hard memory ceiling. Pass 1
reported 886,576 KiB and pass 2 885,440 KiB. These are maximum-process
observations for the outer command, not aggregate concurrent RSS. The no-video
brief did not authorize a campaign, so the shared 4 GiB/no-swap campaign cgroup
was not invoked. The per-child and outer time limits were effective; a forced
0.001-second replay timeout failed nonzero in both focused-test passes.

| Batch | Duration/limits | Attempts | Accepted | Materialized | New states/functions | Result/log hash |
|---|---|---:|---:|---:|---|---|
| Qualification pass 1 | 193.294601 s inside suite; 234.62 s outer; 60 s child / 360 s outer | 5 datasets | 4 metadata-accepted | 2 rows | six positive milestones; four exact rejection stages/classes | qualified; JSON `3ea55c…ac8`, time `57e0a1…934` |
| Qualification pass 2 | 190.838185 s inside suite; 231.88 s outer; same limits | 5 datasets | 4 metadata-accepted | 2 rows | identical stages/classes; valid bundle hashes identical | qualified; JSON `84d507…a07`, time `96e938…39e` |
| Mutation batches 1-3 | not run; not authorized | unavailable | unavailable | unavailable | unavailable | unavailable |

The child replays in pass 2 took 37.52 to 38.96 seconds, below 60 seconds. The
initial 15- and 30-second exploratory values failed because locked PyTorch
import, worker startup and shutdown dominate on the WSL-mounted environment;
the reviewed brief records the measured calibration to 60 seconds. Dataset
operations themselves were sub-second after import. The failed exploratory
runs were not counted as qualification passes.

## Independent review

- Exact commands replayed by reviewer and environment differences: independent
  review was not run. The author performed two fresh five-case CLI matrices,
  two seven-test passes and a second empty-cache bootstrap.
- Benign/control outcomes compared with the author's report: both CLI matrices
  produced the same milestone and exception-class tuple for every case; valid
  file hashes were identical.
- Core tests, workflow results and changed-code tests: focused tests passed 7/7
  twice (79.41 s / 894,048 KiB and 81.26 s / 892,360 KiB outer measurements).
  Two complete Python 3.10 repository passes each reported evidence 5/5,
  chassis 16/16, triage 3/3, resource self-test success, 44-claim schema/render
  success, 31-file/10-target repository validation and clean diff checks.
  Python 3.12 resource tests passed 5/5 twice. `claims.md` remained byte
  identical to `HEAD`. Hosted workflows were unavailable because nothing was
  pushed.
- Exception handling, resource cleanup and instrumentation diff checked:
  `MemoryError`, timeout and signal paths remain non-success; temporary test
  roots use `TemporaryDirectory`; the orchestrator refuses reused output roots.
  The probe changes no upstream loader code.
- Private artifacts and accidental disclosures excluded from review diff:
  generated datasets, dependency trees, caches and logs are ignored under
  `.runs/`. The tracked diff contains only public-source pins, generation/probe
  code, tests and documentation.
- Claims/render synchronization and scope wording checked: no evidence-ledger
  entry was added. The manifest and prose state no-video qualification only.
- Unresolved contradictions or limitations: no independent reviewer; no hosted
  CI; no hard RSS enforcement; no sanitizer; no video, training, policy or
  mutation work; missing-shard behavior was observed only with Hub offline;
  public prior-art search is not exhaustive.

## Decision

**QUALIFIED for the no-video R7 seed; COMPUTE PAUSED before video.** The locked source,
dependency set and generated files reproduced. The positive seed reached all
six named milestones twice, while every control failed at its exact earlier
stage and exception class. No new fault was observed.

The single bounded next action, if separately authorized, is an R8 brief for one
deterministic video-bearing seed. Its prerequisites are a pinned native decoder
environment, one valid decoded frame, missing and out-of-tolerance controls, a
hard resource policy appropriate to native decoding, and fresh prior-art review.
R8 is not started here. No merge, push, publication, disclosure, pull request,
issue or upstream contact is authorized by this packet.

## Local evidence inventory

All paths below are ignored and remain local:

- `.runs/lerobot-r7-2026-09-10/controls-pass1b.json`, SHA-256
  `3ea55c9aae21afec233d54a3ca942f6edc20e46b74e010f311622ad7434fcac8`;
  time record `57e0a1a58beb5c7caf029284461f39a97d1bce2d6029e3d21b3ab14b638b9934`.
- `.runs/lerobot-r7-2026-09-10/controls-pass2.json`, SHA-256
  `84d507672f1e1091e91a037d2a3f6a7acf0f54c18a097f7d4d87c43257306a07`;
  time record `96e938262441e955bf92a20b77f9f42cc9400919e85b39733747c3d3fac63c5c`.
- Final focused pass 1 log/time SHA-256:
  `e56fb1baeedf4e7193b3f4ce143cdbde52bf84b9c73cc695ad20fb22015cffb9` /
  `af6c0be610aa68cecb23ddc0629bc1d6e50e14024fdd2838c2eea19e7cfa73e3`.
- Final focused pass 2 log/time SHA-256:
  `045db49cab3e0fe9506c62e14a16fbc030f890ba8c2045b578532ffd9aabe203` /
  `88a00717dae54f7c3fc8e05deee4a3f0edad8a7a730e58084e895abe986c339e`.
- Second bootstrap log/time SHA-256:
  `31da1993e62a0337332ae95783e1b7ea37ca8464b9f0e7d72edebea859bb8bbd` /
  `b31c0a13c43ac5379124b3bffdfcadbc0bc0fa3a0d075cac4f32a1091f2d595a`.
- Complete repository pass 1 log SHA-256:
  `43f02ec8efec5cfaf8ac44e0870ce90626cfe808f3cc8ac9f00669c1938d27d6`.
- Complete repository pass 2 log SHA-256:
  `c6a79d0ff0bbbff464deb706639fc35b0bcb755c6e9b2df24014fd7d78fc6319`.
- First environment raw package manifest SHA-256
  `dc02faa5bf34b40f40b87bccdf1ae21ee3cc201764c2fd0f06e91dbad2de1a20`;
  second raw manifest
  `73745c4a2eab9430247f0151845a35bdf7e9a6112dbd969e13828bc0a064eae7`;
  normalized manifest for both
  `7c486f14cd5ec680c1a996c8915bf248dc9a9ec74da4eb3a89a0cb8c92415178`.

No external action was taken.
