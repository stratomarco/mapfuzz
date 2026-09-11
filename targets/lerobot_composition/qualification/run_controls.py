#!/usr/bin/env python3
"""Generate fresh cases and enforce a deadline around each semantic replay."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from qualification import generate_seed

CASES = {
    "valid": (0, "dataloader_yielded", None),
    "invalid-fps": (2, "start", "ValueError"),
    "missing-data": (2, "metadata_tables_loaded", "OfflineModeIsEnabled"),
    "truncated-data": (2, "metadata_tables_loaded", "ArrowInvalid"),
    "invalid-task-index": (2, "row_materialized", "IndexError"),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the complete bounded LeRobot R7 control suite")
    parser.add_argument("output", type=Path)
    parser.add_argument("--replay-timeout", type=float, default=60.0)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to reuse output root: {args.output}")
    args.output.mkdir(parents=True)

    environment = os.environ.copy()
    environment["CUDA_VISIBLE_DEVICES"] = ""
    environment["HF_HUB_OFFLINE"] = "1"
    probe = Path(__file__).with_name("qualify_seed.py")
    suite_started = time.monotonic()
    results = []

    for mode, (expected_exit, expected_stage, expected_exception) in CASES.items():
        root = args.output / mode
        generation = generate_seed(root, mode)
        started = time.monotonic()
        try:
            process = subprocess.run(
                [sys.executable, str(probe), str(root)],
                check=False,
                capture_output=True,
                text=True,
                timeout=args.replay_timeout,
                env=environment,
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(f"{mode} replay exceeded {args.replay_timeout}s") from error
        elapsed = time.monotonic() - started
        if process.returncode < 0:
            raise RuntimeError(f"{mode} terminated by signal {-process.returncode}")
        if process.returncode != expected_exit:
            raise RuntimeError(
                f"{mode} exit {process.returncode}, expected {expected_exit}; stderr={process.stderr!r}"
            )
        lines = [line for line in process.stdout.splitlines() if line.strip()]
        if len(lines) != 1:
            raise RuntimeError(f"{mode} emitted {len(lines)} JSON lines; stderr={process.stderr!r}")
        replay = json.loads(lines[0])
        if replay["last_milestone"] != expected_stage:
            raise RuntimeError(
                f"{mode} stopped at {replay['last_milestone']}, expected {expected_stage}: {replay}"
            )
        if replay.get("exception_type") != expected_exception:
            raise RuntimeError(
                f"{mode} raised {replay.get('exception_type')}, expected {expected_exception}: {replay}"
            )
        results.append(
            {
                "mode": mode,
                "generation": generation,
                "replay": replay,
                "exit_code": process.returncode,
                "elapsed_seconds": round(elapsed, 6),
                "stderr": process.stderr,
            }
        )

    report = {
        "result": "qualified",
        "suite_elapsed_seconds": round(time.monotonic() - suite_started, 6),
        "replay_timeout_seconds": args.replay_timeout,
        "cases": results,
    }
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
