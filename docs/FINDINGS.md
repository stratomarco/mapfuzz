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
| 0002 | tokenizers (HuggingFace) | panic on malformed input during load (DoS) | Real, reproduced, prior-art checked. REPORTED 2026-08-13 to security@huggingface.co (combined 0002+0003 systemic-pattern report, PDF). Awaiting response/fix. Public reproducer still withheld until fixed. |
| 0003 | tokenizers (HuggingFace) | panic on malformed normalizer during load (DoS) | Real, reproduced, minimized. Same class as 0002. Reproduced on 0.21.4 and 0.23.1. REPORTED 2026-08-13 to security@huggingface.co (combined report). Public reproducer withheld until fixed. |
| 0004 | minja (llama.cpp C++ chat-template engine) | unbounded-recursion stack overflow in expression parser (DoS on parse) | Real, reproduced, characterized. No parser depth limit; deeply-nested template expressions exhaust the stack at parse time (deterministic PoC ~2000 levels; confirmed depth-driven via stack-size test). Trust boundary: templates ship in model configs. Severity DoS medium-low; not RCE. EMBARGOED pending coordinated disclosure to google/minja + llama.cpp; reproducer withheld. |

## Status vocabulary

- EMBARGOED: verified, not yet disclosed; specifics kept local.
- Reported: disclosed upstream, awaiting fix.
- Fixed: upstream fix shipped.
- Duplicate / known: already reported or public; not attributed to this project.
