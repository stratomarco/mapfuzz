# Architecture

This document explains how the fuzzer is put together and records the decisions behind it, each with the context that forced the choice and the trade-off accepted. It is the reference for why the system looks the way it does. Factual survey claims and per-target evidence live in `REQUIREMENTS.md` and `docs/M0-baseline-audit.md`; this document does not repeat them.

## 1. System overview

The mental model in one line: an untrusted model file is fed into the real loader under sanitizer and coverage instrumentation, a coverage-guided engine mutates inputs to reach deeper into the parser, and any fault is caught by an oracle, minimized, and routed to coordinated disclosure.

End-to-end pipeline:

```
seed corpus ─▶ mutation engine ─▶ harness ─▶ instrumented loader
                    ▲                              │
                    │                        coverage feedback
                    └──────────────────────────────┘
                                                   │
                                        fault ─▶ oracle stack ─▶ triage ─▶ PRIVATE_findings ─▶ upstream disclosure
```

Everything is organized per format. A target is a self-contained directory holding a harness, a pinned reproducible build, a seed corpus, and grammar notes. The core carries no format-specific logic, so adding a format never touches shared code.

## 2. Architectural principles

These are the load-bearing beliefs. Every decision below traces to one of them.

1. Classical security engineering framing. A model file is a file format, a loader is a parser, and the download-to-load transition is a trust boundary. This is not a metaphor; it dictates that the mature parser-fuzzing toolchain applies directly.
2. Reuse the commodity, build the moat. Mutation engines are solved. The value is in the format grammars, the oracle stack, and the disclosure discipline, so effort goes there.
3. Verify against source, pin everything. Entry points and struct layouts are read from upstream at a pinned commit, never assumed. A finding must reproduce on that pinned commit and toolchain.
4. One target, one isolated unit. Targets share structure, not state. Isolation keeps a bug in one harness from contaminating another and keeps the extension path clean.
5. Findings are unpublished exploits. The tooling produces real vulnerabilities in third-party software; reproducers are handled as embargoed material until disclosed.

## 3. Component architecture

Target definition. Each `targets/<format>/` directory is the unit of work: `harness/` (the fuzz entry point), `build.sh` (reproducible instrumented build pinned to an upstream commit), `corpus/` (synthetic seeds), `grammar/` (structure-aware mutation design and modules), and a `README.md` recording the verified entry point and provenance. The `CONTRIBUTING.md` extension contract makes this directory the only thing a new format needs.

Harness. An in-process function receiving a byte buffer and calling the loader's real entry point with no pre-validation. It drives execution past the parse into the read paths by exercising accessors, and gates every accessor on the type the loader reports so it never causes a fault of its own.

Instrumented loader build. The loader is compiled from upstream source as a static, CPU-only library with coverage and sanitizer instrumentation, pinned to a specific commit. Static and CPU-only keeps the instrumented unit simple and deterministic; the pin makes findings reproducible.

Mutation layer. A coverage-guided engine (libFuzzer, or AFL++) supplies the search loop. A per-format structure-aware layer keeps the file envelope parseable while perturbing the fields that drive dangerous paths, so mutation budget is not wasted failing magic and version checks.

Corpus. Seeds are minimal, structurally valid, and synthetic, with no proprietary weights. The seed corpus is tracked; the runtime corpus that the engine grows is not.

Oracle stack. Faults are classified, not lumped. Memory-safety faults come from the sanitizer. Resource-exhaustion faults come from allocation and timeout ceilings. Load-time code-execution faults (pickle reduce, unsandboxed template rendering, path traversal on load) are a separate semantic layer. Assertion-triggered aborts are a fourth triage category, distinct from memory-safety findings.

Triage. Every fault is deduplicated by stack hash, minimized to the smallest reproducing input, and recorded with the input, toolchain, and commit needed to reproduce it.

Continuous fuzzing. The same harness runs in two settings: ClusterFuzzLite for pull-request-time runs in an adopting repo's CI, and OSS-Fuzz for sustained compute on the central instance.

Disclosure pipeline. Reproducers and undisclosed writeups live in a gitignored `PRIVATE_findings/` directory and move to the upstream maintainer under coordinated disclosure before any public reproducer.

## 4. Decision log

Each entry records the context that forced the decision, the decision itself, and the consequences accepted. Status is Accepted unless noted.

### ADR-0001: Fuzz the model-artifact loader, not the graph compiler or model behavior

Context. Several adjacent fuzzing frontiers are already saturated: deep-learning graph and tensor compilers, MCP protocol servers, and surface-level jailbreak generation. The model-artifact loader (the code that turns a file on disk into an in-memory model) is comparatively untooled, and a recent advisory shows real bugs found there by hand.

Decision. Scope the project to the parsing and deserialization code of model-artifact formats. Explicitly exclude the graph optimizer, the inference behavior, and the network protocol.

Consequences. A clear, defensible niche with immediate real-world impact. The trade-off is that behavior-level and compiler-level bugs are out of scope by construction; that is intentional, not an omission.

### ADR-0002: Frame the work as classical security engineering

Context. ML security is often treated as a separate discipline, which pushes teams toward bespoke, immature tooling.

Decision. Treat the model file as a file format, the loader as a parser, and download-to-load as a trust boundary. Anchor the rationale in the established literature (Anderson on trust boundaries, McGraw and BIML on architectural risk analysis for ML systems, the OWASP LLM Top 10 and MITRE ATLAS for the supply-chain threat classes).

Consequences. The full parser-fuzzing toolchain (coverage-guided engines, structure-aware mutation, sanitizers, continuous CI) applies without reinvention. The framing also sets the review and documentation standard for the whole project.

### ADR-0003: Reuse the mutation engine, build the oracles and grammars

Context. Writing a mutation engine is a large effort that duplicates mature tools (libFuzzer, AFL++, libprotobuf-mutator).

Decision. Depend on an existing engine for the search loop. Invest original work in the format grammars, the oracle stack, and the disclosure pipeline.

Consequences. Faster path to a working target and to first findings. The dependency on upstream engines is acceptable because they are standard and already accepted by OSS-Fuzz.

### ADR-0004: In-process, coverage-guided (white-box) harness as the primary mode

Context. For a loader whose source is available, coverage feedback is the strongest possible signal, and it is precisely what a black-box network-style approach cannot get.

Decision. Build in-process harnesses that link the loader directly and run under a coverage-guided engine, rather than driving the loader as an opaque process.

Consequences. Deep reach into parser code and fast bug discovery. This assumes source availability, which holds for the open-source loaders in scope.

### ADR-0005: In-memory buffer entry point, parse-only primary harness

Context. The GGUF loader exposes both a file-path entry point and an in-memory buffer entry point, and a flag controlling whether tensor data is allocated during load.

Decision. Use the in-memory buffer entry point so no filesystem access happens per input, and set the parse-only mode (no tensor-data allocation) for the primary harness.

Consequences. Fast, memory-bounded runs that reach the metadata, descriptor, alignment, offset, enum, and size-computation paths, which is where the majority of the known bug classes live. The trade-off is that the tensor-data allocation path is not exercised by the primary harness; that path is a planned second harness variant, not a gap in the design.

### ADR-0006: Gate every harness accessor on the reported type

Context. Calling a value accessor with the wrong type would fault inside the harness. A fault caused by the harness is noise that wastes triage time and undermines trust in findings.

Decision. Before calling any value accessor, read the type the loader reports and call only the matching accessor. Never call a value accessor for an out-of-range or sentinel type.

Consequences. Findings are attributable to the target, not the harness. The cost is a slightly larger harness with an explicit type switch, which is a worthwhile trade.

### ADR-0007: Layered oracle model with separate assertion triage

Context. Different fault classes need different detection and different handling. A memory-corruption bug and a controlled assertion abort are not the same severity or the same fix.

Decision. Separate the oracles into memory-safety (sanitizer), resource-exhaustion (allocation and timeout ceilings), and load-time code-execution (a semantic layer for pickle reduce, template rendering, and path traversal). Treat assertion-triggered aborts as a distinct fourth triage category.

Consequences. Cleaner findings and correct severity from the start. The load-time execution layer is the harder, higher-value oracle and is scheduled after the memory-safety oracles are working.

### ADR-0008: AddressSanitizer plus coverage as the baseline, UndefinedBehaviorSanitizer opt-in

Context. UndefinedBehaviorSanitizer is exactly what catches the integer-overflow and enum-cast classes, but enabling it across a large numeric codebase during bring-up can surface unrelated noise on the happy path.

Decision. Ship the baseline build with AddressSanitizer and coverage for a clean bring-up, and expose UndefinedBehaviorSanitizer as a one-line opt-in in the build script for hunting the integer and type-confusion classes.

Consequences. A clean first run and a fast path to the arithmetic bug classes when wanted. The consequence is that the integer classes are not caught until the opt-in is enabled, which is a documented, deliberate step.

### ADR-0009: Structure-aware mutation, custom mutator per format before protobuf grammar

Context. Byte-level mutation wastes most of its budget failing envelope checks. Two structure-aware options exist: a custom mutator that parses and re-serializes, or a protobuf model driven by a protobuf-aware mutator.

Decision. For a small self-contained format like GGUF, write a custom mutator first. Reserve the protobuf-grammar approach for the formats that are already protobuf (ONNX, TensorFlow SavedModel), where it reuses a mature engine and composes naturally.

Consequences. Fastest route to effective mutation for the first target, with a clear, reasoned path for the protobuf formats. No single mutation approach is forced across formats that do not share a structure.

### ADR-0010: Pin upstream commits

Context. Loaders change. A finding reported against a moving target is not reproducible, and an entry point verified once can drift.

Decision. Pin the exact upstream commit in every target's build script and README. Re-verify the entry point and re-check findings whenever the pin is bumped.

Consequences. Reproducibility by construction. The cost is periodic, deliberate pin bumps with re-verification, which is the correct discipline rather than a burden.

### ADR-0011: Per-target directory isolation with an extension contract

Context. A suite that grows to many formats needs to add formats without destabilizing existing ones.

Decision. Make each format a self-contained directory with a fixed layout, and keep all format-specific logic there. Document the steps to add a format as an explicit contract.

Consequences. New formats are additive and low-risk. Contributors follow one documented path. There is minor duplication of build scaffolding across targets, accepted in exchange for isolation.

### ADR-0012: Continuous fuzzing via both OSS-Fuzz and ClusterFuzzLite

Context. Bugs surface as a function of accumulated compute, and the corpus is an asset that grows more valuable over time. Two complementary settings exist: in-CI runs on pull requests, and sustained central compute.

Decision. Support ClusterFuzzLite for pull-request-time runs and OSS-Fuzz for sustained compute, sharing one harness and build.

Consequences. Fast feedback during development and long-horizon bug discovery on the central instance. The cost is maintaining two thin integration layers over a shared build, which is small.

### ADR-0013: Coordinated disclosure with a gitignored embargo directory

Context. The tooling produces real vulnerabilities in third-party software. A reproducer committed to a public repository is a published exploit.

Decision. Keep reproducers and undisclosed writeups in a gitignored `PRIVATE_findings/` directory, and disclose to the upstream maintainer privately before any public reproducer.

Consequences. Reflexive public pushes cannot leak a live crasher, verified by checking the ignore rule. The maintainer gets lead time to fix. The cost is that findings are not immediately public, which is the correct trade for responsible disclosure.

### ADR-0014: Require a 32-bit build variant (Accepted, deferred)

Context. The alignment-overflow class from the recent advisory only manifests on 32-bit builds. A 64-bit-only suite is structurally blind to it.

Decision. Require a 32-bit build variant as part of the target definition.

Status. Accepted but not yet implemented. The 64-bit target is built first; the 32-bit toolchain and runtime are a scheduled addition.

Consequences. Full coverage of the known classes once implemented. Until then, the alignment-overflow class is knowingly out of reach, recorded so it is not mistaken for absence of bugs.

### ADR-0015: Apache-2.0 license

Context. The project links loaders under permissive licenses and aims for OSS-Fuzz adoption.

Decision. License the project Apache-2.0.

Consequences. A permissive license with an explicit patent grant, compatible with OSS-Fuzz and with the MIT and Apache-2.0 loaders in the first tiers.

## 5. Open decisions

These are not yet settled and are tracked here rather than decided silently.

1. Project name. The codename is a placeholder pending a final name.
2. First target confirmation. GGUF is chosen first for the highest confirmed bug density and clearest impact; confirm before broadening, or swap to the Rust safetensors path first if that ordering is preferred.
3. Timing of the UndefinedBehaviorSanitizer opt-in. Currently deferred until after the memory-safety baseline; decide when to promote it to default.
4. Differential-across-loaders oracle. Deferred to a later phase as a follow-on capability; confirm it stays deferred.
5. External OSS-Fuzz coverage. In-repo harnesses were confirmed absent at the pinned commit; whether any external OSS-Fuzz project fuzzes the same loader is still open and must be checked before any novelty claim.

## 6. References

- Anderson, Security Engineering (trust boundaries, economics of defense).
- McGraw, Software Security; the Berryville Institute of Machine Learning architectural risk analysis for ML systems.
- OWASP Top 10 for Large Language Model Applications.
- MITRE ATLAS (adversarial threat landscape for AI systems), model-supply-chain techniques.
- Internal: `REQUIREMENTS.md`, `docs/M0-baseline-audit.md`, `SECURITY.md`, and the per-target READMEs.
