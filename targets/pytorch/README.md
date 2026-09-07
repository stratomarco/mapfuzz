# PyTorch restricted-unpickler target

Status: paused pending reproducibility and native-reachability repair.

Exactly two harnesses are tracked:

- `harness/fuzz_weights_only.py`: raw restricted-unpickler opcode bytes.
- `harness/fuzz_rebuild_args_stable.py`: fixed-layout meta-tensor arguments.

`fuzz_rebuild_args.py`, `fuzz_storage_oob.py` and `fuzz_storage_mismatch.py` were
mentioned in historical research but are absent from this checkout. Their run
counts in the evidence ledger are historical observations, not reproducible
commands here. The meta-tensor path does not establish real storage coverage.

The builtin seed is in `corpus/`; `build.sh` can extract a tensor pickle seed
once a reviewed, hash-locked environment is supplied via REQUIREMENTS_LOCK.
Activate a target-specific virtual environment first. No unpinned torch is
installed by default. Record Python, torch, Atheris and native build configuration.

Before resuming: restore provenance-backed deep harness sources, prove a valid
seed reaches a named native consumer, and qualify under the campaign runner.
The historical M0 and CVE references in the ledger must be refreshed before a
new novelty claim. Scope remains crash/robustness demonstration of the restricted
loader, not unrestricted pickle execution.
