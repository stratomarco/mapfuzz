#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from video_qualification import generate_video_seed, qualify_video_seed


class VideoQualificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mapfuzz-lerobot-r8-")
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_valid_video_seed_reaches_consumer(self) -> None:
        dataset = self.root / "valid"
        generated = generate_video_seed(dataset)
        result = qualify_video_seed(dataset)
        self.assertEqual(generated["frames"], 1)
        self.assertEqual(result["result"], "qualified")
        self.assertEqual(result["last_milestone"], "dataloader_yielded")
        self.assertEqual(result["video"]["codec"], "h264")
        self.assertEqual(result["video"]["tensor_shape"], [3, 64, 96])
        self.assertLessEqual(result["video"]["max_pixel_error"], 0.08)
        self.assertLessEqual(result["video"]["mean_pixel_error"], 0.01)
        self.assertEqual(result["counts"]["dataloader_batches"], 1)
        self.assertTrue(result["cpu_only"])

    def test_missing_video_stops_after_metadata(self) -> None:
        dataset = self.root / "missing-video"
        generate_video_seed(dataset, "missing-video")
        result = qualify_video_seed(dataset)
        self.assertEqual(result["result"], "rejected")
        self.assertEqual(result["last_milestone"], "metadata_tables_loaded")
        self.assertEqual(result["exception_type"], "OfflineModeIsEnabled")
        self.assertEqual(result["counts"]["rows_materialized"], 0)

    def test_truncated_video_stops_after_row(self) -> None:
        dataset = self.root / "truncated-video"
        generate_video_seed(dataset, "truncated-video")
        result = qualify_video_seed(dataset)
        self.assertEqual(result["result"], "rejected")
        self.assertEqual(result["last_milestone"], "row_materialized")
        self.assertEqual(result["exception_type"], "InvalidDataError")
        self.assertEqual(result["counts"]["samples_decoded"], 0)

    def test_late_timestamp_stops_before_sample(self) -> None:
        dataset = self.root / "late-timestamp"
        generate_video_seed(dataset, "out-of-tolerance-timestamp")
        result = qualify_video_seed(dataset)
        self.assertEqual(result["result"], "rejected")
        self.assertEqual(result["last_milestone"], "video_validated")
        self.assertEqual(result["exception_type"], "FrameTimestampError")
        self.assertEqual(result["counts"]["tasks_resolved"], 0)
        self.assertEqual(result["counts"]["dataloader_batches"], 0)

    def test_memory_error_remains_visible(self) -> None:
        with patch("video_qualification.LeRobotDatasetMetadata", side_effect=MemoryError):
            with self.assertRaises(MemoryError):
                qualify_video_seed(self.root / "not-read")

    def test_orchestrator_timeout_is_not_success(self) -> None:
        environment = os.environ.copy()
        environment["CUDA_VISIBLE_DEVICES"] = ""
        environment["HF_HUB_OFFLINE"] = "1"
        runner = Path(__file__).with_name("run_video_controls.py")
        process = subprocess.run(
            [sys.executable, str(runner), str(self.root / "timeout"), "--replay-timeout", "0.001"],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
            env=environment,
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("valid replay exceeded 0.001s", process.stderr)


if __name__ == "__main__":
    unittest.main()
