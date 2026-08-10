#!/usr/bin/env bash
#
# Setup + run for the PyTorch weights_only restricted-unpickler harness.
#
# Requires Python 3 and pip. Installs torch (CPU is fine) and atheris, then
# generates a realistic tensor seed and prints the run command.
#
# Entry point (torch._weights_only_unpickler.load) verified against source.
# Pin torch to the version you intend to fuzz; target the CURRENT release so
# you are hunting the next gap, not a fixed CVE. Record the version you used.

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

TORCH_SPEC="${TORCH_SPEC:-torch}"   # e.g. TORCH_SPEC='torch==2.10.0' to pin

python3 -m pip install --quiet "$TORCH_SPEC" atheris

echo "torch version under test:"
python3 -c "import torch; print(' ', torch.__version__)"

# Generate a realistic seed: a small state_dict saved the modern (zip) way,
# then extract its inner data.pkl so the fuzzer mutates the actual opcode
# stream the restricted unpickler consumes. Falls back to the checked-in
# builtin-only seed if extraction is unavailable.
python3 - <<'PY'
import io, zipfile, torch, os
buf = io.BytesIO()
torch.save({"weight": torch.zeros(3), "bias": torch.zeros(1)}, buf)
buf.seek(0)
out = os.path.join("corpus", "seed_tensor_state_dict.pkl")
try:
    with zipfile.ZipFile(buf) as z:
        name = next(n for n in z.namelist() if n.endswith("data.pkl"))
        with open(out, "wb") as f:
            f.write(z.read(name))
    print("wrote realistic seed:", out)
except Exception as e:
    print("could not extract data.pkl (", e, "); using builtin seed only")
PY

echo
echo "run a campaign with:"
echo "  python3 harness/fuzz_weights_only.py -max_total_time=600 -rss_limit_mb=4096 corpus/"
echo
echo "scope reminder: this hunts crashes / unexpected failures in the RESTRICTED"
echo "unpickler (the safe path). Findings are defect demonstrations for coordinated"
echo "disclosure, never weaponized payloads."
