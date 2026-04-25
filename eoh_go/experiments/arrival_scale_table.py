from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..benchmark import parse_numeric_cost, run_test
from .efficiency_table import best_cost_name, best_res_name, fmt_num, parse_algorithms


def _density_pct(density: str) -> float:
    text = density.lower().strip()
    if text.startswith("d"):
        return int(text[1:]) / 100.0
    return float(text)


def _t_label(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text.replace(".", "p")


def prepare_instance(src_path: Path, dst_dir: Path, density: str, arrival_scale: float) -> Path:
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
        if "timeReady" in batch and abs(arrival_scale - 1.0) > 1e-9:
            batch["timeReady"] = max(0, int(round(float(batch.get("timeReady", 0)) * arrival_scale)))
            changed = True

    if not changed:
        return src_path
    dst_path = dst_dir / f"{src_path.stem}_{density}_ta{_t_label(arrival_scale)}.json"
    dst_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return dst_path


def resolve_source_path(root: Path, source_dir: Path, problem: str, density: str, use_density_dirs: bool) -> Path:
    if not use_density_dirs:
        return source_dir / problem
    suffix = density.lower().removeprefix("d")
    candidates = [
        root / f"solomon_benchmark_d{suffix}" / problem,
        root / "solomon_benchmark" / problem,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return source_dir / problem


def build_markdown_table(rows: list[dict[str, Any]], algorithms: list[str]) -> str:
    header = ["Inst.", "d", "t"]
    for name in algorithms:
        header.extend([f"{name} Res.", f"{name} J"])
    lines = ["| " + " | ".join(header) + " |"]
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for row in rows:
        best_j = best_cost_name(row, algorithms)
        best_r = best_res_name(row, algorithms)
        cells = [row["problem"], row["density"], f"{row['arrival_scale']:.1f}"]
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


def build_compact_markdown(rows: list[dict[str, Any]], algorithms: list[str]) -> str:
    lines = ["| Cell | " + " | ".join(algorithms) + " | Observation |"]
    lines.append("| " + " | ".join(["---"] * (len(algorithms) + 2)) + " |")
    for row in rows:
        cells = [f"{row['problem'].replace('.json', '').upper()},{row['density']},t{row['arrival_scale']:.1f}"]
        for name in algorithms:
            item = row.get(name, {})
            res = fmt_num(item.get("Res"), 3)
            raw_cost = item.get("J")
            cost = "-" if raw_cost is not None and raw_cost < 0 else fmt_num(raw_cost, 2)
            cells.append(f"Res {res}, J {cost}")
        obs = ""
        if len(algorithms) >= 2:
            a0, a1 = algorithms[0], algorithms[1]
            j0 = row.get(a0, {}).get("J")
            j1 = row.get(a1, {}).get("J")
            r0 = row.get(a0, {}).get("Res")
            r1 = row.get(a1, {}).get("Res")
            if j0 is not None and j1 is not None and j0 >= 0 and j1 >= 0:
                if abs(j1 - j0) < 1e-9:
                    obs = f"{a1} matches {a0} quality"
                elif j1 < j0:
                    obs = f"{a1} improves quality"
                else:
                    obs = f"{a1} worsens quality"
                if r0 is not None and r1 is not None:
                    obs += " and is faster" if r1 < r0 else " but is slower"
        cells.append(obs)
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def build_latex_table(rows: list[dict[str, Any]], algorithms: list[str]) -> str:
    col_spec = "lcc" + "rr" * len(algorithms)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Sensitivity Comparison under Density and Arrival-Time Scaling}",
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
        cells = [row["problem"].replace(".json", "").upper(), row["density"], f"{row['arrival_scale']:.1f}"]
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
    fields = ["problem", "density", "arrival_scale"]
    for name in algorithms:
        fields.extend([f"{name}_Res", f"{name}_J", f"{name}_wall", f"{name}_return_code"])
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            flat = {key: row[key] for key in ("problem", "density", "arrival_scale")}
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
    scales = args.arrival_scale or [1.0, 0.9, 0.8, 0.7, 0.6]
    source_dir = (root / args.source_dir).resolve()
    base_out_dir = (root / args.output_dir).resolve()
    base_out_dir.mkdir(parents=True, exist_ok=True)
    out_dir = base_out_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    out_dir.mkdir(parents=True, exist_ok=False)

    rows: list[dict[str, Any]] = []
    raw_results: list[dict[str, Any]] = []
    tmp_dir = out_dir / "generated_instances"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for problem in problems:
        src = source_dir / problem
        for density in densities:
            for scale in scales:
                src = resolve_source_path(root, source_dir, problem, density, args.density_source_dirs)
                density_arg = "d100" if args.density_source_dirs else density
                data_path = prepare_instance(src, tmp_dir, density_arg, float(scale))
                row: dict[str, Any] = {
                    "problem": problem,
                    "density": density,
                    "arrival_scale": float(scale),
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
                            "arrival_scale": float(scale),
                            "algorithm": name,
                            "bin_path": bin_path,
                            "data_path": str(data_path),
                            **item,
                            "stdout": result.get("stdout"),
                            "stderr": result.get("stderr"),
                        }
                    )
                rows.append(row)
                (out_dir / "arrival_scale_table_partial.json").write_text(
                    json.dumps(
                        {
                            "output_dir": str(out_dir),
                            "algorithms": algorithms,
                            "problems": problems,
                            "densities": densities,
                            "arrival_scales": scales,
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
        "arrival_scales": scales,
        "rows": rows,
        "raw_results": raw_results,
    }
    (out_dir / "arrival_scale_table_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    algorithms_list = list(algorithms)
    (out_dir / "arrival_scale_table.md").write_text(
        build_markdown_table(rows, algorithms_list),
        encoding="utf-8",
    )
    (out_dir / "arrival_scale_compact.md").write_text(
        build_compact_markdown(rows, algorithms_list),
        encoding="utf-8",
    )
    (out_dir / "arrival_scale_table.tex").write_text(
        build_latex_table(rows, algorithms_list),
        encoding="utf-8",
    )
    write_csv(out_dir / "arrival_scale_table.csv", rows, algorithms_list)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Res/J tables under arrival-time scaling.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--source-dir", default="solomon_benchmark")
    parser.add_argument("--density-source-dirs", action="store_true", help="Read solomon_benchmark_d25/d50/d75 by density when available.")
    parser.add_argument("--output-dir", default="eoh_go_workspace/reports/tables/arrival_scale")
    parser.add_argument("--problem", action="append")
    parser.add_argument("--density", action="append")
    parser.add_argument("--arrival-scale", action="append", type=float)
    parser.add_argument("--algorithm", action="append", help="Algorithm as NAME=path/to/bin.exe")
    parser.add_argument("--sim-time-multi", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    payload = run_table(args)
    print(build_markdown_table(payload["rows"], list(payload["algorithms"])))
    print(f"Wrote table files to {payload['output_dir']}")


if __name__ == "__main__":
    main()
