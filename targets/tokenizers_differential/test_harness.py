"""Run with the qualified differential environment; uses the actual harness."""
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch

path = Path(__file__).parent / "harness/fuzz_fast_slow_divergence.py"
spec = importlib.util.spec_from_file_location("differential", path)
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)


class HarnessTests(unittest.TestCase):
    def test_actual_baseline(self):
        self.assertEqual(harness._selftest(), 0)

    def test_probe_divergence_fails(self):
        with patch.object(harness, "_encode_both", return_value=([1], [2])), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(harness._selftest(), 1)

    def test_exception_types_remain_distinct(self):
        with patch.object(harness._SLOW, "encode", side_effect=ValueError), patch.object(harness._FAST, "encode", side_effect=TypeError):
            slow, fast = harness._encode_both("test")
            self.assertNotEqual(slow, fast)
            with self.assertRaises(AssertionError):
                harness.TestOneInput(b"test")

    def test_both_rejecting_baseline_is_not_success(self):
        with patch.object(harness._SLOW, "encode", side_effect=ValueError), patch.object(harness._FAST, "encode", side_effect=ValueError), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(harness._selftest(), 1)

    def test_invalid_utf8_and_empty_input_reach_pair(self):
        with patch.object(harness, "_encode_both", return_value=([1], [1])) as encode:
            harness.TestOneInput(b"\xff")
            self.assertEqual(encode.call_args.args[0], "\xff")
            harness.TestOneInput(b"")
            self.assertEqual(encode.call_args.args[0], "")


if __name__ == "__main__":
    unittest.main()
