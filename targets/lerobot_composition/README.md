# LeRobot dataset-composition target

Portfolio lifecycle: **paused after qualified video seed**. R6 identified the
project-specific composition boundary. R7 qualified a deterministic no-video
sample. R8 pins the current source, PyAV and bundled FFmpeg libraries and proves
one H.264 frame through metadata, Parquet row materialization, real float32 CHW
decode, task lookup and a one-worker `DataLoader`.

This is not a fuzz target or a vulnerability claim. Generic malformed Parquet
and MP4 parsing remain out of scope because Apache Arrow and FFmpeg already
expose public fuzz targets. Policy construction, training and mutation are not
implemented or authorized.

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
`pyav` backend and does not decode video. For R8, use the current-source video
bootstrap, which additionally verifies PyAV 15.1.0, the bundled FFmpeg library
versions, `libx264` and CPU-only execution:

```bash
timeout 600s bash targets/lerobot_composition/qualification/bootstrap_video.sh \
  /mnt/f/mapfuzz/audit-hardening-dev/.runs/lerobot-r8-replay
```

## Run the semantic controls

Use a new output root for every pass. Each child replay has a 60-second Python
deadline and the complete five-case matrix has a 360-second host deadline:

```bash
timeout 360s env CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 \
  .runs/lerobot-r7-replay/env/bin/python \
  targets/lerobot_composition/qualification/run_controls.py \
  .runs/lerobot-r7-controls-pass1
```

The R7 valid case must report, in order:

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

Run the R8 four-case video matrix only inside the verified hard-resource scope:

```bash
timeout 360s /usr/bin/time -v systemd-run --user --scope --collect \
  -p MemoryMax=4294967296 -p MemorySwapMax=0 \
  taskset -c 0 env CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 \
  .runs/lerobot-r8-replay/env/bin/python \
  targets/lerobot_composition/qualification/video_cgroup_exec.py \
  .runs/lerobot-r8-replay/env/bin/python \
  targets/lerobot_composition/qualification/run_video_controls.py \
  .runs/lerobot-r8-controls-pass1
```

The positive case must reach `metadata_accepted`, `metadata_tables_loaded`,
`row_materialized`, `video_validated`, `sample_decoded` and
`dataloader_yielded`. Missing MP4 must stop with `OfflineModeIsEnabled` after
metadata tables; a 32-byte MP4 must stop with PyAV `InvalidDataError` after row
materialization; and a timestamp one second beyond the one-frame video must
stop with `FrameTimestampError` after MP4 validation. Any changed stage,
exception, timeout, signal or resource proof fails the matrix.

## Scope boundary

Known public corrupted-length, incomplete-metadata/boundary-drift, stale-task,
timestamp-out-of-range, nested-array, revision-race, row-group and scalar/vector
cases remain regression controls and dedup exclusions. Current streaming-video
issue 4524 and PR 4528 are also excluded. R7 and R8 found no new fault.

R8 does not promote the target to mutation. The next possible gate is a new
maintainer lifecycle decision after review; no campaign is implied. See
`../../docs/qualification/lerobot-composition-seed.md` and
`../../docs/qualification/lerobot-composition-video-seed.md` for measured
evidence.
