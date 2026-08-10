# Findings ledger

Tracks findings by id, target, class, and disclosure status. Specifics (source
location, mechanism, reproducer) for embargoed findings live in the gitignored
`PRIVATE_findings/` directory, local only, until disclosed.

Discipline: a fuzz-blocker patch for an unreported finding reveals the fix and is
therefore a disclosure artifact. Blockers for already-public bugs may be
committed; blockers for embargoed findings stay local until the finding is
reported.

| ID | Target | Class | Status |
|----|--------|-------|--------|
| 0001 | GGUF (llama.cpp) | integer division by zero on load (DoS) | Not ours to report. Independently found earlier by another researcher and in disclosure via huntr; confirmed a duplicate. Recorded as a harness-validation result. |
| 0002 | tokenizers (HuggingFace) | panic on malformed input during load (DoS) | Real, reproduced, prior-art checked (not found in tracker; present on `main`). EMBARGOED: sitting on it, not yet reported. Details and reproducer local under `PRIVATE_findings/`. |

## Status vocabulary

- EMBARGOED: verified, not yet disclosed; specifics kept local.
- Reported: disclosed upstream, awaiting fix.
- Fixed: upstream fix shipped.
- Duplicate / known: already reported or public; not attributed to this project.
