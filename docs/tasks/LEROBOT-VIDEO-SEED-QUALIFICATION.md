# LeRobot composition R8: bounded video-seed qualification

## Objective

Qualify one deterministic RGB video-bearing LeRobot v3 dataset through the
non-streaming `LeRobotDataset` consumer. Prove that metadata and Parquet data
select a real local MP4 frame, the pinned PyAV backend returns the expected
tensor, the task resolves, and a one-worker PyTorch `DataLoader` yields the
sample. Deliver exact positive and negative semantic evidence or stop at the
first failed prerequisite. This package authorizes no mutation campaign,
training, policy execution, vulnerability claim or disclosure.

## Refreshed M0 and fixed inputs

- Work through WSL on branch `daybreak-lerobot-r8`, based on clean R7
  checkpoint `7e6f9f4724ef98fd46ff37c8777f127b52bf6b88`.
- Use current official LeRobot
  `b6ec0060779550c0a157ae34feb89e0cf86012a8`, committed
  2026-09-10 14:51:34Z, source archive SHA-256
  `429a869b02b3fd8b9745f390951148f5185fce42d7bd7678337981d4510324d7`.
- Use its exact unchanged `uv.lock` SHA-256
  `4a56d47d2edfdc159bd137c854d37033028f38c4d9d57ec98284d8fce9ea2ccc`
  with upstream-pinned `uv 0.11.30` and Python 3.12 or newer.
- The current dataset metadata, reader, writer and video utility files are
  byte-identical to the R7 pin. The current public tree exposes no fuzz-named
  implementation, and LeRobot remains absent from OSS-Fuzz
  `46184c7b43cb1a97f1e219dc2a37f71eaa841b18`; Arrow and FFmpeg remain present.
- Current open issue 4524 and PR 4528 cover `StreamingLeRobotDataset` video-file
  timestamp coordinates. Closed issues 3513, 3177 and 2680 cover timestamp or
  frame-index failures. These and open PRs 4522/4338 are prior art and controls,
  not novelty. R8 targets only the non-streaming reader and must not reproduce
  or report these cases as new.
- Create a fresh source, dependency cache and environment below ignored
  `.runs/lerobot-r8-2026-09-11/`. Do not modify or rely on an editable R7 source.

If the immutable source/lock hashes, supported non-streaming consumer, public
coverage comparison or decoder prerequisites fail, stop without switching
target or installing an alternative unreviewed stack.

## Exact decoder and encoder boundary

Use the locked PyAV 15.1.0 package explicitly for reading and writing. Before
seed generation, record `av.library_versions`, require the `libx264` encoder and
record the codec object name. The currently observed bundled versions are
libavcodec 61.19.101, libavformat 61.7.100, libavutil 59.39.100 and libswscale
8.3.100; the fresh environment must confirm them. No system `ffmpeg` or
`ffprobe` executable is installed or required by the selected implementation.
Do not fall back to TorchCodec or silently select another encoder/decoder.

## Deterministic positive seed

Use the pinned public writer API with `use_videos=True`, `video_backend="pyav"`,
one 64x96 RGB video feature, one float32 action vector, one fixed task, FPS 10,
one episode and one frame. Supply a deterministic uint8 HWC color pattern and
explicit deterministic H.264 encoder settings supported by pinned source.
Disable parallel and streaming encoding. Finalize, hash every generated file,
inspect the MP4 with PyAV, and reopen it locally with Hub offline.

The positive replay must report each named milestone separately:

1. video schema and `info.json` accepted;
2. one task and one episode metadata row accepted;
3. one Parquet row materialized with agreeing frame/episode indices;
4. metadata resolves one existing MP4 with expected codec, dimensions and FPS;
5. `dataset[0]` decodes one float32 CHW video tensor within a documented lossy
   pixel tolerance and resolves the fixed task;
6. `DataLoader(batch_size=1, num_workers=1)` yields the same video/action/task.

Parsing an MP4, mapping its path or returning an undecoded descriptor is not the
consumer milestone. The probe may inspect returned public objects but must not
patch upstream, delete files after validation or bypass cache/path guards.

## Controls and fail-closed behavior

Generate each control from a fresh valid seed and require its exact last
milestone, exception class and nonzero exit:

- missing MP4: remove the referenced file before construction; metadata must
  remain valid, Hub access remains disabled, and the expected offline cache
  failure must not count as data or video consumption;
- truncated MP4: retain the referenced path but truncate its contents; metadata
  and Parquet row must succeed, then PyAV must reject before decoded-frame/task
  or DataLoader success;
- out-of-tolerance timestamp: keep the valid MP4 but rewrite the otherwise valid
  Parquet row timestamp beyond the one-frame video; row materialization must
  succeed and the PyAV path must raise `FrameTimestampError` before task/batch.

Any different exception at the same stage fails the oracle. Preserve visibility
of `MemoryError`, timeout, signal, abnormal child exit and unexpected exceptions.
Temporary test roots must be cleaned; review evidence roots must never be reused.

## Resource bounds and stopping rules

- CPU only, one frame, one episode, one camera and one DataLoader worker.
- Run the complete matrix inside a cgroup-v2 scope with
  `memory.max=4294967296`, `memory.swap.max=0` and one-CPU affinity. A tracked
  wrapper must read and fail closed on those effective values before execution.
- Each replay has a 60-second Python deadline. The four-case suite has a
  360-second host deadline. Record elapsed time and GNU-time peak RSS while
  distinguishing an observed maximum from an enforced aggregate limit.
- Run no mutations, video corpus expansion, GPU work, network dataset access,
  policy construction or training.
- Stop on the first unexpected fault, failed positive milestone, control that
  reaches task/DataLoader success, ineffective resource limit or decoder drift.
  Keep any raw trigger only in ignored storage and report class/status without
  upstream contact.

## Deliverables and validation

- Extend the R7 environment bootstrap or add an R8 manifest without weakening
  its source/lock verification.
- Add a deterministic video seed generator, semantic probe, hard-resource
  wrapper, orchestration entry point and focused tests under
  `targets/lerobot_composition/qualification/`.
- Update the target README, roadmap, target inventory and qualification manifest
  only after both fresh matrices pass.
- Create `docs/qualification/lerobot-composition-video-seed.md` from
  `docs/tasks/RESEARCH-REVIEW-TEMPLATE.md`. Mark independent review, sanitizer,
  mutation batches and anything not exercised as unavailable or not run.
- Keep generated MP4s, datasets, environments and logs ignored. Add no evidence
  ledger claim unless a separate finding workflow later establishes provenance,
  impact and novelty.

Run the positive seed and all three controls twice from new roots. Run focused
tests twice. Then run the repository-required evidence, chassis, triage,
resource-oracle, render, repository and diff checks twice under WSL, including
Python 3.12 resource tests. Confirm `claims.md` remains unchanged.

R8 acceptance qualifies only this one video-seed path. It does not promote the
paused target to a mutation lifecycle. The only possible next action is a new
maintainer decision after review; this brief does not authorize a campaign,
push, merge, publication, pull request, issue, message or upstream disclosure.
