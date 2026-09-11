# LeRobot dataset-composition R8 review packet

## Identity and scope

- Package ID and objective: `R8-LEROBOT-VIDEO-SEED-2026-09-11`; qualify one
  deterministic RGB video-bearing LeRobot v3 dataset through the non-streaming
  metadata, Parquet, PyAV decode, task and one-worker `DataLoader` path.
- Author/model and independent reviewer: Codex implemented and replayed the
  package. Independent review was **not run**. Two exact-commit matrices and two
  focused-test passes are corroboration, not independent review.
- Date, base SHA, implementation SHA or working-diff identity: 2026-09-11; R7
  base `7e6f9f4724ef98fd46ff37c8777f127b52bf6b88`; R8 brief
  `9219a351efdabecc353e3512e96245557c46cb58`; implementation
  `e06e0d887e16c122cb200e1bb3a43fa253eb7f9a`. This report and portfolio
  updates are the following documentation diff.
- Worktree/branch and exact-head CI link/status:
  `/mnt/f/mapfuzz/audit-hardening-dev`, `daybreak-lerobot-r8`. Hosted CI is
  unavailable because the branch remains local and unpushed.
- Disposition: **QUALIFIED for the one-frame R8 video seed; COMPUTE PAUSED**
- What this disposition establishes and does not establish: the pinned public
  writer emits one local H.264 MP4 and the pinned non-streaming reader returns
  the expected video tensor, action, task and one-worker batch. Three video
  controls fail at their expected stages. This establishes neither a finding
  nor broad compatibility, streaming behavior, sanitizer coverage, training,
  policy safety, mutation authorization or novelty of known video failures.

## M0 and novelty boundary

| Source | Immutable revision and link | Retrieved date | Relevant path/entry point | Observation |
|---|---|---|---|---|
| Loader and writer | LeRobot [`b6ec0060779550c0a157ae34feb89e0cf86012a8`](https://github.com/huggingface/lerobot/tree/b6ec0060779550c0a157ae34feb89e0cf86012a8) | 2026-09-11 | `LeRobotDataset.create`, `add_frame`, `save_episode`, `finalize`, `DatasetReader.get_item` | The official writer created the local bundle; the official non-streaming reader reopened and decoded it. Relevant dataset source was byte-identical to the R7 pin. |
| Video implementation | same revision | 2026-09-11 | [`video_utils.py`](https://github.com/huggingface/lerobot/blob/b6ec0060779550c0a157ae34feb89e0cf86012a8/src/lerobot/datasets/video_utils.py), [`video.py`](https://github.com/huggingface/lerobot/blob/b6ec0060779550c0a157ae34feb89e0cf86012a8/src/lerobot/configs/video.py) | Writing and reading explicitly used PyAV. The environment exposed `libx264`; no system ffmpeg/ffprobe executable was required. |
| Public fuzz build and harness | OSS-Fuzz [`46184c7b43cb1a97f1e219dc2a37f71eaa841b18`](https://github.com/google/oss-fuzz/tree/46184c7b43cb1a97f1e219dc2a37f71eaa841b18/projects) | 2026-09-11 | project inventory | LeRobot was absent; Arrow and FFmpeg were present. This is absence of observed project coverage, not proof no other fuzzing exists. |
| Public prior art/fix status | LeRobot [issue 4524](https://github.com/huggingface/lerobot/issues/4524), [PR 4528](https://github.com/huggingface/lerobot/pull/4528), [PR 4522](https://github.com/huggingface/lerobot/pull/4522), [PR 4338](https://github.com/huggingface/lerobot/pull/4338) | 2026-09-11 | streaming timestamps, cached-video selection and aggregate video validation | These open records and closed timestamp/frame-index issues 3513, 3177 and 2680 are prior art and dedup controls. R8 did not target streaming or claim these cases as new. |

The trust boundary is a third-party or local LeRobot v3 dataset explicitly
selected for training, evaluation, editing or visualization. R8 tests the
LeRobot-specific relationship from typed metadata and episode video mapping to
a Parquet timestamp and decoded MP4 frame. Generic MP4 corruption is a control,
not a candidate finding. Hub access was disabled. No upstream code was patched.

## Reproduction environment

The final environment was WSL2 x86_64, Linux
6.6.87.2-microsoft-standard-WSL2, Python 3.12.13 and upstream-pinned `uv 0.11.30`.
LeRobot 0.6.2 was installed from the fresh immutable source. The source archive
SHA-256 was `429a869b02b3fd8b9745f390951148f5185fce42d7bd7678337981d4510324d7`;
`pyproject.toml` was `d67a60c007eeb4401b29818d99a6ad94aa28c1f10beabdcf77c4da5d97f8e326`;
and `uv.lock` was `4a56d47d2edfdc159bd137c854d37033028f38c4d9d57ec98284d8fce9ea2ccc`.
The reused, previously verified uv executable hash was
`9a4299a0c3bcc01012acbcdae7b5655e5087e0e5d87459306736a1420a902b81`;
the fresh package manifest hash was
`1fc07ac046d8ccbd32c44f7bb3166a476f8c9462e0b5fd6bfed8198526a39274`.

PyAV was 15.1.0. Recorded libraries were libavcodec 61.19.101,
libavdevice 61.3.100, libavfilter 10.4.100, libavformat 61.7.100,
libavutil 59.39.100, libswresample 5.3.100 and libswscale 8.3.100.
`av.codec.Codec("libx264", "w").name` returned `libx264`. The encoder settings
were H.264, yuv420p, GOP 1, CRF 18, preset `medium` and one encoder thread.
Execution set `CUDA_VISIBLE_DEVICES=''`; `torch.cuda.is_available()` was false.
The upstream lock includes CUDA-enabled PyTorch packages, but no GPU path ran.

The tracked `bootstrap_video.sh` downloads and verifies the current source into
a new root, resolves the exact lock with `dataset` and `test` extras, verifies
the decoder/encoder versions, and inventories the environment. The qualification
environment used a fresh source, uv cache and venv under ignored
`.runs/lerobot-r8-2026-09-11/`; only the verified uv executable was reused.

Both final generations were byte-identical in this locked environment:

| File | Bytes | SHA-256 |
|---|---:|---|
| `data/chunk-000/file-000.parquet` | 3,126 | `db79957b8eb8011784c3c4d662fa7ce25be60ea864d834ce9cd3ffdbb94642a1` |
| `meta/episodes/chunk-000/file-000.parquet` | 38,473 | `7d1edc5f8b0f097af28ac5a0f1ebed3a7102a810f97aed02b7b7caa79a227973` |
| `meta/info.json` | 2,214 | `1f9a91cb6ca07826b587e50c92467b9d63e07c3bd05cc4cf0a7a337c471a28d7` |
| `meta/stats.json` | 6,092 | `6953c47273632c39a6383a705798515e8a6c18dd4f5812eab5943102f7600647` |
| `meta/tasks.parquet` | 2,070 | `ee79c6f7d46e6c0a74f8148266a5b39d1761987ef615a3205c16bf5cc8ded584` |
| `videos/observation.images.cam/chunk-000/file-000.mp4` | 1,569 | `7cb5544c85940b1f5cbc01a49eb174fac54294f0670e3158688b5f1978ec10c2` |

The seed is one deterministic 64x96 uint8 HWC four-quadrant RGB frame, one
float32 action `[0.25, -0.25]`, task `move test object`, FPS 10 and one episode.
Cross-version byte identity is not claimed.

## Semantic controls

| Benign/control input and hash | Expected milestone | Observed milestone/count | Source probe location | Exit/result | Local evidence |
|---|---|---|---|---|---|
| Valid bundle; MP4 `7cb554…10c2` | all six milestones and one worker batch | 1 dataset, 2 metadata rows, 1 Parquet row, 1 validated video, 1 decoded sample/task, 1 batch | `video_qualification.py:194-295` | 0 / qualified twice | `matrix-final1.jsonl`, `matrix-final2.jsonl` |
| Missing MP4; valid metadata | metadata tables accepted; no Parquet/video success | last `metadata_tables_loaded`; 0 rows/videos/tasks/batches | `video_qualification.py:198-225` | 2 / `OfflineModeIsEnabled` twice | same logs; offline mode blocked Hub fallback |
| 32-byte MP4 `b1c35f…ba5c` | Parquet row succeeds; MP4 parsing rejects | last `row_materialized`; 1 row, 0 validated videos/tasks/batches | `video_qualification.py:226-247` | 2 / PyAV `InvalidDataError` twice | same logs |
| Timestamp 1.0 s with one frame at 0.0 s | valid MP4; consumer decode rejects before task | last `video_validated`; 1 row/video, 0 decoded samples/tasks/batches | `video_qualification.py:248-262` | 2 / `FrameTimestampError` twice | same logs |

The probe uses public metadata and dataset objects, materializes the real Arrow
row as tensors, resolves the episode's MP4 path from metadata, parses and decodes
that MP4 with PyAV, then calls `dataset[0]` and the real PyTorch `DataLoader`.
Here, row materialization means the Hugging Face dataset returned the action and
indices as tensors. Video consumption means `dataset[0]` returned a float32
`[3,64,96]` tensor; mapping or parsing the file alone does not count.

The decoded frame had maximum absolute normalized pixel error
0.0666666627 and mean error 0.0062908535 against the pre-encode frame, within
the fixed lossy thresholds 0.08 and 0.01. Both passes produced the same values.
`MemoryError` is re-raised; timeout and negative signal exits are orchestration
failures. Unexpected exceptions never become exit-zero qualification.

## Bounded runs and resource behavior

Each final matrix generated four fresh roots. The valid case reached all six
milestones. The three controls reached only their stated prefixes. Thus each
matrix attempted four datasets, accepted metadata for all four, materialized
three Parquet rows, validated two MP4s, decoded one sample/task and yielded one
batch. These are dataset-case counts, not fuzz executions. Mutations were not
run.

Both complete matrices ran in a cgroup-v2 scope. The tracked wrapper observed
and required `memory.max=4294967296`, `memory.swap.max=0` and CPU affinity `[0]`
before exec. This is an aggregate enforced cgroup limit. GNU `time -v` observed
peak RSS of 894,720 KiB and 898,952 KiB for the two outer commands; this is an
observed maximum, not the enforcement mechanism. Each replay had a 60-second
Python timeout and each suite a 360-second host timeout.

| Batch | Duration/limits | Attempts | Accepted | Materialized | New states/functions | Result/log hash |
|---|---|---:|---:|---:|---|---|
| Final matrix 1 | 98.115706 s suite; 2:04.81 outer; 60 s child / 360 s outer; 4 GiB, no swap, CPU 0 | 4 | 4 metadata | 3 rows | six positive milestones; three exact control gates | qualified; JSON `1b16bd…3661`, time `050c0d…0085` |
| Final matrix 2 | 98.148290 s suite; 2:05.32 outer; same limits | 4 | 4 metadata | 3 rows | identical stages, exceptions, hashes and pixel errors | qualified; JSON `51ae10…832b`, time `2234dc…d60c` |
| Mutation batches 1-3 | not run; unauthorized | unavailable | unavailable | unavailable | unavailable | unavailable |

## Independent review

- Exact commands replayed by reviewer and environment differences: independent
  review was **not run**. The author ran two exact-commit cgrouped matrices and
  two six-test focused passes from fresh data roots.
- Benign/control outcomes compared with the author's report: both matrices had
  identical artifact hashes, positive pixel errors, milestone prefixes and
  negative exception classes.
- Core tests, workflow results and changed-code tests: focused tests passed 6/6
  twice in 35.929 and 36.072 seconds. Two complete repository passes each
  reported evidence 5/5, chassis 16/16, triage 3/3, resource self-test success,
  44-claim schema/render success, 37-file/10-target repository validation,
  Python 3.12 resource tests 5/5 and clean diff checks. Hosted workflows are
  unavailable because the branch was not pushed.
- Exception handling, resource cleanup and instrumentation diff checked:
  `MemoryError`, replay timeout, signal exit, reused roots and ineffective
  cgroup limits are non-success. Focused tests use `TemporaryDirectory`; review
  roots are never reused.
- Private artifacts and accidental disclosures excluded from review diff:
  generated MP4s, datasets, caches, environments and logs remain ignored under
  `.runs/`. No reproducer or trigger was sent outside the workspace.
- Claims/render synchronization and scope wording checked: no evidence-ledger
  claim was added; `claims.md` had zero diff from the R7 base before this report.
- Unresolved contradictions or limitations: no independent reviewer, hosted CI,
  sanitizer, mutation, streaming dataset, training or policy execution. One
  frame cannot establish broad codec/dataset compatibility. Public prior-art
  review is evidence of observed records, not an exhaustive proof of absence.
- Maintainer-authorized disposition review: on 2026-09-11, after implementation
  commit `e06e0d8` and report commit `848acb6`, Codex compared the brief and
  tracked diff with both raw matrix logs and both focused-test logs. All four
  evidence hashes and eight case outcomes matched; no tracked generated payload,
  Hub upload, streaming, mutation or campaign path was present. This is a
  documented self-review under maintainer authorization, **not** independent
  review. The lifecycle decision is **PAUSE**.

## Decision

**QUALIFIED for the one-frame R8 video seed; COMPUTE PAUSED.** The immutable
source, lock and decoder prerequisites matched the brief. The official writer
and non-streaming consumer reached all six positive milestones twice under hard
limits, while each control failed at its exact earlier stage and exception
class. No new fault was observed.

The maintainer-authorized decision is to pause R8. Reopen only for a meaningful
upstream boundary change or a separately reviewed brief with named semantic
states, dedup rules and a fresh compute cap. This report authorizes no campaign,
merge, push, publication, disclosure, pull request, issue, message or upstream
contact.

## Local evidence inventory

All paths below are ignored and local:

- `.runs/lerobot-r8-2026-09-11/matrix-final1.jsonl`, SHA-256
  `1b16bd06b450f5122195e8fc36263667b78a14c4f9598f0c09960c5e94763661`;
  time log `050c0de162aec086518e8316153a9c4554d5d74057ca76ea4dbb265a324f0085`.
- `.runs/lerobot-r8-2026-09-11/matrix-final2.jsonl`, SHA-256
  `51ae105f162b7737fa9f4bce199c6f62c8cc8b03993362102fc0afd882d9832b`;
  time log `2234dc0c77aedeab21fe28f6efac986f8eb54f935acd1f47da0c0a05abe2d60c`.
- `.runs/lerobot-r8-2026-09-11/focused-final1.log`, SHA-256
  `37e74a414e69e4f93f8835899c8d6b0cde9fadea0aa0ab2b028096252e855a2b`.
- `.runs/lerobot-r8-2026-09-11/focused-final2.log`, SHA-256
  `8a0bf97a2dcdf3ca99300f1d9fe06f6a54a6d9649156517f931d1094eee04eb4`.
- Fresh package manifest SHA-256
  `1fc07ac046d8ccbd32c44f7bb3166a476f8c9462e0b5fd6bfed8198526a39274`.
- Initial complete repository pass logs SHA-256
  `114855bfb23bbd72f51c10b1f901a71bbe50553c5a74ec92e018e44de01ddef4`
  and `e14b3d1585411e1fb5ee88f5e9c8da950a0b263b52f469fd9db43ad68f833e2e`.

No external action was taken.
