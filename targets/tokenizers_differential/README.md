# Target: tokenizer cross-implementation differential oracle

## A new kind of oracle

Not "does it crash" but "do two implementations that should agree, disagree." The
fast (Rust-backed) and slow (pure-Python) tokenizers in transformers are built
from the SAME vocab and are contractually supposed to produce identical token ids
for any input. A divergence means the same text becomes different tokens depending
on which stack loads the model: a security-relevant supply-chain bug, because a
guardrail, filter, or safety classifier tuned on one tokenization can be silently
bypassed under the other. No crash is required; disagreement is the finding.

## Oracle

`harness/fuzz_fast_slow_divergence.py` builds a matched fast/slow BERT WordPiece
pair from one vocab (once), fuzzes the input text, encodes with both, and flags
any token-id divergence. Agreement (same ids, or both raising) is not a finding.

Baseline invariant verified: fast == slow on 15 adversarial probes (zero-width
space, null byte, fullwidth chars, ligatures, long runs, continuation-piece
boundaries). Because the invariant holds, a divergence found by fuzzing is a real
implementation bug, not config noise.

## Status and honest limitation

The oracle is correct and trustworthy (invariant holds). A first in-sandbox
campaign found no divergence, but with a caveat: coverage stayed flat (cov 97),
because both tokenizers are native (Rust/C) extension calls with little
instrumented Python for libFuzzer to guide on. So coverage-guidance is weak here,
and "no divergence" means random-ish text mutation did not stumble on one, not
that the space was searched thoroughly.

Random UTF-8 mostly produces [UNK] on both sides (agreement). Divergences live at
specific structural boundaries: Unicode normalization forms (NFC/NFD/NFKC/NFKD),
combining-character sequences, control characters, the byte-vs-char boundary, and
continuation-piece merges. Finding them needs a STRUCTURE-AWARE generator aimed at
those categories, not raw bytes.

## Next step (technique composition)

Combine this oracle with the structure-aware generation used for the parsing
targets: a generator that emits inputs biased toward the divergence-prone Unicode
and subword categories above, rather than random text. The two techniques built in
this project (differential oracle + structure-aware, coverage-stable generation)
compose directly here.

Further pairings: byte-level BPE fast vs slow (GPT2), and cross-version (same
tokenizer, two library versions) for regression divergence.

## Scope

Correctness/divergence demonstration. A finding is a minimized input that
tokenizes differently across implementations, disclosed as a divergence bug (which
side is wrong is for the maintainers). Defect demonstration only.
