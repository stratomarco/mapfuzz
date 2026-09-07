# Audit hardening implementation, 2026-09-07

Baseline: clean linked worktree at f3f70d4. WSL access was restored through the
normal permission mechanism; Git metadata was not rewritten. Use WSL Git for
this checkout. Changes are local and uncommitted; no upstream publication or CI
run is claimed.

## Implemented

- Restored C-0001/C-0020 to verified based on recorded provenance, not a fresh
  finding reproduction. An independent comparison against HEAD confirmed no
  statement, observation, boundary, date or finding-status changes.
- Added strict structural validation, duplicate-key rejection, useful malformed
  input errors, reference checks and validate-before-render. Normalized provenance
  in ten claims; retained unknown execution environments explicitly. Removed 14
  severity fields from audit/negative records as required by the schema.
- Added a capped campaign runner retaining exit status, logs and every artifact.
  Nonzero exits without reports, artifacts, timeouts and recognized diagnostics
  fail. Standalone triage fails on every fault, unparsed, missing or empty report
  input. No blanket allowance for assertions or invalid enums remains.
- Replaced Queue.empty synchronization with bounded pipe messages. Distinguished
  timeout, MemoryError and unexplained child death. Hostile normal return needs
  explicit policy. Allocation and constant-memory timeout probes are independent.
- Fixed differential self-test exit status, exception-type erasure, discarded
  invalid UTF-8 mutations and equal-exception baseline false positives.
- Replaced unqualified automatic campaigns with infrastructure and locked
  differential regression jobs. No automatic fault-artifact publishing.
- Removed moving dependency defaults from historical build scripts. Python builds
  require a hash lock and venv; minja requires immutable revisions and header
  hashes; tokenizers requires a dated toolchain, exact tool version and a reviewed
  lock. Verified cargo-fuzz 0.13.2 does not accept --locked and adapted the wrapper.
- Corrected the nine-target inventory, absent PyTorch harness documentation,
  finding counts, retired config scope, historical architecture promises and
  broad Frontier conclusions. Current promotion requirements are in TARGETS.md.

## Validation

Local checks passed: five evidence tests, six gate/resource tests, three original
triage tests, five real differential-harness tests, resource-oracle self-test,
all 44 evidence records, generated Markdown, workflow YAML parsing, Python/shell
syntax and git diff whitespace checks. The malformed-data tests include many
field/type subcases; passing these does not establish evidence truth.

The actual differential pair accepted and agreed on 15/15 baseline probes with
CPython 3.10.12, transformers 4.55.4, tokenizers 0.21.4 and Atheris 2.3.0. Atheris
3.0.0 failed to import on Python 3.10 and was replaced only in the isolated test
environment. A second fresh virtual environment installed the exact wheels offline with hash
verification, passed pip check and repeated all five differential tests. The real
Atheris harness also passed a 32-input smoke through the shared campaign runner.
That smoke validates integration, not research coverage.
All resolved wheel versions and hashes are recorded in
`targets/tokenizers_differential/requirements-linux-py310.lock`.

Core tests ran with both system PyYAML 5.4.1 and isolated PyYAML 6.0.2. The real
stdlib JSON parser was tested under caps with increasing nesting sizes; this
qualifies the oracle integration only, not an ML model loader.

## Work still required before research promotion

- Fresh upstream M0, disclosure-status and public fuzz-coverage checks.
- Full pinned native builds and tensor-carrying CLIP seed reaching materialization.
- Provenance-backed recovery of missing private/deep PyTorch harnesses if that
  target is reopened. They were not invented or reconstructed in this repair.
- Complete environment qualification for paused/archived targets, including
  transitive locks and semantic reachability. Build scripts now refuse incomplete
  inputs; that is not equivalent to having reproduced every historical target.
- Model-loader resource regressions and accepted-input/semantic coverage metrics.

Arbitrary unknown exit-zero log text cannot universally be identified as a fault.
A target must satisfy the exit/artifact contract before promotion. Source-location
triage can merge root causes and requires manual investigation. No long research
campaign or whole-component safety conclusion is part of this implementation.
