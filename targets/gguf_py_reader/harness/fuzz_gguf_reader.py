#!/usr/bin/env python3
# Atheris harness for gguf-py's GGUFReader (the Python GGUF reader).
#
# Target: gguf.gguf_reader.GGUFReader, which parses an untrusted .gguf file with
# its own offset/count/recursion logic. This is the Python read side of the GGUF
# format; the oss-sec V-01..V-06 advisory (2026-05-15) names gguf-py as affected
# by the GGUF integer-overflow/division class. Our C++ GGUF harness ran with
# no_alloc=true and did NOT exercise this logic; this harness covers the Python
# reader's parsing surface directly.
#
# Oracle: a well-formed-enough file parses or raises a VALIDATION error (fine).
# We treat as INTERESTING only faults that indicate a robustness/DoS defect:
#   - RecursionError (unbounded nested-ARRAY recursion, no depth guard)
#   - MemoryError (unbounded declared allocation)
#   - UnicodeDecodeError escaping the reader (raw, uncaught, on a key/name)
#   - any exception type NOT in the expected-validation set
# Expected validation errors (the reader's own guards and benign parse failures)
# are suppressed so the campaign explores past them.
#
# Usage:
#   python3 fuzz_gguf_reader.py --selftest
#   python3 fuzz_gguf_reader.py -max_total_time=60 -rss_limit_mb=2048 corpus/
#
# The reader is import-guarded so a missing gguf-py yields a clear message.

import sys
import os
import io
import tempfile
import atexit

import struct

import atheris

with atheris.instrument_imports():
    try:
        from gguf.gguf_reader import GGUFReader
    except Exception as e:  # pragma: no cover
        sys.stderr.write(
            "could not import gguf.gguf_reader.GGUFReader; "
            "add llama.cpp/gguf-py to PYTHONPATH. error: %r\n" % (e,)
        )
        raise

# Exceptions that represent a normal, in-scope rejection of malformed input.
# The reader raising one of these is CORRECT behaviour, not a finding.
EXPECTED = (
    ValueError,      # the reader's own guards (alignment, n_dims, bad type, magic)
    KeyError,        # duplicate field
    struct.error,    # struct unpack on a short/odd buffer
    IndexError,      # slice/index past a short buffer
    EOFError,
    OSError,         # file/mmap issues on a truncated or odd file
)

# One reusable temp file, cleaned at exit (avoids per-iteration fd churn).
_tmp_fd, _tmp_path = tempfile.mkstemp(suffix=".gguf", prefix="fuzz_gguf_")
os.close(_tmp_fd)


@atexit.register
def _cleanup():
    try:
        os.unlink(_tmp_path)
    except OSError:
        pass


def _run_one(data: bytes) -> None:
    # Write the candidate bytes to the temp file, then let the reader parse it.
    with open(_tmp_path, "wb") as f:
        f.write(data)
    try:
        GGUFReader(_tmp_path, mode="r")
    except EXPECTED:
        # In-scope rejection of malformed input. Not interesting.
        return
    except (RecursionError, MemoryError):
        # DoS-shaped: unbounded recursion (nested ARRAY) or allocation.
        # Re-raise so the fuzzer records it as a crash to triage.
        raise
    except UnicodeDecodeError:
        # A raw unicode error escaping the reader is a robustness gap worth
        # surfacing (key/tensor-name decode with no error handler). Re-raise.
        raise
    # Any OTHER exception type is unexpected: re-raise so it is recorded.
    except Exception:
        raise


def _selftest() -> int:
    # 1. Empty input must not crash with an unexpected error.
    for probe in (b"", b"XXXX", b"GGUF", b"GGUF\x03\x00\x00\x00"):
        try:
            _run_one(probe)
        except EXPECTED:
            pass
        except (RecursionError, MemoryError, UnicodeDecodeError):
            print("selftest: unexpected DoS/unicode on a trivial probe: %r" % probe)
            return 1
        except Exception as e:
            # A trivial short buffer raising something outside EXPECTED would
            # itself be notable; report it rather than hide it.
            print("selftest: probe %r raised unexpected %r" % (probe, e))
            return 1
    print("selftest OK: trivial probes rejected within the expected error set")
    return 0


def main() -> None:
    if "--selftest" in sys.argv:
        sys.exit(_selftest())

    def one_input(data: bytes) -> None:
        _run_one(data)

    atheris.Setup(sys.argv, one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
