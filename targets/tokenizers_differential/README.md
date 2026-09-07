# Tokenizer differential side research

Status: locked baseline regression; campaigns paused pending broader
configuration qualification and a richer feature matrix. One small BERT WordPiece vocabulary is compared through slow and
fast implementations. Fifteen baseline probes check that pairing only; agreement
does not establish universal equivalence or that every later divergence is a bug.
A disagreement requires configuration, correctness and security-impact review.

The harness preserves exception types and exits nonzero when self-test probes
disagree. Valid UTF-8 decodes normally; invalid UTF-8 maps through Latin-1 so bytes
are not silently discarded. These modes do not exhaust Unicode behavior.

Historical runs had weak semantic coverage and are bounded negative results.
Before promotion, lock the environment, verify matched settings and vocabulary,
add Unicode/subword structure, and measure accepted inputs and semantic states.
Run with `python3 harness/fuzz_fast_slow_divergence.py --selftest` in the qualified
environment. Use the shared campaign runner for short local fuzz runs.

## Reproduce the regression environment

On Linux x86_64 with CPython 3.10.12, create and activate a fresh virtual environment:

```bash
python3 -m pip install --require-hashes -r requirements-linux-py310.lock
python3 test_harness.py
```

The lock records exact wheel hashes for all resolved packages. This baseline uses
transformers 4.55.4, tokenizers 0.21.4 and Atheris 2.3.0. It is not a claim about
latest upstream. Atheris 3.0.0 failed to import with this host's Python 3.10;
that incompatible combination is not used. The workflow runs regression tests,
not renewed long fuzz campaigns. Both implementations must accept baseline
probes; equal exceptions cannot satisfy the baseline gate.
