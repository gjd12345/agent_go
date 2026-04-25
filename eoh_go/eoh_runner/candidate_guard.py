from __future__ import annotations

import re
from typing import Any


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _has_failed_insert_break(code: str) -> bool:
    compact = re.sub(r"\s+", " ", code)
    patterns = [
        r"if\s+bestIndex\s*==\s*-1\s*\{[^{}]*\bbreak\b",
        r"if\s+bestIdx\s*==\s*-1\s*\{[^{}]*\bbreak\b",
        r"if\s+bestAssign\s*==\s*-1\s*\{[^{}]*\bbreak\b",
        r"if\s+best\s*==\s*-1\s*\{[^{}]*\bbreak\b",
    ]
    return any(re.search(pattern, compact) for pattern in patterns)


def classify_candidate(
    item: dict[str, Any],
    *,
    seed_j: float | None = None,
    candidate_j: float | None = None,
    invalid_threshold: float = 1e8,
    suspicious_low_ratio: float = 0.3,
) -> dict[str, Any]:
    objective = _safe_float(item.get("objective"))
    code = item.get("code")
    flags: list[str] = []

    if objective is None:
        flags.append("missing_objective")
    elif objective >= invalid_threshold:
        flags.append("penalty_objective")
    elif objective < 0:
        flags.append("negative_objective")

    if not isinstance(code, str) or not code.strip():
        flags.append("missing_code")
        code = ""
    elif "func InsertShips" not in code:
        flags.append("missing_insertships")

    if isinstance(code, str) and code:
        if "RenewnTotalCost" not in code:
            flags.append("missing_total_cost_refresh")
        if _has_failed_insert_break(code):
            flags.append("early_break_after_failed_insert")
        if code.count("return dispatch") > 1:
            flags.append("multiple_return_dispatch")

    seed = _safe_float(seed_j)
    external_j = _safe_float(candidate_j)
    if external_j is not None and external_j < 0:
        flags.append("negative_external_j")
    if seed is not None and seed > 0:
        if objective is not None and 0 <= objective < seed * suspicious_low_ratio:
            flags.append("suspicious_low_objective")
        if external_j is not None and 0 <= external_j < seed * suspicious_low_ratio:
            flags.append("suspicious_low_external_j")

    invalid_flags = {"missing_objective", "penalty_objective", "missing_code", "missing_insertships"}
    if any(flag in invalid_flags for flag in flags):
        status = "invalid"
    elif any(
        flag.startswith("suspicious_")
        or flag
        in {
            "early_break_after_failed_insert",
            "multiple_return_dispatch",
            "missing_total_cost_refresh",
            "negative_objective",
            "negative_external_j",
        }
        for flag in flags
    ):
        status = "suspicious"
    else:
        status = "valid"

    return {
        "status": status,
        "objective": objective,
        "flags": flags,
        "reason": ", ".join(flags) if flags else "ok",
    }


def select_best_candidate(
    population: list[dict[str, Any]],
    *,
    seed_j: float | None = None,
    invalid_threshold: float = 1e8,
    suspicious_low_ratio: float = 0.3,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    ranked: list[tuple[float, int, dict[str, Any], dict[str, Any]]] = []
    statuses: list[dict[str, Any]] = []
    for index, item in enumerate(population):
        if not isinstance(item, dict):
            continue
        status = classify_candidate(
            item,
            seed_j=seed_j,
            invalid_threshold=invalid_threshold,
            suspicious_low_ratio=suspicious_low_ratio,
        )
        status = {"index": index, **status}
        statuses.append(status)
        objective = status.get("objective")
        if status["status"] == "valid" and objective is not None:
            ranked.append((float(objective), index, item, status))

    if not ranked:
        return None, statuses
    ranked.sort(key=lambda pair: (pair[0], pair[1]))
    return ranked[0][2], statuses


def best_raw_candidate(population: list[dict[str, Any]]) -> dict[str, Any] | None:
    ranked: list[tuple[float, int, dict[str, Any]]] = []
    for index, item in enumerate(population):
        if not isinstance(item, dict):
            continue
        objective = _safe_float(item.get("objective"))
        code = item.get("code")
        if objective is None or not isinstance(code, str) or "func InsertShips" not in code:
            continue
        ranked.append((objective, index, item))
    if not ranked:
        return None
    ranked.sort(key=lambda pair: (pair[0], pair[1]))
    return ranked[0][2]
