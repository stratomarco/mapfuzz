#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from qualification import generate_seed


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one deterministic no-video LeRobot v3 seed")
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--mode",
        choices=("valid", "invalid-fps", "missing-data", "truncated-data", "invalid-task-index"),
        default="valid",
    )
    args = parser.parse_args()
    print(json.dumps(generate_seed(args.output, args.mode), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
