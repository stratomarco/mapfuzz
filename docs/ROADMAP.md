# mapfuzz roadmap

A living document. Grounded in what the project has established, not a wishlist.

## What mapfuzz is (established)

Continuous, structure-aware fuzzing of ML model-artifact parsers and loaders,
framed as classical security engineering: the model file is a format, the loader
is a parser, the download-to-load transition is a trust boundary.

Delivered and working:
- Five crash targets across three toolchains: GGUF (C++/libFuzzer), tokenizers
  (Rust/cargo-fuzz + Python/Atheris), pytorch weights_only (Python/Atheris),
  transformers config (Python/Atheris).
- Two cross-cutting oracles: cross-implementation differential (fast vs slow
  tokenizer) and resource-exhaustion (decompression-bomb / declared-huge class).
- Two real findings (0002 decoder panic, 0003 normalizer panic), one systemic
  .expect-on-deserialize class, consolidated into one disclosure.
- Proven technique: coverage-guided structure-STABLE generation (found 0003 in
  seconds; the pytorch corridor showed it needs a rich surface to pay off).
- Triage chassis (dedup + classify, tested) and a continuous-fuzz CI pipeline
  that gates on real findings, green on real runners, with persistent+minimized
  corpus so runs compound.

## The strategic constraint (established by M0 sweep)

Mainstream ML format parsers are SATURATED in OSS-Fuzz: numpy, hdf5, h5py, keras,
tensorflow, onnx, safetensors, sentencepiece are all covered, including the RCE
and format surfaces. "Fuzz another well-known format" duplicates professional
work. mapfuzz's defensible value is the three things OSS-Fuzz does not do:

1. Newer / less-hardened loaders not yet onboarded (GGUF and tokenizers Rust
   internals were both open, and both yielded).
2. Cross-cutting bug CLASSES a single-project crash fuzzer misses (resource
   exhaustion, cross-implementation divergence, trust-boundary composition).
3. The maintained, continuous, structure-aware machine itself.

Also established, and worth stating plainly: the reachable, obvious surfaces of
mature libraries are mostly robust. Rigorous negative results (pytorch tensor
path, config parsing, BERT fast/slow, untouched tokenizer components, GGUF
resource exhaustion) are a real part of the yield. They map what is solid.

## Near-term

- [ ] Submit the 0002+0003 disclosure (security@huggingface.co). Converts private
      work to public credibility. Ready now; needs only the crediting line.
- [ ] Wire the two oracles (differential, resource) into the continuous pipeline
      so they run alongside the crash oracle, not just standalone. Completes the
      "continuous" story the corpus persistence started.
- [ ] Enrich thin seeds (one hand-made seed per target is a weak cold start).

## Medium-term

- [ ] Cross-version differential: same tokenizer through transformers N vs N-1.
      The untested differential angle with real regression-finding potential;
      needs two installed versions (runnable on a dev machine, not the sandbox).
- [ ] Apply the resource oracle to a genuinely less-hardened loader (GGUF is
      hardened and serves as calibration; the fertile ground is newer loaders).
- [ ] Structure-stable generation pointed at more tokenizer components and other
      rich-grammar loaders (the technique that found 0003, under-applied).

## Longer-term (the OSS-Fuzz-can't-do-it tier)

- [ ] Trust-boundary COMPOSITION: a file that crosses from a parser to a
      consumer, where each is fine alone but the handoff is not. Single-project
      fuzzers structurally cannot see this.
- [ ] Multi-implementation divergence as a first-class capability across serving
      stacks (llama.cpp vs vLLM vs transformers on the same artifact).
- [ ] A public, always-on continuous instance (ClusterFuzzLite/OSS-Fuzz-style)
      once a target set justifies it.

## Non-goals

- Re-fuzzing formats already in OSS-Fuzz.
- Building weaponized exploits or new code-execution/config-injection vectors.
  Scope is defect demonstration (crash, DoS, divergence).
