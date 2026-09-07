import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from chassis.campaign import run


class GateTests(unittest.TestCase):
    def test_execution_and_artifacts(self):
        scripts = [("pass", 0), ("raise SystemExit(7)", 1),
                   ("print('SUMMARY: NewSanitizer: unknown fault')", 1),
                   ("import time; time.sleep(10)", 1)]
        for prefix in ("crash-", "timeout-", "oom-", "leak-", "future-"):
            scripts.append(("import pathlib,sys; "
                            "p=sys.argv[-1].split('=',1)[1]; "
                            f"pathlib.Path(p, '{prefix}fixture').write_text('fixture')", 1))
        with tempfile.TemporaryDirectory() as tmp:
            for i, (script, expected) in enumerate(scripts):
                with self.subTest(script=script):
                    self.assertEqual(run([sys.executable, "-c", script], Path(tmp)/str(i), .5), expected)
            self.assertEqual(run(["/does/not/exist"], Path(tmp)/"missing", .5), 1)

    def test_triage_exit_policy(self):
        fixtures = Path(__file__).parent / "fixtures"
        with tempfile.TemporaryDirectory() as tmp:
            unknown = Path(tmp) / "unknown.txt"
            unknown.write_text("unknown sanitizer format")
            for path in [*fixtures.glob("*.txt"), unknown, Path(tmp)/"missing"]:
                result = subprocess.run([sys.executable, "-m", "chassis.triage", str(path)], capture_output=True)
                self.assertEqual(result.returncode, 1, str(path))
            unknown.unlink()
            result = subprocess.run([sys.executable, "-m", "chassis.triage", tmp], capture_output=True)
            self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
