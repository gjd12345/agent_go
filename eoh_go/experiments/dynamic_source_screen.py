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


def _valid(item: dict[str, Any]) -> bool:
    return item.get("Res") is not None and item.get("J") is not None and item.get("J") >= 0


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def _status(item: dict[str, Any]) -> str:
    if _valid(item):
        return "valid"
    raw = str(item.get("raw_cost") or "")
    if "TIMEOUT" in raw:
        return "timeout"
    if item.get("return_code") not in (None, 0):
        return f"rc{item.get('return_code')}"
    return "invalid"


def sensitivity(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((row["problem"], row["density"]), []).append(row)
    out = []
    for (problem, density), group in sorted(grouped.items()):
        item: dict[str, Any] = {"problem": problem, "density": density}
        for alg in ("SA", "EOH"):
            valid_rows = [row for row in group if _valid(row[alg])]
            values = [round(float(row[alg]["J"]), 6) for row in valid_rows]
            item[f"{alg}_valid_count"] = len(valid_rows)
            item[f"{alg}_distinct_J"] = len(set(values))
            item[f"{alg}_t_sensitive"] = len(set(values)) > 1
            item[f"{alg}_all_valid"] = len(valid_rows) == len(group)
        item["both_all_valid"] = item["SA_all_valid"] and item["EOH_all_valid"]
        item["both_t_sensitive"] = item["SA_t_sensitive"] and item["EOH_t_sensitive"]
        item["usable_for_table"] = item["both_all_valid"] and item["both_t_sensitive"]
        out.append(item)
    return out


def build_summary_markdown(rows: list[dict[str, Any]], sens: list[dict[str, Any]]) -> str:
    lines = [
        "# Dynamic Source Screen",
        "",
        "## Usability By Problem And Density",
        "",
        "| Inst. | d | SA valid | SA distinct J | EOH valid | EOH distinct J | usable |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in sens:
        lines.append(
            "| "
            + " | ".join(
                [
                    item["problem"].replace(".json", "").upper(),
                    item["density"],
                    str(item["SA_valid_count"]),
                    str(item["SA_distinct_J"]),
                    str(item["EOH_valid_count"]),
                    str(item["EOH_distinct_J"]),
                    "yes" if item["usable_for_table"] else "no",
                ]
            )
            + " |"
        )
    lines.extend(["", "## Cell Details", ""])
    for problem in sorted({row["problem"] for row in rows}):
        lines.append(f"### {problem.replace('.json', '').upper()}")
        lines.append("| d | t | SA status | SA Res | SA J | EOH status | EOH Res | EOH J |")
        lines.append("| --- | ---: | --- | ---: | ---: | --- | ---: | ---: |")
        for row in [r for r in rows if r["problem"] == problem]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        row["density"],
                        f"{row['arrival_scale']:.1f}",
                        _status(row["SA"]),
                        _fmt(row["SA"].get("Res"), 3),
                        _fmt(row["SA"].get("J"), 2),
                        _status(row["EOH"]),
                        _fmt(row["EOH"].get("Res"), 3),
                        _fmt(row["EOH"].get("J"), 2),
                    ]
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines)


def run_screen(args: argparse.Namespace) -> dict[str, Any]:
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
            src = resolve_source_path(root, source_dir, problem, density, True)
            for scale in scales:
                data_path = prepare_instance(src, tmp_dir, "d100", float(scale))
                row: dict[str, Any] = {
                    "problem": problem,
                    "density": density,
                    "arrival_scale": float(scale),
                    "data_path": str(data_path),
                }
                for name, bin_path in algorithms.items():
                    result = run_test(bin_path, str(data_path), args.sim_time_multi, timeout_seconds=args.timeout)
                    cost = result.get("cost")
                    row[name] = {
                        "Res": result.get("first_response_time"),
                        "J": parse_numeric_cost(cost),
                        "wall": result.get("response_time"),
                        "return_code": result.get("return_code"),
                        "raw_cost": cost,
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
                            "stdout_tail": (result.get("stdout") or "")[-500:],
                            "stderr_tail": (result.get("stderr") or "")[-500:],
                        }
                    )
                rows.append(row)
                sens = sensitivity(rows)
                partial = {"rows": rows, "raw": raw, "sensitivity": sens, "algorithms": algorithms}
                (out_dir / "dynamic_source_screen_partial.json").write_text(
                    json.dumps(partial, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                (out_dir / "dynamic_source_screen_partial.md").write_text(
                    build_summary_markdown(rows, sens),
                    encoding="utf-8",
                )

    sens = sensitivity(rows)
    payload = {
        "output_dir": str(out_dir),
        "config": vars(args),
        "algorithms": algorithms,
        "rows": rows,
        "raw": raw,
        "sensitivity": sens,
    }
    (out_dir / "dynamic_source_screen_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "dynamic_source_screen.md").write_text(
        build_summary_markdown(rows, sens),
        encoding="utf-8",
    )
    with (out_dir / "dynamic_source_screen.csv").open("w", newline="", encoding="utf-8") as f:
        fields = [
            "problem",
            "density",
            "arrival_scale",
            "SA_status",
            "SA_Res",
            "SA_J",
            "EOH_status",
            "EOH_Res",
            "EOH_J",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "problem": row["problem"],
                    "density": row["density"],
                    "arrival_scale": row["arrival_scale"],
                    "SA_status": _status(row["SA"]),
                    "SA_Res": row["SA"].get("Res"),
                    "SA_J": row["SA"].get("J"),
                    "EOH_status": _status(row["EOH"]),
                    "EOH_Res": row["EOH"].get("Res"),
                    "EOH_J": row["EOH"].get("J"),
                }
            )
    print(build_summary_markdown(rows, sens))
    print(f"Wrote dynamic source screen to {out_dir}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Screen dynamic density sources for valid/t-sensitive cells.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--source-dir", default="solomon_benchmark")
    parser.add_argument("--output-dir", default="eoh_go_workspace/reports/tables/dynamic_source_screen")
    parser.add_argument("--problem", action="append")
    parser.add_argument("--density", action="append")
    parser.add_argument("--arrival-scale", action="append", type=float)
    parser.add_argument("--sa-bin", default="mainbin_sa.exe")
    parser.add_argument("--eoh-bin", default="eoh_go_workspace/generated/bins/clean3gen_nonseed_1_20260424_103910.exe")
    parser.add_argument("--sim-time-multi", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    run_screen(args)


if __name__ == "__main__":
    main()
