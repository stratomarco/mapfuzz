#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from video_qualification import generate_video_seed


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one deterministic video-bearing LeRobot v3 seed")
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--mode",
        choices=("valid", "missing-video", "truncated-video", "out-of-tolerance-timestamp"),
        default="valid",
    )
    args = parser.parse_args()
    print(json.dumps(generate_video_seed(args.output, args.mode), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
