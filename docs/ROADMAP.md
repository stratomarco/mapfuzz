# mapfuzz hardening roadmap

The priority is trustworthy evidence and execution gates before more compute.
See TARGETS.md for the complete nine-directory inventory and promotion criteria.

## Repository repairs

- Correct C-0001 and C-0020 confidence from their recorded provenance.
- Enforce the structural evidence schema and reject malformed records cleanly.
- Preserve legacy provenance without guessing execution environments.
- Fail closed on campaign execution errors, artifacts, review/unparsed reports.
- Separate timeout, memory exhaustion and unexplained child death in the oracle.
- Require explicit policy before a hostile input returning normally passes.
- Run infrastructure regressions on push/PR; pause unqualified target campaigns.
- Align tracked harness counts, historical claims and reproducibility boundaries.

The ledger contains eight entries: one known duplicate used for validation and
seven project discoveries. This is not seven independently novel vulnerabilities;
0004 also has public prior art. Disclosure status is historical until refreshed.

## Research sequence after qualification

First candidate: CLIP/mmproj tensor materialization. Refresh upstream and public
fuzz coverage, establish a pinned build, then prove a tensor-carrying seed reaches
the actual consumer under resource caps. The existing metadata harness does not
establish that reachability. Stop when semantic coverage plateaus.

Next short M0 candidates: stable-diffusion.cpp artifact-to-consumer reconciliation
and ExecuTorch program/segment loading. These are hypotheses, not commitments to
long campaigns. Check the current llama.cpp Jinja harness before duplicating it.
LeRobot is limited to dataset-composition seams. World-model projects need custom
parsing beyond standard checkpoint/video libraries to justify work.

For each candidate, progress through M0, valid-seed reachability, short smoke,
depth, and only then a long campaign. Record accepted-input rate, tensors/segments
materialized, consumer handoffs and time/memory growth across input sizes.

## Limits

Passing infrastructure checks does not reproduce historical findings, establish
native backend coverage, prove evidence truth, or certify a component as safe.
Missing private artifacts cannot be reconstructed or validated from this checkout.
