# LeRobot dataset-composition target

Portfolio lifecycle: **paused after qualified M0**. The 2026-09-10 source review
identified a useful project-specific boundary across `info.json`, tasks and
episode metadata, Parquet rows, task lookup, optional video references and the
training `DataLoader`. No environment, seed, harness, dependency, build or fuzz
campaign exists yet.

Generic malformed Parquet and MP4 parsing are out of scope because Apache Arrow
and FFmpeg already expose public fuzz targets. A future driver must instead keep
individual files valid enough to test LeRobot's cross-file relationships and
must count these named milestones:

1. dataset metadata accepted;
2. tasks and episode metadata loaded;
3. referenced data shard loaded under the metadata-derived feature schema;
4. one row materialized to tensors with agreeing episode/frame indices;
5. `task_index` resolved and a one-worker DataLoader yielded the sample;
6. only in a later phase, a referenced video frame decoded within tolerance.

Known public corrupted-length, incomplete-metadata/boundary-drift, stale-task,
timestamp-out-of-range, nested-array, revision-race, row-group and scalar/vector
cases are regression controls and dedup exclusions, not new findings.

The next gate is a separately reviewed build-and-seed brief using the pinned
LeRobot revision and `uv.lock`. Until then, run no dependency installation,
seed execution or mutation campaign. See
`../../docs/qualification/lerobot-composition-m0.md` for the full review packet.
