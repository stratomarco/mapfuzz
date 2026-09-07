#!/usr/bin/env bash
# Source from a target build script. No moving package defaults are permitted.
set -euo pipefail
: "${REQUIREMENTS_LOCK:?Provide an absolute path to a reviewed pip lock with exact versions and hashes; see docs/TARGETS.md}"
[[ "$REQUIREMENTS_LOCK" = /* && -f "$REQUIREMENTS_LOCK" ]] || { echo 'lock must be an existing absolute path' >&2; exit 1; }
python3 -c 'import sys; assert sys.prefix != sys.base_prefix, "activate a target-specific virtual environment"'
python3 -m pip install --require-hashes -r "$REQUIREMENTS_LOCK"
python3 -m pip freeze --all
