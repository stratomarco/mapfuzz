"""Validate the target qualification portfolio manifest.

This checks structure and local evidence references. It does not establish that
an M0 observation is current, that a semantic claim is true, or that compute is
safe to start.
"""

from datetime import date
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "targets" / "qualification.yaml"

LIFECYCLES = {
    "regression-maintenance",
    "m0-candidate",
    "paused",
    "archived",
    "retired",
    "qualified-parked",
}
COMPUTE_DECISIONS = {"none", "m0-only", "regression-only", "parked"}
EXPECTED_DECISION = {
    "regression-maintenance": "regression-only",
    "m0-candidate": "m0-only",
    "paused": "none",
    "archived": "none",
    "retired": "none",
    "qualified-parked": "parked",
}
CAP_CEILINGS = {
    "cpu_workers": 1,
    "memory_bytes": 4294967296,
    "input_timeout_seconds": 5,
    "campaign_seconds": 60,
    "outer_timeout_seconds": 90,
}
CONTRACT_LISTS = {
    "semantic_counters": [
        "attempted inputs",
        "accepted inputs",
        "inputs reaching the named consumer milestone",
        "new named states or functions",
    ],
    "negative_controls": [
        "malformed input rejected before the consumer milestone",
        "missing or truncated payload distinguished from metadata success",
        "timeout, abnormal exit, sanitizer fault, and resource failure remain visible",
    ],
    "stop_rules": [
        "stop at M0 when no useful uncovered consumer boundary is demonstrated",
        "stop on the first new fault and retain the reproducer only in ignored local storage",
        "stop after three equal bounded batches with no new named state or function",
        "never extend compute based only on execution count or aggregate coverage",
    ],
}


class UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that rejects duplicate mapping keys."""


def _mapping(loader: UniqueKeyLoader, node: yaml.Node, deep: bool = False) -> dict:
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping
)


def _require_text(record: dict[str, Any], field: str, target_id: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{target_id}: {field} must be non-empty text")
    return value


def _validate_date(value: str, target_id: str) -> None:
    if value == "not-current":
        return
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(
            f"{target_id}: last_m0 must be YYYY-MM-DD or not-current"
        ) from error
    if parsed > date.today():
        raise ValueError(f"{target_id}: last_m0 cannot be in the future")


def _validate_evidence(paths: Any, target_id: str, root: Path) -> None:
    if not isinstance(paths, list) or not paths:
        raise ValueError(f"{target_id}: evidence must be a non-empty list")
    resolved_root = root.resolve()
    for relative in paths:
        if not isinstance(relative, str) or not relative:
            raise ValueError(f"{target_id}: evidence entries must be paths")
        relative_path = Path(relative)
        if (
            relative_path.is_absolute()
            or "\\" in relative
            or any(part in {"", ".", ".."} for part in relative_path.parts)
            or relative_path.as_posix() != relative
        ):
            raise ValueError(
                f"{target_id}: evidence path must be canonical and repository-relative: "
                f"{relative}"
            )
        candidate = (root / relative_path).resolve()
        if resolved_root not in candidate.parents:
            raise ValueError(f"{target_id}: evidence path escapes repository: {relative}")
        if not candidate.is_file():
            raise ValueError(f"{target_id}: missing evidence path: {relative}")


def validate_manifest(path: Path = MANIFEST, root: Path = ROOT) -> dict[str, Any]:
    document = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    if not isinstance(document, dict):
        raise ValueError("qualification manifest must be a mapping")
    if document.get("schema_version") != 1:
        raise ValueError("qualification manifest schema_version must be 1")

    contract = document.get("qualification_contract")
    if not isinstance(contract, dict):
        raise ValueError("qualification_contract must be a mapping")
    caps = contract.get("caps")
    if not isinstance(caps, dict):
        raise ValueError("qualification_contract.caps must be a mapping")
    for field, ceiling in CAP_CEILINGS.items():
        value = caps.get(field)
        if type(value) is not int or not 0 < value <= ceiling:
            raise ValueError(
                f"qualification_contract.caps.{field} must be an integer from "
                f"1 through {ceiling}"
            )
    if type(caps.get("swap_bytes")) is not int or caps["swap_bytes"] != 0:
        raise ValueError("qualification_contract.caps.swap_bytes must be integer zero")
    if caps["outer_timeout_seconds"] < caps["campaign_seconds"]:
        raise ValueError("outer timeout must not be shorter than campaign duration")
    for field, required in CONTRACT_LISTS.items():
        values = contract.get(field)
        if values != required:
            raise ValueError(f"qualification_contract.{field} must match the reviewed contract")

    records = document.get("targets")
    if not isinstance(records, list) or not records:
        raise ValueError("targets must be a non-empty list")
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("each target must be a mapping")
        target_id = _require_text(record, "id", "target")
        if target_id in seen:
            raise ValueError(f"duplicate target id: {target_id}")
        seen.add(target_id)
        if not (root / "targets" / target_id).is_dir():
            raise ValueError(f"unknown target directory: {target_id}")

        lifecycle = _require_text(record, "lifecycle", target_id)
        decision = _require_text(record, "compute_decision", target_id)
        if lifecycle not in LIFECYCLES:
            raise ValueError(f"{target_id}: invalid lifecycle: {lifecycle}")
        if decision not in COMPUTE_DECISIONS:
            raise ValueError(f"{target_id}: invalid compute_decision: {decision}")
        if decision != EXPECTED_DECISION[lifecycle]:
            raise ValueError(
                f"{target_id}: {lifecycle} requires compute_decision "
                f"{EXPECTED_DECISION[lifecycle]}"
            )
        last_m0 = _require_text(record, "last_m0", target_id)
        _validate_date(last_m0, target_id)
        for field in (
            "consumer",
            "trust_boundary",
            "semantic_milestone",
            "next_gate",
        ):
            _require_text(record, field, target_id)
        controls = record.get("controls")
        if not isinstance(controls, list) or not all(
            isinstance(control, str) and control.strip() for control in controls
        ):
            raise ValueError(f"{target_id}: controls must be a text list")
        _validate_evidence(record.get("evidence"), target_id, root)

    target_dirs = {path.name for path in (root / "targets").iterdir() if path.is_dir()}
    if seen != target_dirs:
        missing = sorted(target_dirs - seen)
        extra = sorted(seen - target_dirs)
        raise ValueError(f"target inventory mismatch: missing={missing}, extra={extra}")
    return document


def main() -> None:
    document = validate_manifest()
    print(f"qualification manifest valid: {len(document['targets'])} targets")


if __name__ == "__main__":
    main()
