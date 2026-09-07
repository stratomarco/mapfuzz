# mapfuzz

Security research on parsers and loaders of machine-learning model artifacts.
ML security is security engineering: a downloaded model file crosses a trust
boundary when a loader parses and materializes it.

The project combines structure-aware fuzzing, source review, crash triage and
bounded negative results. Coverage of mature formats varies by entry point;
check current upstream fuzz targets before claiming a gap or spending compute.

## Results and scope

The [finding ledger](docs/FINDINGS.md) has eight entries: one known duplicate
used for harness validation and seven project discoveries. Discovery does not
establish independent novelty; the minja recursion class also has public prior
art. Findings and disclosure statuses are historical records unless explicitly
reverified. No whole-component safety claim follows from a clean campaign.

The canonical [evidence](evidence/claims.yaml) records provenance, observations,
confidence and boundaries. The validator checks schema structure, not truth or
adequacy of research evidence. Private reproductions are not available from this
public checkout.

## Targets

Nine target directories are inventoried in [TARGETS.md](docs/TARGETS.md), with
tracked harnesses, seeds, status and promotion requirements. Targets include GGUF,
tokenizers, PyTorch, transformers config, Flax, minja, CLIP/mmproj, gguf-py and
tokenizer differential research. Two PyTorch harnesses are tracked; historical
deep storage/container harnesses are absent.

Automatic target campaigns are paused while qualification is repaired.
Infrastructure tests run on push/PR. CLIP/mmproj materialization is the first
candidate for renewed depth work, after current M0 and valid-seed reachability.
Existing no_alloc harnesses do not prove tensor-materialization coverage.

## Working locally

This linked worktree uses WSL Git. See [local setup](docs/TARGETS.md#local-execution).
Core checks on Linux/WSL, with PyYAML installed in an isolated environment:

```bash
python3 -m unittest discover -s evidence -p 'test_*.py'
python3 -m unittest discover -s chassis/tests -p 'test_*.py'
python3 chassis/tests/test_triage.py
python3 chassis/resource_oracle.py --selftest
python3 evidence/tool.py --check --render
python3 chassis/check_repository.py
```

`chassis.campaign` records command, exit status, combined output and artifacts,
and fails closed on execution failures or fault artifacts. Triage labels are
review aids, not severity or novelty determinations. Unknown reports fail.
The resource oracle independently tests memory limits and wall-clock timeout;
its synthetic tests do not establish real model-loader protection.

## Layout

- `targets/`: harnesses and historical build/seed material; completeness varies.
- `chassis/`: campaign runner, triage, resource oracle and regression tests.
- `evidence/`: canonical YAML, generated Markdown and schema validation.
- `docs/`: findings, scope, historical research and the current roadmap.
- `.github/workflows/`: infrastructure and evidence gates.
- `ci/`, `oss-fuzz/`: integration scaffolds, not proof of deployed services.

## Security and disclosure

Scope is defect demonstration: crashes, resource exhaustion and correctness
observations. See [SECURITY.md](SECURITY.md). Private findings, campaign logs and
live reproducers stay local unless disclosure is authorized. Public upstream PRs
may already contain details; each ledger entry records its own status.

Apache-2.0; see LICENSE.
