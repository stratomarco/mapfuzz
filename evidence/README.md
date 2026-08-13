# mapfuzz Research Evidence Base

A structured, provenance-preserving record of what was tested, observed,
concluded, and explicitly NOT concluded across the mapfuzz project.

## Principle

For research, the canonical record is deterministic and human-auditable. This
directory IS that canonical record. A vector database / RAG system may later
index these files, but it is an index over the truth, never the truth itself.
Every claim here is traceable to how it is known.

## The unit of record: a claim

Not "a finding" and not "a fact" in isolation, but a CLAIM WITH PROVENANCE:
- what was tested (the target, entry point, method)
- how it was tested (harness, campaign size, environment)
- what was observed (raw result, verbatim where it matters)
- what was concluded (the claim itself)
- confidence and boundary (what this does and does NOT let us conclude)

Negative results are first-class. "X is robust over N runs" is a claim of equal
standing to a finding. Robust-surface maps are part of the yield.

## Files

- `schema.md`      the claim schema and field definitions
- `claims.yaml`    the canonical machine-parseable claim records
- `claims.md`      the same claims rendered for human reading (generated)
- `methods.md`     reusable method definitions referenced by claims
- `glossary.md`    terms, severity definitions, environment facts

## Auditability rules

1. Every claim cites its provenance (method + observation), never bare assertion.
2. Raw observations are preserved verbatim where they are load-bearing (crash
   traces, exit codes, run counts, coverage numbers).
3. Confidence is explicit and calibrated. "Verified" requires a reproduction;
   "observed" is a single data point; "inferred" is reasoning from other claims.
4. Every claim states its BOUNDARY: the specific thing it does not establish.
5. Superseded claims are marked superseded with a pointer, never deleted.
6. Provenance distinguishes: source-read, in-sandbox run, on-machine run.
