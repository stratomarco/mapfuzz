# Lessons

Short engineering log of failure modes hit during development and the guardrails added in response. The through-line is one rule: verify state before trusting it. Every failure below was a stale or incomplete artifact presenting itself as current.

## Verify the binary before trusting a run

Symptom: a rebuilt fuzzer kept reproducing a bug that had supposedly been patched.
Cause: the binary was stale; the link step had not refreshed it, so an old build was being run.
Guardrail: before trusting any run, confirm the BuildId changed and that `-help=1` works. A run against an unverified binary proves nothing.

## Verify the patch landed before trusting the build

Symptom: the build reported `fuzz-blockers: applied`, but the target kept crashing at a site the patch was supposed to fix.
Cause: the patch file was missing one of its hunks. `git apply` returned success because the other hunks applied; the missing one left a known bug in the build.
Guardrail: `build.sh` now counts the hunk markers in the patch and in the patched source, and aborts before compiling if they disagree. `git apply`'s exit code is never trusted alone. Root cause of the incomplete patch: it was regenerated with `git diff` from a tree that did not have the last hunk staged. Always regenerate the patch from a tree that contains every hunk, and verify the count.

## Verify a crash is current before triaging it

Symptom: a per-file loop over the corpus flagged hundreds of files as crashing.
Cause 1: the corpus directory had accumulated inputs from earlier unpatched runs; most "crashes" were fossils the current binary no longer produces the same way.
Cause 2: the loop treated any nonzero exit as a crash, which conflates clean rejections and other exits with real faults.
Guardrail: start campaigns from a clean corpus (seed only) so every crash is one the current build actually produces. Triage by fault signature (function, file, line, sanitizer class), not by exit code. This is the C1 dedup-by-location chassis feature; this incident is why it is prioritized.

## Distinguish a signal-less segfault from a finding

Symptom: a bare `Segmentation fault (core dumped)` with no libFuzzer banner and no sanitizer report.
Reading: a real parser finding comes with a sanitizer report. A signal-less, instant segfault points at startup or environment (stale binary, resource limit) or at a stack overflow that outruns the sanitizer's own handler, not at the parse path. Confirm with `-help=1`, `-runs=0`, a single-file run, and `ulimit -a` before assuming a bug.

## General

Most of this session's lost time was archaeology on stale artifacts. The chassis features already on the roadmap (C1 crash dedup by location, C2 shallow-blocker classifier) exist precisely to automate the verify-before-trust checks done by hand here. This log is the evidence for building them before the next target.
