# Glossary and calibration definitions

## Severity (for findings and non-findings)

- `high`: memory corruption with plausible code-execution, or trivial RCE.
- `medium`: reliable memory-safety crash (OOB/UAF) or a widely-reachable DoS.
- `medium-low`: reliable DoS (crash on crafted input) at a real trust boundary,
  not memory corruption. (minja 0004, 0005 sit here.)
- `low`: DoS requiring an unusual precondition, or a safe-language panic.
  (tokenizers 0002, 0003 sit here.)
- `none`: not a security issue (a robustness/correctness nit). Used on
  non-findings.

Severity is calibrated HONESTLY. A UBSan flag that does not crash a release build
is `none` (non-finding), not a severity. See C-0052.

## Confidence

- `verified`: reproduced, or cross-checked against a second source or version.
- `observed`: a single data point, not yet reproduced.
- `inferred`: reasoned from other claims/source, not directly observed.

## Provenance weight

- `machine-run`: executed on the researcher's machine (can install torch, run
  multi-million-run campaigns). Highest weight for negatives.
- `sandbox-run`: executed in Claude's sandbox (pure-Python + clang only; cannot
  install torch; short campaigns). Good for validation, weaker for large negatives.
- `source-read`: read from primary source. Necessary for entry-point and
  root-cause claims.

## Environment facts (as of 2026-08-13)

- Researcher: WSL Ubuntu, Python 3.12 venvs, clang 18 (libFuzzer+ASan+UBSan),
  torch 2.13.0+cu130, RTX 4080 Super. Two-copy workflow: Windows copy is
  git-authed; WSL copy runs builds/campaigns and is NOT git-authed.
- Sandbox: pure-Python installable (transformers, tokenizers, flax, atheris,
  reportlab); clang 18 present (C++ targets build); torch NOT installable.

## Recurring conclusion

Mature libraries' reachable surfaces are mostly robust; rigorous negatives that
MAP robust surfaces are part of the yield, not a failure. Findings cluster in
newer/smaller-ecosystem loaders (GGUF, tokenizers Rust internals, minja) and in
cross-cutting classes OSS-Fuzz does not cover.
