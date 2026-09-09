# mapfuzz implementation roadmap

Planning baseline: 8dc3101, inspected on 2026-09-07. The maintainer reports the
latest CI run is green; this planning pass did not independently query GitHub.
The hardening branch is not assumed merged. This roadmap authorizes no merge,
publication, upstream contact or long campaign by itself.

Execution checkpoint, 2026-09-09: the CLIP pilot is locally checkpointed at
`ff8d51e1149a35b930ba6e13b3f105001deaca75`. M0, two pinned builds, semantic
controls, one bounded batch, local fix validation, a current-master port and
independent review are complete. The first mutation batch found a candidate and
triggered the mandatory stop. The target and local PR draft are parked; nothing
was pushed, opened, published or sent upstream.

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
- Machine-checked target portfolio: `targets/qualification.yaml`

## Delivery order

| ID | State | Work package | Reviewable outcome and exit |
|---|---|---|---|
| R0 | complete for the local pilot | Close the hardening review | Approved base `5e52993`; no merge was inferred or performed. |
| R1 | complete | CLIP/mmproj current M0 | Useful public-coverage gap and actual multimodal consumer boundary identified. |
| R2 | complete | Reproducible CLIP build | Two pinned fresh builds plus a 2026-09-09 current-master build exercised the real loader. |
| R3 | complete | Valid seed and semantic reachability | Tensor bytes were read; standard/Yi consumers constructed; negative controls failed earlier. |
| R4 | stopped as designed | Short qualification runs | Batch 1 found an ASan null-read candidate; batches 2 and 3 were not run. |
| R5 | complete; parked | Independent review and disposition | Fix and controls independently replayed; current-master evidence reviewed twice; no external action. |
| R6 | CLIP parked; ExecuTorch M0 stopped | Depth campaign or next M0 | ExecuTorch has a real consumer, but official records show historical internal fuzz discoveries and later planning while the harness, coverage and current operation remain unavailable. No build/fuzz compute; next candidate requires explicit selection. |

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

1. ExecuTorch: **M0-STOP on 2026-09-09.** Current `Program::load`, segment and
   verification contracts were established, but official project records show
   historical internal fuzz discoveries and later planning while the harness,
   coverage and current operation remain unavailable.
   Public-tree and OSS-Fuzz absence cannot establish an uncovered boundary. See
   `qualification/executorch-m0.md`; do not allocate build or fuzz compute.
2. stable-diffusion.cpp: short M0 on tensor-name/shape/type reconciliation with
   consumers and companion artifacts. Avoid duplicating generic container work.
3. Current llama.cpp Jinja: proceed only if existing fuzz targets leave a
   demonstrated parser/runtime/resource path unexercised.
4. LeRobot composition: revisit manifest/schema/dataset relationships only if
   current source supplies a concrete boundary. World-model runtimes need custom
   parsing beyond delegated checkpoint and codec libraries.
5. CLIP depth remains parked. Reopen only under a separate brief after the local
   finding/fix disposition is decided and only with named semantic states; never
   extend merely to raise execution counts.

Candidate M0s produce a review packet under `docs/qualification/` before a new
target directory is created. A passing M0 must then add a manifest entry with
the exact consumer, trust boundary, semantic milestone, controls, evidence and
compute decision. A duplicate, uncertain boundary or missing immutable
prerequisite is an `M0-STOP`, not an invitation to switch targets silently.

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
