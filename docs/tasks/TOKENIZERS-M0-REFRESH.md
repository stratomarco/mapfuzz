# Hugging Face Tokenizers: current M0 refresh

## Objective

Refresh the historical Tokenizers target against current official source and
public coverage. Decide whether a new bounded qualification package can avoid
known same-boundary work and reach a named consumer state beyond JSON acceptance.
This package authorizes source/public-record inspection only. It does not
authorize a build, seed replay, mutation campaign, vulnerability claim,
publication, pull request, issue, message or other upstream contact.

## Fixed inputs

- Work through WSL on branch `daybreak-tokenizers-m0`, based on clean checkpoint
  `2b6e29bf6baace193b7d4136670ac631edde5a84`.
- Inspect official Hugging Face Tokenizers current main
  `6cfd9d385ca0ed91c10b49f0ce97d02cfde1b607`, committed
  2026-09-03 12:01:53Z. Its source archive SHA-256 is
  `4ab44da3ae45af06bcd2182d9abd8ae89eb80d3fd49f74ca1a69a475b1df3e96`.
- Inspect official OSS-Fuzz
  `4e65aea32254fe988ac4b84dbb088d2d08d789e7`, committed
  2026-09-11 14:51:38Z. Check exact project paths and a positive control.
- Keep downloaded source, API snapshots and search results below ignored
  `.runs/next-m0-2026-09-12/`.
- Treat existing local findings and public issue/PR records as dedup boundaries.
  Do not copy private reports or reproducers into the tracked packet.

## M0 questions

1. Does the current public tree expose an in-repository fuzz target or equivalent
   continuous property test for tokenizer deserialization?
2. Does current OSS-Fuzz expose a dedicated Tokenizers project?
3. Is `Tokenizer::from_bytes` still the exact in-memory consumer, and what
   construction paths execute during deserialization?
4. Is a model-supplied `tokenizer.json` a defended load boundary rather than a
   parser that intentionally executes arbitrary code?
5. Do current official issues, pull requests or existing project findings cover
   the same load-time panic/resource classes and component families?
6. Can a narrower package name a new semantic milestone, seed family and control
   set that is complementary to those records?

## Pass and stop rules

M0 passes only if current immutable source establishes a supported consumer and
the public/local comparison identifies a complementary, independently
deduplicable component or state. A generic `from_bytes` harness, absence from a
project list, or a historical valid seed is insufficient.

Stop without build or replay if any of the following holds:

- an open official issue or fix covers the same consumer and bug class;
- existing project findings already cover the proposed component family;
- current source/toolchain or a complete dependency lock is unavailable;
- the only remaining rationale is execution count, generic JSON parsing, or
  rediscovery of low-severity load-time denial of service;
- a named consumer milestone and earlier-failing control cannot be specified.

## Deliverable

Create `docs/qualification/tokenizers-m0-refresh.md` from the research review
template. Record immutable links, retrieved dates, exact current source paths,
public coverage limits, dedup exclusions and an explicit `QUALIFIED` or
`M0-STOP` disposition. Update the roadmap, target inventory, target README and
qualification manifest only to reflect the evidence. Run repository validation
twice. Keep `claims.md` unchanged unless a separate evidence workflow is
authorized.
