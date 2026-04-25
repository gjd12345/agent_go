from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..benchmark import parse_numeric_cost, run_test
from .arrival_scale_table import prepare_instance, resolve_source_path


DEFAULT_PROBLEMS = [f"rc10{i}.json" for i in range(1, 9)]


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def _is_valid(item: dict[str, Any]) -> bool:
    return item.get("Res") is not None and item.get("J") is not None and item.get("J") >= 0


def _best_name(row: dict[str, Any], metric: str) -> str | None:
    best = None
    best_value = None
    for name in ("SA", "EOH"):
        item = row.get(name, {})
        value = item.get(metric)
        if value is None or (metric == "J" and value < 0):
            continue
        if best_value is None or value < best_value:
            best = name
            best_value = value
    return best


def build_problem_table(problem: str, rows: list[dict[str, Any]]) -> str:
    lines = [f"### {problem.replace('.json', '').upper()}"]
    lines.append("| d | t | SA Res. | SA J | EOH Res. | EOH J |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for row in rows:
        best_res = _best_name(row, "Res")
        best_j = _best_name(row, "J")
        cells = [row["density"], f"{row['arrival_scale']:.1f}"]
        for name in ("SA", "EOH"):
            res = _fmt(row[name].get("Res"), 3)
            cost = _fmt(row[name].get("J"), 2)
            if name == best_res and res != "-":
                res = f"**{res}**"
            if name == best_j and cost != "-":
                cost = f"**{cost}**"
            cells.extend([res, cost])
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def sensitivity_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        by_key.setdefault((row["problem"], row["density"]), []).append(row)
    for (problem, density), group in sorted(by_key.items()):
        item: dict[str, Any] = {"problem": problem, "density": density}
        for alg in ("SA", "EOH"):
            values = [
                round(float(row[alg]["J"]), 6)
                for row in group
                if _is_valid(row.get(alg, {}))
            ]
            item[f"{alg}_valid_count"] = len(values)
            item[f"{alg}_distinct_J"] = len(set(values))
            item[f"{alg}_t_sensitive"] = len(set(values)) > 1
        out.append(item)
    return out


def run_tables(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    out_base = (root / args.output_dir).resolve()
    out_dir = out_base / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=False)
    tmp_dir = out_dir / "generated_instances"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    problems = args.problem or DEFAULT_PROBLEMS
    densities = args.density or ["d25", "d50", "d75"]
    scales = args.arrival_scale or [1.0, 0.8, 0.6]
    source_dir = (root / args.source_dir).resolve()
    algorithms = {
        "SA": str((root / args.sa_bin).resolve()),
        "EOH": str((root / args.eoh_bin).resolve()),
    }

    rows: list[dict[str, Any]] = []
    raw: list[dict[str, Any]] = []
    for problem in problems:
        for density in densities:
            src = resolve_source_path(root, source_dir, problem, density, args.use_density_source_dirs)
            density_arg = "d100" if args.use_density_source_dirs else density
            for scale in scales:
                data_path = prepare_instance(src, tmp_dir, density_arg, float(scale))
                row: dict[str, Any] = {
                    "problem": problem,
                    "density": density,
                    "arrival_scale": float(scale),
                    "data_path": str(data_path),
                }
                for name, bin_path in algorithms.items():
                    result = run_test(
                        bin_path,
                        str(data_path),
                        args.sim_time_multi,
                        timeout_seconds=args.timeout,
                    )
                    row[name] = {
                        "Res": result.get("first_response_time"),
                        "J": parse_numeric_cost(result.get("cost")),
                        "wall": result.get("response_time"),
                        "return_code": result.get("return_code"),
                    }
                    raw.append(
                        {
                            "problem": problem,
                            "density": density,
                            "arrival_scale": float(scale),
                            "algorithm": name,
                            "bin_path": bin_path,
                            "data_path": str(data_path),
                            **row[name],
                            "stdout": result.get("stdout"),
                            "stderr": result.get("stderr"),
                        }
                    )
                rows.append(row)
                (out_dir / "eight_problem_dt_partial.json").write_text(
                    json.dumps({"rows": rows, "raw": raw, "algorithms": algorithms}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

    by_problem = {problem: [row for row in rows if row["problem"] == problem] for problem in problems}
    table_parts = []
    for problem, problem_rows in by_problem.items():
        text = build_problem_table(problem, problem_rows)
        table_parts.append(text)
        (out_dir / f"{problem.replace('.json', '')}_dt_table.md").write_text(text, encoding="utf-8")

    sensitivity = sensitivity_summary(rows)
    payload = {
        "output_dir": str(out_dir),
        "config": vars(args),
        "algorithms": algorithms,
        "rows": rows,
        "raw": raw,
        "sensitivity": sensitivity,
    }
    (out_dir / "eight_problem_dt_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "eight_problem_dt_tables.md").write_text("\n".join(table_parts), encoding="utf-8")
    (out_dir / "sensitivity_summary.json").write_text(
        json.dumps(sensitivity, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    csv_path = out_dir / "eight_problem_dt_tables.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "problem",
            "density",
            "arrival_scale",
            "SA_Res",
            "SA_J",
            "EOH_Res",
            "EOH_J",
            "SA_valid",
            "EOH_valid",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "problem": row["problem"],
                    "density": row["density"],
                    "arrival_scale": row["arrival_scale"],
                    "SA_Res": row["SA"].get("Res"),
                    "SA_J": row["SA"].get("J"),
                    "EOH_Res": row["EOH"].get("Res"),
                    "EOH_J": row["EOH"].get("J"),
                    "SA_valid": _is_valid(row["SA"]),
                    "EOH_valid": _is_valid(row["EOH"]),
                }
            )

    print("\n".join(table_parts))
    print(f"Wrote eight problem dt tables to {out_dir}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Build 8 problem SA-vs-EOH d/t tables.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--source-dir", default="solomon_benchmark")
    parser.add_argument("--output-dir", default="eoh_go_workspace/reports/tables/eight_problem_dt")
    parser.add_argument("--problem", action="append")
    parser.add_argument("--density", action="append")
    parser.add_argument("--arrival-scale", action="append", type=float)
    parser.add_argument("--use-density-source-dirs", action="store_true")
    parser.add_argument("--sa-bin", default="mainbin_sa.exe")
    parser.add_argument("--eoh-bin", default="eoh_go_workspace/generated/bins/clean3gen_nonseed_1_20260424_103910.exe")
    parser.add_argument("--sim-time-multi", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()
    run_tables(args)


if __name__ == "__main__":
    main()
