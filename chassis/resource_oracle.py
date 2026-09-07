#!/usr/bin/env python3
"""Resource-exhaustion oracle for the declared-huge allocation class.

This oracle regression-guards a bug CLASS that mapfuzz has confirmed across
multiple targets: a loader reads an untrusted declared size/count/length and
allocates or iterates on it with no bound, so a tiny input drives unbounded
memory or time. Confirmed instances of the class:
  - gguf-py GGUFReader array length (finding 0008 / C-0015)
  - clip/mmproj block_count (finding 0007 / C-0014)
  - LeRobot total_episodes range (non-finding, latent / C-0023)

The oracle does not itself find bugs; it is a REGRESSION GUARD. Given a loader
and a crafted "bomb" input, it asserts the loader rejects or fails FAST within a
memory-and-time cap rather than consuming unbounded resources. A benign input
must pass. If a future change reintroduces an unbounded path, the guarded case
flips from "rejected within caps" to "killed by the cap", failing the check.

The check runs the loader in a separate process with RLIMIT_AS (address space)
and a wall-clock timeout, so a genuine unbounded allocation is killed by the OS
rather than taking down the runner.

Usage:
  python3 resource_oracle.py --selftest        # CI regression guard (exit 0/1)
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import math
import resource
import sys
from typing import Any, Callable


# Outcome codes returned from the capped child.
OK = "ok"                 # loader returned normally
REJECTED = "rejected"     # loader raised (a clean, fast rejection: good)
EXHAUSTED = "exhausted"   # loader hit the memory cap (MemoryError under RLIMIT_AS)


def _child(mem_bytes: int, fn: Callable[..., Any], args: tuple, q) -> None:
    # Apply an address-space cap so an unbounded allocation raises MemoryError
    # (or is killed) instead of exhausting the host.
    try:
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    except (ValueError, OSError):
        # If we cannot set the cap, report so the caller does not misread the run.
        q.send(("nocap", None))
        return
    try:
        fn(*args)
        q.send((OK, None))
    except MemoryError:
        q.send((EXHAUSTED, "MemoryError"))
    except RecursionError as e:
        # A catchable fast failure. Treated as a rejection, not exhaustion.
        q.send((REJECTED, "RecursionError: %s" % str(e)[:512]))
    except Exception as e:  # noqa: BLE001 - any clean raise is a rejection
        q.send((REJECTED, "%s: %s" % (type(e).__name__[:128], str(e)[:512])))


def run_capped(
    fn: Callable[..., Any],
    *args: Any,
    mem_mb: int = 512,
    timeout_s: float = 5.0,
) -> tuple[str, str | None]:
    """Run fn(*args) in a memory-and-time-capped subprocess.

    Returns (outcome, detail) where outcome is one of:
      OK        - returned normally within caps
      REJECTED  - raised a clean exception fast (good for a bomb)
      EXHAUSTED - hit the memory cap (an unbounded allocation)
      "timeout" - exceeded the wall-clock timeout (an unbounded loop)
      "nocap"   - the memory cap could not be applied (inconclusive)
      "child-error" - abnormal exit or no result; cause unconfirmed
    """
    if type(mem_mb) is not int or mem_mb <= 0 or not math.isfinite(timeout_s) or timeout_s <= 0:
        raise ValueError("memory and time caps must be positive")
    ctx = mp.get_context("spawn")
    receiver, sender = ctx.Pipe(duplex=False)
    p = ctx.Process(target=_child, args=(mem_mb * 1024 * 1024, fn, args, sender))
    try:
        p.start()
        sender.close()
        p.join(timeout_s)
        if p.is_alive():
            p.kill()
            p.join()
            return ("timeout", "wall-clock limit exceeded")
        if p.exitcode != 0:
            return ("child-error", f"child exit code {p.exitcode}; cause unconfirmed")
        if receiver.poll():
            try:
                return receiver.recv()
            except EOFError:
                pass
        return ("child-error", "child exited without a result; cause unconfirmed")
    finally:
        sender.close()
        receiver.close()
        if p.pid is not None:
            if p.is_alive():
                p.kill()
                p.join()
            p.close()



def assert_guards_class(
    loader: Callable[[bytes], Any],
    bomb: bytes,
    benign: bytes,
    mem_mb: int = 512,
    timeout_s: float = 5.0,
    *,
    allow_bomb_ok: bool = False,
) -> list[str]:
    """Assert the loader guards the declared-huge class for one (bomb, benign) pair.

    A correctly-bounded loader REJECTS the bomb fast (REJECTED) and accepts the
    benign input (OK). Set allow_bomb_ok=True only for a loader whose documented
    contract safely ignores the hostile declaration. Returns failures. A rejected
    exception is only a resource outcome, not proof of semantically correct rejection.
    """
    failures: list[str] = []

    b_outcome, b_detail = run_capped(loader, bomb, mem_mb=mem_mb, timeout_s=timeout_s)
    allowed = (REJECTED, OK) if allow_bomb_ok else (REJECTED,)
    if b_outcome not in allowed:
        failures.append(f"bomb outcome={b_outcome} ({b_detail}); expected {allowed}")

    g_outcome, g_detail = run_capped(loader, benign, mem_mb=mem_mb, timeout_s=timeout_s)
    if g_outcome != OK:
        failures.append(
            "benign input did not pass: outcome=%s (%s)" % (g_outcome, g_detail)
        )

    return failures


# --------------------------------------------------------------------------
# Self-test: self-contained synthetic probes (no external model libraries).
# Proves the oracle actually distinguishes an unbounded loader from a bounded one.
# --------------------------------------------------------------------------

def _unbounded_alloc_loader(data: bytes) -> None:
    # Stand-in for the declared-huge class: read a declared count and allocate it
    # with NO bound. A tiny input declares a huge count.
    declared = int.from_bytes(data[:8], "little") if len(data) >= 8 else 0
    _ = bytearray(declared)  # unbounded: huge declared -> huge allocation


def _unbounded_loop_loader(data: bytes) -> None:
    # Stand-in for the declared-huge ITERATION class (like gguf-py 0008): loop a
    # declared count doing work, with no bound.
    declared = int.from_bytes(data[:8], "little") if len(data) >= 8 else 0
    for _ in range(declared):
        pass  # constant memory: tests time independently of allocation


def _bounded_loader(data: bytes) -> None:
    # A correctly-bounded loader: reject a declared count larger than the input.
    declared = int.from_bytes(data[:8], "little") if len(data) >= 8 else 0
    remaining = len(data) - 8
    if declared > remaining:
        raise ValueError("declared %d exceeds remaining %d bytes" % (declared, remaining))
    _ = bytearray(declared)


def _selftest() -> int:
    huge = (2 ** 40).to_bytes(8, "little")       # declares ~1TB / 1T iterations
    benign = (4).to_bytes(8, "little") + b"data"  # declares 4, has 4 bytes: valid

    failures: list[str] = []

    for loader, expected in ((_unbounded_alloc_loader, EXHAUSTED),
                             (_unbounded_loop_loader, "timeout")):
        actual, detail = run_capped(loader, huge, timeout_s=1.0)
        if actual != expected:
            failures.append(f"expected {expected}, got {actual}: {detail}")
        else:
            print(f"ok: independently detected {expected}")

    # 3. The oracle must PASS a correctly-bounded loader (no failures).
    f = assert_guards_class(_bounded_loader, huge, benign)
    if f:
        failures.append("oracle wrongly flagged the bounded loader: %s" % f)
    else:
        print("ok: bounded loader correctly passed (bomb rejected, benign ok)")

    if failures:
        print("\nRESOURCE ORACLE SELFTEST FAILED:")
        for x in failures:
            print("  -", x)
        return 1
    print("\nresource oracle selftest OK: flags unbounded alloc and loop; passes bounded")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="declared-huge resource-exhaustion oracle")
    ap.add_argument("--selftest", action="store_true", help="run the regression guard")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(_selftest())
    ap.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
