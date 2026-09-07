# Daybreak pilot: qualify CLIP/mmproj tensor materialization

Copy the brief below into an implementation task using Daybreak. This file is a
handoff artifact; writing it does not start an agent or create a new task.

## Objective

Implement the R1-R4 pilot in docs/ROADMAP.md. Determine whether mapfuzz can
reproducibly reach a useful CLIP/mmproj tensor-materialization surface under
resource caps. Deliver working qualification code and measured evidence, or a
well-supported early-stop report if the M0 or prerequisites fail. Do not assume
that a new harness is warranted or that a defect exists.

## Starting context

The planning checkout is `/mnt/f/mapfuzz/audit-hardening-dev` in WSL (Windows path
`F:\mapfuzz\audit-hardening-dev`). Baseline inspected: `8dc3101`. This includes
fail-closed campaign/triage handling and the Python-version resource-test fix.
The maintainer reported green CI; independently check the exact selected base.
The roadmap and brief may be committed after that SHA: include their reviewed
revision in your base or read the supplied documents explicitly.

Before editing, inspect branch/status and applicable AGENTS.md. Use an isolated
branch/worktree based on the agreed reviewed revision; report its SHA and path.
If this task was opened in an isolated worktree, use that worktree. Do not reset,
clean or overwrite someone else's working changes. Do not merge, push, publish,
contact upstream or modify unrelated target implementations in this pilot.
Run Git, tests and builds through WSL. Windows credential-based push is handled
by the maintainer from `F:\mapfuzz\repo` after review.

Read these files line by line:
- docs/ROADMAP.md, docs/TARGETS.md and docs/HARDENING-2026-09-07.md
- targets/clip_mmproj/README.md and every tracked file under that target
- chassis/campaign.py, chassis/resource_oracle.py and their regression tests
- evidence/schema.md and SECURITY.md

Verified local limitations: the existing harness passes no_alloc=true; the seed
generator supplies metadata without tensor data; there is no complete tracked
CLIP build script. The harness broadly catches C++ exceptions and can conceal
resource faults. Do not interpret its clean return as materialization evidence.
Historical comments about OSS-Fuzz coverage are not current facts.

## Execute in order

1. M0, at most two hours. Read current official upstream and public OSS-Fuzz
   build/harness sources. Record retrieval date, repository SHAs and immutable
   source links. Trace the actual consumer and compare call paths, seed coverage
   and mutation surfaces. Inspect current API and relevant public fix status.
   If the proposed work duplicates existing coverage or no defensible boundary
   is found, stop with the comparison and a recommendation. Do not switch targets.
2. Build, at most four hours. Select an immutable loader revision, exact compiler
   and dependency environment. Use a CPU-only ASan/coverage build with at most
   four build jobs. Record any overrides and local instrumentation patches.
   Create a reproducible build entry point, then replay from a fresh dependency
   and build directory. Network fetches must resolve immutable inputs; no moving
   main/develop/latest defaults or silent fallback builds.
3. Seed and reachability, at most four hours. Choose one supported architecture.
   Create a small deterministic synthetic seed containing the tensors required
   by its real consumer. Record tensor names, shapes, types, byte counts and seed
   SHA-256. No proprietary model download. Demonstrate the actual materialization
   milestones in pinned source: metadata accepted, descriptors accepted, tensor
   data consumed, and the selected bounded consumer constructed. Use trace/probe
   evidence with source locations and expected counts, not a harness-call counter.
   Use a malformed control rejected before materialization and a missing/truncated
   tensor control that distinguishes metadata success from data consumption.
   Verify that a benign replay succeeds repeatedly without ignored exceptions.
4. Failure behavior. Narrow exception handling based on documented loader behavior.
   Preserve visibility of allocation failure, unexpected exceptions, sanitizer
   diagnostics, timeout and abnormal exit. Validate tempfile/resource cleanup.
   Add focused regression tests for these changes. Never bypass upstream guards
   to force deeper reach. Keep instrumentation and any defect fix separate.
5. Smoke. Only after the controls pass, run three 60-second batches through
   chassis.campaign, one worker, CPU only, 4 GiB resident-memory ceiling, 5-second
   per-input timeout and 90-second outer deadline. Seed replays have a 15-second
   outer deadline. Prove how the host enforces caps; libFuzzer RSS monitoring is
   not a substitute for a hard host limit if allocation can outrun it. ASan maps
   large virtual regions, so do not use RLIMIT_AS as its RSS cap. If suitable
   containment is unavailable, finish qualification setup and report the blocker
   instead of running unbounded. Record all commands, versions, exits, seed hashes,
   attempted/accepted/materialized counts and new named functions/states per batch.
   Distinguish validation rejections from faults and seed replays from mutations.
6. Review packet. Run applicable core checks and provide the deliverables below.
   If a new fault appears, stop campaign expansion, retain artifacts locally and
   report class/status without including an undisclosed reproducer in the diff.

Routine implementation choices within these limits are yours. Escalate only a
concrete scope change, missing external prerequisite or action outside the pilot.
A time limit is a stopping rule, not permission to claim incomplete work passed.
No long campaign, GPU execution or scheduled automation is included.

## Deliverables

Prefer one focused review diff with clearly separable code, tests and evidence:
- `targets/clip_mmproj/build.sh` plus an exact environment/dependency manifest.
- A deterministic tensor seed generator and benign seed or reproduction recipe.
- A qualification entry point/probes and focused tests. Proposed filenames may
  change if the repository convention gives a better fit; explain the mapping.
- Updated target README with reproducible commands and precise surface limits.
- `docs/qualification/clip-mmproj.md` using the review template. Include M0,
  pin/toolchain, fresh-build replay, milestone/control results, smoke metrics,
  stop/continue decision and everything not tested.
- A list of local log/artifact paths and hashes. Raw logs stay in ignored paths
  unless individually reviewed as safe for publication. Do not fabricate missing
  evidence, overwrite historical claims or include private reproduction material.

Only add a claim to evidence/claims.yaml when its actual measurements, provenance
and boundary are available; regenerate claims.md and run the validator afterward.
If the pilot stops at M0, deliver its report without claiming build/seed completion.

## Required checks

Use the recorded compatible environment, then run from your worktree root:

```bash
python3 -m unittest discover -s evidence -p 'test_*.py'
python3 -m unittest discover -s chassis/tests -p 'test_*.py'
python3 chassis/tests/test_triage.py
python3 chassis/resource_oracle.py --selftest
python3 evidence/tool.py --check --render
python3 chassis/check_repository.py
git diff --check
```

Record the Python version; replay resource tests on 3.10 and 3.12 when available.
If a version is unavailable, report that and use exact-head CI for that coverage.
Also run your build/seed/control qualification and changed-code tests. If evidence
was untouched, confirm regenerated claims.md is unchanged; if updated, review it.
Report actual results, never 'should pass'. Do not alter unrelated tests to get green.

## Acceptance and final response

A pass requires a demonstrated useful gap, reproducible instrumented build,
positive and negative semantic controls, functioning resource/failure gates and
bounded run evidence. It permits independent review, not automatic campaign
promotion. A documented M0 stop is an acceptable completed investigation, but is
not a qualified target. Use the exact disposition in the review template.

Finish with: base and resulting branch; changed files; commands and outcomes;
semantic milestones and counts; log locations; any observed fault class; limits;
and one next action. Leave the code reviewable and do not push it.
