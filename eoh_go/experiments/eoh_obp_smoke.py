from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from eoh_go.eoh_runner import EOHConfig, run_v0_eoh


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _best_valid(population: list[dict[str, Any]]) -> dict[str, Any] | None:
    ranked: list[tuple[float, int, dict[str, Any]]] = []
    for index, item in enumerate(population):
        objective = _safe_float(item.get("objective")) if isinstance(item, dict) else None
        code = item.get("code") if isinstance(item, dict) else None
        if objective is None or objective >= 1e8 or not isinstance(code, str) or "func ScoreBin" not in code:
            continue
        ranked.append((objective, index, item))
    if not ranked:
        return None
    ranked.sort(key=lambda row: (row[0], row[1]))
    return ranked[0][2]


def _seed_objective(root: Path) -> float | None:
    example_root = root / "Agent_EOH" / "eoh" / "src" / "eoh" / "examples" / "user_bin_packing_go"
    sys.path.insert(0, str(example_root))
    try:
        from prob_bin_packing_go import Evaluation

        seed = json.loads((example_root / "seeds_bin_packing_go.json").read_text(encoding="utf-8"))[0]["code"]
        return _safe_float(Evaluation().evaluate(seed))
    finally:
        try:
            sys.path.remove(str(example_root))
        except ValueError:
            pass


def _latest_offspring_audit(result: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    population_file = result.get("population_file") if isinstance(result, dict) else None
    if not population_file:
        return {}, None
    results_dir = Path(population_file).resolve().parents[1]
    def generation_index(path: Path) -> int:
        matched = re.search(r"offspring_audit_generation_(\d+)\.json$", path.name)
        return int(matched.group(1)) if matched else -1

    audit_files = sorted((results_dir / "offsprings").glob("offspring_audit_generation_*.json"), key=generation_index)
    if not audit_files:
        return {}, None
    audit_file = audit_files[-1]
    try:
        audit = json.loads(audit_file.read_text(encoding="utf-8"))
    except Exception:
        return {}, str(audit_file)
    return audit if isinstance(audit, dict) else {}, str(audit_file)


def run_smoke(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = (root / args.output_dir / f"run_{run_tag}").resolve()
    out_dir.mkdir(parents=True, exist_ok=False)

    cfg = EOHConfig(
        agent_eoh_root=str(root / "Agent_EOH"),
        exp_output_path=str(out_dir / "agent_eoh_results"),
        problem_name="bin_packing_online",
        target_function="ScoreBin",
        llm_model=args.llm_model,
        ec_n_pop=args.generations,
        ec_pop_size=args.pop_size,
        eva_timeout=args.eva_timeout,
        run_timeout_s=args.run_timeout_s,
        use_rag_context=args.use_rag_context,
        rag_context_path=args.rag_context_path or "",
        rag_mode=args.rag_mode,
        rag_top_k=args.rag_top_k,
        rag_query=args.rag_query,
        rag_max_chars=args.rag_max_chars,
        rag_include_warnings=not args.no_rag_warnings,
    )
    result = run_v0_eoh(cfg)
    population = result.get("population", []) if isinstance(result, dict) else []
    if not isinstance(population, list):
        population = []
    best = _best_valid(population)
    best_objective = _safe_float(best.get("objective")) if best else None
    offspring_audit, offspring_audit_file = _latest_offspring_audit(result if isinstance(result, dict) else {})
    summary = {
        "problem_name": "bin_packing_online",
        "target": "ScoreBin",
        "run_tag": run_tag,
        "eoh_ok": result.get("ok") if isinstance(result, dict) else False,
        "seed_objective": _seed_objective(root),
        "population_size": len(population),
        "valid_candidates": sum(
            1
            for item in population
            if isinstance(item, dict)
            and _safe_float(item.get("objective")) is not None
            and _safe_float(item.get("objective")) < 1e8
            and "func ScoreBin" in str(item.get("code", ""))
        ),
        "best_objective": best_objective,
        "best_gap_to_lb": best_objective,
        "best_code": best.get("code") if best else None,
        "population_file": result.get("population_file") if isinstance(result, dict) else None,
        "offspring_audit_file": offspring_audit_file,
        "rag_trace": result.get("rag_trace") if isinstance(result, dict) else None,
    }
    summary["raw_offspring_count"] = offspring_audit.get("raw_offspring_count")
    summary["raw_with_code_count"] = offspring_audit.get("raw_with_code_count")
    summary["raw_penalty_count"] = offspring_audit.get("raw_penalty_count")
    summary["raw_valid_candidates"] = offspring_audit.get("raw_valid_candidate_count")
    summary["unique_code_count"] = offspring_audit.get("unique_code_count")
    summary["unique_objective_count"] = offspring_audit.get("unique_objective_count")
    summary["final_population_size"] = offspring_audit.get("survivor_population_size", len(population))
    summary["survivor_objectives"] = offspring_audit.get("survivor_objectives", [])
    summary["survivor_drop_reason"] = offspring_audit.get(
        "survivor_drop_reason",
        "missing_audit" if not offspring_audit else None,
    )
    rag_trace = summary["rag_trace"] if isinstance(summary["rag_trace"], dict) else None
    summary["rag_context_chars"] = rag_trace.get("rag_context_chars") if rag_trace else None
    summary["rag_context_truncated"] = rag_trace.get("rag_context_truncated") if rag_trace else None
    summary["rag_global_items_available"] = rag_trace.get("rag_global_items_available") if rag_trace else []
    summary["rag_global_items_injected"] = rag_trace.get("rag_global_items_injected") if rag_trace else []
    summary["rag_global_items"] = rag_trace.get("rag_global_items") if rag_trace else []
    summary["rag_selected_items"] = rag_trace.get("rag_selected_items") if rag_trace else []
    (out_dir / "eoh_obp_smoke_summary.json").write_text(
        json.dumps(summary, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", type=Path, default=Path("eoh_go_workspace/reports/tables/eoh_obp_smoke"))
    parser.add_argument("--llm-model", default="deepseek-v4-pro")
    parser.add_argument("--generations", type=int, default=1)
    parser.add_argument("--pop-size", type=int, default=4)
    parser.add_argument("--eva-timeout", type=int, default=120)
    parser.add_argument("--run-timeout-s", type=int, default=30)
    parser.add_argument("--use-rag-context", action="store_true")
    parser.add_argument("--rag-context-path", default="")
    parser.add_argument("--rag-mode", choices=["history", "literature", "mixed"], default="literature")
    parser.add_argument("--rag-top-k", type=int, default=3)
    parser.add_argument("--rag-query", default="")
    parser.add_argument("--rag-max-chars", type=int, default=2500)
    parser.add_argument("--no-rag-warnings", action="store_true")
    run_smoke(parser.parse_args())


if __name__ == "__main__":
    main()
