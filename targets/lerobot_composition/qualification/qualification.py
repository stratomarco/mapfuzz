#!/usr/bin/env python3
"""Deterministic LeRobot v3 seed generation and semantic qualification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import torch
from lerobot.datasets.dataset_metadata import LeRobotDatasetMetadata
from lerobot.datasets.lerobot_dataset import LeRobotDataset

REPO_ID = "mapfuzz/lerobot-r7-seed"
TASK = "move test object"
FPS = 10
FEATURES = {
    "observation.state": {"dtype": "float32", "shape": (2,), "names": None},
    "action": {"dtype": "float32", "shape": (2,), "names": None},
}
STATE = torch.tensor([1.0, 2.0], dtype=torch.float32)
ACTION = torch.tensor([0.25, -0.25], dtype=torch.float32)


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


def data_file(root: Path) -> Path:
    paths = sorted((root / "data").rglob("*.parquet"))
    _require(len(paths) == 1, f"expected one data shard, found {len(paths)}")
    return paths[0]


def generate_seed(root: Path, mode: str = "valid") -> dict[str, Any]:
    if root.exists():
        raise FileExistsError(f"refusing to reuse output root: {root}")

    dataset = LeRobotDataset.create(
        repo_id=REPO_ID,
        fps=FPS,
        features=FEATURES,
        root=root,
        use_videos=False,
        video_backend="pyav",
        image_writer_processes=0,
        image_writer_threads=0,
    )
    dataset.add_frame(
        {
            "observation.state": STATE.clone(),
            "action": ACTION.clone(),
            "task": TASK,
        }
    )
    dataset.save_episode(parallel_encoding=False)
    dataset.finalize()

    shard = data_file(root)
    if mode == "invalid-fps":
        info_path = root / "meta" / "info.json"
        info = json.loads(info_path.read_text(encoding="utf-8"))
        info["fps"] = 0
        info_path.write_text(json.dumps(info, indent=4) + "\n", encoding="utf-8")
    elif mode == "missing-data":
        shard.unlink()
    elif mode == "truncated-data":
        with shard.open("r+b") as stream:
            stream.truncate(32)
    elif mode == "invalid-task-index":
        table = pq.read_table(shard)
        field_index = table.schema.get_field_index("task_index")
        _require(field_index >= 0, "generated data lacks task_index")
        replacement = pa.array([1], type=table.schema.field(field_index).type)
        table = table.set_column(field_index, "task_index", replacement)
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
        "files": file_inventory(root),
    }


def qualify_seed(root: Path) -> dict[str, Any]:
    milestones: list[str] = []
    stage = "start"
    try:
        metadata = LeRobotDatasetMetadata(
            repo_id=REPO_ID,
            root=root,
            token=False,
        )
        _require(metadata.fps == FPS, f"unexpected fps: {metadata.fps}")
        _require(metadata.video_keys == [], f"unexpected video keys: {metadata.video_keys}")
        for key, expected in FEATURES.items():
            actual = metadata.features[key]
            _require(actual["dtype"] == expected["dtype"], f"{key} dtype mismatch")
            _require(tuple(actual["shape"]) == expected["shape"], f"{key} shape mismatch")
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
        stage = "data_shard_loaded"
        milestones.append(stage)

        row = hf_dataset[0]
        _require(isinstance(row["observation.state"], torch.Tensor), "state was not tensorized")
        _require(isinstance(row["action"], torch.Tensor), "action was not tensorized")
        _require(torch.equal(row["observation.state"], STATE), "state value mismatch")
        _require(torch.equal(row["action"], ACTION), "action value mismatch")
        _require(row["index"].item() == 0, "absolute index mismatch")
        _require(row["episode_index"].item() == 0, "episode index mismatch")
        _require(row["frame_index"].item() == 0, "frame index mismatch")
        stage = "row_materialized"
        milestones.append(stage)

        item = dataset[0]
        _require(item["task"] == TASK, f"task resolution mismatch: {item['task']!r}")
        stage = "task_resolved"
        milestones.append(stage)

        loader = torch.utils.data.DataLoader(dataset, batch_size=1, num_workers=1)
        batch = next(iter(loader))
        _require(batch["task"] == [TASK], "DataLoader task mismatch")
        _require(torch.equal(batch["observation.state"], STATE.unsqueeze(0)), "DataLoader state mismatch")
        _require(torch.equal(batch["action"], ACTION.unsqueeze(0)), "DataLoader action mismatch")
        stage = "dataloader_yielded"
        milestones.append(stage)

        return {
            "result": "qualified",
            "last_milestone": stage,
            "milestones": milestones,
            "counts": {
                "datasets_attempted": 1,
                "datasets_accepted": 1,
                "episodes": 1,
                "parquet_rows": 1,
                "rows_materialized": 1,
                "tasks_resolved": 1,
                "dataloader_batches": 1,
            },
            "cpu_only": not torch.cuda.is_available(),
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
            "exception_message": str(error),
            "counts": {
                "datasets_attempted": 1,
                "datasets_accepted": int(stage != "start"),
                "rows_materialized": int(stage in {"row_materialized", "task_resolved", "dataloader_yielded"}),
                "tasks_resolved": int(stage in {"task_resolved", "dataloader_yielded"}),
                "dataloader_batches": int(stage == "dataloader_yielded"),
            },
        }
