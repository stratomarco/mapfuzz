# mapfuzz implementation roadmap

Planning baseline: 8dc3101, inspected on 2026-09-07. The maintainer reports the
latest CI run is green; this planning pass did not independently query GitHub.
The hardening branch is not assumed merged. This roadmap authorizes no merge,
publication, upstream contact or long campaign by itself.

## Working agreement

The planning/review task owns priorities, acceptance criteria and independent
review. Daybreak implements one bounded work package at a time. The maintainer
owns merges, publication and disclosure. Model identity is not evidence of
correctness: the same review criteria apply to every implementation.

Each package uses an isolated branch/worktree from an explicitly recorded base.
Do not concurrently edit the same checkout from two tasks. Run builds, tests and
Git in WSL for this linked worktree. The maintainer can push its branch with
Windows credentials from `F:\mapfuzz\repo`; do not use Windows Git inside the
WSL-linked checkout. Never copy private artifacts into a public review diff.

Reference documents:
- [Target inventory and promotion contract](TARGETS.md)
- [Implemented hardening and its limits](HARDENING-2026-09-07.md)
- [Daybreak pilot brief](tasks/DAYBREAK-CLIP-QUALIFICATION.md)
- [Independent review template](tasks/RESEARCH-REVIEW-TEMPLATE.md)

## Delivery order

| ID | Work package | Dependency | Reviewable outcome | Exit condition |
|---|---|---|---|---|
| R0 | Close the hardening review | Existing branch | Reviewed exact-head diff and CI evidence; baseline recorded | Merge only through maintainer workflow; otherwise use the explicitly approved branch base |
| R1 | CLIP/mmproj current M0 | R0 base selected | Pinned upstream/OSS-Fuzz source inventory, consumer map and coverage comparison | Continue only with an identified useful gap; otherwise return a documented duplicate/uncertain result |
| R2 | Reproducible CLIP build | R1 passes | CPU instrumented build, exact dependency/toolchain record and fresh-build replay | Both builds exercise the real selected loader; unresolved prerequisites are reported |
| R3 | Valid seed and semantic reachability | R2 | Deterministic tensor-carrying seed, milestone probes and negative controls | Actual tensor bytes consumed and bounded consumer construction proved; metadata-only success does not pass |
| R4 | Short qualification runs | R3 | Capped smoke results, failure-path tests, semantic counters and resource measurements | Qualification decision, not automatic promotion to long fuzzing |
| R5 | Independent review and disposition | R1-R4 report | Replayed critical evidence and reviewed diff | Accept qualification, request changes, or park the target |
| R6 | Depth campaign or next M0 | R5 | Separately scoped task with compute budget | Continue only with measurable new semantic reach |

R1-R4 form the first Daybreak pilot. R1 may legitimately end the pilot early;
a well-supported decision that the surface duplicates existing work is useful.
No target is promised a finding. Do not pre-assign a vulnerability count.

## R0: checkpoint and integration

Review the exact branch head, workflow results and intended changes. Include the
Python 3.10/3.12 resource-test correction. Check that private files, generated
campaign artifacts and local environments are absent from the staged diff.
Record the selected base SHA and review URLs in the handoff report. The user's
'all green' report is historical context, not a substitute for fresh checks at
merge time. Creating the roadmap does not establish that R0 is complete.

## R1-R4: first implementation pilot

Use the complete brief linked above. Its scope is qualification of one CPU
CLIP/mmproj loader family, not restoration of every target or a suite-wide fuzzing
service. Choose an architecture supported by the pinned source and justify it.

Proposed default effort limits for the pilot:
- R1: two hours of source/coverage reconnaissance.
- R2: four hours of build qualification, at most four compiler jobs.
- R3: four hours of seed and probe development.
- R4: three 60-second campaigns after controls pass; seed replay at most 15
  seconds each, outer campaign deadline 90 seconds, per-input deadline 5 seconds.
- Runtime: CPU only, one fuzz worker and a 4 GiB resident-memory ceiling. Record
  how the host enforces it. ASan's large virtual mapping is not resident memory;
  do not impose the Python oracle's RLIMIT_AS blindly on an ASan executable.

These are task limits, not duration predictions or an active scheduled job.
Stop early on decisive negative evidence. If the prerequisite or resource cap
cannot be established within the limit, report the exact blocker and propose the
smallest follow-up. Do not silently increase compute or switch to another target.

## Evidence required for acceptance

| Question | Required evidence | Insufficient evidence |
|---|---|---|
| Is the surface worth testing? | Dated immutable source links, target list and actual harness-call comparison | Project-directory presence or absence alone |
| Can another environment build it? | Exact revision/toolchain/dependency resolution, command log and isolated rebuild | A binary left in the author's checkout |
| Does the seed reach the consumer? | Named source milestones and observed events/counts tied to a seed hash | Exit zero, coverage growth, or no_alloc flag change alone |
| Do errors remain visible? | Controls for rejection, unexpected exception, resource failure and process failure | Broad catch-all followed by success |
| What did mutations accomplish? | Attempted, accepted and materialized counts with explicit denominators; named new states/functions | Total executions or raw cov number alone |
| Is the result reproducible? | Reviewer rerun using recorded commands and benign tracked inputs | Author's summary alone |

Instrumentation must observe real loader behavior without bypassing validation,
changing accepted input semantics, or incrementing counters merely because the
harness attempted a call. Record probe patches separately from upstream fixes.
Inspect exception handling: std::bad_alloc and unexplained failures must not be
silently recategorized as ordinary malformed-input rejection.

## R5: independent review

Use RESEARCH-REVIEW-TEMPLATE.md. The reviewer reads the implementation before
accepting the report and reruns the benign seed and negative controls from the
recorded environment. A second opinion without a replay is not independent
verification of reproduction. Record any platform/version differences.

Require core checks to remain green and the qualification commands to be
replayable. A qualification acceptance permits a subsequent bounded depth task;
it does not certify the loader, establish novelty or enable automatic campaigns.
Only the reviewed target can be promoted. Keep existing paused/archived statuses
until their own evidence satisfies the contract.

## R6: conditional research queue

These are candidates for future source verification, not verified-current gaps:

1. CLIP depth: only if the pilot demonstrates useful uncovered materialization.
   Design structure-preserving mutations around the demonstrated seed. Define
   semantic states before spending compute. After three equal-duration batches
   with no new named states/functions, stop and review the instrumentation and
   mutation strategy; do not extend merely to raise execution counts.
2. stable-diffusion.cpp: short M0 on tensor-name/shape/type reconciliation with
   consumers and companion artifacts. Avoid duplicating generic container work.
3. ExecuTorch: short M0 on program/segment loading and verification modes. First
   establish their documented contracts; disagreement alone is not a defect.
4. Current llama.cpp Jinja: proceed only if existing fuzz targets leave a
   demonstrated parser/runtime/resource path unexercised.
5. LeRobot composition: revisit manifest/schema/dataset relationships only if
   current source supplies a concrete boundary. World-model runtimes need custom
   parsing beyond delegated checkpoint and codec libraries.

Tokenizers remains regression maintenance; its Rust build needs a reviewed lock
and toolchain qualification. PyTorch remains paused while deep sources and native
coverage are missing. GGUF no_alloc, Flax and archived minja/gguf-py work do not
receive more campaigns solely because their harnesses exist. The retired base
config generator remains retired. See TARGETS.md for all nine directories.

## Research and disclosure limits

Eight ledger entries mean one known duplicate and seven project discoveries,
not seven independently novel vulnerabilities. Status and upstream fixes require
fresh checks. Preserve original observations when making corrections; add new
measurements with their exact environment and boundaries. Structural evidence
validation does not prove truth or adequate effort.

New faults stop the pilot for local triage. Store reports and reproductions in
ignored local locations; the public deliverable states class/status and limitations.
Do not turn a crash into an RCE claim or publish private material. Follow SECURITY.md
and obtain explicit authorization before contacting maintainers or publishing.
