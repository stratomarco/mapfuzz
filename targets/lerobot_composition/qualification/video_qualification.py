#!/usr/bin/env python3
"""Deterministic LeRobot v3 video-seed generation and semantic replay."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import av
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import torch
from lerobot.configs.video import RGBEncoderConfig
from lerobot.datasets.dataset_metadata import LeRobotDatasetMetadata
from lerobot.datasets.lerobot_dataset import LeRobotDataset

REPO_ID = "mapfuzz/lerobot-r8-video-seed"
TASK = "move test object"
VIDEO_KEY = "observation.images.cam"
FPS = 10
HEIGHT = 64
WIDTH = 96
ACTION = torch.tensor([0.25, -0.25], dtype=torch.float32)
MAX_PIXEL_ERROR = 0.08
MEAN_PIXEL_ERROR = 0.01
FEATURES = {
    VIDEO_KEY: {
        "dtype": "video",
        "shape": (HEIGHT, WIDTH, 3),
        "names": ["height", "width", "channels"],
    },
    "action": {"dtype": "float32", "shape": (2,), "names": None},
}


class QualificationError(RuntimeError):
    """A semantic assertion failed without hiding its stage."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise QualificationError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_inventory(root: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]


def expected_frame() -> np.ndarray:
    """Return a fixed four-quadrant uint8 HWC RGB frame."""
    frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    frame[: HEIGHT // 2, : WIDTH // 2] = [32, 64, 96]
    frame[: HEIGHT // 2, WIDTH // 2 :] = [192, 64, 32]
    frame[HEIGHT // 2 :, : WIDTH // 2] = [32, 192, 64]
    frame[HEIGHT // 2 :, WIDTH // 2 :] = [160, 160, 224]
    return frame


def data_file(root: Path) -> Path:
    paths = sorted((root / "data").rglob("*.parquet"))
    _require(len(paths) == 1, f"expected one data shard, found {len(paths)}")
    return paths[0]


def video_file(root: Path) -> Path:
    paths = sorted((root / "videos").rglob("*.mp4"))
    _require(len(paths) == 1, f"expected one video file, found {len(paths)}")
    return paths[0]


def generate_video_seed(root: Path, mode: str = "valid") -> dict[str, Any]:
    if root.exists():
        raise FileExistsError(f"refusing to reuse output root: {root}")

    encoder = RGBEncoderConfig(
        vcodec="h264",
        pix_fmt="yuv420p",
        g=1,
        crf=18,
        preset="medium",
        fast_decode=0,
        video_backend="pyav",
    )
    dataset = LeRobotDataset.create(
        repo_id=REPO_ID,
        fps=FPS,
        features=FEATURES,
        root=root,
        use_videos=True,
        video_backend="pyav",
        image_writer_processes=0,
        image_writer_threads=0,
        rgb_encoder=encoder,
        streaming_encoding=False,
        encoder_threads=1,
    )
    dataset.add_frame(
        {
            VIDEO_KEY: expected_frame(),
            "action": ACTION.clone(),
            "task": TASK,
        }
    )
    dataset.save_episode(parallel_encoding=False)
    dataset.finalize()

    video = video_file(root)
    shard = data_file(root)
    if mode == "missing-video":
        video.unlink()
    elif mode == "truncated-video":
        with video.open("r+b") as stream:
            stream.truncate(32)
    elif mode == "out-of-tolerance-timestamp":
        table = pq.read_table(shard)
        field_index = table.schema.get_field_index("timestamp")
        _require(field_index >= 0, "generated data lacks timestamp")
        replacement = pa.array([1.0], type=table.schema.field(field_index).type)
        table = table.set_column(field_index, "timestamp", replacement)
        pq.write_table(table, shard)
    elif mode != "valid":
        raise ValueError(f"unsupported mode: {mode}")

    return {
        "result": "generated",
        "mode": mode,
        "root": str(root.resolve()),
        "repo_id": REPO_ID,
        "fps": FPS,
        "episodes": 1,
        "frames": 1,
        "task": TASK,
        "features": {
            key: {"dtype": value["dtype"], "shape": list(value["shape"])}
            for key, value in FEATURES.items()
        },
        "encoder": {
            "backend": "pyav",
            "codec": "h264",
            "encoder": "libx264",
            "pixel_format": "yuv420p",
            "gop": 1,
            "crf": 18,
            "preset": "medium",
            "threads": 1,
        },
        "files": file_inventory(root),
    }


def _counts(stage: str) -> dict[str, int]:
    ordered = [
        "metadata_accepted",
        "metadata_tables_loaded",
        "row_materialized",
        "video_validated",
        "sample_decoded",
        "dataloader_yielded",
    ]
    stage_index = ordered.index(stage) if stage in ordered else -1
    reached = {name: int(index <= stage_index) for index, name in enumerate(ordered)}
    return {
        "datasets_attempted": 1,
        "datasets_accepted": reached["metadata_accepted"],
        "metadata_rows": reached["metadata_tables_loaded"] * 2,
        "parquet_rows": reached["row_materialized"],
        "rows_materialized": reached["row_materialized"],
        "videos_validated": reached["video_validated"],
        "samples_decoded": reached["sample_decoded"],
        "tasks_resolved": reached["sample_decoded"],
        "dataloader_batches": reached["dataloader_yielded"],
    }


def qualify_video_seed(root: Path) -> dict[str, Any]:
    milestones: list[str] = []
    stage = "start"
    try:
        metadata = LeRobotDatasetMetadata(repo_id=REPO_ID, root=root, token=False)
        _require(metadata.fps == FPS, f"unexpected fps: {metadata.fps}")
        _require(metadata.video_keys == [VIDEO_KEY], f"unexpected video keys: {metadata.video_keys}")
        for key, expected in FEATURES.items():
            actual = metadata.features[key]
            _require(actual["dtype"] == expected["dtype"], f"{key} dtype mismatch")
            _require(tuple(actual["shape"]) == expected["shape"], f"{key} shape mismatch")
        video_info = metadata.features[VIDEO_KEY]["info"]
        _require(video_info["video.codec"] == "h264", "metadata codec mismatch")
        _require(video_info["video.pix_fmt"] == "yuv420p", "metadata pixel format mismatch")
        _require(video_info["video.fps"] == FPS, "metadata video fps mismatch")
        stage = "metadata_accepted"
        milestones.append(stage)

        _require(metadata.total_frames == 1, "expected one metadata frame")
        _require(metadata.total_episodes == 1, "expected one metadata episode")
        _require(len(metadata.tasks) == 1, "expected one task metadata row")
        _require(len(metadata.episodes) == 1, "expected one episode metadata row")
        stage = "metadata_tables_loaded"
        milestones.append(stage)

        dataset = LeRobotDataset(
            repo_id=REPO_ID,
            root=root,
            download_videos=False,
            video_backend="pyav",
            token=False,
        )
        hf_dataset = dataset.hf_dataset
        _require(len(hf_dataset) == 1, "expected one Parquet row")
        row = hf_dataset[0]
        _require(isinstance(row["action"], torch.Tensor), "action was not tensorized")
        _require(torch.equal(row["action"], ACTION), "action value mismatch")
        _require(row["index"].item() == 0, "absolute index mismatch")
        _require(row["episode_index"].item() == 0, "episode index mismatch")
        _require(row["frame_index"].item() == 0, "frame index mismatch")
        stage = "row_materialized"
        milestones.append(stage)

        relative_video = metadata.get_video_file_path(0, VIDEO_KEY)
        resolved_video = root / relative_video
        _require(resolved_video.is_file(), f"resolved video is not a file: {resolved_video}")
        with av.open(str(resolved_video)) as container:
            stream = container.streams.video[0]
            _require(stream.codec_context.name == "h264", "stream codec mismatch")
            _require(stream.codec_context.width == WIDTH, "stream width mismatch")
            _require(stream.codec_context.height == HEIGHT, "stream height mismatch")
            _require(float(stream.average_rate) == FPS, "stream fps mismatch")
            decoded_frames = sum(1 for _ in container.decode(stream))
        _require(decoded_frames == 1, f"expected one encoded frame, got {decoded_frames}")
        stage = "video_validated"
        milestones.append(stage)

        item = dataset[0]
        actual = item[VIDEO_KEY]
        expected = torch.from_numpy(expected_frame()).permute(2, 0, 1).float() / 255.0
        _require(actual.dtype == torch.float32, f"decoded dtype mismatch: {actual.dtype}")
        _require(tuple(actual.shape) == (3, HEIGHT, WIDTH), f"decoded shape mismatch: {tuple(actual.shape)}")
        max_error = float((actual - expected).abs().max())
        mean_error = float((actual - expected).abs().mean())
        _require(max_error <= MAX_PIXEL_ERROR, f"maximum lossy error {max_error} exceeds {MAX_PIXEL_ERROR}")
        _require(mean_error <= MEAN_PIXEL_ERROR, f"mean lossy error {mean_error} exceeds {MEAN_PIXEL_ERROR}")
        _require(item["task"] == TASK, f"task resolution mismatch: {item['task']!r}")
        _require(torch.equal(item["action"], ACTION), "decoded item action mismatch")
        stage = "sample_decoded"
        milestones.append(stage)

        loader = torch.utils.data.DataLoader(dataset, batch_size=1, num_workers=1)
        batch = next(iter(loader))
        _require(batch["task"] == [TASK], "DataLoader task mismatch")
        _require(torch.equal(batch["action"], ACTION.unsqueeze(0)), "DataLoader action mismatch")
        _require(torch.equal(batch[VIDEO_KEY], actual.unsqueeze(0)), "DataLoader video mismatch")
        stage = "dataloader_yielded"
        milestones.append(stage)

        return {
            "result": "qualified",
            "last_milestone": stage,
            "milestones": milestones,
            "counts": _counts(stage),
            "cpu_only": not torch.cuda.is_available(),
            "video": {
                "path": relative_video.as_posix(),
                "sha256": _sha256(resolved_video),
                "codec": "h264",
                "width": WIDTH,
                "height": HEIGHT,
                "fps": FPS,
                "decoded_frames": decoded_frames,
                "tensor_dtype": str(actual.dtype),
                "tensor_shape": list(actual.shape),
                "max_pixel_error": max_error,
                "mean_pixel_error": mean_error,
                "max_pixel_error_limit": MAX_PIXEL_ERROR,
                "mean_pixel_error_limit": MEAN_PIXEL_ERROR,
            },
            "files": file_inventory(root),
        }
    except MemoryError:
        raise
    except Exception as error:
        return {
            "result": "rejected",
            "last_milestone": stage,
            "milestones": milestones,
            "exception_type": type(error).__name__,
            "exception_module": type(error).__module__,
            "exception_message": str(error),
            "counts": _counts(stage),
        }
