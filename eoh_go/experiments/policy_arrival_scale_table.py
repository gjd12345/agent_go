from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..benchmark import parse_numeric_cost, run_test
from .arrival_scale_table import prepare_instance, resolve_source_path
from .efficiency_table import best_cost_name, best_res_name, fmt_num


def _is_dynamic_instance(path: Path) -> bool:
    data = json.loads(path.read_text(encoding="utf-8"))
    return len(data.get("batch", [])) > 1


def _resolve_path(root: Path, raw_path: str) -> str:
    path = Path(raw_path)
    if not path.is_absolute():
        path = root / path
    return str(path.resolve())


def build_markdown_table(rows: list[dict[str, Any]], algorithms: list[str]) -> str:
    header = ["Inst.", "d", "t", "Policy"]
    for name in algorithms:
        header.extend([f"{name} Res.", f"{name} J"])
    lines = ["| " + " | ".join(header) + " |"]
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for row in rows:
        best_j = best_cost_name(row, algorithms)
        best_r = best_res_name(row, algorithms)
        cells = [row["problem"], row["density"], f"{row['arrival_scale']:.1f}", row["policy_kind"]]
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
    col_spec = "lccc" + "rr" * len(algorithms)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Experiment-Layer Policy Router under Arrival-Time Scaling}",
        rf"\begin{{tabular}}{{{col_spec}}}",
        r"\toprule",
    ]
    group = ["Inst.", "$d$", "$t$", "Policy"]
    for name in algorithms:
        group.extend([rf"\multicolumn{{2}}{{c}}{{{name}}}"])
    lines.append(" & ".join(group) + r" \\")
    sub = ["", "", "", ""]
    for _ in algorithms:
        sub.extend(["Res.", "$J$"])
    lines.append(" & ".join(sub) + r" \\")
    lines.append(r"\midrule")
    for row in rows:
        best_j = best_cost_name(row, algorithms)
        best_r = best_res_name(row, algorithms)
        cells = [
            row["problem"].replace(".json", "").upper(),
            row["density"],
            f"{row['arrival_scale']:.1f}",
            row["policy_kind"],
        ]
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
    fields = ["problem", "density", "arrival_scale", "policy_kind", "policy_bin"]
    for name in algorithms:
        fields.extend([f"{name}_Res", f"{name}_J", f"{name}_wall", f"{name}_return_code"])
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            flat = {key: row[key] for key in ("problem", "density", "arrival_scale", "policy_kind", "policy_bin")}
            for name in algorithms:
                item = row.get(name, {})
                flat[f"{name}_Res"] = item.get("Res")
                flat[f"{name}_J"] = item.get("J")
                flat[f"{name}_wall"] = item.get("wall")
                flat[f"{name}_return_code"] = item.get("return_code")
            writer.writerow(flat)


def run_table(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    source_dir = (root / args.source_dir).resolve()
    base_out_dir = (root / args.output_dir).resolve()
    base_out_dir.mkdir(parents=True, exist_ok=True)
    out_dir = base_out_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    out_dir.mkdir(parents=True, exist_ok=False)

    sa_bin = _resolve_path(root, args.sa_bin)
    dynamic_policy_bin = _resolve_path(root, args.dynamic_policy_bin)
    static_policy_bin = _resolve_path(root, args.static_policy_bin)
    algorithms = ["SA", "PolicyRouter"]
    problems = args.problem or ["rc101.json"]
    densities = args.density or ["d25", "d50", "d75", "d100"]
    scales = args.arrival_scale or [1.0, 0.9, 0.8, 0.7, 0.6]

    rows: list[dict[str, Any]] = []
    raw_results: list[dict[str, Any]] = []
    tmp_dir = out_dir / "generated_instances"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for problem in problems:
        for density in densities:
            src = resolve_source_path(root, source_dir, problem, density, args.density_source_dirs)
            dynamic = _is_dynamic_instance(src)
            policy_bin = dynamic_policy_bin if dynamic else static_policy_bin
            policy_kind = "dynamic-robust" if dynamic else "static-router"
            density_arg = "d100" if args.density_source_dirs else density
            for scale in scales:
                data_path = prepare_instance(src, tmp_dir, density_arg, float(scale))
                row: dict[str, Any] = {
                    "problem": problem,
                    "density": density,
                    "arrival_scale": float(scale),
                    "policy_kind": policy_kind,
                    "policy_bin": policy_bin,
                }
                for name, bin_path in (("SA", sa_bin), ("PolicyRouter", policy_bin)):
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
                            "policy_kind": policy_kind,
                            **item,
                            "stdout": result.get("stdout"),
                            "stderr": result.get("stderr"),
                        }
                    )
                rows.append(row)
                (out_dir / "policy_arrival_scale_partial.json").write_text(
                    json.dumps(
                        {
                            "output_dir": str(out_dir),
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
        "problems": problems,
        "densities": densities,
        "arrival_scales": scales,
        "rows": rows,
        "raw_results": raw_results,
        "sa_bin": sa_bin,
        "dynamic_policy_bin": dynamic_policy_bin,
        "static_policy_bin": static_policy_bin,
    }
    (out_dir / "policy_arrival_scale_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "policy_arrival_scale_table.md").write_text(
        build_markdown_table(rows, algorithms),
        encoding="utf-8",
    )
    (out_dir / "policy_arrival_scale_table.tex").write_text(
        build_latex_table(rows, algorithms),
        encoding="utf-8",
    )
    write_csv(out_dir / "policy_arrival_scale_table.csv", rows, algorithms)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an experiment-layer policy router under arrival-time scaling.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--source-dir", default="solomon_benchmark")
    parser.add_argument("--density-source-dirs", action="store_true")
    parser.add_argument("--output-dir", default="eoh_go_workspace/reports/tables/policy_arrival_scale")
    parser.add_argument("--problem", action="append")
    parser.add_argument("--density", action="append")
    parser.add_argument("--arrival-scale", action="append", type=float)
    parser.add_argument("--sa-bin", default="mainbin_sa.exe")
    parser.add_argument("--dynamic-policy-bin", default="eoh_go_workspace/generated/bins/eoh_robust_002_sa_exact.exe")
    parser.add_argument("--static-policy-bin", default="eoh_go_workspace/generated/bins/eoh_router_004_density_window_switch.exe")
    parser.add_argument("--sim-time-multi", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    payload = run_table(args)
    print(build_markdown_table(payload["rows"], ["SA", "PolicyRouter"]))
    print(f"Wrote table files to {payload['output_dir']}")


if __name__ == "__main__":
    main()
