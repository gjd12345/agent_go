from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _num(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _classify(row: dict[str, Any]) -> str:
    sa_j = _num(row.get("seed_J"))
    eoh_j = _num(row.get("best_EOH_J"))
    if sa_j is None:
        return "no_sa"
    if eoh_j is None:
        return "no_eoh"
    if eoh_j < 0:
        return "negative_eoh"
    if sa_j > 0 and eoh_j < 0.3 * sa_j:
        return "suspicious_low"
    if eoh_j < sa_j:
        return "improved"
    if abs(eoh_j - sa_j) <= 1e-9:
        return "tie"
    return "worse"


def _fmt(value: Any, digits: int = 2) -> str:
    number = _num(value)
    if number is None:
        return "-"
    return f"{number:.{digits}f}"


def summarize(manifest: Path, out_dir: Path) -> dict[str, Any]:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    rows = []
    for record in data.get("records", []):
        row = record.get("row")
        if not isinstance(row, dict):
            continue
        item = {
            "repeat": record.get("repeat"),
            "problem": row.get("problem"),
            "density": row.get("density"),
            "arrival_scale": row.get("arrival_scale"),
            "seed_Res": row.get("seed_Res"),
            "seed_J": row.get("seed_J"),
            "best_EOH_Res": row.get("best_EOH_Res"),
            "best_EOH_J": row.get("best_EOH_J"),
            "valid_candidates": row.get("valid_candidates"),
            "suspicious_candidates": row.get("suspicious_candidates"),
            "invalid_candidates": row.get("invalid_candidates"),
            "result_file": record.get("result_file"),
            "duration_s": record.get("duration_s"),
        }
        item["class"] = _classify(row)
        sa_j = _num(item["seed_J"])
        eoh_j = _num(item["best_EOH_J"])
        item["delta_J"] = None if sa_j is None or eoh_j is None else eoh_j - sa_j
        rows.append(item)

    grouped: dict[tuple[str, str, float], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["problem"]), str(row["density"]), float(row["arrival_scale"]))].append(row)

    summary = []
    for (problem, density, scale), group in sorted(grouped.items()):
        valid_deltas = [_num(row.get("delta_J")) for row in group if row["class"] in {"improved", "tie", "worse"}]
        valid_deltas = [delta for delta in valid_deltas if delta is not None]
        summary.append(
            {
                "problem": problem,
                "density": density,
                "arrival_scale": scale,
                "runs": len(group),
                "improved": sum(row["class"] == "improved" for row in group),
                "tie": sum(row["class"] == "tie" for row in group),
                "worse": sum(row["class"] == "worse" for row in group),
                "excluded": sum(row["class"] not in {"improved", "tie", "worse"} for row in group),
                "mean_delta_J": sum(valid_deltas) / len(valid_deltas) if valid_deltas else None,
                "best_delta_J": min(valid_deltas) if valid_deltas else None,
            }
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    row_fields = [
        "repeat",
        "problem",
        "density",
        "arrival_scale",
        "seed_Res",
        "seed_J",
        "best_EOH_Res",
        "best_EOH_J",
        "delta_J",
        "class",
        "valid_candidates",
        "suspicious_candidates",
        "invalid_candidates",
        "duration_s",
        "result_file",
    ]
    with (out_dir / "selected_repeat_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=row_fields)
        writer.writeheader()
        writer.writerows(rows)

    summary_fields = [
        "problem",
        "density",
        "arrival_scale",
        "runs",
        "improved",
        "tie",
        "worse",
        "excluded",
        "mean_delta_J",
        "best_delta_J",
    ]
    with (out_dir / "selected_repeat_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=summary_fields)
        writer.writeheader()
        writer.writerows(summary)

    lines = ["# Selected Repeat Validation", ""]
    lines.append("| Inst. | d | t | Runs | Improved | Tie | Worse | Excluded | Mean Delta J | Best Delta J |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for item in summary:
        inst = str(item["problem"]).replace(".json", "").upper()
        lines.append(
            f"| {inst} | {item['density']} | {float(item['arrival_scale']):.1f} | {item['runs']} | {item['improved']} | {item['tie']} | {item['worse']} | {item['excluded']} | {_fmt(item['mean_delta_J'])} | {_fmt(item['best_delta_J'])} |"
        )
    lines.append("")
    lines.append("## Raw Repeat Rows")
    lines.append("")
    lines.append("| Rep. | Inst. | d | t | SA J | EOH J | Delta J | Class |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---|")
    for row in rows:
        inst = str(row["problem"]).replace(".json", "").upper()
        lines.append(
            f"| {row['repeat']} | {inst} | {row['density']} | {float(row['arrival_scale']):.1f} | {_fmt(row['seed_J'])} | {_fmt(row['best_EOH_J'])} | {_fmt(row['delta_J'])} | {row['class']} |"
        )
    (out_dir / "selected_repeat_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    payload = {"manifest": str(manifest), "rows": rows, "summary": summary}
    (out_dir / "selected_repeat_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize selected repeat validation runs.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    payload = summarize(Path(args.manifest), Path(args.out_dir))
    print(json.dumps({"rows": len(payload["rows"]), "groups": len(payload["summary"]), "out_dir": args.out_dir}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
