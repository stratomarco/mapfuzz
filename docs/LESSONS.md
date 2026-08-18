# Lessons

Short engineering log of failure modes hit during development and the guardrails added in response. The through-line is one rule: verify state before trusting it. Every failure below was a stale or incomplete artifact presenting itself as current.

## Verify the binary before trusting a run

Symptom: a rebuilt fuzzer kept reproducing a bug that had supposedly been patched.
Cause: the binary was stale; the link step had not refreshed it, so an old build was being run.
Guardrail: before trusting any run, confirm the BuildId changed and that `-help=1` works. A run against an unverified binary proves nothing.

## Verify the patch landed before trusting the build

Symptom: the build reported `fuzz-blockers: applied`, but the target kept crashing at a site the patch was supposed to fix.
Cause: the patch file was missing one of its hunks. `git apply` returned success because the other hunks applied; the missing one left a known bug in the build.
Guardrail: `build.sh` now counts the hunk markers in the patch and in the patched source, and aborts before compiling if they disagree. `git apply`'s exit code is never trusted alone. Root cause of the incomplete patch: it was regenerated with `git diff` from a tree that did not have the last hunk staged. Always regenerate the patch from a tree that contains every hunk, and verify the count.

## Verify a crash is current before triaging it

Symptom: a per-file loop over the corpus flagged hundreds of files as crashing.
Cause 1: the corpus directory had accumulated inputs from earlier unpatched runs; most "crashes" were fossils the current binary no longer produces the same way.
Cause 2: the loop treated any nonzero exit as a crash, which conflates clean rejections and other exits with real faults.
Guardrail: start campaigns from a clean corpus (seed only) so every crash is one the current build actually produces. Triage by fault signature (function, file, line, sanitizer class), not by exit code. This is the C1 dedup-by-location chassis feature; this incident is why it is prioritized.

## Distinguish a signal-less segfault from a finding

Symptom: a bare `Segmentation fault (core dumped)` with no libFuzzer banner and no sanitizer report.
Reading: a real parser finding comes with a sanitizer report. A signal-less, instant segfault points at startup or environment (stale binary, resource limit) or at a stack overflow that outruns the sanitizer's own handler, not at the parse path. Confirm with `-help=1`, `-runs=0`, a single-file run, and `ulimit -a` before assuming a bug.

## General

Most of this session's lost time was archaeology on stale artifacts. The chassis features already on the roadmap (C1 crash dedup by location, C2 shallow-blocker classifier) exist precisely to automate the verify-before-trust checks done by hand here. This log is the evidence for building them before the next target.

## Registry-crate edits do not rebuild; use a local checkout plus [patch]

Symptom: a fix edited directly into a dependency's source under `~/.cargo/registry` appeared correct on disk (grep confirmed it), but the rebuilt fuzzer kept hitting the patched bug, and the build finished in a fraction of a second with no compile.
Cause: cargo fingerprints registry crates by checksum and will not recompile an edited registry copy; it reuses the cached artifact. The source was patched, the binary was not.
Guardrail: to patch a dependency for fuzzing, clone it at the pinned version, edit the clone, and wire it in with `[patch.crates-io] name = { path = "..." }`. Confirm cargo actually rebuilds by seeing `Compiling <crate>` with the local path in the build output.

## Verify a fix behaviorally, not by a proxy string

Symptom: after patching a panic, a check `strings binary | grep -c 'Helper'` returned 120, suggesting the fix had not taken.
Cause: the marker was a common substring. The codebase has many `...Helper` type names, so the count reflected unrelated identifiers, not the panic. The proxy was meaningless.
Guardrail: prove a fix by behavior. Run the known reproducer through the freshly built binary; if the input that used to crash now parses cleanly, the fix is genuinely in the binary. A string grep is only trustworthy when the string is unique to the thing being checked.

## A fuzz-blocker for an unreported bug is a disclosure artifact

Symptom: n/a (process rule learned while packaging).
Principle: a fuzz-blocker patch encodes the exact fix at the exact location of a bug. For an already-public bug that is harmless; for an unreported, embargoed finding it discloses the bug. Guardrail: commit blockers only for already-public bugs. Keep blockers for embargoed findings local and gitignored alongside the reproducer, until the finding is reported.

## Structure-stable encoding makes coverage guidance work on generators

A generator that draws from FuzzedDataProvider in a mutation-unstable order
(variable-length draws, counts drawn before the values they size) breaks coverage
guidance: libFuzzer mutates raw bytes, but a one-byte flip reshuffles the whole
generated structure, so the fuzzer cannot attribute a coverage change to a field.
Guardrail: use a FIXED-LAYOUT decode. Read every choice and value from a fixed
byte offset with fixed width; reserve slots for unused capacity so positions never
shift. Then a value-byte flip changes exactly one field, and libFuzzer's coverage-
guided byte mutations become coverage-guided structural mutations. Verify the
property directly: enumerate single-byte flips and confirm value-slot flips change
one field (fuzz_rebuild_args_stable.py --selftest does this).

## Differential oracles need structure-aware input too (native-code blind spot)

A cross-implementation differential oracle (fast vs slow tokenizer, same vocab,
divergence = bug) is a new kind of oracle that finds non-crashing bugs. But when
both implementations are native (Rust/C) extensions, libFuzzer sees little
instrumented code and coverage-guidance is weak (coverage stays flat). Random
text mutation then mostly produces agreement (both map junk to [UNK]).
Guardrail: pair a differential oracle with a structure-aware generator aimed at
the divergence-prone categories (Unicode normalization forms, combining marks,
control chars, byte-vs-char boundaries, subword-merge boundaries), not raw bytes.
The oracle and the generator compose.

## Check the OSS-Fuzz build.sh target LIST, not just project membership

A project being in OSS-Fuzz does not mean the entry point you care about is
fuzzed. llama.cpp IS in OSS-Fuzz, but its target list (fuzz_grammar,
fuzz_json_to_grammar, fuzz_apply_template, fuzz_load_model, fuzz_inference,
fuzz_structured) does not include the multimodal projector loader (tools/mtmd/
clip.cpp). The GBNF grammar parser was correctly declined as saturated because
fuzz_grammar exists; the mmproj loader was an open entry point in the same
project and yielded two findings (0006, 0007). Guardrail: in M0, read the actual
projects/<name>/build.sh and enumerate which entry points ARE and are NOT built
as fuzz targets. In-OSS-Fuzz projects with an entry point absent from their
build.sh are the richest remaining vein. Corroboration: a maintainer security-
audit branch (xsn/security_audit_0) was concurrently active on the exact file,
independently validating the target selection.

## Confirm reachability before calling an allocation primitive a DoS

An allocation that OOMs in isolation is not a finding until an untrusted-input
path actually reaches it. LeRobot's resolve_episode_indices does
list(range(total_episodes)) with only a <0 guard, and total_episodes comes from a
downloaded info.json; in isolation range(10**12) raises MemoryError. But the
download-path site takes the range branch only when episodes is None, while its
sole caller invokes it only when episodes is not None, so that branch is dead on
the reachable path. The "download DoS" hypothesis was retracted after reading the
one caller. Contrast clip 0007, where block_count reaches model.layers.resize on
the normal load path with no such guard. Guardrail: trace the primitive back to a
real entry point through its actual callers before claiming a DoS; a confirmed
OOM primitive plus an unreachable path is a non-finding, not a finding.

## Re-confirm against pristine current upstream immediately before submitting

Upstream moves. Before opening the clip PR, a fresh fork clone was on a newer
master than the local working tree, and a wholesale file copy would have reverted
recently-merged upstream guards (array is-array checks, n_merge, image_size,
audio_chunk_size). A maintainer audit branch had also removed the array checks
pending a rework. Guardrail: regenerate the patch against current master, diff it,
and confirm each finding still reproduces on pristine current upstream before
submitting. Scope the PR to only what is genuinely still missing (here: scalar
type checks + n_layer bound; the array checks were already upstream and left
untouched to avoid colliding with the maintainer's rework).

## A project's reference implementation may be weaker than its production one

llama.cpp's C++ GGUF reader guards untrusted array lengths (gguf_read_emplace_helper
returns false on short read and catches length_error and bad_alloc). The Python
reference reader in the SAME repository (gguf-py) loops range(alen) over the same
untrusted length with none of those guards, and hangs on a 49-byte file (finding
0008). The maintainers already treat this input class as hostile in C++; the
Python reference impl simply never received the equivalent hardening. Guardrail:
when a project ships more than one implementation of the same parser (a fast
production one and a reference/secondary one), fuzz the reference impl too. It is
often less exercised, less hardened, and still reachable by real tooling
(inspectors, converters, editors, CI that reads metadata). A cross-impl diff of
how each handles the same untrusted field is a fast way to find the weaker one.
