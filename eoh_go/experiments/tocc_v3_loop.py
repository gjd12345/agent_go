"""TOCC V3 — bounded auto-loop pilot.

max_iterations=2, gen≤1, runs≤4. Proposer cannot modify budget.
Human confirmation required before paid API execution.

Flow:
  trace_0 → agent propose → gatekeeper → manifest run → trace_1
  trace_1 → agent propose → gatekeeper → manifest run → trace_2
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def run_v3_loop(
    start_trace_path: str,
    *,
    problem: str,
    available_cards: list[str],
    output_dir: str,
    max_iterations: int = 2,
    dry_run: bool = True,
) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    current_trace = start_trace_path

    for iteration in range(1, max_iterations + 1):
        print(f"\n=== V3 iteration {iteration}/{max_iterations} ===")

        # Step 1: Agent propose (V1 rule-based for dry-run, V2 LLM for real)
        if dry_run:
            cmd = [
                sys.executable, "-m", "eoh_go.experiments.operator_card_controller",
                "--trace", current_trace,
            ]
        else:
            cmd = [
                sys.executable, "-m", "eoh_go.experiments.tocc_v2_pipeline",
                "--trace", current_trace,
                "--problem", problem,
                "--available-cards", ",".join(available_cards),
            ]
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=120)
        if result.returncode != 0:
            history.append({"iteration": iteration, "error": "proposer failed", "stderr": result.stderr[-500:]})
            break

        if dry_run:
            v1 = json.loads(result.stdout)
            proposal_result = {
                "accepted": True,
                "safe_arm": {
                    "name": f"v1_{v1.get('diagnosis','')}",
                    "runner_arm": "literature_rag",
                    "context_strategy": "tocc_selected_cards",
                    "rag_query": v1.get("recommended_query", ""),
                    "selected_card_ids": v1.get("recommended_cards", []),
                },
            }
            print(f"[V1 DIAGNOSIS] {v1.get('diagnosis')} -> {v1.get('recommended_cards')}")
        else:
            proposal_result = json.loads(result.stdout)
            print(f"[V2 PROPOSE] from {current_trace}")
            break
        proposal_result = json.loads(result.stdout)
        history.append({"iteration": iteration, "phase": "proposed", "result": proposal_result})

        if not proposal_result.get("accepted"):
            print(f"[REJECTED] {proposal_result.get('gatekeeper', {}).get('violations')}")
            break

        safe_arm = proposal_result["safe_arm"]
        cards = safe_arm["selected_card_ids"]
        query = safe_arm["rag_query"]

        # Step 2: Write mini-manifest
        suite = f"v3_pilot_iter{iteration}"
        manifest_path = Path(output_dir) / f"{suite}.json"
        manifest = {
            "suite": suite,
            "model": "JoyAI-LLM-Pro",
            "problems": [problem],
            "arms": [safe_arm],
            "generations": [0],
            "pop_size": 4,
            "repeats": 1,
            "max_runs": 1,
            "max_llm_calls_estimate": 8,
            "require_confirm_for_real_run": True,
            "operators": "i1",
            "run_timeout_s": 1800,
            "rag": {"top_k": 2, "max_chars": 2500},
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        print(f"[MANIFEST] {manifest_path}")

        if dry_run:
            print(f"[DRY] Would run: cards={cards}, query={query}")
            dm_cmd = [
                sys.executable, "-m", "eoh_go.experiments.run_experiment_manifest",
                "--manifest", str(manifest_path),
                "--output-dir", output_dir,
                "--dry-run",
            ]
            subprocess.run(dm_cmd, text=True, timeout=30)
            current_trace = "(would be new trace from this run)"
            continue

        # Step 3: Run experiment
        print(f"[RUN] cards={cards}")
        run_cmd = [
            sys.executable, "-m", "eoh_go.experiments.run_experiment_manifest",
            "--manifest", str(manifest_path),
            "--output-dir", output_dir,
            "--force",
        ]
        proc = subprocess.run(run_cmd, text=True, capture_output=True, timeout=2100)
        history[-1]["run_status"] = "ok" if proc.returncode == 0 else f"exit_{proc.returncode}"

        # Step 4: Find new trace
        suite_dir = Path(output_dir) / suite
        index_path = suite_dir / "run_index.json"
        if index_path.exists():
            idx = json.loads(index_path.read_text())
            if idx:
                new_run = idx[0]
                new_summary = Path(new_run["output_dir"]) / "official_eoh_run_summary.json"
                if new_summary.exists():
                    current_trace = str(new_summary)
                    history[-1]["new_trace"] = str(new_summary)
                    history[-1]["best_objective"] = new_run.get("best_objective")
                    history[-1]["valid_candidates"] = new_run.get("valid_candidates")
                    print(f"[OBSERVE] best={new_run.get('best_objective')}, valid={new_run.get('valid_candidates')}")
                else:
                    history[-1]["error"] = "summary not found"
                    break
            else:
                history[-1]["error"] = "run_index empty"
                break
        else:
            history[-1]["error"] = "run_index not found"
            break

        time.sleep(1)

    return history


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="TOCC V3 bounded auto-loop pilot")
    parser.add_argument("--trace", required=True, help="Starting trace (official_eoh_run_summary.json)")
    parser.add_argument("--problem", required=True)
    parser.add_argument("--cards", required=True, help="Comma-separated available card IDs")
    parser.add_argument("--output-dir", default="eoh_go_workspace/reports/auto_experiment_reports/v3_pilot")
    parser.add_argument("--max-iterations", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true", help="Print plan, do not execute")
    args = parser.parse_args()

    available = [c.strip() for c in args.cards.split(",")]
    history = run_v3_loop(
        args.trace,
        problem=args.problem,
        available_cards=available,
        output_dir=args.output_dir,
        max_iterations=args.max_iterations,
        dry_run=args.dry_run,
    )

    out = Path(args.output_dir) / "v3_loop_history.json"
    out.write_text(json.dumps(history, ensure_ascii=False, indent=2))
    print(f"\nLoop history: {out}")


if __name__ == "__main__":
    main()
