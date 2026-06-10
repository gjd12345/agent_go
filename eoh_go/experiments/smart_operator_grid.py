"""
Grid experiment runner for Smart EOH Operator.

Runs the Smart Operator across instance × density × arrival_scale cells.
Each cell: SA baseline → Smart Operator (LLM mutation + self-repair + guard).

WARNING: Each cell runs generations × pop_size LLM calls (+ repair calls).
75 cells × 5 gens × 4 candidates = 1500+ LLM calls. Run with --dry-run first.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from ..operator import SmartOperator


def _estimate_cost(
    cells: int, generations: int, pop_size: int, mutation_mode: str = "llm",
) -> dict[str, Any]:
    """Estimate LLM calls and approximate time."""
    if mutation_mode == "templates":
        mutation_calls = 0
    elif mutation_mode == "hybrid":
        template_count = max(1, (pop_size + 1) // 2)
        mutation_calls = generations * max(pop_size - template_count, 0)
    else:
        mutation_calls = generations * pop_size

    llm_calls_per_cell = mutation_calls
    if mutation_mode != "templates":
        llm_calls_per_cell += generations * pop_size * 0.5  # ~50% need repair
    total_llm = int(cells * llm_calls_per_cell)
    est_minutes = total_llm * 5 / 60  # rough: 5s per LLM call
    return {
        "cells": cells,
        "generations": generations,
        "pop_size": pop_size,
        "mutation_mode": mutation_mode,
        "est_llm_calls": total_llm,
        "est_minutes": round(est_minutes, 0),
        "est_hours": round(est_minutes / 60, 1),
    }


def run_smart_grid(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    densities = args.density or ["d25", "d50", "d75"]
    scales = args.arrival_scale or [1.0, 0.9, 0.8, 0.7, 0.6]
    problems = args.problem or ["rc101.json", "rc102.json", "rc103.json", "rc104.json", "rc105.json"]

    # Limit cells if specified
    if args.max_cells:
        from itertools import product
        all_cells = list(product(problems, densities, scales))
        all_cells = all_cells[:args.max_cells]
        problems = sorted(set(c[0] for c in all_cells))
        # filter to only included problems/densities/scales per cell

    total_cells = len(problems) * len(densities) * len(scales)
    if args.max_cells:
        total_cells = min(total_cells, args.max_cells)

    # Cost estimate
    est = _estimate_cost(total_cells, args.generations, args.pop_size, args.mutation_mode)
    print("=" * 60)
    print("Smart Operator Grid — Cost Estimate")
    print(f"  Cells: {total_cells}")
    print(f"  Generations/cell: {args.generations}")
    print(f"  Pop size: {args.pop_size}")
    print(f"  Mutation mode: {args.mutation_mode}")
    print(f"  Est. LLM calls: {est['est_llm_calls']}")
    print(f"  Est. time: {est['est_minutes']} min ({est['est_hours']} h)")
    print(f"  API endpoint: {os.environ.get('DEEPSEEK_API_ENDPOINT', 'api.deepseek.com')}")
    print(f"  Model: {args.llm_model}")
    print("=" * 60)

    if args.dry_run:
        print("DRY RUN — exiting without execution.")
        return {"dry_run": True, "estimate": est}

    # Check API key
    if args.mutation_mode in {"llm", "hybrid"} and not os.environ.get("DEEPSEEK_API_KEY") and not args.api_key:
        print("ERROR: Set DEEPSEEK_API_KEY environment variable or pass --api-key")
        sys.exit(1)

    # Setup output
    run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = (root / args.output_dir).resolve() / f"run_{run_tag}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save SA baseline if available
    sa_bin = root / "mainbin_sa.exe"
    if not sa_bin.exists():
        print("WARNING: mainbin_sa.exe not found, baseline comparison disabled")

    rows: list[dict[str, Any]] = []
    cell_count = 0

    for problem in problems:
        for density in densities:
            for scale in scales:
                cell_count += 1
                if args.max_cells and cell_count > args.max_cells:
                    break

                cell_tag = (f"{problem.replace('.json', '')}_{density}"
                           f"_t{scale:.1f}").replace(".", "p")
                print(f"\n{'='*60}")
                print(f"Cell {cell_count}/{total_cells}: {cell_tag}")
                print(f"{'='*60}")

                # Run SA baseline
                seed_j = None
                seed_res = None
                if sa_bin.exists():
                    import subprocess
                    import tempfile
                    import shutil

                    # Find data file
                    src_dir = root / f"solomon_benchmark_{density}"
                    if not src_dir.exists():
                        src_dir = root / "solomon_benchmark"
                    data_file = src_dir / problem if src_dir.exists() else None

                    if data_file and data_file.exists():
                        tmp = tempfile.mkdtemp(prefix="sa_baseline_")
                        try:
                            shutil.copy2(str(data_file), os.path.join(tmp, problem))
                            proc = subprocess.run(
                                [str(sa_bin), os.path.join(tmp, problem), str(args.sim_time_multi)],
                                cwd=tmp, capture_output=True, text=True,
                                timeout=args.run_timeout_s,
                            )
                            output = (proc.stdout or "") + "\n" + (proc.stderr or "")
                            for line in output.splitlines():
                                lower = line.lower().strip()
                                if lower.startswith("final cost"):
                                    try:
                                        seed_j = float(lower.split("final cost", 1)[1].strip())
                                    except (ValueError, IndexError):
                                        pass
                                if lower.startswith("res "):
                                    try:
                                        seed_res = float(lower.split("res", 1)[1].strip())
                                    except (ValueError, IndexError):
                                        pass
                        except Exception as e:
                            print(f"  SA baseline failed: {e}")
                        finally:
                            shutil.rmtree(tmp, ignore_errors=True)

                print(f"  SA baseline: J={seed_j}, Res={seed_res}")

                # Run Smart Operator
                cell_start = datetime.now()
                try:
                    op = SmartOperator(
                        project_root=str(root),
                        api_key=args.api_key or "",
                        api_endpoint=os.environ.get("DEEPSEEK_API_ENDPOINT", "api.deepseek.com"),
                        model=args.llm_model,
                        pop_size=args.pop_size,
                        generations=args.generations,
                        run_timeout_s=args.run_timeout_s,
                        dataset_density=density,
                        arrival_scale=scale,
                        use_density_source_dirs=args.use_density_source_dirs,
                        baseline_cost=seed_j,
                        mutation_mode=args.mutation_mode,
                    )
                    result = op.run()
                except Exception as e:
                    print(f"  Smart Operator failed: {e}")
                    result = {"error": str(e)}

                cell_elapsed = (datetime.now() - cell_start).total_seconds()

                # Build row
                row = {
                    "problem": problem,
                    "density": density,
                    "arrival_scale": float(scale),
                    "seed_Res": seed_res,
                    "seed_J": seed_j,
                    "cell_elapsed_s": round(cell_elapsed, 1),
                    "operator_ok": "error" not in result,
                    "operator_error": result.get("error", ""),
                    "best_cost": result.get("best_cost"),
                    "best_generation": result.get("best_generation"),
                    "improvement_pct": result.get("improvement_pct"),
                    "total_elapsed_s": result.get("total_elapsed_s"),
                    "memory_total_attempts": result.get("failure_memory", {}).get("total_attempts", 0),
                    "memory_total_failures": result.get("failure_memory", {}).get("total_failures", 0),
                    "memory_top_failures": json.dumps(
                        result.get("failure_memory", {}).get("top_failures", [])
                    ),
                    "generation_count": len(result.get("generation_log", [])),
                }

                # Per-generation summary
                for g in result.get("generation_log", []):
                    gen_num = g.get("gen", "?")
                    row[f"gen{gen_num}_best"] = g.get("best_fitness")
                    row[f"gen{gen_num}_compiled_ok"] = g.get("compiled_ok")
                    row[f"gen{gen_num}_eval_ok"] = g.get("evaluated_ok")
                    row[f"gen{gen_num}_repairs"] = g.get("repair_count")

                rows.append(row)

                # Save partial results
                partial = {"rows": rows, "config": vars(args), "run_tag": run_tag}
                (out_dir / "smart_grid_partial.json").write_text(
                    json.dumps(partial, ensure_ascii=False, indent=2), encoding="utf-8"
                )

                # Print cell summary
                print(f"  Cell result: best_cost={result.get('best_cost')}, "
                      f"improvement={result.get('improvement_pct')}")
                print(f"  Cell elapsed: {cell_elapsed:.0f}s")

            if args.max_cells and cell_count >= args.max_cells:
                break
        if args.max_cells and cell_count >= args.max_cells:
            break

    # Final report
    payload = {
        "output_dir": str(out_dir),
        "run_tag": run_tag,
        "config": vars(args),
        "rows": rows,
    }
    (out_dir / "smart_grid_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    md = build_summary_markdown(rows, args)
    (out_dir / "smart_grid_summary.md").write_text(md, encoding="utf-8")
    print("\n" + md)
    print(f"\nResults written to {out_dir}")
    return payload


def build_summary_markdown(rows: list[dict[str, Any]], args: argparse.Namespace) -> str:
    lines = [
        "# Smart Operator Grid Results",
        "",
        f"**Generations**: {args.generations}, **Pop size**: {args.pop_size}",
        f"**Model**: {args.llm_model}",
        f"**Cells**: {len(rows)}",
        "",
        "## Results",
        "",
        "| Inst. | d | t | SA J | Best J | Δ J | Δ% | Best Gen | Elapsed | Compiled | Eval OK | Repairs |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    improved = 0
    tie = 0
    worse = 0
    excluded = 0

    for row in rows:
        sa_j = row.get("seed_J")
        best_j = row.get("best_cost")
        imp_pct = row.get("improvement_pct")

        # Classify
        if best_j is None or sa_j is None:
            cls = "excluded"
            excluded += 1
        elif imp_pct is not None and imp_pct < -1:
            cls = "improved"
            improved += 1
        elif imp_pct is not None and imp_pct > 1:
            cls = "worse"
            worse += 1
        else:
            cls = "tie"
            tie += 1

        delta_j = ""
        if best_j is not None and sa_j is not None:
            delta_j = f"{best_j - sa_j:+.2f}"

        compiled_ok = sum(
            row.get(f"gen{g}_compiled_ok", 0) or 0
            for g in range(1, (args.generations or 1) + 1)
        )
        eval_ok = sum(
            row.get(f"gen{g}_eval_ok", 0) or 0
            for g in range(1, (args.generations or 1) + 1)
        )
        repairs = sum(
            row.get(f"gen{g}_repairs", 0) or 0
            for g in range(1, (args.generations or 1) + 1)
        )

        cells = [
            str(row["problem"]).replace(".json", "").upper(),
            str(row["density"]),
            f"{float(row['arrival_scale']):.1f}",
            f"{sa_j:.2f}" if sa_j is not None else "-",
            f"{best_j:.2f}" if best_j is not None else "-",
            delta_j,
            f"{imp_pct:+.1f}%" if imp_pct is not None else "-",
            str(row.get("best_generation", "-")),
            f"{row.get('cell_elapsed_s', 0):.0f}s",
            str(compiled_ok),
            str(eval_ok),
            str(repairs),
        ]
        lines.append("| " + " | ".join(cells) + " |")

    lines.extend([
        "",
        "## Summary",
        "",
        f"| Class | Count |",
        f"|---|---|",
        f"| improved | {improved} |",
        f"| tie | {tie} |",
        f"| worse | {worse} |",
        f"| excluded | {excluded} |",
        f"| **total** | **{len(rows)}** |",
    ])

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Smart EOH Operator over density × arrival-scale grid."
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", default="eoh_go_workspace/reports/tables/smart_operator_grid")
    parser.add_argument("--problem", action="append", help="e.g. rc101.json (repeatable)")
    parser.add_argument("--density", action="append", help="e.g. d25 (repeatable)")
    parser.add_argument("--arrival-scale", action="append", type=float, help="e.g. 1.0 (repeatable)")
    parser.add_argument("--use-density-source-dirs", action="store_true")
    parser.add_argument("--api-key", default="", help="DeepSeek API key")
    parser.add_argument("--llm-model", default="deepseek-v4-flash")
    parser.add_argument(
        "--mutation-mode",
        choices=["llm", "templates", "hybrid"],
        default="llm",
        help="Candidate generator: free-form LLM, bounded templates, or templates plus LLM",
    )
    parser.add_argument("--generations", type=int, default=3, help="Generations per cell")
    parser.add_argument("--pop-size", type=int, default=4, help="Population size")
    parser.add_argument("--sim-time-multi", type=int, default=10)
    parser.add_argument("--run-timeout-s", type=int, default=60)
    parser.add_argument("--max-cells", type=int, default=0, help="Limit to N cells (0=all)")
    parser.add_argument("--dry-run", action="store_true", help="Show estimate without running")
    args = parser.parse_args()

    # Default: run a small test first
    if not args.problem and not args.density and not args.arrival_scale:
        args.problem = ["rc101.json"]
        args.density = ["d25"]
        args.arrival_scale = [1.0]

    run_smart_grid(args)


if __name__ == "__main__":
    main()
