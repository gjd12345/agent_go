from __future__ import annotations

import argparse
import json
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


def run_smoke(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = (root / args.output_dir / f"run_{run_tag}").resolve()
    out_dir.mkdir(parents=True, exist_ok=False)

    cfg = EOHConfig(
        agent_eoh_root=str(root / "Agent_EOH"),
        exp_output_path=str(out_dir / "agent_eoh_results"),
        problem_name="mixer_split",
        target_function="SplitOrders",
        llm_model=args.llm_model,
        ec_n_pop=args.generations,
        ec_pop_size=args.pop_size,
        eva_timeout=args.eva_timeout,
        run_timeout_s=args.run_timeout_s,
        use_rag_context=args.use_rag_context,
        rag_context_path=args.rag_context_path or "",
        rag_mode=args.rag_mode,
        rag_top_k=args.rag_top_k,
        rag_max_chars=args.rag_max_chars,
    )
    result = run_v0_eoh(cfg)
    population = result.get("population", []) if isinstance(result, dict) else []
    objectives = [_safe_float(item.get("objective")) for item in population if isinstance(item, dict)]
    valid = [x for x in objectives if x is not None and x < 1e8]
    best_objective = min(valid) if valid else None
    summary = {
        "problem_name": "mixer_split",
        "target": "SplitOrders",
        "run_tag": run_tag,
        "eoh_ok": result.get("ok") if isinstance(result, dict) else False,
        "population_size": len(population) if isinstance(population, list) else 0,
        "valid_candidates": len(valid),
        "best_objective": best_objective,
        "population_file": result.get("population_file") if isinstance(result, dict) else None,
        "rag_trace": result.get("rag_trace") if isinstance(result, dict) else None,
    }
    rag_trace = summary["rag_trace"] if isinstance(summary["rag_trace"], dict) else None
    summary["rag_context_chars"] = rag_trace.get("rag_context_chars") if rag_trace else None
    summary["rag_global_items"] = rag_trace.get("rag_global_items") if rag_trace else []
    (out_dir / "mixer_split_smoke_summary.json").write_text(
        json.dumps(summary, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", type=Path, default=Path("eoh_go_workspace/reports/tables/mixer_split_smoke"))
    parser.add_argument("--llm-model", default="deepseek-v4-pro")
    parser.add_argument("--generations", type=int, default=1)
    parser.add_argument("--pop-size", type=int, default=4)
    parser.add_argument("--eva-timeout", type=int, default=120)
    parser.add_argument("--run-timeout-s", type=int, default=30)
    parser.add_argument("--use-rag-context", action="store_true")
    parser.add_argument("--rag-context-path", default="")
    parser.add_argument("--rag-mode", choices=["history", "literature", "mixed"], default="mixed")
    parser.add_argument("--rag-top-k", type=int, default=0)
    parser.add_argument("--rag-max-chars", type=int, default=1500)
    run_smoke(parser.parse_args())


if __name__ == "__main__":
    main()
