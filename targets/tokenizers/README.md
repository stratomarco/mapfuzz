# Target: tokenizers (HuggingFace)

## Loader under test

- Format: `tokenizer.json`, the JSON document describing a tokenizer (model, normalizer, pre-tokenizer, post-processor, decoder, vocab, merges, added tokens).
- Implementation: huggingface/tokenizers (Rust crate `tokenizers`).
- Entry point: `Tokenizer::from_bytes<P: AsRef<[u8]>>(bytes) -> Result<Self>`.
- Pinned version: `tokenizers = "=0.21.4"` (see `fuzz/Cargo.toml`).

The entry point was read from `tokenizer/mod.rs:473` in the crate source, not assumed. `from_bytes` runs the full deserialization and tokenizer construction over an in-memory buffer, so the harness never touches the filesystem per input. If the pin is bumped, re-verify the signature before trusting the harness.

## M0 audit result

Historical check recorded 2026-08-13; refresh before a new campaign:

- In-repo fuzz target: none. A fresh clone of huggingface/tokenizers contains no `fuzz/` directory and no fuzz target.
- OSS-Fuzz: not a project. The OSS-Fuzz `projects/tokenizers/` path returns 404 (confirmed against a positive control, `sentencepiece`, which returns 200).
- Published fuzzing work: none surfaced in search.

Conclusion: open ground, in contrast to safetensors (which ships its own fuzz target and runs a per-commit security audit) and SentencePiece (already in OSS-Fuzz). Caveat: absence of public evidence is not proof the crate is untouched; private or academic fuzzing may exist. M0 tells us the ground is open, not that bugs are guaranteed.

## Bug classes targeted

This is safe Rust, so memory corruption is largely off the table. The targets are logic faults reachable from an untrusted tokenizer file:

- Panics: `unwrap`, `expect`, slice or index out of bounds, arithmetic overflow in debug builds.
- Unbounded or attacker-scaled allocation from declared vocab, merges, or added-token sizes.
- Integer overflow in offset, id, or rank math.
- Pathological structures (deeply nested or self-referential config) causing stack exhaustion.

A panic reached from a malicious tokenizer file is a denial-of-service finding. Note the caveat from the Rust security community: DoS-class findings in crates are often deprioritized by maintainers, so triage severity honestly and expect DoS to be lower-interest than a memory or logic bug with real consequence.

## Feature surface

`fuzz/Cargo.toml` pins `default-features = false` to keep the build light: no `onig` (which needs the system `libonig-dev` C library) and no `http` (network). This still exercises the full parse path for most tokenizer files. To widen the surface toward components that need those features, enable them in `fuzz/Cargo.toml`; for `onig`, install `libonig-dev` first. Wider features mean more parse paths reachable, at the cost of heavier builds and a system dependency.

## Seed corpus

`corpus/seed_tokenizer.json` is a minimal valid tokenizer (WordLevel model, Whitespace pre-tokenizer, three-entry vocab), generated with the official Python `tokenizers` writer. No proprietary vocab. Add more seeds covering BPE, WordPiece, Unigram, byte-level pre-tokenizers, and populated normalizer and post-processor sections to give the fuzzer more structure to mutate.

## Build and run

The build requires an installed dated nightly (`RUST_TOOLCHAIN=nightly-YYYY-MM-DD`),
an exact `CARGO_FUZZ_VERSION`, and a reviewed `fuzz/Cargo.lock`. It does not install
moving global tools. The direct target pin is 0.21.4 for historical regression,
not a claim that this is current upstream. Qualify toolchain and transitive
resolution before promotion; see ../../docs/TARGETS.md.

## Status

Regression maintenance; automatic campaigns paused. Findings 0002 and 0003 were
reported on 2026-08-13 according to the ledger. Public reproducers remain withheld;
current upstream response/fix status has not been refreshed in this repair.
Private blockers stay local. Six synthetic JSON seeds are tracked. Broader
features and current-version checks require separate qualification.
