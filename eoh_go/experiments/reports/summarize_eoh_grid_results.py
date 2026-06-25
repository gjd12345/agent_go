from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _num(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _fmt(value: Any, digits: int = 2) -> str:
    number = _num(value)
    if number is None:
        return "-"
    return f"{number:.{digits}f}"


def _fmt_count(value: Any) -> str:
    if value is None:
        return "-"
    return str(value)


def _classify(row: dict[str, Any], suspicious_low_ratio: float) -> str:
    sa_j = _num(row.get("seed_J"))
    eoh_j = _num(row.get("best_EOH_J"))
    if sa_j is None:
        return "excluded_no_sa"
    if eoh_j is None:
        return "excluded_no_eoh"
    if eoh_j < 0:
        return "excluded_negative_eoh"
    if sa_j > 0 and eoh_j < suspicious_low_ratio * sa_j:
        return "excluded_suspicious_low"
    if eoh_j < sa_j:
        return "improved"
    if abs(eoh_j - sa_j) <= 1e-9:
        return "tie"
    return "worse"


def _load_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        source_rows = data.get("rows", [])
        if not isinstance(source_rows, list):
            continue
        for row in source_rows:
            if isinstance(row, dict):
                row = dict(row)
                row["source_file"] = str(path)
                rows.append(row)
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def _build_markdown(
    rows: list[dict[str, Any]],
    valid_rows: list[dict[str, Any]],
    excluded_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    counter: Counter[str],
) -> str:
    lines: list[str] = []
    lines.append("# EOH Grid Cleaned Summary")
    lines.append("")
    lines.append("清洗规则：")
    lines.append("")
    lines.append("- `SA J` 为空：剔除为 `excluded_no_sa`。")
    lines.append("- `EOH J` 为空：剔除为 `excluded_no_eoh`。")
    lines.append("- `EOH J < 0`：剔除为 `excluded_negative_eoh`。")
    lines.append("- `EOH J < 0.3 * SA J`：剔除为 `excluded_suspicious_low`。")
    lines.append("- 其余按 `EOH J - SA J` 分为 improved / tie / worse。")
    lines.append("")
    lines.append("## Overall Counts")
    lines.append("")
    lines.append("| Type | Count |")
    lines.append("|---|---:|")
    for key in sorted(counter):
        lines.append(f"| {key} | {counter[key]} |")
    lines.append(f"| total | {len(rows)} |")
    lines.append("")
    lines.append("## Valid Comparison Rows")
    lines.append("")
    lines.append("| Inst. | d | t | SA Res. | SA J | EOH Res. | EOH J | Delta J | Class | Valid | Susp. | Invalid |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|")
    for row in valid_rows:
        lines.append(
            "| {inst} | {d} | {t:.1f} | {sa_res} | {sa_j} | {eoh_res} | {eoh_j} | {delta} | {cls} | {valid} | {susp} | {invalid} |".format(
                inst=str(row.get("problem", "")).replace(".json", "").upper(),
                d=row.get("density"),
                t=float(row.get("arrival_scale")),
                sa_res=_fmt(row.get("seed_Res"), 3),
                sa_j=_fmt(row.get("seed_J"), 2),
                eoh_res=_fmt(row.get("best_EOH_Res"), 3),
                eoh_j=_fmt(row.get("best_EOH_J"), 2),
                delta=_fmt(row.get("delta_J"), 2),
                cls=row.get("clean_class"),
                valid=_fmt_count(row.get("valid_candidates")),
                susp=_fmt_count(row.get("suspicious_candidates")),
                invalid=_fmt_count(row.get("invalid_candidates")),
            )
        )
    lines.append("")
    lines.append("## Summary By Instance And Density")
    lines.append("")
    lines.append("| Inst. | d | Rows | Improved | Tie | Worse | Excluded | Best Delta J |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for row in summary_rows:
        lines.append(
            f"| {row['inst']} | {row['density']} | {row['rows']} | {row['improved']} | {row['tie']} | {row['worse']} | {row['excluded']} | {_fmt(row['best_delta_J'], 2)} |"
        )
    lines.append("")
    lines.append("## Excluded Rows")
    lines.append("")
    lines.append("| Inst. | d | t | SA J | EOH J | Reason |")
    lines.append("|---|---|---:|---:|---:|---|")
    for row in excluded_rows:
        lines.append(
            "| {inst} | {d} | {t:.1f} | {sa_j} | {eoh_j} | {reason} |".format(
                inst=str(row.get("problem", "")).replace(".json", "").upper(),
                d=row.get("density"),
                t=float(row.get("arrival_scale")),
                sa_j=_fmt(row.get("seed_J"), 2),
                eoh_j=_fmt(row.get("best_EOH_J"), 2),
                reason=row.get("clean_class"),
            )
        )
    lines.append("")
    return "\n".join(lines)


def summarize(paths: list[Path], out_dir: Path, suspicious_low_ratio: float) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = _load_rows(paths)
    for row in rows:
        clean_class = _classify(row, suspicious_low_ratio)
        row["clean_class"] = clean_class
        sa_j = _num(row.get("seed_J"))
        eoh_j = _num(row.get("best_EOH_J"))
        row["delta_J"] = None if sa_j is None or eoh_j is None else eoh_j - sa_j

    valid_rows = [row for row in rows if row["clean_class"] in {"improved", "tie", "worse"}]
    excluded_rows = [row for row in rows if row["clean_class"].startswith("excluded_")]
    valid_rows.sort(key=lambda row: (str(row.get("problem")), str(row.get("density")), float(row.get("arrival_scale", 0))))
    excluded_rows.sort(key=lambda row: (str(row.get("problem")), str(row.get("density")), float(row.get("arrival_scale", 0))))

    counter = Counter(row["clean_class"] for row in rows)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("problem", "")).replace(".json", "").upper(), str(row.get("density")))].append(row)

    summary_rows: list[dict[str, Any]] = []
    for (inst, density), group in sorted(grouped.items()):
        deltas = [_num(row.get("delta_J")) for row in group if row.get("clean_class") in {"improved", "tie", "worse"}]
        deltas = [delta for delta in deltas if delta is not None]
        summary_rows.append(
            {
                "inst": inst,
                "density": density,
                "rows": len(group),
                "improved": sum(1 for row in group if row["clean_class"] == "improved"),
                "tie": sum(1 for row in group if row["clean_class"] == "tie"),
                "worse": sum(1 for row in group if row["clean_class"] == "worse"),
                "excluded": sum(1 for row in group if row["clean_class"].startswith("excluded_")),
                "best_delta_J": min(deltas) if deltas else None,
            }
        )

    fields = [
        "problem",
        "density",
        "arrival_scale",
        "seed_Res",
        "seed_J",
        "best_EOH_Res",
        "best_EOH_J",
        "delta_J",
        "clean_class",
        "valid_candidates",
        "suspicious_candidates",
        "invalid_candidates",
        "raw_best_objective",
        "filtered_best_objective",
        "best_candidate_id",
        "source_file",
    ]
    _write_csv(out_dir / "clean_valid_comparisons.csv", valid_rows, fields)
    _write_csv(out_dir / "clean_excluded_rows.csv", excluded_rows, fields)
    _write_csv(out_dir / "summary_by_instance_density.csv", summary_rows, list(summary_rows[0].keys()) if summary_rows else [])

    markdown = _build_markdown(rows, valid_rows, excluded_rows, summary_rows, counter)
    (out_dir / "clean_summary.md").write_text(markdown, encoding="utf-8")
    payload = {
        "sources": [str(path) for path in paths],
        "suspicious_low_ratio": suspicious_low_ratio,
        "counts": dict(counter),
        "rows": rows,
        "summary_by_instance_density": summary_rows,
    }
    (out_dir / "clean_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean and summarize EOH arrival-grid results.")
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--suspicious-low-ratio", type=float, default=0.3)
    args = parser.parse_args()
    payload = summarize([Path(item) for item in args.input], Path(args.out_dir), args.suspicious_low_ratio)
    print(json.dumps({"counts": payload["counts"], "out_dir": args.out_dir}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
