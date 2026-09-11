#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from qualification import generate_seed, qualify_seed


class QualificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mapfuzz-lerobot-r7-")
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_valid_seed_reaches_consumer(self) -> None:
        dataset = self.root / "valid"
        generated = generate_seed(dataset)
        result = qualify_seed(dataset)
        self.assertEqual(generated["frames"], 1)
        self.assertEqual(result["result"], "qualified")
        self.assertEqual(result["last_milestone"], "dataloader_yielded")
        self.assertEqual(result["counts"]["rows_materialized"], 1)
        self.assertEqual(result["counts"]["dataloader_batches"], 1)
        self.assertTrue(result["cpu_only"])

    def test_malformed_metadata_stops_before_acceptance(self) -> None:
        dataset = self.root / "invalid-fps"
        generate_seed(dataset, "invalid-fps")
        result = qualify_seed(dataset)
        self.assertEqual(result["result"], "rejected")
        self.assertEqual(result["last_milestone"], "start")
        self.assertEqual(result["exception_type"], "ValueError")
        self.assertEqual(result["counts"]["datasets_accepted"], 0)

    def test_missing_data_stops_after_metadata(self) -> None:
        dataset = self.root / "missing-data"
        generate_seed(dataset, "missing-data")
        result = qualify_seed(dataset)
        self.assertEqual(result["result"], "rejected")
        self.assertEqual(result["last_milestone"], "metadata_tables_loaded")
        self.assertEqual(result["exception_type"], "OfflineModeIsEnabled")
        self.assertEqual(result["counts"]["rows_materialized"], 0)

    def test_truncated_data_stops_after_metadata(self) -> None:
        dataset = self.root / "truncated-data"
        generate_seed(dataset, "truncated-data")
        result = qualify_seed(dataset)
        self.assertEqual(result["result"], "rejected")
        self.assertEqual(result["last_milestone"], "metadata_tables_loaded")
        self.assertEqual(result["exception_type"], "ArrowInvalid")
        self.assertEqual(result["counts"]["rows_materialized"], 0)

    def test_invalid_task_index_stops_after_materialization(self) -> None:
        dataset = self.root / "invalid-task-index"
        generate_seed(dataset, "invalid-task-index")
        result = qualify_seed(dataset)
        self.assertEqual(result["result"], "rejected")
        self.assertEqual(result["last_milestone"], "row_materialized")
        self.assertEqual(result["exception_type"], "IndexError")
        self.assertEqual(result["counts"]["rows_materialized"], 1)
        self.assertEqual(result["counts"]["tasks_resolved"], 0)
        self.assertEqual(result["counts"]["dataloader_batches"], 0)

    def test_memory_error_remains_visible(self) -> None:
        with patch("qualification.LeRobotDatasetMetadata", side_effect=MemoryError):
            with self.assertRaises(MemoryError):
                qualify_seed(self.root / "not-read")

    def test_orchestrator_timeout_is_not_success(self) -> None:
        environment = os.environ.copy()
        environment["CUDA_VISIBLE_DEVICES"] = ""
        environment["HF_HUB_OFFLINE"] = "1"
        runner = Path(__file__).with_name("run_controls.py")
        process = subprocess.run(
            [sys.executable, str(runner), str(self.root / "timeout"), "--replay-timeout", "0.001"],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
            env=environment,
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("valid replay exceeded 0.001s", process.stderr)


if __name__ == "__main__":
    unittest.main()
