from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..benchmark import parse_numeric_cost, run_test


DEFAULT_ALGORITHMS = {
    "SA": "mainbin_sa.exe",
    "EOH": "eoh_go_workspace/generated/bins/clean3gen_nonseed_1_20260424_103910.exe",
}


def _density_pct(density: str) -> float:
    text = density.lower().strip()
    if text.startswith("d"):
        return int(text[1:]) / 100.0
    return float(text)


def prepare_instance(src_path: Path, dst_dir: Path, density: str, time_interval: int) -> Path:
    data = json.loads(src_path.read_text(encoding="utf-8"))
    pct = _density_pct(density)
    changed = False
    for batch in data.get("batch", []):
        for key in ("ori", "des"):
            arr = batch.get(key, [])
            if arr:
                keep = max(1, int(len(arr) * pct))
                if keep < len(arr):
                    batch[key] = arr[:keep]
                    changed = True
        if time_interval > 1:
            for key in ("ori", "des"):
                for item in batch.get(key, []):
                    item["timeEnd"] = max(1, int(item.get("timeEnd", 0) / time_interval))
                    changed = True
    if not changed:
        return src_path
    dst_path = dst_dir / f"{src_path.stem}_{density}_t{time_interval}.json"
    dst_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return dst_path


def parse_algorithms(root: Path, values: list[str]) -> dict[str, str]:
    if not values:
        return {name: str((root / rel).resolve()) for name, rel in DEFAULT_ALGORITHMS.items()}
    out = {}
    for item in values:
        if "=" not in item:
            raise ValueError(f"algorithm must be NAME=PATH, got {item!r}")
        name, raw_path = item.split("=", 1)
        path = Path(raw_path)
        if not path.is_absolute():
            path = root / path
        out[name] = str(path.resolve())
    return out


def fmt_num(value: Any, digits: int = 3) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def best_cost_name(row: dict[str, Any], algorithms: list[str]) -> str | None:
    best_name = None
    best_cost = None
    for name in algorithms:
        cost = row.get(name, {}).get("J")
        if cost is None or cost < 0:
            continue
        if best_cost is None or cost < best_cost:
            best_cost = cost
            best_name = name
    return best_name


def best_res_name(row: dict[str, Any], algorithms: list[str]) -> str | None:
    best_name = None
    best_res = None
    for name in algorithms:
        res = row.get(name, {}).get("Res")
        if res is None:
            continue
        if best_res is None or res < best_res:
            best_res = res
            best_name = name
    return best_name


def build_markdown_table(rows: list[dict[str, Any]], algorithms: list[str]) -> str:
    header = ["Inst.", "d", "t"]
    for name in algorithms:
        header.extend([f"{name} Res.", f"{name} J"])
    lines = ["| " + " | ".join(header) + " |"]
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for row in rows:
        best_j = best_cost_name(row, algorithms)
        best_r = best_res_name(row, algorithms)
        cells = [row["problem"], row["density"], str(row["time_interval"])]
        for name in algorithms:
            res = fmt_num(row.get(name, {}).get("Res"), 3)
            raw_cost = row.get(name, {}).get("J")
            cost = "-" if raw_cost is not None and raw_cost < 0 else fmt_num(raw_cost, 2)
            if name == best_r and res != "-":
                res = f"**{res}**"
            if name == best_j and cost != "-":
                cost = f"**{cost}**"
            cells.extend([res, cost])
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def build_latex_table(rows: list[dict[str, Any]], algorithms: list[str]) -> str:
    col_spec = "lcc" + "rr" * len(algorithms)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Algorithm Efficiency Comparison under Density and Time-Window Variants}",
        rf"\begin{{tabular}}{{{col_spec}}}",
        r"\toprule",
    ]
    group = ["Inst.", "$d$", "$t$"]
    for name in algorithms:
        group.extend([rf"\multicolumn{{2}}{{c}}{{{name}}}"])
    lines.append(" & ".join(group) + r" \\")
    sub = ["", "", ""]
    for _ in algorithms:
        sub.extend(["Res.", "$J$"])
    lines.append(" & ".join(sub) + r" \\")
    lines.append(r"\midrule")
    for row in rows:
        best_j = best_cost_name(row, algorithms)
        best_r = best_res_name(row, algorithms)
        cells = [row["problem"].replace(".json", "").upper(), row["density"], str(row["time_interval"])]
        for name in algorithms:
            res = fmt_num(row.get(name, {}).get("Res"), 3)
            raw_cost = row.get(name, {}).get("J")
            cost = "-" if raw_cost is not None and raw_cost < 0 else fmt_num(raw_cost, 2)
            if name == best_r and res != "-":
                res = rf"\textbf{{{res}}}"
            if name == best_j and cost != "-":
                cost = rf"\textbf{{{cost}}}"
            cells.extend([res, cost])
        lines.append(" & ".join(cells) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, Any]], algorithms: list[str]) -> None:
    fields = ["problem", "density", "time_interval"]
    for name in algorithms:
        fields.extend([f"{name}_Res", f"{name}_J", f"{name}_wall", f"{name}_return_code"])
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            flat = {key: row[key] for key in ("problem", "density", "time_interval")}
            for name in algorithms:
                item = row.get(name, {})
                flat[f"{name}_Res"] = item.get("Res")
                flat[f"{name}_J"] = item.get("J")
                flat[f"{name}_wall"] = item.get("wall")
                flat[f"{name}_return_code"] = item.get("return_code")
            writer.writerow(flat)


def run_table(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    algorithms = parse_algorithms(root, args.algorithm)
    problems = args.problem or ["rc101.json"]
    densities = args.density or ["d25", "d50", "d75", "d100"]
    intervals = args.time_interval or [1, 2, 3]
    source_dir = (root / args.source_dir).resolve()
    base_out_dir = (root / args.output_dir).resolve()
    base_out_dir.mkdir(parents=True, exist_ok=True)
    if args.no_run_subdir:
        out_dir = base_out_dir
    else:
        out_dir = base_out_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    out_dir.mkdir(parents=True, exist_ok=False)

    rows: list[dict[str, Any]] = []
    raw_results: list[dict[str, Any]] = []
    tmp_dir = out_dir / "generated_instances"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for problem in problems:
        src = source_dir / problem
        for density in densities:
            for interval in intervals:
                data_path = prepare_instance(src, tmp_dir, density, int(interval))
                row: dict[str, Any] = {
                    "problem": problem,
                    "density": density,
                    "time_interval": int(interval),
                }
                for name, bin_path in algorithms.items():
                    result = run_test(
                        bin_path,
                        str(data_path),
                        args.sim_time_multi,
                        timeout_seconds=args.timeout,
                    )
                    item = {
                        "Res": result.get("first_response_time"),
                        "J": parse_numeric_cost(result.get("cost")),
                        "wall": result.get("response_time"),
                        "return_code": result.get("return_code"),
                    }
                    row[name] = item
                    raw_results.append(
                        {
                            "problem": problem,
                            "density": density,
                            "time_interval": int(interval),
                            "algorithm": name,
                            "bin_path": bin_path,
                            "data_path": str(data_path),
                            **item,
                            "stdout": result.get("stdout"),
                            "stderr": result.get("stderr"),
                        }
                    )
                rows.append(row)
                (out_dir / "efficiency_table_partial.json").write_text(
                    json.dumps(
                        {
                            "output_dir": str(out_dir),
                            "algorithms": algorithms,
                            "problems": problems,
                            "densities": densities,
                            "time_intervals": intervals,
                            "sim_time_multi": args.sim_time_multi,
                            "rows": rows,
                            "raw_results": raw_results,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )

    payload = {
        "output_dir": str(out_dir),
        "algorithms": algorithms,
        "problems": problems,
        "densities": densities,
        "time_intervals": intervals,
        "sim_time_multi": args.sim_time_multi,
        "rows": rows,
        "raw_results": raw_results,
    }
    (out_dir / "efficiency_table_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "efficiency_table.md").write_text(
        build_markdown_table(rows, list(algorithms)),
        encoding="utf-8",
    )
    (out_dir / "efficiency_table.tex").write_text(
        build_latex_table(rows, list(algorithms)),
        encoding="utf-8",
    )
    write_csv(out_dir / "efficiency_table.csv", rows, list(algorithms))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate paper-style Res/J efficiency tables.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--source-dir", default="solomon_benchmark")
    parser.add_argument("--output-dir", default="eoh_go_workspace/reports/tables/efficiency")
    parser.add_argument("--no-run-subdir", action="store_true", help="Write directly to output-dir instead of a timestamped run_* subdirectory.")
    parser.add_argument("--problem", action="append")
    parser.add_argument("--density", action="append")
    parser.add_argument("--time-interval", action="append", type=int)
    parser.add_argument("--algorithm", action="append", help="Algorithm as NAME=path/to/bin.exe")
    parser.add_argument("--sim-time-multi", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    payload = run_table(args)
    print(build_markdown_table(payload["rows"], list(payload["algorithms"])))
    print(f"Wrote table files to {payload['output_dir']}")


if __name__ == "__main__":
    main()
