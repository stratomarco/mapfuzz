#!/usr/bin/env bash
# Setup for the transformers config-parsing robustness harness.
# Installs transformers and atheris. torch is NOT required (config parsing works
# without it). Pin the current release to fuzz current code.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
TRANSFORMERS_SPEC="${TRANSFORMERS_SPEC:-transformers}"
python3 -m pip install --quiet "$TRANSFORMERS_SPEC" atheris
python3 -c "import transformers; print('transformers', transformers.__version__)"
echo "run: python3 harness/fuzz_config_from_dict.py --selftest   (then a campaign)"
echo "scope: robustness/DoS only; the code-execution surface is out of scope by design."
