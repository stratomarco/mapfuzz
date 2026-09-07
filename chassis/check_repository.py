"""Cheap repository checks; no claim of target build or finding reproduction."""
import ast
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    # Include new source files in a developer worktree, excluding dependencies.
    new = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    count = 0
    for name in sorted(set(tracked + new) - {""}):
        path = ROOT / name
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=name)
            count += 1
        elif path.suffix == ".sh":
            subprocess.run(["bash", "-n", str(path)], check=True)
    targets = {p.name for p in (ROOT / "targets").iterdir() if p.is_dir()}
    inventory = (ROOT / "docs/TARGETS.md").read_text(encoding="utf-8-sig")
    for target in targets:
        assert f"| {target} |" in inventory, f"missing target inventory: {target}"
        assert (ROOT / "targets" / target / "README.md").is_file(), target
    print(f"syntax checked for {count} Python files and tracked shell scripts; {len(targets)} targets inventoried")


if __name__ == "__main__":
    main()
