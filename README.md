# mapfuzz

Continuous, structure-aware fuzzing for the parsers and loaders of machine learning model artifacts.

> Working codename. `mapfuzz` (Model Artifact Parser fuzzer) is a placeholder pending a final name.

## Why

A model file downloaded from a public hub is attacker-controlled input fed into a parser, exactly like a font, a media container, or a PDF. The loaders that consume GGUF, safetensors, ONNX, and pickle-based checkpoints are large C, C++, and Rust codebases carrying the usual parser bug surface, plus a serialization-driven code-execution surface unique to the ML stack.

This project treats the model artifact as a file format, the loader as a parser, and the download-to-load transition as a trust boundary, then applies the established parser-fuzzing toolchain (libFuzzer, AFL++, structure-aware mutation, sanitizers, continuous CI) to the whole local-AI supply chain. The framing follows classical security engineering: Anderson on trust boundaries and economics of defense, McGraw and BIML on architectural risk analysis for ML systems, the OWASP LLM Top 10 and MITRE ATLAS for the model-supply-chain threat classes. ML security here is an extension of security engineering, not a separate discipline.

The gap is real. As of the pinned commit, the reference GGUF loader in llama.cpp ships no fuzz targets at all (see `docs/M0-baseline-audit.md`), and a May 2026 advisory disclosed six parser bugs found by manual review. The first harness in this repo reproduces a division-by-zero in the current parser within seconds of fuzzing.

## Status

Milestone M1 (GGUF, memory-safety and resource oracles) in progress. The GGUF harness builds against the real loader and produces reproducing findings. Other formats (safetensors, ONNX, PyTorch/pickle, tokenizers) are scoped in `REQUIREMENTS.md` and not yet implemented.

## Layout

```
REQUIREMENTS.md            full v1 requirements specification
docs/                      baseline audit and design records
targets/<format>/          one directory per artifact format
  harness/                 fuzz harness source
  build.sh                 reproducible build (pinned upstream commit)
  corpus/                  seed corpus (synthetic, no proprietary weights)
  grammar/                 structure-aware mutation notes and modules
  README.md                target provenance, entry point, bug classes
ci/clusterfuzzlite/        run the suite in an adopting repo's CI
oss-fuzz/                  layout for the central continuous instance
```

## Quickstart (GGUF target)

Requires `clang` (with libFuzzer), `cmake`, `ninja`, `git`.

```
cd targets/gguf
./build.sh          # clones llama.cpp at the pinned commit, builds instrumented ggml, links the harness
./fuzz_gguf -max_total_time=60 corpus/
```

The build pins the exact upstream commit so findings are reproducible (REQ-N1). See `targets/gguf/README.md` for the verified entry point and the bug classes targeted.

## Security and disclosure

This tooling finds real vulnerabilities in third-party software. Findings are handled under coordinated disclosure (see `SECURITY.md`): reported privately to the upstream maintainer first, with public reproducers withheld until a fix ships or an embargo lapses. Live crash reproducers are kept in a gitignored `PRIVATE_findings/` directory and must never be pushed to a public remote before disclosure.

## License

Apache-2.0. See `LICENSE`.
