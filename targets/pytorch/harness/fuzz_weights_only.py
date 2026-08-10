"""Atheris harness for PyTorch's restricted (weights_only) unpickler.

Target: torch._weights_only_unpickler.load  (verified entry point at line 592
of torch/_weights_only_unpickler.py on main).

Scope and intent (read this):
    This harness looks for CRASHES and unexpected failures in the RESTRICTED
    unpickler, the code path that torch.load(..., weights_only=True) uses and
    that is explicitly meant to be safe against untrusted checkpoint files. The
    productive, current frontier here is malformed opcode streams and malformed
    storage/reduce arguments reaching the tensor backend through allowlisted
    functions (the class of CVE-2026-24747), not the ancient fact that raw
    pickle is unsafe.

    This is defect demonstration, not weaponization. The harness feeds mutated
    bytes to the restricted unpickler and treats a process crash or an
    unexpected exception as a finding. It never constructs a working RCE
    payload. If a safelist escape is found, the correct output is a minimal
    reproducer that demonstrates the restricted loader reached something it
    should not, for coordinated disclosure, not a deployable exploit.

Why call the unpickler directly (not torch.load): torch.load wraps this in a
zip-container parse. Feeding bytes straight to the restricted unpickler puts
the fuzzer's input directly into the opcode dispatch, which is where the
opcode/metadata validation bugs live. A second harness can target the full
torch.load container path separately.
"""

import io
import struct
import sys

import atheris

with atheris.instrument_imports():
    import torch  # noqa: F401  (needed so allowlisted globals/rebuild fns resolve)
    from torch import _weights_only_unpickler as wou

# Exceptions the restricted unpickler is DESIGNED to raise on bad input. These
# are correct, safe rejections, not findings. Anything outside this set that is
# not a clean rejection is worth a look; a hard crash (segfault) is caught by
# the fuzzer itself regardless.
_EXPECTED = (
    wou.UnpicklingError,
    EOFError,
    ValueError,
    KeyError,
    IndexError,
    TypeError,
    AttributeError,
    ImportError,
    struct.error,
)


def TestOneInput(data: bytes) -> None:
    try:
        wou.load(io.BytesIO(data))
    except _EXPECTED:
        # Designed-for rejection or a benign malformed-input error. Not a finding.
        return
    except RecursionError:
        # Deep-nesting DoS class. Let the fuzzer record it as a distinct signal
        # by re-raising; comment out to treat as benign if it dominates.
        raise
    # Any other exception type propagates and is recorded by Atheris. A native
    # crash (memory corruption in the C++ backend reached via an allowlisted
    # reduce) aborts the process and is caught as a crash artifact.


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
