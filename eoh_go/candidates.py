from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import EOHGoPaths, ensure_workspace
from .store import read_json, write_json


def _candidate_file_name(candidate_id: str) -> str:
    return f"{candidate_id}.json"


def add_candidate(
    paths: EOHGoPaths,
    candidate_id: str,
    algorithm: str,
    target_file: str,
    code: str,
    rationale: str = "",
    metadata: dict[str, Any] | None = None,
) -> Path:
    ensure_workspace(paths)
    payload = {
        "candidate_id": candidate_id,
        "algorithm": algorithm,
        "target_file": target_file,
        "code": code,
        "rationale": rationale,
        "metadata": metadata or {},
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    candidate_path = paths.candidates_dir / _candidate_file_name(candidate_id)
    write_json(candidate_path, payload)

    registry = read_json(paths.registry_path, [])
    if not isinstance(registry, list):
        registry = []
    registry = [item for item in registry if item.get("candidate_id") != candidate_id]
    registry.append(
        {
            "candidate_id": candidate_id,
            "algorithm": algorithm,
            "target_file": target_file,
            "candidate_path": str(candidate_path),
            "created_at": payload["created_at"],
            "metadata": payload["metadata"],
        }
    )
    write_json(paths.registry_path, registry)
    return candidate_path


def list_candidates(paths: EOHGoPaths) -> list[dict[str, Any]]:
    data = read_json(paths.registry_path, [])
    return data if isinstance(data, list) else []


def load_candidate(paths: EOHGoPaths, candidate_id: str) -> dict[str, Any]:
    candidate_path = paths.candidates_dir / _candidate_file_name(candidate_id)
    data = read_json(candidate_path, {})
    if not isinstance(data, dict):
        return {}
    return data


def register_candidate_result(paths: EOHGoPaths, candidate_payload: dict[str, Any]) -> None:
    ensure_workspace(paths)
    registry = read_json(paths.registry_path, [])
    if not isinstance(registry, list):
        registry = []

    candidate_id = candidate_payload.get("candidate_id")
    if not candidate_id:
        return

    registry = [item for item in registry if item.get("candidate_id") != candidate_id]
    registry.append(candidate_payload)
    write_json(paths.registry_path, registry)
