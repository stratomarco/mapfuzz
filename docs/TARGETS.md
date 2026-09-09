# mapfuzz target status

Reviewed against the tracked checkout on 2026-09-09. Historical findings remain
in the evidence ledger; lifecycle and compute decisions here control future work,
not attribution. No target is promoted to automatic campaigns. Infrastructure
and locked differential regression CI run on push/PR; this is not a claim of
suite-wide continuous fuzzing.

The machine-checked source for lifecycle, last M0, consumer boundary, controls,
evidence paths and compute decision is `targets/qualification.yaml`.

| Directory | Lifecycle | Last M0 | Semantic milestone | Compute decision and next gate |
|---|---|---|---|---|
| clip_mmproj | qualified locally; parked | 2026-09-09 | Standard and Yi tensor bytes are synchronously read and a CPU vision consumer is constructed; incomplete standard MLP rejects before reads. | Parked. No more mutations. Maintainer may later choose the local normal hardening PR draft through official channels. |
| tokenizers | regression maintenance | 2026-08-13; historical, refresh required | Valid seeds exercise `Tokenizer::from_bytes`; breadth across named component families is not yet measured. | Regression only. Refresh M0 and pin dated Rust/cargo-fuzz plus the complete dependency lock before qualification compute. |
| gguf | paused | not current | Metadata and descriptors only under `no_alloc=true`; allocation and a downstream consumer remain unproved. | No compute. Refresh M0 and prove a named consumer with controls. |
| gguf_py_reader | archived | not current | Valid-seed acceptance and downstream consumer reach are not tracked. | No compute. Reopen only after meaningful upstream changes with exact pins and controls. |
| pytorch | paused | not current | Restricted-unpickler/meta-tensor paths exist; native storage reach remains unproved. | No compute. Recover provenance-backed deep harnesses, lock the environment and refresh M0. |
| transformers_config | retired | not current | Self-generated base-config round trips do not reach malformed JSON or model-specific validation. | No compute. Replace with a newly scoped target rather than extend this generator. |
| flax_checkpoint | paused | not current | Historical msgpack and structural paths lack a current locked environment and semantic controls. | No compute. Refresh M0/environment and prove accepted inputs plus named structural states. |
| minja_template | archived | not current | Historical google/minja parser/render reach does not establish current llama.cpp Jinja reach. | No compute. Run current llama.cpp M0 only if a concrete public-coverage gap is identified. |
| tokenizers_differential | regression maintenance | not current | Fifteen locked WordPiece probes agree; broader Unicode/subword states remain unqualified. | Regression only. Refresh M0, widen matched configurations and add accepted-input/state metrics before campaigns. |

## Lifecycle meanings

- **Regression maintenance:** run deterministic locked regression checks only;
  fuzz campaigns need a new M0 and promotion decision.
- **M0 candidate:** source and public-coverage reconnaissance only. Build or fuzz
  compute is not authorized until M0 identifies a defensible consumer boundary.
- **Paused:** preserve tracked work, but spend no compute until the named
  prerequisite is repaired.
- **Archived:** bounded historical result retained to prevent rediscovery; reopen
  only after a meaningful external or scope change.
- **Retired:** the target design does not reach the intended surface. Do not
  revive it incrementally.
- **Qualified locally; parked:** build and semantic reachability are locally
  reproducible, but the recorded stop rule forbids additional mutation. This is
  not a vulnerability, novelty, upstream-fix or publication claim.

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

The shared qualification defaults are one CPU worker, a hard 4 GiB resident
memory ceiling, zero swap, five seconds per input, 60 seconds per batch and a
90-second outer deadline. A package may tighten these values but must not loosen
them without a separately reviewed brief. Required counters, controls and stop
rules are defined in `targets/qualification.yaml` and checked by
`chassis/qualification_manifest.py`.

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
