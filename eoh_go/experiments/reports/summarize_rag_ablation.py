from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CellKey = tuple[str, str, float]
_SEED_MISMATCH_REL_TOL = 0.05


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _cell_key(row: dict[str, Any]) -> CellKey:
    return (str(row.get("problem")), str(row.get("density")), float(row.get("arrival_scale")))


def _load_rows(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    return rows if isinstance(rows, list) else []


def _rate(numerator: Any, denominator: Any) -> float | None:
    denom = _safe_float(denominator)
    num = _safe_float(numerator)
    if denom is None or num is None or denom <= 0:
        return None
    return num / denom


def _ratio(numerator: Any, denominator: Any) -> float | None:
    denom = _safe_float(denominator)
    num = _safe_float(numerator)
    if denom is None or num is None or denom == 0:
        return None
    return num / denom


def _direction(ratio: float | None) -> str | None:
    if ratio is None:
        return None
    if ratio < 1:
        return "faster"
    if ratio > 1:
        return "slower"
    return "same"


def _relative_mismatch(left: Any, right: Any, rel_tol: float = _SEED_MISMATCH_REL_TOL) -> bool:
    left_num = _safe_float(left)
    right_num = _safe_float(right)
    if left_num is None or right_num is None:
        return False
    scale = max(abs(left_num), 1.0)
    return abs(left_num - right_num) / scale > rel_tol


def _compact_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    population_size = row.get("population_size")
    suspicious = row.get("suspicious_candidates")
    invalid = row.get("invalid_candidates")
    bad_candidates = (suspicious or 0) + (invalid or 0)
    return {
        "valid_candidates": row.get("valid_candidates"),
        "suspicious_candidates": suspicious,
        "invalid_candidates": invalid,
        "population_size": population_size,
        "valid_rate": _rate(row.get("valid_candidates"), population_size),
        "bad_rate": _rate(bad_candidates, population_size),
        "seed_J": row.get("seed_J"),
        "best_EOH_J": row.get("best_EOH_J"),
        "seed_Res": row.get("seed_Res"),
        "best_EOH_Res": row.get("best_EOH_Res"),
        "best_build_ok": row.get("best_build_ok"),
        "selected_best_status_after_eval": row.get("selected_best_status_after_eval"),
    }


def _notes(baseline: dict[str, Any] | None, rag: dict[str, Any] | None) -> list[str]:
    notes: list[str] = []
    for side, row in (("baseline", baseline), ("rag", rag)):
        if row is None:
            notes.append(f"missing_{side}")
            continue
        population_size = _safe_float(row.get("population_size"))
        if population_size is None or population_size <= 0:
            notes.append("no_population")
        if row.get("best_build_ok") is False:
            notes.append("build_failed")
        if row.get("selected_best_status_after_eval") not in (None, "valid"):
            notes.append("no_valid_candidate")
        if row.get("seed_J") is None or row.get("best_EOH_J") is None:
            notes.append("missing_j")
        if row.get("seed_Res") is None or row.get("best_EOH_Res") is None:
            notes.append("missing_res")
    return sorted(set(notes))


def _comparison_notes(baseline: dict[str, Any], rag: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    if _relative_mismatch(baseline.get("seed_J"), rag.get("seed_J")):
        notes.append("seed_j_mismatch")
    if _relative_mismatch(baseline.get("seed_Res"), rag.get("seed_Res")):
        notes.append("seed_res_mismatch")
    return notes


def _is_complete(notes: list[str]) -> bool:
    blocking_prefixes = (
        "missing_",
        "no_population",
        "build_failed",
        "no_valid_candidate",
    )
    return not any(note.startswith(blocking_prefixes) or note in blocking_prefixes for note in notes)


def _build_cell(key: CellKey, baseline: dict[str, Any], rag: dict[str, Any]) -> dict[str, Any]:
    baseline_compact = _compact_row(baseline)
    rag_compact = _compact_row(rag)
    baseline_valid_rate = baseline_compact["valid_rate"] if baseline_compact else None
    rag_valid_rate = rag_compact["valid_rate"] if rag_compact else None
    baseline_bad_rate = baseline_compact["bad_rate"] if baseline_compact else None
    rag_bad_rate = rag_compact["bad_rate"] if rag_compact else None
    baseline_j = _safe_float(baseline.get("best_EOH_J"))
    rag_j = _safe_float(rag.get("best_EOH_J"))
    res_ratio_baseline = _ratio(baseline.get("best_EOH_Res"), baseline.get("seed_Res"))
    res_ratio_rag = _ratio(rag.get("best_EOH_Res"), rag.get("seed_Res"))
    notes = sorted(set(_notes(baseline, rag) + _comparison_notes(baseline, rag)))
    complete = _is_complete(notes)
    return {
        "key": [key[0], key[1], key[2]],
        "problem": key[0],
        "density": key[1],
        "arrival_scale": key[2],
        "complete": complete,
        "notes": notes,
        "baseline": baseline_compact,
        "rag": rag_compact,
        "delta_valid_rate": None if baseline_valid_rate is None or rag_valid_rate is None else rag_valid_rate - baseline_valid_rate,
        "delta_bad_rate": None if baseline_bad_rate is None or rag_bad_rate is None else rag_bad_rate - baseline_bad_rate,
        "delta_J": None if baseline_j is None or rag_j is None else rag_j - baseline_j,
        "res_ratio_baseline": res_ratio_baseline,
        "res_ratio_rag": res_ratio_rag,
        "res_direction_baseline": _direction(res_ratio_baseline),
        "res_direction_rag": _direction(res_ratio_rag),
    }


def _stats(paired_cells: list[dict[str, Any]], unpaired_cells: list[dict[str, Any]]) -> dict[str, Any]:
    complete_cells = [cell for cell in paired_cells if cell.get("complete")]
    j_deltas = [cell.get("delta_J") for cell in complete_cells if cell.get("delta_J") is not None]
    return {
        "paired_count": len(paired_cells),
        "complete_count": len(complete_cells),
        "incomplete_count": len(paired_cells) - len(complete_cells),
        "unpaired_count": len(unpaired_cells),
        "seed_j_mismatch_count": sum(1 for cell in paired_cells if "seed_j_mismatch" in cell.get("notes", [])),
        "seed_res_mismatch_count": sum(1 for cell in paired_cells if "seed_res_mismatch" in cell.get("notes", [])),
        "rag_j_improved": sum(1 for delta in j_deltas if delta < 0),
        "rag_j_same": sum(1 for delta in j_deltas if delta == 0),
        "rag_j_worse": sum(1 for delta in j_deltas if delta > 0),
    }


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _build_markdown(summary: dict[str, Any]) -> str:
    stats = summary["stats"]
    lines = [
        "# RAG Ablation Summary",
        "",
        "## Overall",
        "",
        f"- Paired cells: {stats['paired_count']}",
        f"- Complete cells: {stats['complete_count']}",
        f"- Unpaired cells: {stats['unpaired_count']}",
        f"- Seed J mismatches (>5%): {stats['seed_j_mismatch_count']}",
        f"- Seed Res. mismatches (>5%): {stats['seed_res_mismatch_count']}",
        f"- RAG improved J: {stats['rag_j_improved']}",
        f"- RAG same J: {stats['rag_j_same']}",
        f"- RAG worse J: {stats['rag_j_worse']}",
        "",
        "Legend: delta_J < 0 = RAG improves J; res_ratio < 1 = faster first response; n/a = incomplete.",
        "",
        "## Core Questions",
        "",
        "| Problem | Density | t | Complete | Δ valid rate | Δ bad rate | ΔJ | Baseline Res ratio | RAG Res ratio | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for cell in summary["paired_cells"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(cell["problem"]),
                    str(cell["density"]),
                    f"{float(cell['arrival_scale']):.1f}",
                    str(bool(cell["complete"])).lower(),
                    _fmt(cell.get("delta_valid_rate")),
                    _fmt(cell.get("delta_bad_rate")),
                    _fmt(cell.get("delta_J"), digits=2),
                    _fmt(cell.get("res_ratio_baseline")),
                    _fmt(cell.get("res_ratio_rag")),
                    ", ".join(cell.get("notes", [])) or "-",
                ]
            )
            + " |"
        )

    if summary["unpaired_cells"]:
        lines.extend(["", "## Unpaired Cells", "", "| Side | Problem | Density | t |", "| --- | --- | --- | --- |"])
        for cell in summary["unpaired_cells"]:
            key = cell["key"]
            lines.append(f"| {cell['side']} | {key[0]} | {key[1]} | {float(key[2]):.1f} |")
    return "\n".join(lines) + "\n"


def summarize(baseline_json_path: str, rag_json_path: str, output_dir: str) -> dict[str, Any]:
    baseline_rows = {_cell_key(row): row for row in _load_rows(baseline_json_path)}
    rag_rows = {_cell_key(row): row for row in _load_rows(rag_json_path)}
    paired_keys = sorted(set(baseline_rows) & set(rag_rows))
    paired_cells = [_build_cell(key, baseline_rows[key], rag_rows[key]) for key in paired_keys]
    unpaired_cells = [
        {"side": "baseline", "key": [key[0], key[1], key[2]], "row": _compact_row(baseline_rows[key])}
        for key in sorted(set(baseline_rows) - set(rag_rows))
    ]
    unpaired_cells.extend(
        {"side": "rag", "key": [key[0], key[1], key[2]], "row": _compact_row(rag_rows[key])}
        for key in sorted(set(rag_rows) - set(baseline_rows))
    )
    summary = {
        "baseline_json_path": str(baseline_json_path),
        "rag_json_path": str(rag_json_path),
        "paired_cells": paired_cells,
        "unpaired_cells": unpaired_cells,
        "stats": _stats(paired_cells, unpaired_cells),
    }

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "rag_ablation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "rag_ablation_summary.md").write_text(_build_markdown(summary), encoding="utf-8")
    return summary


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Summarize baseline vs RAG EOH grid results.")
    parser.add_argument("baseline_json_path")
    parser.add_argument("rag_json_path")
    parser.add_argument("--output-dir", default="eoh_go_workspace/reports/tables/rag_ablation_summary")
    args = parser.parse_args()
    summarize(args.baseline_json_path, args.rag_json_path, args.output_dir)


if __name__ == "__main__":
    main()
