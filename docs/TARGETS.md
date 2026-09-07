# mapfuzz target status

Reviewed against the tracked checkout on 2026-09-07. Historical findings remain
in the evidence ledger; status here controls future compute, not attribution.
No target is currently promoted to automatic campaigns. Infrastructure and locked differential regression CI run
on push/PR. This is not a claim of suite-wide continuous fuzzing.

| Directory | Status | Tracked surface and next gate |
|---|---|---|
| clip_mmproj | candidate, build incomplete | Metadata harness and seed generator; `no_alloc=true`. Establish pinned build and tensor-carrying seed reaching materialization before a depth campaign. |
| tokenizers | regression maintenance, build qualification pending | Rust from_bytes and Python stable generator; six JSON seeds. Exact crate pin; record dated nightly and cargo-fuzz version, resolve/commit dependency lock, and rerun seed regression before promotion. Private regressions remain local. |
| gguf | paused | Pinned C++ metadata/descriptor parser with no_alloc=true and one GGUF seed. Keep as historical calibration; allocation behavior is untested here. |
| gguf_py_reader | archived as mapped | Python reader harness and seed generator. Historical environment and negative campaign are not a complete tracked reproduction package. Reopen after meaningful upstream changes. |
| pytorch | paused | Exactly two tracked harnesses: fuzz_weights_only.py and fuzz_rebuild_args_stable.py. Deep storage/container harnesses mentioned historically are absent. Restore provenance-backed sources, exact environment and native reachability before promotion. |
| transformers_config | retired | Generates dictionaries and round-trips its own JSON through base PretrainedConfig. Does not fuzz malformed JSON or model-specific validation. |
| flax_checkpoint | paused | msgpack_restore and from_state_dict; three msgpack seeds. Exact environment and semantic coverage required before any return. |
| minja_template | archived for llama.cpp work | Historical google/minja parser/render harnesses and three template seeds. Does not represent llama.cpp's newer engine; build now requires immutable dependency revisions. |
| tokenizers_differential | locked regression; campaigns paused | One small WordPiece pairing and 15 baseline probes, CPython 3.10.12 Linux x86_64 wheel-hash lock. Richer feature matrix and semantic coverage still required. Correctness divergence does not establish a security bypass. |

## Promotion contract

1. Date the M0: record upstream SHA, exact consumer, trust boundary and public
   fuzz-target inventory. Absence from one project list does not establish novelty.
2. Record exact Python/Rust/compiler versions and transitive dependency lock or
   image digest. A pinned direct dependency alone is insufficient.
3. Track synthetic seeds or deterministic generators. Demonstrate that a valid
   seed reaches a named semantic milestone, with a control that fails earlier.
4. Run a short capped campaign through `chassis.campaign`; retain local command,
   exit status, logs, accepted-input rate and semantic reach.
5. Promote only after fresh-environment reproduction. Continue while new target
   functions/states are reached; otherwise archive a bounded negative.

Do not reconstruct absent private reproducers from public descriptions merely to
make an inventory complete. Public checkout reproducibility and private finding
reproducibility are separate deliverables.

## Local execution

Use WSL for this linked worktree. Its `.git` points to a Linux path and is valid
there; Windows Git does not resolve that path. From PowerShell:

```powershell
wsl -e bash -lc 'cd /mnt/f/mapfuzz/audit-hardening-dev && git status --short'
```

For a qualified local libFuzzer/Atheris target, use a fresh output directory:

```bash
python3 -m chassis.campaign --output .runs/example --timeout 90 -- \
  /absolute/path/to/fuzzer -max_total_time=60 -rss_limit_mb=2048 /path/to/corpus
```

The runner overrides the artifact prefix, saves combined output and result.json,
then fails on nonzero exit, timeout, any artifact, or recognized fault diagnostics.
Unrecognized reports supplied to triage fail. Arbitrary exit-zero text cannot be
universally recognized as a fault: qualification must verify the driver's exit
and artifact contract. No blockers are allowlisted. A future exception must be
specific to a pinned target and reviewed reproducer, never a whole fault class.
Logs and artifacts stay local by default and are ignored by Git.
