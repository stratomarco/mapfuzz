"""Run a bounded campaign and fail closed on execution or artifact failures.

Use a fresh output directory for every run. Logs/artifacts can be disclosure
sensitive: this runner does not print or upload their contents.
"""
import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys

def run(command, output, timeout_s):
    if not math.isfinite(timeout_s) or timeout_s <= 0:
        raise ValueError("timeout must be finite and positive")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    artifacts = output / "artifacts"
    artifacts.mkdir()
    command = [*command, f"-artifact_prefix={artifacts}/"]
    outcome = {"command": command, "exit_code": None, "timed_out": False}
    with (output / "run.log").open("wb") as log:
        try:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            try:
                outcome["exit_code"] = process.wait(timeout=timeout_s)
            except subprocess.TimeoutExpired:
                outcome["timed_out"] = True
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # exited between the timeout and the kill
                outcome["exit_code"] = process.wait()
        except OSError as e:
            outcome["error"] = str(e)
    # Any artifact is suspicious, including future/unknown artifact prefixes.
    outcome["artifacts"] = [p.name for p in sorted(artifacts.iterdir())]
    outcome["passed"] = (outcome["exit_code"] == 0 and not outcome["timed_out"]
                         and not outcome["artifacts"])
    # Diagnostic sanitizer reports must not disappear behind an exit-zero driver.
    markers = ("ERROR:", "SUMMARY:", "runtime error:", "Traceback (most recent",
               "panicked at", "GGML_ASSERT", "Sanitizer:", "DEADLYSIGNAL")
    with (output / "run.log").open(errors="replace") as log:
        tail = ""
        while chunk := log.read(65536):
            text = tail + chunk
            if any(marker in text for marker in markers):
                outcome["passed"] = False
                outcome["diagnostic_report"] = True
                break
            tail = text[-64:]
    (output / "result.json").write_text(json.dumps(outcome, indent=2) + "\n")
    print("campaign passed" if outcome["passed"] else "campaign failed; inspect local run.log and result.json")
    return 0 if outcome["passed"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("a command and positive timeout are required")
    try:
        return run(command, args.output, args.timeout)
    except OSError as e:
        print(f"campaign setup failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
