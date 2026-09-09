#!/usr/bin/env python3
import os
import sys
from pathlib import Path


EXPECTED_MEMORY_MAX = 4 * 1024 * 1024 * 1024


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: cgroup_exec.py COMMAND [ARG ...]")
    entry = Path("/proc/self/cgroup").read_text().strip()
    if "::" not in entry:
        raise SystemExit(f"unexpected cgroup v2 entry: {entry}")
    relative = entry.split("::", 1)[1].lstrip("/")
    cgroup = Path("/sys/fs/cgroup") / relative
    memory_max = (cgroup / "memory.max").read_text().strip()
    swap_max = (cgroup / "memory.swap.max").read_text().strip()
    cpu_affinity = sorted(os.sched_getaffinity(0))
    print(
        f"CGROUP_PROOF path={cgroup} memory.max={memory_max} "
        f"memory.swap.max={swap_max} cpu_affinity={cpu_affinity}",
        flush=True,
    )
    if (
        memory_max != str(EXPECTED_MEMORY_MAX)
        or swap_max != "0"
        or len(cpu_affinity) != 1
    ):
        raise SystemExit("required resource limits are not active")
    os.execvp(sys.argv[1], sys.argv[1:])


if __name__ == "__main__":
    main()
