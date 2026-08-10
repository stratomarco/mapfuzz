# Chassis

The reusable machinery shared across every target, as opposed to the specialized
per-target harnesses. The chassis is what makes this a maintained tool rather
than a collection of one-off fuzzers.

## triage.py (C1 dedup + C2 classify)

Collapses a pile of crash artifacts into the few DISTINCT faults they represent,
and tags each as a likely shallow blocker, a likely real finding, or needs
review. This codifies the manual triage done repeatedly during development (for
example, the run that produced 14,724 artifacts that were a handful of bugs).

It parses fault-report TEXT and is language-agnostic. Handled formats:
AddressSanitizer, UndefinedBehaviorSanitizer, Rust panics, Python tracebacks,
GGML_ASSERT aborts, and bare native signals.

Usage:

```
# a directory of saved fault reports (one per file):
python3 -m chassis.triage reports/

# or from stdin:
cat somefault.txt | python3 -m chassis.triage
```

Output is a frequency table: count, verdict, fault class, location, and an
example source. Exit code is non-zero if any bucket is classified `real`, so CI
can gate on it.

### Verdicts

- `real`: worth triaging as a finding. AddressSanitizer memory-safety
  violations, native signals, and unwrap/index panics on untrusted input.
- `shallow`: a known-cheap fault that walls the fuzzer (unvalidated enum cast,
  assertion abort). Block it locally to fuzz deeper; see each target's
  `fuzz-blockers/`.
- `review`: cannot decide from the signature alone (division by zero, integer
  overflow, generic panics, most Python exceptions). Inspect and prior-art check.

The verdicts encode the judgments this project actually made: enum casts and
asserts were the GGUF fuzz-blockers; the tokenizers `decoders/mod.rs:90` panic
was the real finding; the GGUF division by zero was `review` and turned out to be
a known duplicate.

### Tests

`python3 chassis/tests/test_triage.py` validates dedup and classification against
fault reports captured from real runs (fixtures in `tests/fixtures/`).

## Continuous layer (C3)

`.github/workflows/continuous-fuzz.yml` runs a short campaign per target on every
push and PR (and a longer nightly run), pipes crashes through triage, and fails
the job on a `real` verdict. GGUF runs by default because its blockers are
public. Targets with embargoed findings or blockers (tokenizers, pytorch) stay
gated off until their findings are reported, so public CI never discloses.
```
