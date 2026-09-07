#!/usr/bin/env bash
# Setup for the flax checkpoint-restore harness. Pure Python (no torch/GPU JAX
# needed for the serialization path). Requires a reviewed hash-locked environment.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ../../chassis/install_locked.sh
python3 -c "import flax; print('flax', flax.__version__)"
echo "run: python3 harness/fuzz_msgpack_restore.py --selftest   (then a campaign)"
