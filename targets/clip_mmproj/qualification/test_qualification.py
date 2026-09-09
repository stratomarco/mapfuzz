import hashlib
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


EXPECTED_SEED_SHA256 = "858b1e02a7a0eb809cafd6f39f441044a89cb0fbda59c7d575dbf157e3b74106"
ASAN_WRAPPER = ["setarch", "x86_64", "-R"]


class QualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configured = os.environ.get("CLIP_MM_PROJ_BUILD_DIR")
        if not configured:
            raise unittest.SkipTest("set CLIP_MM_PROJ_BUILD_DIR to a completed pinned build")
        cls.build_dir = Path(configured).resolve()
        cls.seed = cls.build_dir / "clip-mmproj-seed"
        cls.qualify = cls.build_dir / "clip-mmproj-qualify"
        cls.fuzzer = cls.build_dir / "fuzz-clip-materialize"
        for binary in (cls.seed, cls.qualify, cls.fuzzer):
            if not binary.is_file():
                raise RuntimeError(f"missing qualification binary: {binary}")

    def run_command(self, command, timeout=15, env=None):
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        return subprocess.run(
            [str(part) for part in command],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=merged_env,
            check=False,
        )

    def run_asan_binary(self, binary, *arguments, timeout=15, env=None):
        return self.run_command(
            [*ASAN_WRAPPER, binary, *arguments],
            timeout=timeout,
            env=env,
        )

    def test_seed_and_semantic_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            inputs = {}
            for mode in ("benign", "malformed", "missing", "missing-projector", "yi"):
                model = tmp_path / f"{mode}.gguf"
                generated = self.run_asan_binary(self.seed, model, mode)
                self.assertEqual(generated.returncode, 0, generated.stderr)
                inputs[mode] = model

            digest = hashlib.sha256(inputs["benign"].read_bytes()).hexdigest()
            self.assertEqual(digest, EXPECTED_SEED_SHA256)

            for replay in range(3):
                result = self.run_asan_binary(
                    self.qualify,
                    inputs["benign"],
                    env={"LLVM_PROFILE_FILE": str(tmp_path / f"benign-{replay}-%p.profraw")},
                )
                combined = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, combined)
                self.assertIn("MILESTONE metadata_accepted", combined)
                self.assertIn("MILESTONE descriptors_accepted count=12", combined)
                self.assertIn("MILESTONE tensor_read_events count=12", combined)
                self.assertIn(
                    "MILESTONE consumer_constructed modality=vision output_embedding=4",
                    combined,
                )

            for mode, count in (("malformed", 12), ("missing", 11), ("missing-projector", 11)):
                result = self.run_asan_binary(self.qualify, inputs[mode])
                combined = result.stdout + result.stderr
                self.assertEqual(result.returncode, 4, combined)
                self.assertIn(f"MILESTONE descriptors_accepted count={count}", combined)
                self.assertIn("MILESTONE tensor_read_events count=0", combined)
                self.assertIn("MILESTONE consumer_rejected", combined)
                if mode == "missing-projector":
                    self.assertIn(
                        "incomplete MLP projector: missing tensor mm.2.weight",
                        combined,
                    )

            yi = self.run_asan_binary(self.qualify, inputs["yi"])
            yi_combined = yi.stdout + yi.stderr
            self.assertEqual(yi.returncode, 0, yi_combined)
            self.assertIn("MILESTONE descriptors_accepted count=16", yi_combined)
            self.assertIn("MILESTONE tensor_read_events count=16", yi_combined)
            self.assertIn(
                "MILESTONE consumer_constructed modality=vision output_embedding=4",
                yi_combined,
            )

    def test_fuzzer_seed_replay_and_tempfile_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            corpus = tmp_path / "corpus"
            corpus.mkdir()
            seed = corpus / "benign.gguf"
            generated = self.run_asan_binary(self.seed, seed, "benign")
            self.assertEqual(generated.returncode, 0, generated.stderr)

            before = set(Path("/tmp").glob("mapfuzz_clip_*"))
            result = self.run_asan_binary(
                self.fuzzer,
                "-runs=1",
                corpus,
                env={"LLVM_PROFILE_FILE": str(tmp_path / "fuzzer-%p.profraw")},
            )
            after = set(Path("/tmp").glob("mapfuzz_clip_*"))
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, combined)
            self.assertEqual(after, before)
            metrics = re.search(
                r"MAPFUZZ_METRICS attempted=(\d+) accepted=(\d+) materialized=(\d+)",
                combined,
            )
            self.assertIsNotNone(metrics, combined)
            self.assertGreaterEqual(int(metrics.group(1)), 1)
            self.assertGreaterEqual(int(metrics.group(2)), 1)
            self.assertGreaterEqual(int(metrics.group(3)), 1)


if __name__ == "__main__":
    unittest.main()
