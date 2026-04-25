from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..benchmark import parse_numeric_cost, run_test
from ..candidates import add_candidate, load_candidate
from ..eoh_runner import EOHConfig, run_v0_eoh
from ..eoh_runner.candidate_guard import best_raw_candidate, classify_candidate, select_best_candidate
from ..evolution import _prepare_candidate_project
from ..paths import EOHGoPaths
from .arrival_scale_table import prepare_instance, resolve_source_path


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _status_for_item(
    population: list[dict[str, Any]],
    item: dict[str, Any] | None,
    statuses: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if item is None:
        return None
    for status in statuses:
        index = status.get("index")
        if isinstance(index, int) and 0 <= index < len(population) and population[index] is item:
            return status
    return None


def _register_and_build_best(
    root: Path,
    paths: EOHGoPaths,
    *,
    code: str,
    density: str,
    arrival_scale: float,
    run_tag: str,
) -> dict[str, Any]:
    candidate_id = f"eoh_arrival_{density}_t{arrival_scale:.1f}_{run_tag}".replace(".", "p")
    add_candidate(
        paths,
        candidate_id=candidate_id,
        algorithm="agent_eoh_arrival_scale_best",
        target_file="main.go",
        code=code,
        rationale="Best EOH candidate from arrival-scale grid experiment.",
        metadata={
            "origin": "eoh_arrival_grid",
            "strategy_family": "insertships",
            "code_mode": "insertships_only",
            "dataset_density": density,
            "arrival_scale": arrival_scale,
        },
    )
    return _prepare_candidate_project(paths, load_candidate(paths, candidate_id))


def run_grid(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    paths = EOHGoPaths(root=root)
    densities = args.density or ["d25", "d50", "d75", "d100"]
    scales = args.arrival_scale or [1.0, 0.9, 0.8, 0.7, 0.6]
    problems = args.problem or ["rc101.json"]
    source_dir = (root / args.source_dir).resolve()
    base_out_dir = (root / args.output_dir).resolve()
    run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = base_out_dir / f"run_{run_tag}"
    out_dir.mkdir(parents=True, exist_ok=False)
    tmp_dir = out_dir / "generated_instances"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    raw: list[dict[str, Any]] = []
    for problem in problems:
        for density in densities:
            src = resolve_source_path(root, source_dir, problem, density, args.use_density_source_dirs)
            density_arg = "d100" if args.use_density_source_dirs else density
            for scale in scales:
                cell_tag = f"{problem.replace('.json', '')}_{density}_t{scale:.1f}".replace(".", "p")
                cell_out = out_dir / "cells" / cell_tag
                eoh_out = cell_out / "agent_eoh_results"
                eoh_out.mkdir(parents=True, exist_ok=True)

                cfg = EOHConfig(
                    agent_eoh_root=str(root / "Agent_EOH"),
                    exp_output_path=str(eoh_out),
                    llm_model=args.llm_model,
                    ec_n_pop=args.generations,
                    ec_pop_size=args.pop_size,
                    sim_time_multi=args.sim_time_multi,
                    max_instances=args.max_instances,
                    eva_timeout=args.eva_timeout,
                    run_timeout_s=args.run_timeout_s,
                    objective_use_composite=args.objective_use_composite,
                    objective_res_weight=args.objective_res_weight,
                    dataset_density=density,
                    sim_time_interval=args.sim_time_interval,
                    arrival_scale=scale,
                    use_density_source_dirs=args.use_density_source_dirs,
                    use_sa_seed_as_init=True,
                )
                result = run_v0_eoh(cfg)
                population = result.get("population", []) if isinstance(result, dict) else []

                data_path = prepare_instance(src, tmp_dir, density_arg, float(scale))
                sa_result = run_test(str((root / "mainbin_sa.exe").resolve()), str(data_path), args.sim_time_multi, timeout_seconds=args.run_timeout_s)
                seed_res = sa_result.get("first_response_time")
                seed_j = parse_numeric_cost(sa_result.get("cost"))
                population_items = population if isinstance(population, list) else []
                raw_best = best_raw_candidate(population_items)
                filtered_best, candidate_statuses = select_best_candidate(
                    population_items,
                    seed_j=seed_j,
                    invalid_threshold=args.invalid_threshold,
                    suspicious_low_ratio=args.suspicious_low_ratio,
                )
                best = filtered_best or raw_best
                selected_kind = "filtered" if filtered_best else ("raw_fallback" if raw_best else None)
                raw_status = _status_for_item(population_items, raw_best, candidate_statuses)
                filtered_status = _status_for_item(population_items, filtered_best, candidate_statuses)

                best_eval: dict[str, Any] = {
                    "candidate_id": None,
                    "build_ok": False,
                    "Res": None,
                    "J": None,
                    "return_code": None,
                    "bin_path": None,
                }
                build_info = None
                if best:
                    build_info = _register_and_build_best(
                        root,
                        paths,
                        code=best["code"],
                        density=density,
                        arrival_scale=float(scale),
                        run_tag=cell_tag + "_" + run_tag,
                    )
                    best_eval["candidate_id"] = build_info.get("candidate_id")
                    best_eval["build_ok"] = bool(build_info.get("build_ok"))
                    best_eval["bin_path"] = build_info.get("bin_path")
                    if build_info.get("build_ok"):
                        eoh_eval_result = run_test(build_info["bin_path"], str(data_path), args.sim_time_multi, timeout_seconds=args.run_timeout_s)
                        best_eval.update(
                            {
                                "Res": eoh_eval_result.get("first_response_time"),
                                "J": parse_numeric_cost(eoh_eval_result.get("cost")),
                                "return_code": eoh_eval_result.get("return_code"),
                            }
                        )

                objectives = [_safe_float(item.get("objective")) for item in population_items]
                non_penalty_objectives = [x for x in objectives if x is not None and x < args.invalid_threshold]
                valid_statuses = [status for status in candidate_statuses if status.get("status") == "valid"]
                suspicious_statuses = [status for status in candidate_statuses if status.get("status") == "suspicious"]
                invalid_statuses = [status for status in candidate_statuses if status.get("status") == "invalid"]
                selected_after_eval = None
                if best:
                    selected_after_eval = classify_candidate(
                        best,
                        seed_j=seed_j,
                        candidate_j=best_eval.get("J"),
                        invalid_threshold=args.invalid_threshold,
                        suspicious_low_ratio=args.suspicious_low_ratio,
                    )
                row = {
                    "problem": problem,
                    "density": density,
                    "arrival_scale": float(scale),
                    "eoh_ok": result.get("ok") if isinstance(result, dict) else False,
                    "eoh_duration": result.get("duration") if isinstance(result, dict) else None,
                    "population_file": result.get("population_file") if isinstance(result, dict) else None,
                    "population_size": len(population) if isinstance(population, list) else 0,
                    "valid_candidates": len(valid_statuses),
                    "suspicious_candidates": len(suspicious_statuses),
                    "invalid_candidates": len(invalid_statuses),
                    "non_penalty_candidates": len(non_penalty_objectives),
                    "raw_best_objective": raw_status.get("objective") if raw_status else None,
                    "raw_best_status": raw_status.get("status") if raw_status else None,
                    "raw_best_flags": raw_status.get("flags") if raw_status else None,
                    "filtered_best_objective": filtered_status.get("objective") if filtered_status else None,
                    "filtered_best_status": filtered_status.get("status") if filtered_status else None,
                    "filtered_best_flags": filtered_status.get("flags") if filtered_status else None,
                    "selected_best_kind": selected_kind,
                    "best_objective": filtered_status.get("objective") if filtered_status else (raw_status.get("objective") if raw_status else None),
                    "selected_best_status_after_eval": selected_after_eval.get("status") if selected_after_eval else None,
                    "selected_best_flags_after_eval": selected_after_eval.get("flags") if selected_after_eval else None,
                    "seed_Res": seed_res,
                    "seed_J": seed_j,
                    "best_EOH_Res": best_eval.get("Res"),
                    "best_EOH_J": best_eval.get("J"),
                    "best_candidate_id": best_eval.get("candidate_id"),
                    "best_build_ok": best_eval.get("build_ok"),
                    "data_path": str(data_path),
                }
                rows.append(row)
                raw.append(
                    {
                        "row": row,
                        "eoh_result": result,
                        "raw_best_population_item": raw_best,
                        "filtered_best_population_item": filtered_best,
                        "best_population_item": best,
                        "candidate_statuses": candidate_statuses,
                        "selected_after_eval": selected_after_eval,
                        "build_info": build_info,
                        "best_eval": best_eval,
                    }
                )
                (out_dir / "eoh_arrival_grid_partial.json").write_text(
                    json.dumps({"rows": rows, "raw": raw}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

    payload = {
        "output_dir": str(out_dir),
        "config": vars(args),
        "rows": rows,
        "raw": raw,
    }
    (out_dir / "eoh_arrival_grid_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "eoh_arrival_grid.md").write_text(build_markdown(rows), encoding="utf-8")
    print(build_markdown(rows))
    print(f"Wrote EOH arrival grid to {out_dir}")
    return payload


def build_markdown(rows: list[dict[str, Any]]) -> str:
    header = [
        "Inst.",
        "d",
        "t",
        "Valid",
        "Susp.",
        "Invalid",
        "Seed Res.",
        "Seed J",
        "Best EOH Res.",
        "Best EOH J",
        "Raw Obj.",
        "Filt. Obj.",
        "Selected",
        "Status",
        "Best Candidate",
    ]
    lines = ["| " + " | ".join(header) + " |"]
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for row in rows:
        def f3(v: Any) -> str:
            return "-" if v is None else f"{float(v):.3f}"

        def f2(v: Any) -> str:
            return "-" if v is None else f"{float(v):.2f}"

        cells = [
            str(row["problem"]).replace(".json", "").upper(),
            str(row["density"]),
            f"{float(row['arrival_scale']):.1f}",
            str(row["valid_candidates"]),
            str(row.get("suspicious_candidates", 0)),
            str(row.get("invalid_candidates", 0)),
            f3(row.get("seed_Res")),
            f2(row.get("seed_J")),
            f3(row.get("best_EOH_Res")),
            f2(row.get("best_EOH_J")),
            f3(row.get("raw_best_objective")),
            f3(row.get("filtered_best_objective")),
            str(row.get("selected_best_kind") or "-"),
            str(row.get("selected_best_status_after_eval") or row.get("filtered_best_status") or row.get("raw_best_status") or "-"),
            str(row.get("best_candidate_id") or "-"),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run EOH over density and arrival-scale grid.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--source-dir", default="solomon_benchmark")
    parser.add_argument("--output-dir", default="eoh_go_workspace/reports/tables/eoh_arrival_grid")
    parser.add_argument("--problem", action="append")
    parser.add_argument("--density", action="append")
    parser.add_argument("--arrival-scale", action="append", type=float)
    parser.add_argument("--use-density-source-dirs", action="store_true")
    parser.add_argument("--llm-model", default="deepseek-v4-pro")
    parser.add_argument("--generations", type=int, default=1)
    parser.add_argument("--pop-size", type=int, default=4)
    parser.add_argument("--sim-time-multi", type=int, default=10)
    parser.add_argument("--max-instances", type=int, default=1)
    parser.add_argument("--eva-timeout", type=int, default=120)
    parser.add_argument("--run-timeout-s", type=int, default=60)
    parser.add_argument("--objective-res-weight", type=float, default=0.2)
    parser.add_argument("--objective-use-composite", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--sim-time-interval", type=int, default=1)
    parser.add_argument("--invalid-threshold", type=float, default=1e8)
    parser.add_argument("--suspicious-low-ratio", type=float, default=0.3)
    args = parser.parse_args()
    run_grid(args)


if __name__ == "__main__":
    main()
