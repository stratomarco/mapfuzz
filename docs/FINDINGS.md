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
| 0005 | minja (llama.cpp C++ chat-template engine) | integer division/modulo by zero in interpreter (DoS, SIGFPE on render) | Real, reproduced, characterized. operator/ and operator% lack a zero-divisor check; {{ 1/0 }} or {{ 1%0 }} crash via SIGFPE. Confirmed in a NON-sanitized -O2 build (real release crash, exit 136), not sanitizer-only. Trust boundary: templates render at inference. Severity DoS medium-low; trivially triggered; not RCE. EMBARGOED, bundle with 0004 for google/minja + llama.cpp. Reproducer withheld. |
| 0006 | clip/mmproj (llama.cpp) | type-confusion abort on load (SIGABRT DoS) | Real, reproduced, characterized. Scalar metadata getters (get_bool/i32/u32/f32/string) check key presence but not GGUF type before the typed accessor, which GGML_ASSERTs and aborts. Wrong-typed hparam key aborts any loader. Confirmed in NON-sanitized -O2 (exit 134). Trust boundary: mmproj files are downloaded artifacts. Severity low DoS; not RCE. REPORTED via PR ggml-org/llama.cpp (harden-mmproj-metadata), with fails-before/passes-after regression test. Reproducer withheld until merged. |
| 0007 | clip/mmproj (llama.cpp) | unbounded allocation from block_count (std::bad_alloc DoS) | Real, reproduced, characterized. clip.vision.block_count sizes model.layers.resize(n_layer) with no bound beyond INT32_MAX; ~200M layers OOMs (~137GB) before tensor validation. Passes the INT32_MAX cap yet still OOMs. Cleanly reachable on the normal load path. Confirmed release std::bad_alloc + ASan OOM. Severity low-medium DoS. REPORTED in the same PR as 0006. Reproducer withheld until merged. |
| 0008 | gguf-py GGUFReader (llama.cpp Python reference reader) | unbounded array-length loop (DoS, hang/OOM on read) | Real, reproduced, minimized to 49 bytes, cross-impl grounded. A KV field declaring type ARRAY with a huge uint64 length drives an unbounded range(alen) loop with no bound, no alloc guard, and no EOF break (confirmed 5s timeout). The C++ reference reader in the same repo guards this exact case (short-read return, length_error/bad_alloc catch); the Python one does not. Trust boundary: GGUF files are downloaded artifacts. Severity DoS low-medium; Python memory-safe so not RCE. Low-severity DoS. ggml-org treats DoS as public-PR-class (private disclosure program disabled), so handled as a public PR with fix and regression test; may be declined as won't-fix per their DoS policy. |

## Status vocabulary

- EMBARGOED: verified, not yet disclosed; specifics kept local.
- Reported: disclosed upstream, awaiting fix.
- Fixed: upstream fix shipped.
- Duplicate / known: already reported or public; not attributed to this project.
