"""Adaptive Operator Selection — cross-process operator performance tracking.

Tracks which operators (e1, e2, m1, m2) produce improvements vs regressions
for each problem, and provides weighted sampling to favor successful operators.
"""

from __future__ import annotations

import fcntl
import json
import time
from collections import defaultdict
from pathlib import Path


def _stats_path(pool_dir: Path, problem: str) -> Path:
    return pool_dir / f"operator_stats_{problem}.jsonl"


def register_operator_result(
    pool_dir: Path,
    problem: str,
    operator: str,
    improved: bool,
    delta: float,
) -> None:
    """Register an operator's result (improved or not) in shared stats."""
    pool_dir.mkdir(parents=True, exist_ok=True)
    path = _stats_path(pool_dir, problem)
    entry = json.dumps({
        "operator": operator,
        "improved": improved,
        "delta": delta,
        "ts": time.time(),
    })
    with open(path, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(entry + "\n")
        fcntl.flock(f, fcntl.LOCK_UN)


def get_operator_weights(pool_dir: Path, problem: str) -> dict[str, float]:
    """Compute operator weights based on historical success rates.

    Returns a dict like {"e1": 1.2, "e2": 0.8, "m1": 1.0, "m2": 1.5}
    where higher = more successful = should be sampled more often.
    Default weight = 1.0 for operators with no data.
    """
    path = _stats_path(pool_dir, problem)
    if not path.exists():
        return {}

    stats: dict[str, dict[str, int]] = defaultdict(lambda: {"success": 0, "total": 0})
    for line in path.read_text().strip().split("\n"):
        if not line:
            continue
        entry = json.loads(line)
        op = entry["operator"]
        stats[op]["total"] += 1
        if entry["improved"]:
            stats[op]["success"] += 1

    weights = {}
    for op, s in stats.items():
        if s["total"] >= 3:
            rate = s["success"] / s["total"]
            weights[op] = 0.5 + rate  # range [0.5, 1.5]
        else:
            weights[op] = 1.0
    return weights
