# Target: tokenizers (HuggingFace)

## Loader under test

- Format: `tokenizer.json`, the JSON document describing a tokenizer (model, normalizer, pre-tokenizer, post-processor, decoder, vocab, merges, added tokens).
- Implementation: huggingface/tokenizers (Rust crate `tokenizers`).
- Entry point: `Tokenizer::from_bytes<P: AsRef<[u8]>>(bytes) -> Result<Self>`.
- Pinned version: `tokenizers = "=0.21.4"` (see `fuzz/Cargo.toml`).

The entry point was read from `tokenizer/mod.rs:473` in the crate source, not assumed. `from_bytes` runs the full deserialization and tokenizer construction over an in-memory buffer, so the harness never touches the filesystem per input. If the pin is bumped, re-verify the signature before trusting the harness.

## Current M0 result

The 2026-09-12 refresh is **M0-STOP** against Tokenizers
`6cfd9d385ca0ed91c10b49f0ce97d02cfde1b607` and OSS-Fuzz
`4e65aea32254fe988ac4b84dbb088d2d08d789e7`:

- The complete public Tokenizers tree contains no fuzz-named path, and the exact
  OSS-Fuzz `projects/tokenizers/project.yaml` lookup returns 404 while the
  SentencePiece positive control returns 200. These inventory results do not
  prove that no private, differently named or external fuzzing exists.
- `Tokenizer::from_bytes` remains the exact in-memory deserialization and
  construction entry point on current main.
- Open official issues 2094 and 2198 plus open PRs 2104, 2219 and 2333 cover a
  current BPE merge-construction panic at this same load boundary.
- The current decoder and Precompiled-normalizer expect-on-deserialize sites are
  already represented by verified, reported claims C-0001 and C-0002; C-0003
  bounds that historically probed component class.
- The tracked harness pins 0.21.4 and has no `fuzz/Cargo.lock`. Its six seeds are
  historical regression inputs, not evidence of current-main reachability.

No complementary component/state survived the dedup gate, so no build, seed
replay or mutation ran. See
`../../docs/qualification/tokenizers-m0-refresh.md` for the complete packet.

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

`corpus/seed_tokenizer.json` is a minimal valid tokenizer (WordLevel model,
Whitespace pre-tokenizer, three-entry vocab), generated with the official
Python `tokenizers` writer. No proprietary vocab. The tracked corpus remains
available for deterministic historical regression. Do not extend it for a new
campaign until a separate qualification brief passes the current dedup and
semantic-control gates.

## Build and run

The build requires an installed dated nightly (`RUST_TOOLCHAIN=nightly-YYYY-MM-DD`),
an exact `CARGO_FUZZ_VERSION`, and a reviewed `fuzz/Cargo.lock`. It does not install
moving global tools. The direct target pin is 0.21.4 for historical regression,
not a claim that this is current upstream. Qualify toolchain and transitive
resolution before promotion; see ../../docs/TARGETS.md.

## Status

Regression maintenance; current qualification M0 stopped and automatic
campaigns remain paused. Findings 0002 and 0003 were reported on 2026-08-13
according to the ledger; public reproducers remain withheld. The 2026-09-12
refresh inspected current source and official public BPE prior art but did not
reproduce any condition or update an evidence claim. Reopen only after the
active BPE issue/fix state changes and a separate brief defines a current locked
environment plus a non-BPE, non-decoder, non-Precompiled-normalizer semantic
state and controls.
