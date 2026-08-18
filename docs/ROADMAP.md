# mapfuzz roadmap

A living document. Grounded in what the project has established, not a wishlist.

## What mapfuzz is (established)

Continuous, structure-aware fuzzing of ML model-artifact parsers and loaders,
framed as classical security engineering: the model file is a format, the loader
is a parser, the download-to-load transition is a trust boundary.

Delivered and working:
- Crash targets across three toolchains: GGUF (C++/libFuzzer), tokenizers
  (Rust/cargo-fuzz + Python/Atheris), pytorch weights_only (Python/Atheris),
  transformers config (Python/Atheris), minja and clip/mmproj (C++/libFuzzer).
- One cross-cutting oracle delivered and CI-wired: the cross-implementation
  differential (fast vs slow tokenizer). The resource-exhaustion class is
  validated by findings (clip block_count C-0014, LeRobot range C-0023, GGUF
  resource negative) but is NOT yet packaged as a reusable oracle artifact with a
  selftest; that remains to be written.
- Six real findings across four components: tokenizers 0002/0003 (reported to
  HuggingFace), minja 0004/0005 (Google-validated, PR google/minja#92), clip/mmproj
  0006/0007 (PR to ggml-org/llama.cpp with regression test). All DoS-class, all
  coordinated-disclosed. Two targets evaluated and set aside honestly (LeRobot
  robust, jax no defended boundary).
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

1. Newer / less-hardened loaders not yet onboarded (tokenizers Rust internals,
   minja, clip/mmproj were open and yielded). Note on GGUF: hardened only on the
   no_alloc metadata surface we tested; the allocation-size-math class is active
   and repeatedly reopened upstream (see docs/RELATED-WORK.md), not covered by our
   harness.
2. Cross-cutting bug CLASSES a single-project crash fuzzer misses (resource
   exhaustion, cross-implementation divergence, trust-boundary composition).
3. The maintained, continuous, structure-aware machine itself.

Also established, and worth stating plainly: the reachable, obvious surfaces of
mature libraries are mostly robust. Rigorous negative results (pytorch tensor
path, config parsing, BERT fast/slow, untouched tokenizer components, GGUF
resource exhaustion) are a real part of the yield. They map what is solid.

## Near-term

- [x] Submitted the 0002+0003 disclosure (security@huggingface.co).
- [x] minja 0004/0005 disclosed via PR google/minja#92 (Google-validated).
- [x] clip 0006/0007 disclosed via PR to ggml-org/llama.cpp (with regression test).
- [x] Differential oracle wired into the continuous pipeline (differential-fuzz
      job, invariant selftest + short divergence campaign).
- [ ] Write chassis/resource_oracle.py with a --selftest (regression-guard the
      declared-huge allocation class: flag a bomb, pass a benign loader, in a
      memory-capped child) and wire it in. The class is proven by findings; the
      reusable oracle artifact is not yet written. A CI job referencing it was
      removed until the file exists.
- [ ] Enrich thin seeds (one hand-made seed per target is a weak cold start).

## Medium-term

- [ ] Cross-version differential: same tokenizer through transformers N vs N-1.
      The untested differential angle with real regression-finding potential;
      needs two installed versions (runnable on a dev machine, not the sandbox).
- [ ] Apply the resource oracle to a genuinely less-hardened loader. GGUF is
      hardened ONLY on the no_alloc metadata/descriptor surface we tested and
      serves as calibration there; its allocation-size-math path is an active CVE
      class (see docs/RELATED-WORK.md), not calibration-clean. Fertile ground is
      newer loaders and the size-math surface.
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

## Where the vein stands (as of the clip work)

The "newer / less-hardened loader" vein is largely worked out: GGUF hardened on
the no_alloc metadata surface we tested (but its size-math path is an active CVE
class we did NOT exercise, see docs/RELATED-WORK.md), tokenizers and minja and
clip all yielded, LeRobot robust, jax declined. The
repeatable technique that found clip is the sharpest remaining lead: in-OSS-Fuzz
projects with an entry point ABSENT from their build.sh target list (check the
list, not just membership). Next directions, in order of established promise:

1. Apply the build.sh-gap technique to other in-OSS-Fuzz projects (breadth, low
   barrier, already proven once).
2. The cross-cutting classes OSS-Fuzz structurally cannot do: trust-boundary
   composition and multi-implementation divergence.
3. Deeper memory-corruption surfaces (e.g. the clip tensor-loading path, reached
   only with a tensor-carrying seed) as a growth direction.
