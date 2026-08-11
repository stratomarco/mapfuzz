# mapfuzz

Continuous, structure-aware fuzzing for the parsers and loaders of machine
learning model artifacts.

> Working codename. `mapfuzz` (Model Artifact Parser Fuzzer) is a placeholder
> pending a final name.

## Thesis

A model file downloaded from a public hub is attacker-controlled input fed into a
parser, exactly like a font, a media container, or a PDF. The loaders that consume
GGUF, safetensors, ONNX, tokenizer files, and pickle-based checkpoints are large
C, C++, Rust, and Python codebases carrying the usual parser bug surface, plus a
serialization-driven code-execution surface unique to the ML stack.

This project treats the model artifact as a file format, the loader as a parser,
and the download-to-load transition as a trust boundary, then applies the
established parser-fuzzing toolchain (libFuzzer, cargo-fuzz, Atheris, structure-
aware mutation, sanitizers, continuous CI) to the local-AI supply chain. The
framing is classical security engineering: Anderson on trust boundaries, McGraw
and BIML on architectural risk analysis for ML systems, the OWASP LLM Top 10 and
MITRE ATLAS for the supply-chain threat classes. ML security here is an extension
of security engineering, not a separate discipline.

## Where this fits (and where it does not)

The field is not empty. Scanners (picklescan, modelscan, ProtectAI Guardian,
HiddenLayer) detect known-bad patterns. Bounty hunters and vendors find
individual bugs by hand. Academics build defenses (PickleBall, fickling). Format
maintainers run their own scans (HuggingFace scanned 116k+ GGUF chat templates;
onnx and safetensors ship their own fuzz targets).

The open seam is what almost nobody does: maintained, continuous, coverage-guided
fuzzing of loader internals for unknown memory-safety and logic defects, with
structure-aware generation to reach past the shallow layer that blind fuzzing and
scanners cannot. That is what this project is.

It deliberately stays on the defect-demonstration side of the line. It hunts
crashes, memory-safety violations, and denial-of-service. It does not build
weaponized exploits or discover new code-execution/config-injection vectors; the
config target is scoped to parsing robustness only, with the code-execution
surface excluded by construction.

## Targets and results

Every target begins with an M0 audit (is it already fuzzed?) before any harness is
written; several candidates were ruled out this way (safetensors, ONNX,
sentencepiece all already fuzzed). See `docs/M0-baseline-audit.md`.

| Target | Loader | Toolchain | Result |
|--------|--------|-----------|--------|
| GGUF | llama.cpp `gguf_init_from_buffer` | C++ / libFuzzer | 5 known-bug reproductions; clean after fuzz-blockers (58M runs) |
| tokenizers | HF `Tokenizer::from_bytes` | Rust / cargo-fuzz | 1 real finding (decoder panic on load, DoS); clean after blocker |
| pytorch | `weights_only` unpickler | Python / Atheris | 4 harnesses incl. structure-aware; storage surface mapped, robust |
| transformers config | `PretrainedConfig.from_dict` | Python / Atheris | parsing robustness; clean over a real campaign |

Findings are tracked in `docs/FINDINGS.md`. Clean results are recorded honestly:
across these targets the shallow bug layer is largely exhausted, and the remaining
defects need the structure-aware depth that is this project's differentiation. A
clean run that provably reached the target (confirmed by coverage growth) is a
useful negative result, not a non-result.

## What is in here

```
targets/<name>/        one directory per target
  harness/             fuzz harness source (verified entry point)
  build.sh             reproducible build (pinned upstream version)
  corpus/              seed corpus (synthetic, no proprietary weights)
  grammar/             structure-aware mutation notes and generators
  fuzz-blockers/       local patches to fuzz past known-shallow bugs (public bugs only)
  README.md            provenance, M0 result, bug classes, scope
chassis/               shared machinery, not per-target
  triage.py            dedup crash reports by fault location; classify shallow/real
  tests/               validated against real fault reports from actual runs
docs/                  M0 audit, findings ledger, architecture, lessons, roadmap
.github/workflows/     continuous-fuzz: short per-target runs, triage-gated
ci/, oss-fuzz/         layouts for continuous instances
```

## Structure-aware generation

Blind byte mutation exhausts the shallow layer quickly and cannot assemble the
valid-but-malformed inputs that reach a backend. The generators here build valid
structures and fuzz the dangerous fields: for the pytorch unpickler, valid pickle
opcode streams calling an allowlisted rebuild function with fuzzer-chosen
size/stride/offset arguments, reaching the C++ tensor backend on every iteration
(verified by coverage growth). This is the capability scanners and blind fuzzers
do not have, and where an unknown defect would most plausibly live.

## Triage chassis

`chassis/triage.py` collapses a pile of crash artifacts into the few distinct
faults they represent (dedup by fault location, not by input) and classifies each
as shallow, real, or review. It parses AddressSanitizer, UBSan, Rust panic, Python
traceback, and native-signal reports, and is validated against fault reports
captured from real runs. This codifies the manual triage the project did
repeatedly, and is what lets the continuous layer gate on genuine findings.

## Discipline (the lessons that shaped the tool)

- Verify the entry point and behavior against source, never assume; probe that a
  generated input actually loads before spending a campaign.
- Verify fixes behaviorally, not by proxy strings; a registry-crate edit does not
  rebuild (use a local checkout plus a patch override).
- Dedup crashes by fault location, not file count (14,724 artifacts were one bug).
- Check prior art before treating a crash as a finding.
- A fuzz-blocker patch for an unreported bug is a disclosure artifact; embargo it.

See `docs/LESSONS.md`.

## Security and disclosure

This tooling finds real vulnerabilities in third-party software. Findings are
handled under coordinated disclosure (`SECURITY.md`): reported privately first,
with public reproducers withheld until a fix ships. Live reproducers and the
disclosure reports for unreported findings are kept in a gitignored
`PRIVATE_findings/` directory and never pushed before disclosure.

## License

Apache-2.0. See `LICENSE`.
