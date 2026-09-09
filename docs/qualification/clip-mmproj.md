# CLIP/mmproj tensor-materialization review packet

## Identity and scope

- Package ID and objective: R1-R4 Daybreak CLIP/mmproj pilot; determine whether
  mapfuzz can reproducibly reach a useful tensor-materialization surface under
  the prescribed caps.
- Author/model and independent reviewer: Codex implemented and replayed the
  package; a separate Codex reviewer task independently replayed and traced the
  candidate on 2026-09-08.
- Date, base SHA, implementation SHA or working-diff identity: 2026-09-07;
  `5e52993f0abd7c1a9428e659e0c007fd15c5caff`; uncommitted working diff on the
  branch below (staged locally for review, with no commit).
- Worktree/branch and exact-head CI link/status:
  `/mnt/f/mapfuzz/audit-hardening-dev`, `daybreak-clip-qualification`;
  exact-head CI is unavailable because this local branch was not pushed. Local
  required checks are recorded below.
- Disposition: **CHANGES-REQUIRED**
- What this disposition establishes and does not establish: M0 found a useful
  current public-coverage gap; two isolated builds and semantic controls reached
  real tensor reads and graph construction. The first mutation batch produced a
  reproducible ASan null-read candidate, so batches 2 and 3 were not run. This
  report now also includes a local layout-validation fix and deterministic
  regression evidence. This does not establish novelty, exploitability,
  security impact, complete public or private fuzz coverage, fix completeness,
  or readiness for promotion. Independent review accepted the fix narrowly for
  the observed standard/Yi layout and retained-input paths.

## M0 and novelty boundary

| Source | Immutable revision and link | Retrieved date | Relevant path/entry point | Observation |
|---|---|---|---|---|
| Loader | llama.cpp [`67672dc5b76f8bc17785a19d3dc6d1463fc2902c`](https://github.com/ggml-org/llama.cpp/blob/67672dc5b76f8bc17785a19d3dc6d1463fc2902c/tools/mtmd/clip.cpp#L3957-L4012) | 2026-09-07 | `clip_init`; `clip_model_loader::load_tensors`; `clip_model_loader::init_ctx` | `clip_init` loads hparams, synchronously reads tensors when `no_alloc=false`, then constructs a bounded graph before returning a context. |
| Public fuzz build and harness | OSS-Fuzz [`26191226a5539ae6048dce12740857febaea107d`](https://github.com/google/oss-fuzz/blob/26191226a5539ae6048dce12740857febaea107d/projects/llamacpp/build.sh) | 2026-09-07 | `projects/llamacpp/build.sh`; six produced harnesses | The build produces `fuzz_json_to_grammar`, `fuzz_apply_template`, `fuzz_grammar`, `fuzz_load_model`, `fuzz_inference` and `fuzz_structured`; none calls `clip_init`, `mtmd_init_from_file`, or links the mtmd loader. This is absence from the inspected public build, not proof that no other fuzzing exists. |
| Public prior art/fix status | PR head [`32d5f124dc09c828705e7d8f30dc9949514ae0f9`](https://github.com/ggml-org/llama.cpp/commit/32d5f124dc09c828705e7d8f30dc9949514ae0f9), base `4df29be4f4c3673f428170fda944a5b19f743bb8` | 2026-09-07 | [llama.cpp PR 27202](https://github.com/ggml-org/llama.cpp/pull/27202) | The public PR covers scalar metadata-type validation and a layer-count bound. Its API snapshot was open, non-draft and unmerged. Its described campaign was metadata-focused; it does not remove the tensor-materialization comparison gap. Status can change after retrieval. |
| Current upstream source check | llama.cpp master [`f3f1a8f2760f28325a5ec20c05b171e5b7c83a29`](https://github.com/ggml-org/llama.cpp/blob/f3f1a8f2760f28325a5ec20c05b171e5b7c83a29/tools/mtmd/clip.cpp#L2204-L2209) | 2026-09-08 | MLP tensor loading and [`clip_n_mmproj_embd`](https://github.com/ggml-org/llama.cpp/blob/f3f1a8f2760f28325a5ec20c05b171e5b7c83a29/tools/mtmd/clip.cpp#L5562-L5575) | The current master source still requests MLP `mm.2.weight` with `required=false`, then dereferences `mm_2_w` unconditionally when deriving the projector embedding size. This is source confirmation only; the private input was not replayed against current master. |
| Current-master fix validation | llama.cpp master [`df750f76bb6126566621803b69ddaeb993be5b08`](https://github.com/ggml-org/llama.cpp/blob/df750f76bb6126566621803b69ddaeb993be5b08/tools/mtmd/clip.cpp#L2341-L2354) | 2026-09-09 | MLP tensor loading and [`clip_n_mmproj_embd`](https://github.com/ggml-org/llama.cpp/blob/df750f76bb6126566621803b69ddaeb993be5b08/tools/mtmd/clip.cpp#L5912-L5924) | The gap remained on the newly pinned master. The standalone layout patch applied cleanly to the pristine index. The fresh CPU ASan/coverage validation build included the known-blocker, `std::bad_alloc`, and layout patches, completed 278/278 steps, passed tracked controls, and produced only the expected pre-read rejection with no ASan diagnostic in one capped private replay. |
| Public duplicate check | [llama.cpp discussion 5092](https://github.com/ggml-org/llama.cpp/discussions/5092) and repository-scoped GitHub issue, pull-request and code searches | 2026-09-08 | Missing `mm.2.weight`; MLP loader and dimension path | The search found a 2024 Yi-VL report where a required-tensor lookup rejected a missing `mm.2.weight`, plus unrelated `clip_n_mmproj_embd` failures. No public report of this exact optional-lookup then null-dereference chain was found. Search incompleteness prevents a novelty claim. |

The trust boundary is an untrusted GGUF projector file passed to the supported
multimodal consumer. The current consumer enters at
[`mtmd_init_from_file`](https://github.com/ggml-org/llama.cpp/blob/67672dc5b76f8bc17785a19d3dc6d1463fc2902c/tools/mtmd/mtmd.cpp#L1085-L1093),
whose constructor calls `clip_init` at lines 568-588. The pilot directly targets
that same loader to isolate a one-layer CPU vision-MLP consumer. The inspected
OSS-Fuzz harnesses cover text-model/container, inference, grammar, template and
structured-input surfaces, but not this call path. Upstream mtmd tests exist;
no public mtmd fuzz harness was observed in the pinned repository tree. These
observations do not exclude unpublished, private, downstream or later coverage.

## Reproduction environment

- Host: Ubuntu 22.04.5 LTS on WSL2, Linux
  `6.6.87.2-microsoft-standard-WSL2`, x86_64.
- Tools: Git 2.34.1; Clang/Clang++ 14.0.0
  (`Ubuntu clang version 14.0.0-1ubuntu1.1`); CMake 3.22.1; Ninja 1.10.1;
  Python 3.10.12. Python 3.12.13 was also available for resource tests.
- Upstream: llama.cpp `67672dc5b76f8bc17785a19d3dc6d1463fc2902c`.
  The external checkout and build directory were created from empty paths.
- Build: `RelWithDebInfo`, static libraries, CPU backend, native tuning and
  OpenMP disabled, ASan enabled, LLVM source coverage enabled, maximum four
  build jobs. No Docker daemon was available or used.
- Local patches: known loader blockers
  `15bfac1a77572f6c3967017ca11ae54f71811a37443939cdd5219ab5231350c0`;
  separate `std::bad_alloc` rethrow/cleanup patch
  `345d2292b24ef8d4d8f78780622f7ebf487b836edd762d56d5005f041f66f1b2`;
  separate MLP-layout validation patch
  `8f14466c46b1f3918768c9a6b9f9241a7fd4d0abd8f1ac0b3bbba2c499ee3692`.
  Both the pinned and current-master validation builds included all three
  qualification patches. The layout patch also passed a standalone
  `git apply --check` against the pristine current-master index; it was not
  compiled alone.
  The bad-allocation patch preserves allocation-failure visibility but does not
  classify every other `std::exception` that upstream converts to a null result.
  The layout patch requires the complete standard `mm.0`/`mm.2` tensor set or
  the complete Yi-style `mm.0`/`mm.1`/`mm.3`/`mm.4` set before materialization.
- Replay override: WSL PIE+ASan launches with ordinary address randomization
  failed before producing output in 4/20 and 6/20 bounded trials. With
  `setarch x86_64 -R`, 20/20 trials reached the consumer. The tracked replay and
  smoke commands therefore use that wrapper. Root cause is inferred to be
  process-startup/instrumentation interaction; it was not proved by a kernel
  setting read, which was unavailable.

Exact initial and fresh-directory build commands:

```bash
CLIP_MM_PROJ_WORK_ROOT="$PWD/.runs/clip-mmproj-build-2" \
  targets/clip_mmproj/build.sh > .runs/clip-mmproj-build-2.log 2>&1
CLIP_MM_PROJ_WORK_ROOT="$PWD/.runs/clip-mmproj-build-3" \
  targets/clip_mmproj/build.sh > .runs/clip-mmproj-build-3.log 2>&1
CLIP_MM_PROJ_WORK_ROOT="$PWD/.runs/clip-mmproj-fix-build-authorized" \
  targets/clip_mmproj/build.sh
```

The first two builds resolved the same source and patch hashes and completed all
278 Ninja
steps. The build logs contain SHA-256
`45067a549a9f1fc7b16a758243e3ff9a255dc8c3769f2c76437a9b1f638541de`
for the same bad-allocation hunk before its patch-file-only blank-context
normalization; the inserted source lines are unchanged, and the current patch
passes `git apply --check` against the pristine pinned checkout. Build 3 was the
fresh replay. The toolchain installation was reused;
the llama.cpp source checkout, CMake configure and all compiled objects were
rebuilt. The current script adds fail-closed tool-version and architecture
assertions after those builds; that assertion path was exercised and reached
the expected refusal to reuse build 3. The compile/fetch steps were unchanged.
The third command used the current script, applied the layout fix separately,
and completed all 278 steps from an empty source/build root.

| Build | `clip-mmproj-seed` | `clip-mmproj-qualify` | `fuzz-clip-materialize` |
|---|---|---|---|
| Initial patched build 2 | `5fd42256e974e615be0e7fddbb732566910d7a0d2828f5ed3d7e14ca20117f55` | `76bebb6cfad69ef51cee2d14d380e9b5151909cf026eadb78c736451df5ac66e` | `43e234baafa23d1fc650b40f5af1fbcbd5a1e97fc090a9ed48f4abaf4f18bdc1` |
| Fresh patched build 3 | `f50aa0015df6b3d27f74f02e1b9347dd2cbf7fa8fc80caeedc91e579faecfa32` | `fbbe32babfad1f4e3d5714aec6843c187efd310e498a06a7cccc29ce4f09f17a` | `457a2123b74899deff3201e39a458153dac3e83be34579e868005788d57cab0d` |
| Fresh local-fix build | `281f58a0f66b1c7d7314d4afd4c292005c868344f538cebadbdf068bd4db572f` | `75242cd67abf9522a6c392d37f1d80d83d1a6b159a7980d089790b75e04d17bb` | `ec3b72acdf2f6a3e9fd6ad48d48742b80f1f53604603412e10deec5a43154488` |
| Current-master local-fix build (`df750f76bb6126566621803b69ddaeb993be5b08`) | `fd7f8a2c458b521c9693eb288dedf321f26b13ff936113d8030944f732e33a6e` | `acfe1053666a3c19f9e81a80cdf2d02c70c1233e3067b932e6671beac0d4e5dc` | `3186e11ad4767ba2512fc7ae657a6ca7753e38032c3687cc8bc4dc40ce3fb40b` |

The binary hashes differ because absolute source/build paths are retained in the
instrumented debug binaries. Reproducibility is instead established by identical
source/patch identities, successful fresh compilation, byte-identical generated
seed and repeated semantic outcomes. The benign seed is 2,304 bytes with SHA-256
`858b1e02a7a0eb809cafd6f39f441044a89cb0fbda59c7d575dbf157e3b74106`
in both builds.

## Semantic controls

| Benign/control input and hash | Expected milestone | Observed milestone/count | Source probe location | Exit/result | Local evidence |
|---|---|---|---|---|---|
| Tensor-carrying seed, `858b1e02a7a0eb809cafd6f39f441044a89cb0fbda59c7d575dbf157e3b74106` | Metadata and all required descriptors accepted; 12 reads; vision consumer constructed | 12 descriptors, 880 declared tensor bytes, 12 increasing read callbacks out of 13 total callbacks, final progress 1.0, non-null vision context, output embedding 4 | Pinned `clip.cpp` 3584-3637 and 3957-3976; `qualification/qualify_clip.cpp` | Exit 0 in three original replays; two later stabilized suites passed, each containing three benign replays | `.runs/clip-mmproj-controls/benign-replay-{1,2,3}.log`, each SHA-256 `2ba1f568067ed8385c68fd3f9c4de474ab9dbcdc61bd59f4a8e69cbd9055ab23`; fresh suite hashes below |
| Malformed metadata, `56e93fe949d1a866caa36a01323b51fb7c8ac2aceda2fbf02ddd619d25d12f67` | GGUF metadata/descriptors parse, unsupported projector rejects before reads | Metadata accepted, 12 descriptors, 0 tensor-read events, consumer rejected | Same loader/probe; `clip.projector_type=mapfuzz-unsupported` generated by tracked code | Exit 4, expected gate | `.runs/clip-mmproj-controls/malformed-replay.log`, SHA-256 `de25f493e2a030af329f5f01121c9f9249da8508936bfa0a119d0a5c8f638731` |
| Missing required tensor, `187fff0173eeca0a9154709019bcd34c7f87608016abd74cedfb7fa5780bb2a1` | Metadata parses but required-tensor validation rejects before data consumption | Metadata accepted, 11 descriptors, 0 tensor-read events, consumer rejected | Same loader/probe; tracked generator omits `v.blk.0.attn_out.weight` | Exit 4, expected gate | `.runs/clip-mmproj-controls/missing-replay-clean.log`, SHA-256 `728a3a4931dd933e58165baaeb3aabc7380af77f087669ef4adae6668e4e5fda` |
| Missing standard projector weight, `8805edc16998de15aeba0df435357268b072d33884fd9b89c6f0795c6bb45fa8` | Layout validation rejects an incomplete standard MLP before data consumption | Metadata accepted, 11 descriptors, 0 tensor-read events, explicit missing-`mm.2.weight` rejection | Local MLP-layout patch after optional projector lookups; tracked generator omits `mm.2.weight` | Exit 4 in the focused Python test, expected gate | `.runs/clip-mmproj-fix-verification/missing-projector.log`, SHA-256 `8dd09c242b774a4090c2d7c3c2fe080783fa489fa2cf2cbee236a050bbaf6fef` |
| Yi-style MLP, `fafbd5ff5f61b76dabeb86fbe851beda36cbd87d6043946e1a0ae9b8339ed2a8` | Complete alternate layout remains supported | Metadata accepted, 16 descriptors, 16 tensor-read events, non-null vision context, output embedding 4 | Same validation patch; tracked generator supplies complete `mm.0`/`mm.1`/`mm.3`/`mm.4` layout | Exit 0 | `.runs/clip-mmproj-fix-verification/yi.log`, SHA-256 `d9f90c07236665c34137c7df3b9545027a55a4e8869df22c041a7c08d10a8852` |

The selected architecture is a minimal one-layer vision CLIP MLP: embedding 4,
one attention head, feed-forward width 8, image/patch size 2, projection width 4.
It has 12 F32 tensors: patch embedding `2x2x3x4` (192 bytes), positional
embedding `4x1` (16), four attention matrices `4x4` (64 each), feed-forward
up `4x8` (128), down `8x4` (128), and MLP projector weights/biases `4x4`,
`4`, `4x4`, `4` (64, 16, 64, 16).

For the CPU backend, pinned lines 3617-3620 read file bytes directly into the
allocated tensor buffer, synchronously. Each progress increment occurs after the
corresponding `fin.read`; the callback only records progress and returns true.
`strace` independently observed reads spanning the tensor-data region. Thus
materialization here means copied bytes, not a mapped descriptor or deferred
load. Consumer construction is separately required after `init_ctx`; no image
encode or numerical inference was run.

## Bounded runs and resource behavior

The pre-run scope printed `memory.max=4294967296` and `memory.swap.max=0`, proving
the 4 GiB cgroup-v2 hard limit and disabled swap for the process tree. The actual
batch requested `CPUQuota=100%`; a later scope with the same property exposed no
readable `cpu.max`, so that request is not reported as proved effective. The
batch did use one libFuzzer worker and
CPU-only loader settings. After the stop, the tracked wrapper was tightened to
`taskset -c 0`; a gate-only replay proved `cpu_affinity=[0]` together with the
same memory/swap values. No mutation batch was rerun with the tightened wrapper.

Actual batch 1 command, abbreviated only by line wrapping:

```bash
systemd-run --user --scope --collect \
  -p MemoryMax=4294967296 -p MemorySwapMax=0 -p CPUQuota=100% \
  python3 targets/clip_mmproj/qualification/cgroup_exec.py \
  python3 -m chassis.campaign \
  --output .runs/clip-mmproj-smoke/batch1 --timeout 90 -- \
  .runs/clip-mmproj-build-2/build/fuzz-clip-materialize \
  -max_total_time=60 -timeout=5 -rss_limit_mb=4096 \
  -jobs=1 -workers=1 .runs/clip-mmproj-smoke/corpus
```

Counters are per `LLVMFuzzerTestOneInput` call: attempted increments on entry;
accepted requires a non-null vision context; materialized requires at least one
post-read progress increase. The libFuzzer parent emitted
`attempted=0 accepted=0 materialized=0`, but the crashing worker did not execute
the `atexit` metrics callback. Those zeroes therefore have the wrong denominator
and are not used. The last libFuzzer progress counter was 118, but it is not
substituted for the unavailable harness attempt count. Counter overhead is three
atomic increments at most plus one boolean/float progress update per input.

| Batch | Duration/limits | Attempts | Accepted | Materialized | New states/functions | Result/log hash |
|---|---|---|---|---|---|---|
| 1 | Approximately 1.7 s before fault; requested 60 s, 5 s/input, 90 s outer; effective 4 GiB cgroup and no swap; maximum progress-reported RSS 89 MiB, true peak unavailable | Unavailable; last libFuzzer progress counter 118 | Unavailable; worker metrics not flushed | Unavailable; worker metrics not flushed | New ASan fault state: near-null read in `clip_n_mmproj_embd` during `clip_graph_llava` construction; exact new function coverage unavailable | Exit 1, not outer timeout; `result.json` `6f7c7c86ff3e69da754ba830f62482ecfbfdca57a74fb111add8609a61b3d89b`; `run.log` `09e005b59410e5779cbf02b63e15da7de3379c2d1899b74ed58979bebe9a0bdd` |
| 2 | Not run: mandatory stop after batch-1 sanitizer fault | Not run | Not run | Not run | Not run | Not run |
| 3 | Not run: mandatory stop after batch-1 sanitizer fault | Not run | Not run | Not run | Not run | Not run |

Failure controls:

- Malformed metadata and missing required tensor both produced the expected
  pre-materialization rejection gate with zero read events.
- Wrong resource settings: the cgroup checker failed closed at 3 GiB instead of
  the required 4 GiB. The current correct memory/swap/affinity gate
  then passed with `/usr/bin/true`; it was not used to resume mutations.
- Allocation failure: the separate patch rethrows `std::bad_alloc`; an actual
  loader OOM was not induced, so end-to-end allocation-failure behavior remains
  untested.
- Tempfile cleanup: the focused fuzzer replay compared `/tmp/mapfuzz_clip_*`
  before/after and passed. Sanitizer, timeout and abnormal process exits remain
  visible to `chassis.campaign`; the batch-1 exit was recorded as a diagnostic
  failure rather than success.
- Local fix regression: the generated missing-projector control rejected before
  reads, and one retained-input replay under CPU 0, 4 GiB, no swap, 5-second
  fuzzer timeout and 15-second service deadline exited cleanly with
  `attempted=2 accepted=0 materialized=0` and no ASan diagnostic. This proves the
  observed reproducer is blocked, not that every malformed layout is safe.

## Independent review

- Exact commands replayed by reviewer and environment differences: the reviewer
  verified HEAD, binary and input hashes, then ran exactly one private input with
  `setarch x86_64 -R`, one-CPU affinity, `memory.max=4294967296`,
  `memory.swap.max=0`, `RuntimeMaxSec=15s` and fuzzer `-timeout=5`. The replay
  exited 1 after approximately 0.57 seconds, before either deadline. After the
  local fix, the same separate reviewer verified the fresh-build provenance,
  replayed the tracked standard, missing-projector and Yi controls, ran the
  focused suite, and replayed the retained input once under the same caps.
- Benign/control outcomes compared with the author's report: the reviewer did
  not rerun the original controls during fault triage; it independently
  reproduced the retained fault and matched the reported MLP,
  12-declared/10-loaded graph-construction path. During fix review, the standard
  control reached 12 descriptors/reads and output embedding 4; the incomplete
  projector reached 11 descriptors, zero reads and the explicit
  missing-`mm.2.weight` rejection; the Yi control reached 16 descriptors/reads
  and output embedding 4. The focused suite passed 2/2 in 0.415 seconds.
- Core tests, workflow results and changed-code tests: evidence 5/5; chassis
  7/7; triage 3/3; resource-oracle self-test passed; resource tests 5/5 on both
  Python 3.10.12 and 3.12.13; qualification 2/2; repository checker, shell
  syntax, pristine-patch apply check and `git diff --check` passed. Exact-head
  hosted workflow result is unavailable for the unpushed branch.
- Exception handling, resource cleanup and instrumentation diff checked: read
  line by line by the author. `std::bad_alloc` is rethrown after cleanup; the
  harness has no catch-all; tempfiles use RAII. Other upstream-caught standard
  exceptions are still not semantically classified, a remaining limitation.
- Private artifacts and accidental disclosures excluded from review diff: yes;
  one 2,304-byte artifact remains only under ignored `.runs/`. Its bytes and
  filename are not in this diff. The fix-review private directory contains only
  its replay log, with no reproducer copy or encoded payload.
- Claims/render synchronization and scope wording checked: yes;
  `evidence/tool.py --check --render` passed for 44 claims and `claims.md`
  remained byte-identical at SHA-256
  `961384a5aebf7ea0c002afce356881858c563c28539795d525762782641036f0`.
  No claim addition is proposed because the fault's impact and novelty are
  unconfirmed.
- Unresolved contradictions or limitations: no actual OOM control; smoke
  counters lost on sanitizer exit; true peak RSS unavailable;
  current affinity/ASLR wrapper not mutation-tested after the mandatory stop;
  intermittent ordinary-ASLR ASan startup failures are mitigated but root cause
  is unproved; image encode/inference and non-MLP surfaces were not tested. Fix
  review used synthetic graph construction, not a real Yi artifact or numerical
  inference; shape/dimension validation and mixed-layout compatibility remain
  unproved. A separate non-projector tensor-validation gap is outside this fix.

## Decision

**CHANGES-REQUIRED.** R1 passed: the pinned public OSS-Fuzz build does not target
the actual mtmd/CLIP load path. R2 and R3 produced isolated instrumented builds,
a byte-stable tensor seed and positive/negative semantic controls. R4 stopped in
batch 1 as required when ASan reported a read near address `0x18` in
`clip_n_mmproj_embd`, reached from `clip_graph_llava` construction. One private
single-input replay on the pristine build, one on the patched build and one on
the fresh build under `setarch -R` reproduced that fault class. A separate
reviewer then reproduced the same path once and confirmed that pristine and
patched source both perform an optional MLP `mm_2_w` lookup followed by an
unconditional dereference during graph construction. A 2026-09-08 read-only
check confirmed the same source pattern on current upstream master at
`f3f1a8f2760f28325a5ec20c05b171e5b7c83a29`. Public searches found older
missing-`mm.2.weight` handling reports but no exact duplicate of this chain.
This is a finding candidate only; neither security impact nor novelty is
established.

The subsequent local fix requires the complete standard or Yi-style MLP tensor
layout immediately after optional lookup. A fresh 278-step build passed; the
standard benign path, incomplete-projector rejection, valid Yi path, focused
suite and one capped retained-input replay all produced their expected outcomes.
The same patch applies cleanly to current upstream master
`df750f76bb6126566621803b69ddaeb993be5b08`. A 2026-09-09 fresh build against
that revision included all three qualification patches, completed all 278
steps and passed the same focused suite in 0.440 seconds. Standard and Yi replay
logs recorded 12/12 and 16/16 descriptor/
read milestones respectively; the incomplete projector recorded 11 descriptors,
zero reads and the explicit missing-`mm.2.weight` rejection. One capped private
replay reported `attempted=2 accepted=0 materialized=0`, two expected rejections
and zero ASan diagnostics. Independent review accepted the pinned local fix:
the standard and Yi controls constructed their consumers, the incomplete
projector rejected before reads, and one capped retained-input replay exited 0
in approximately 0.5 seconds with `attempted=2 accepted=0 materialized=0` and
no ASan diagnostic.

The current-master port and regression gate are complete. A normal hardening PR
is technically supportable, but the draft remains local and unopened. Run no
further mutations. Opening a pull request or making any disclosure remains a
separate explicitly authorized action.

## Local evidence inventory

All paths below are ignored local files; raw logs and reproduction bytes are not
part of the review diff.

- M0 snapshots: `.runs/daybreak-clip-m0/sources/`; key SHA-256 values are
  `5b2b58d219b68fb1c71ee059536cc87f1b566091dd468b2529387eb1a7fef7fb`
  (`clip.cpp`),
  `b5f5660650d5abd1b8e23b6e4246f33eedc73b79fc904c2ff521796060bd56bb`
  (`mtmd.cpp`), and
  `b5b385618b756a4b7ec9578dfef5ff81f63d31e3e3e2e341d08d1ecd23213ba2`
  (OSS-Fuzz `build.sh`). PR API snapshot:
  `.runs/daybreak-clip-m0/pr-27202.json`,
  `ef52dd35fa718fe2ab00c4124c0acf858db9453cbb8ec56ca7248fa2162cbf95`.
- Build logs: `.runs/clip-mmproj-build-2.log`,
  `0e302340bdfb5c55ac59496d9bd1d662858149b5275780193b9af9fb20e6c47f`;
  `.runs/clip-mmproj-build-3.log`,
  `b8b3356d7e026037dfe0e35e0ca6fe0776f6defba2348ad7ffb11f6112a03a3a`.
- Final required-check log: `.runs/daybreak-clip-final-checks-3.log`,
  `5c6de56eb9b8c085edb92e7c0fe8ad79724e9eb07d2cf804beb1ba41dada8c99`.
- Stable fresh-build test logs:
  `.runs/clip-mmproj-build-3/qualification-tests-stable-1.log`,
  `cecb237906b33ce1a9db026323aabc82fc7df92d9e0d931b0fd7d1456e1a9206`;
  `qualification-tests-stable-2.log`,
  `b5f63d26b1c3be36e78441eab10f17eae6364c28169c3348d2a052f19deaa197`.
  The ordinary-ASLR intermittent-failure log is
  `.runs/clip-mmproj-build-3/qualification-tests.log`,
  `cf5d25affaf5e23057ec9b83c155e2d6fb4c79795632ef5f436da50155edace5`.
- Independent read trace within this implementation task:
  `.runs/clip-mmproj-controls-2/benign-clean.strace`,
  `07e4fcb1baf208ecfb2bc0c71dc085ed93eea8f9210e25a816b65e5ce30c4d79`;
  paired replay log `benign-strace-clean-replay.log`,
  `26a26f6e9420db6ed4f5debd8f084d4ef63f5d509cbbfc2f56cb0121623bf68d`.
- Smoke wrapper log: `.runs/clip-mmproj-smoke/batch1-outer.log`,
  `549b49563285e1ff41ad23a7a1e0f06c59ceff0db4ece158033e02db65e73331`.
  Batch result and run-log hashes are in the table above.
- Resource-gate controls: `.runs/clip-mmproj-resource-gate-wrong-2.log`,
  `f459b3c675d0c9790ad591811a32e182fdaf4ef11c77b2f049d3118dfee95c83`;
  `.runs/clip-mmproj-resource-gate-correct-2.log`,
  `94c93bbd33d78b164701e5a96a04dd21f30601bbe7ca9017aa7cc88afbd90d7b`.
- Private retained artifact: one file in
  `.runs/clip-mmproj-smoke/batch1/artifacts/`, 2,304 bytes, SHA-256
  `195d9f2a8bc6832e519b3812b9b3b05c9b3ba56456d4c7e912a7f320bcb0269b`.
  Its filename and content are deliberately omitted.
- Stabilized private replay summary:
  `.runs/clip-mmproj-private-replay/patched-setarch.log`,
  `3c4ea818b1004d87b36068219450415bbc3e9271c086223f40a801291a7ee6c2`.
  Earlier pristine and patched replay logs are
  `c7a78360e8cc383d499e68dd9b235705102b51182e1a8d4f1bdb1bc44aad888b`
  and `74efac66aa1fa184b10f54411fb333c00f56d262770f4ba34237340a909c4116`.
- Independent reviewer replay:
  `.runs/clip-mmproj-independent-review-2026-09-08/single-input-replay.log`,
  6,460 bytes, SHA-256
  `039d4b5bafb6681925ac0ea7a963ee4bf56dd5baf629877db9c17ea6c2b2bbf2`.
  The ignored review directory contains no reproducer copy or encoded payload.
- Local fix verification: fresh build root
  `.runs/clip-mmproj-fix-build-authorized/`; focused-test log
  `.runs/clip-mmproj-fix-verification/focused-tests.log`, SHA-256
  `865a767d5d26223805f3f4ddd066fde3e123eebf389ec574ce305f9c09ddd080`;
  required-check log `required-checks.log`, SHA-256
  `83af9bc50ec7cf3aebed973de595cb5dddc5e971a94acd3fcfc79db2d6e12502`;
  provenance log `provenance.log`, SHA-256
  `0e79260636aaf924a9a2e4dfe9fc5f5fb912ac51fdd06da905ad60619dcbf89c`;
  capped private replay `private/replay.log`, SHA-256
  `3c978c1f9e0d061f844585eb2aa3175482620496db20ba4d1961535313c0bcd7`.
- Independent fix review:
  `.runs/clip-mmproj-independent-fix-review-2026-09-08/`; standard replay
  `controls/benign-replay.log`, SHA-256
  `c6091a8464bdc107b828075b4cee57a2896b0ffab855256517a649447eebd39f`;
  incomplete-projector replay `controls/missing-projector-replay.log`, SHA-256
  `b192bb81fac0020702fa3d0be7244ba8c9edc54e7b52d39a58bcfc98eab9f55b`;
  Yi replay `controls/yi-replay.log`, SHA-256
  `a49634982e29e91d29b974812cdd997bdd112df43d76818b30765b5efae42f25`;
  focused suite `focused-tests.log`, SHA-256
  `c322527d1fd6babbce41d4f96de13ff537e0d99be967479ff4ba87fa9011db0c`;
  capped private replay `private/replay.log`, SHA-256
  `1d20074938b02579b78a9d035fd90979369102dc2e514012fcd4f7a0238212c2`.
  The private subdirectory contains only the replay log.
- Current-master validation:
  `.runs/clip-mmproj-current-master-2026-09-09/` at
  `df750f76bb6126566621803b69ddaeb993be5b08`; standard replay
  `verification/benign-replay.log`, SHA-256
  `4ca9e9c9d9af388a9cc66c8985c450479e4f9dd3a52dab8a2bed676ee779b21f`;
  incomplete-projector replay `verification/missing-projector-replay.log`,
  SHA-256
  `23a24027752800bf5c4f8059adc0d7fd8dc3cb857c1b73d89044642534d66859`;
  Yi replay `verification/yi-replay.log`, SHA-256
  `1f9525ac04d644d4b95b7c877573b1d254ea059ca988790f7557d082eaccf392`;
  focused suite `verification/focused-tests.log`, SHA-256
  `a5e446df38486c4b99c52dcc1fda93946220927364fb0bdcb1bbe9347c9b5467`;
  capped private replay `verification/private/replay.log`, SHA-256
  `2189dcfa87ac8d69df7e1c0ffe650ef7dcfd5240e1879694bbdb47f28fd97068`.
