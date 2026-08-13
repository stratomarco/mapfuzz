#!/usr/bin/env bash
# Setup for the flax checkpoint-restore harness. Pure Python (no torch/GPU JAX
# needed for the serialization path). Pins current releases to fuzz current code.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
python3 -m pip install --quiet flax orbax-checkpoint msgpack atheris
python3 -c "import flax; print('flax', flax.__version__)"
echo "run: python3 harness/fuzz_msgpack_restore.py --selftest   (then a campaign)"
