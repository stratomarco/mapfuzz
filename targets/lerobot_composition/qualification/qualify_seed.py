#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from qualification import qualify_seed


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay a LeRobot v3 seed and report semantic milestones")
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args()
    result = qualify_seed(args.dataset)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "qualified" else 2


if __name__ == "__main__":
    raise SystemExit(main())
