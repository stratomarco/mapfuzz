# LeRobot composition R7: environment and semantic seed qualification

## Objective

Qualify one deterministic, no-video LeRobot v3 dataset-composition seed at the
official LeRobot revision selected by R6. Prove the supported path from dataset
metadata through episode and Parquet materialization, task resolution and a
one-worker PyTorch `DataLoader`. Deliver replayable code, focused controls and a
review packet, or stop with an explicit failed prerequisite. This package does
not authorize video decoding, mutation fuzzing, a defect claim or disclosure.

## Fixed inputs and isolation

- Work in `/mnt/f/mapfuzz/audit-hardening-dev` through WSL on branch
  `daybreak-lerobot-r7`, based on local M0 checkpoint
  `3d723e46508cc25a16a6ceacb957042616faa304`.
- Use LeRobot `71a11efe77f55e61f3ab2ce45b40da8cf626afa9` and its exact
  `uv.lock` SHA-256
  `4a56d47d2edfdc159bd137c854d37033028f38c4d9d57ec98284d8fce9ea2ccc`.
- Require Python 3.12 or newer. Create a fresh environment and source directory
  below ignored `.runs/lerobot-r7-2026-09-10/`; do not modify the R6 snapshot.
- Resolve dependencies with locked `uv` inputs. Record the `uv` executable
  version and SHA-256, Python version, OS/architecture, installed package list,
  source hash and all exact commands. No moving source or dependency revisions.
- Keep generated datasets, logs, package caches and raw controls ignored. Track
  only reviewed scripts, tests, manifests, documentation and deterministic
  generation recipes. Do not include tokens, credentials or private inputs.

## Supported seed

Use the pinned public API only:

1. `LeRobotDataset.create(..., use_videos=False)` with two fixed float32 vector
   features (`observation.state` and `action`), one fixed task and fixed FPS.
2. Add exactly one deterministic frame, save exactly one episode and finalize.
3. Reopen the local dataset through `LeRobotDataset`, without Hub access.
4. Hash every generated file and a canonical bundle manifest. Record feature
   names, shapes, dtypes, values, frame/episode/task counts and Parquet row
   count. Byte-identical output across dependency versions is not assumed.

The positive replay must observe and report each named milestone separately:

1. `info.json` accepted and the expected no-video feature schema loaded;
2. exactly one task and one episode metadata row loaded;
3. the episode-selected Parquet shard loaded with exactly one row;
4. row values materialized as tensors with matching frame and episode indices;
5. `task_index` resolved to the fixed task string;
6. a `DataLoader(batch_size=1, num_workers=1)` yielded that same sample once.

A metadata object, file-open event or Parquet parse alone is not successful
composition. Probe code may observe returned objects and public metadata but
must not change upstream behavior or catch an unexpected exception as success.

## Semantic controls and failure behavior

Generate controls from a fresh valid seed and require distinct nonzero results:

- malformed metadata: set `fps` to zero; reject before episode or data loading;
- missing data shard: retain valid metadata but remove the referenced Parquet
  file; fail after metadata/episode acceptance and before row materialization;
- truncated data shard: retain valid metadata but truncate the referenced
  Parquet file; fail as a Parquet/data-load error at the same semantic stage;
- invalid task index: rewrite the one otherwise valid Parquet row so its
  `task_index` is outside the one-row task table; fail after row
  materialization and before task resolution or DataLoader success.

The driver must classify the last completed milestone and exception type in
machine-readable output. Allocation failure, timeout, signal, abnormal child
exit and unexpected exceptions remain visible and must not be labeled as a
normal rejection. Temporary control copies must be cleaned up after tests.

## Bounds and stopping rules

- CPU only; no GPU, video, network dataset, policy construction or training.
- One seed, one episode, one frame and one `DataLoader` worker.
- Each subprocess replay has a 30-second outer deadline. This includes cold
  import time for the locked CUDA-enabled PyTorch wheel on the WSL-mounted
  workspace; a measured exact-import probe exceeded 15 seconds. The complete
  control suite has a 180-second outer deadline.
- Run no mutation campaign and report attempts/accepted/materialized counts as
  not applicable rather than zero fuzz inputs.
- Stop immediately if the locked environment cannot be created, the positive
  seed misses any milestone, a negative control reaches the DataLoader, an
  unexpected fault appears, or effective deadlines cannot be demonstrated.
- A newly observed fault stops scope expansion. Preserve raw artifacts only in
  ignored storage and report the class/status without adding a reproducer to the
  review diff or contacting upstream.

## Deliverables

- A pinned environment/bootstrap entry point and reviewed environment manifest.
- A deterministic seed generator, semantic replay probe and focused controls
  under `targets/lerobot_composition/qualification/`.
- Updated target README with exact fresh replay commands and scope limits.
- `docs/qualification/lerobot-composition-seed.md`, following
  `docs/tasks/RESEARCH-REVIEW-TEMPLATE.md` and explicitly marking unrun batches,
  unavailable independent review and all limitations.
- R7 status updates in `docs/ROADMAP.md`, `docs/TARGETS.md` and
  `targets/qualification.yaml` only after the runtime gate is demonstrated.
- Ignored logs and manifests with SHA-256 inventories. No evidence-ledger claim
  is warranted by qualification alone.

## Required validation

Run the seed and every control twice from fresh generated dataset directories.
Then run the focused test suite twice and the following repository checks twice
through WSL, recording Python versions and exact outcomes:

```bash
python3 -m unittest discover -s evidence -p 'test_*.py'
python3 -m unittest discover -s chassis/tests -p 'test_*.py'
python3 chassis/tests/test_triage.py
python3 chassis/resource_oracle.py --selftest
python3 evidence/tool.py --check --render
python3 chassis/check_repository.py
git diff --check
```

Inspect the final diff and ignored-file boundary separately on both passes. A
passing test establishes only the named gate it asserts, not defect novelty,
security impact, broad dataset compatibility or video safety.

## Acceptance and next boundary

R7 is qualified only if both fresh replays produce the expected six positive
milestones, all four controls stop at their expected semantic gates, deadlines
are enforced and both focused and repository validation passes are green. The
review packet may then recommend one separately authorized R8 video-seed brief.
It may not start R8, mutate inputs, push, merge, publish, open a pull request,
contact upstream or characterize a known public regression as a new finding.
