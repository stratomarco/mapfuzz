# CLIP/mmproj qualification target

Portfolio lifecycle: **qualified locally; parked**. The review packet disposition
remains **CHANGES-REQUIRED** because the first bounded mutation batch found a
candidate and triggered the stop rule. M0 found a current public-coverage gap,
and the synthetic control reached real tensor reads plus bounded CLIP graph
construction.
The first 60-second smoke batch then produced a reproducible ASan null-read
candidate, so campaign expansion stopped. Batches 2 and 3 were not run. This is
not a novelty, exploitability, or impact determination. A subsequent local,
layout-aware validation patch converts the retained crash to a pre-read
rejection while preserving the supported Yi-style MLP layout. The fix has not
been proposed upstream. An independent 2026-09-08 review accepted the fix for
the observed path after replaying both layouts and the retained private input.
The same fix was then built and replayed locally against upstream master
`df750f76bb6126566621803b69ddaeb993be5b08` on 2026-09-09 with the separate
qualification patches present and the same expected outcomes. The fix alone
also passed `git apply --check` against pristine current master but was not
compiled alone. No pull request was opened.

The earlier `harness/` prototype remains historical. It uses `no_alloc=true`, a
metadata-only seed and broad exception catches, so it does not establish tensor
materialization. The qualification implementation is isolated under
`qualification/` and uses a pinned external llama.cpp checkout.

## Exact environment and build

Run Git, builds and tests in WSL from the repository root. `environment.env`
pins the upstream revisions and tool versions. `build.sh` refuses to reuse a
source or build directory, fetches only the exact llama.cpp commit, applies the
known loader-blocker patch and the separate `std::bad_alloc` visibility patch,
then applies the separate MLP-layout validation fix and builds CPU-only
ASan/coverage binaries with at most four jobs.

```bash
export CLIP_MM_PROJ_WORK_ROOT="$PWD/.runs/clip-mmproj-review-build"
targets/clip_mmproj/build.sh
```

The recorded WSL2/Clang 14 PIE+ASan build sometimes failed before `main` under
normal address randomization. Replays therefore use `setarch x86_64 -R`; this
changes process layout, not loader validation or accepted-input semantics. The
review packet records both the failing control and the stabilized replay.

## Seed and semantic controls

The deterministic seed is a one-layer vision CLIP MLP with 12 small F32 tensors;
it is generated from tracked code and contains no model-derived data.

```bash
build="$CLIP_MM_PROJ_WORK_ROOT/build"
mkdir -p .runs/clip-mmproj-review-inputs .runs/clip-mmproj-review-corpus
setarch x86_64 -R "$build/clip-mmproj-seed" \
  .runs/clip-mmproj-review-inputs/benign.gguf benign
setarch x86_64 -R "$build/clip-mmproj-seed" \
  .runs/clip-mmproj-review-inputs/malformed.gguf malformed
setarch x86_64 -R "$build/clip-mmproj-seed" \
  .runs/clip-mmproj-review-inputs/missing.gguf missing
setarch x86_64 -R "$build/clip-mmproj-seed" \
  .runs/clip-mmproj-review-inputs/missing-projector.gguf missing-projector
setarch x86_64 -R "$build/clip-mmproj-seed" \
  .runs/clip-mmproj-review-inputs/yi.gguf yi
cp .runs/clip-mmproj-review-inputs/benign.gguf \
  .runs/clip-mmproj-review-corpus/benign.gguf

setarch x86_64 -R "$build/clip-mmproj-qualify" \
  .runs/clip-mmproj-review-inputs/benign.gguf
setarch x86_64 -R "$build/clip-mmproj-qualify" \
  .runs/clip-mmproj-review-inputs/malformed.gguf
setarch x86_64 -R "$build/clip-mmproj-qualify" \
  .runs/clip-mmproj-review-inputs/missing.gguf
setarch x86_64 -R "$build/clip-mmproj-qualify" \
  .runs/clip-mmproj-review-inputs/missing-projector.gguf
setarch x86_64 -R "$build/clip-mmproj-qualify" \
  .runs/clip-mmproj-review-inputs/yi.gguf

CLIP_MM_PROJ_BUILD_DIR="$build" \
  python3 -m unittest -v \
  targets.clip_mmproj.qualification.test_qualification
```

The probe first parses metadata/descriptors without allocation, then calls the
real pinned `clip_init` path with `no_alloc=false`. Its progress callback observes
the loader after each synchronous tensor read; it does not advance the loader or
bypass a guard. The final milestone requires a non-null vision context and reads
the constructed graph's output embedding size. `missing-projector` verifies
that an incomplete standard MLP is rejected before tensor reads; `yi` verifies
that the supported alternate layout still constructs a consumer.

## Bounded smoke wrapper

`run_smoke.sh` verifies the corpus seed, runs one libFuzzer process on CPU 0, and
uses a cgroup-v2 scope with `memory.max=4294967296` and `memory.swap.max=0`.
`cgroup_exec.py` fails closed unless those values and single-CPU affinity are
effective. LibFuzzer is limited to 60 seconds, 5 seconds per input and 4096 MiB
RSS; `chassis.campaign` adds a 90-second outer deadline.

```bash
targets/clip_mmproj/run_smoke.sh \
  "$build" \
  .runs/clip-mmproj-review-inputs/benign.gguf \
  .runs/clip-mmproj-review-corpus \
  .runs/clip-mmproj-review-smoke/batch1
```

Do not run further mutation batches while this target is parked. The retained
private input stays under ignored `.runs/`; it is not part of the review diff.

## Surface limits

- Selected consumer: CPU vision CLIP, projector type `mlp`, one transformer
  block, graph construction only.
- Proved: metadata accepted, 12 descriptors accepted, 12 tensor-read events,
  and a non-null consumer with output embedding size 4.
- Local fix proof: a standard MLP missing `mm.2.weight` rejects with zero tensor
  reads; a 16-tensor Yi-style layout loads all 16 tensors and constructs a
  consumer with output embedding size 4. The retained private input no longer
  produces an ASan diagnostic in one capped replay.
- Not proved: image preprocessing/encoding, numerical correctness, other CLIP
  architectures/projectors, GPU backends, long-run depth, exploitability,
  security impact, novelty, all malformed MLP combinations, or completeness of
  all private/public fuzzing. The independent fix review did not include a real
  Yi artifact, numerical inference, or tensor shape/dimension validation.
- Mutation counters are process-local. A sanitizer exit can prevent the `atexit`
  metrics line, so missing accepted/materialized counts are reported as
  unavailable rather than inferred from total executions.

See `../../docs/qualification/clip-mmproj.md` for the full review packet and local
evidence inventory.
