# Research implementation review packet

Replace placeholders with observations. Use 'not run', 'unavailable' or
'inferred' explicitly; an empty field is not evidence of success.

## Identity and scope

- Package ID and objective:
- Author/model and independent reviewer:
- Date, base SHA, implementation SHA or working-diff identity:
- Worktree/branch and exact-head CI link/status:
- Disposition: QUALIFIED / M0-STOP / BLOCKED / CHANGES-REQUIRED
- What this disposition establishes and does not establish:

## M0 and novelty boundary

| Source | Immutable revision and link | Retrieved date | Relevant path/entry point | Observation |
|---|---|---|---|---|
| Loader | | | | |
| Public fuzz build and harness | | | | |
| Public prior art/fix status | | | | |

Describe the trust boundary, supported consumer and existing-coverage comparison.
Separate absence of observed coverage from proof that no other fuzzing exists.

## Reproduction environment

Record OS/architecture, compiler/sanitizers, Python/tool versions, dependency
locks or image digest, upstream SHA and all local patches. Include exact build
commands, a fresh-directory replay and binary/seed hashes. State what was reused
(cache/toolchain) and what was rebuilt. Never include tokens or credentials.

## Semantic controls

| Benign/control input and hash | Expected milestone | Observed milestone/count | Source probe location | Exit/result | Local evidence |
|---|---|---|---|---|---|
| Tensor-carrying seed | | | | | |
| Malformed metadata | | | | | |
| Missing/truncated tensor | | | | | |

Show why the probe observes real consumer behavior and does not alter it. State
whether materialization means bytes copied, mapped, or deferred in this loader.
Avoid claiming a mapped descriptor proves that downstream code consumed data.

## Bounded runs and resource behavior

Record host enforcement and effective limits, not just requested flags. Give
per-batch command, exit code, attempts, accepted inputs, materialized inputs,
unique semantic states/functions, elapsed time and peak resident memory. Define
counter denominators and instrumentation overhead. List failure controls and
whether each produced the expected failing gate.

| Batch | Duration/limits | Attempts | Accepted | Materialized | New states/functions | Result/log hash |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

## Independent review

- Exact commands replayed by reviewer and environment differences:
- Benign/control outcomes compared with the author's report:
- Core tests, workflow results and changed-code tests:
- Exception handling, resource cleanup and instrumentation diff checked:
- Private artifacts and accidental disclosures excluded from review diff:
- Claims/render synchronization and scope wording checked:
- Unresolved contradictions or limitations:

## Decision

Explain QUALIFIED, M0-STOP, BLOCKED or CHANGES-REQUIRED with evidence. Distinguish
a finding candidate from confirmed impact/novelty. State one bounded next action,
its prerequisite and compute limit. No merge, publication, disclosure or long
campaign is authorized by a report's disposition alone.
