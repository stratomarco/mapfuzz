# LeRobot dataset-composition target

Portfolio lifecycle: **paused after qualified no-video seed**. R6
identified the project-specific composition boundary. R7 now supplies a locked
Python 3.12 environment recipe and proves one deterministic LeRobot v3 sample
through metadata, episode metadata, Parquet loading, tensor materialization,
task lookup and a one-worker `DataLoader`.

This is not a fuzz target or a vulnerability claim. Generic malformed Parquet
and MP4 parsing remain out of scope because Apache Arrow and FFmpeg already
expose public fuzz targets. Video, policy construction, training and mutation
are not implemented or authorized.

## Reproduce the environment

Run through WSL from the repository root. The bootstrap refuses to reuse an
existing output root, downloads the immutable official source archive, verifies
its hash, installs the upstream-pinned `uv 0.11.30`, and resolves the exact
upstream `uv.lock` with only the `dataset` and `test` extras:

```bash
timeout 600s bash targets/lerobot_composition/qualification/bootstrap.sh \
  /mnt/f/mapfuzz/audit-hardening-dev/.runs/lerobot-r7-replay
```

The official lock selects CUDA-enabled PyTorch packages on Linux. Qualification
sets `CUDA_VISIBLE_DEVICES` to empty and verifies that CUDA is unavailable; no
GPU code is exercised. The no-video seed explicitly selects the supported
`pyav` backend and does not decode video.

## Run the semantic controls

Use a new output root for every pass. Each child replay has a 60-second Python
deadline and the complete five-case matrix has a 360-second host deadline:

```bash
timeout 360s env CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 \
  .runs/lerobot-r7-replay/env/bin/python \
  targets/lerobot_composition/qualification/run_controls.py \
  .runs/lerobot-r7-controls-pass1
```

The valid case must report, in order:

1. `metadata_accepted`;
2. `metadata_tables_loaded`;
3. `data_shard_loaded`;
4. `row_materialized`;
5. `task_resolved`;
6. `dataloader_yielded`.

The exact controls are fail-closed: invalid FPS raises `ValueError` before
metadata acceptance; a missing data shard reaches valid metadata and then the
offline Hub fallback raises `OfflineModeIsEnabled`; a 32-byte Parquet shard
raises `ArrowInvalid`; and an out-of-range `task_index` raises `IndexError` only
after the row tensors materialize. Any different exception, milestone, timeout,
signal or exit code fails the matrix.

## Scope boundary

Known public corrupted-length, incomplete-metadata/boundary-drift, stale-task,
timestamp-out-of-range, nested-array, revision-race, row-group and scalar/vector
cases remain regression controls and dedup exclusions. R7 found no new fault.

The next possible gate is a separately reviewed R8 brief for one deterministic
video-bearing seed and missing/out-of-tolerance controls. It requires an exact
native decoder environment and explicit authorization. Do not start video or
mutation work from this README. See
`../../docs/qualification/lerobot-composition-seed.md` for measured evidence.
