from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .config import EOHConfig


_RUNNER_ENV_KEYS = [
    "PYTHONUTF8",
    "PYTHONIOENCODING",
    "EOH_OBJECTIVE_USE_COMPOSITE",
    "EOH_RES_WEIGHT",
    "EOH_RUN_TIMEOUT_S",
    "EOH_RAG_CONTEXT",
]

_RAG_CONTEXT_MAX_BYTES = 50 * 1024
_RAG_CONTEXT_MAX_CHARS = 8000


def _extract_insertships_from_main(main_text: str) -> str:
    import re
    pat = r"func\s+InsertShips\s*\(\s*dispatch\s+Dispatch\s*,\s*oris\s*,\s*dess\s*\[\]Station\s*,\s*total_ship\s+int\s*\)\s*Dispatch\s*\{[\s\S]*?\n\}"
    matched = re.search(pat, main_text)
    if not matched:
        raise ValueError("InsertShips method not found in SA main.go")
    return matched.group(0).strip() + "\n"


def _prepare_sa_seed(example_root: str, project_root: str) -> str:
    sa_main = Path(project_root) / "main.go"
    if not sa_main.exists():
        return str(Path(example_root) / "seeds_insertships_go.json")
    insertships_code = _extract_insertships_from_main(sa_main.read_text(encoding="utf-8"))
    sa_seed_path = Path(example_root) / "seeds_insertships_go_sa.json"
    payload = [
        {
            "algorithm": "SA baseline InsertShips extracted from project root main.go",
            "code": insertships_code,
        }
    ]
    sa_seed_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return str(sa_seed_path)


def _restore_env(saved: dict[str, Optional[str]]) -> None:
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _manual_rag_context_dir(project_root: str) -> Path:
    return (Path(project_root) / "eoh_go_workspace" / "rag" / "manual_contexts").resolve()


def _resolve_manual_rag_context_path(config: EOHConfig, project_root: str) -> Path:
    allowed_dir = _manual_rag_context_dir(project_root)
    configured_path = config.rag_context_path.strip()
    if configured_path:
        raw_path = Path(configured_path)
        context_path = raw_path if raw_path.is_absolute() else allowed_dir / raw_path
    else:
        context_path = allowed_dir / "insertships_v1.txt"

    resolved_path = context_path.resolve()
    try:
        resolved_path.relative_to(allowed_dir)
    except ValueError:
        raise ValueError("RAG context path must stay under eoh_go_workspace/rag/manual_contexts")
    return resolved_path


def _read_manual_rag_context(config: EOHConfig, project_root: str) -> tuple[str, bool]:
    context_path = _resolve_manual_rag_context_path(config, project_root)
    try:
        stat_result = context_path.stat()
    except OSError as exc:
        raise ValueError(f"RAG context path is not readable: {context_path}") from exc
    if not context_path.is_file():
        raise ValueError(f"RAG context path is not a file: {context_path}")
    if stat_result.st_size > _RAG_CONTEXT_MAX_BYTES:
        raise ValueError("RAG context file exceeds 50KB limit")

    text = context_path.read_text(encoding="utf-8").strip()
    if len(text) > _RAG_CONTEXT_MAX_CHARS:
        return text[:_RAG_CONTEXT_MAX_CHARS], True
    return text, False


def _automatic_rag_query(config: EOHConfig) -> str:
    query = config.rag_query.strip()
    if query:
        return query
    return (
        f"dynamic InsertShips insertion heuristic density={config.dataset_density} "
        f"arrival_scale={config.arrival_scale} medium density route capacity "
        "insertion cost final cost"
    )


def _build_retrieved_rag_context(config: EOHConfig, project_root: str) -> tuple[str, dict[str, Any]]:
    from eoh_go.rag.build_corpus import filter_corpus_by_mode, load_all_corpora, resolve_corpus_dir
    from eoh_go.rag.prompt_context import format_prompt_context
    from eoh_go.rag.retriever import retrieve, score_corpus

    corpus_dir = resolve_corpus_dir(project_root, config.rag_corpus_dir.strip())
    corpus = load_all_corpora(project_root, corpus_dir)
    corpus_size_before = len(corpus)
    filtered_corpus = filter_corpus_by_mode(corpus, config.rag_mode)
    global_items = [item for item in filtered_corpus if item.kind in {"api_constraint", "failure_case"}]
    strategy_pool = [item for item in filtered_corpus if item.kind == "algorithm_card"]
    query = _automatic_rag_query(config)
    retrieved = retrieve(query, strategy_pool, top_k=config.rag_top_k)
    all_scores = score_corpus(query, strategy_pool)
    score_by_id = {item.id: score for score, item in all_scores}
    full_context = format_prompt_context(
        retrieved,
        max_chars=max(config.rag_max_chars, 1_000_000),
        global_items=global_items,
    ).strip()
    rag_context = format_prompt_context(retrieved, max_chars=config.rag_max_chars, global_items=global_items).strip()
    trace = {
        "rag_mode": config.rag_mode,
        "rag_query": query,
        "rag_top_k": config.rag_top_k,
        "rag_corpus_size_before_filter": corpus_size_before,
        "rag_corpus_size_after_filter": len(filtered_corpus),
        "rag_global_items": [{"id": item.id, "kind": item.kind, "title": item.title} for item in global_items],
        "rag_all_scores": [{"id": item.id, "kind": item.kind, "score": score} for score, item in all_scores],
        "rag_selected_items": [
            {"id": item.id, "kind": item.kind, "title": item.title, "score": score_by_id.get(item.id, 0)}
            for item in retrieved
        ],
        "rag_context_chars": len(rag_context),
        "rag_context_truncated": len(rag_context) < len(full_context),
    }
    return rag_context, trace


def _set_rag_context_env(config: EOHConfig, project_root: str) -> dict[str, Any] | None:
    if not config.use_rag_context:
        os.environ.pop("EOH_RAG_CONTEXT", None)
        return None

    if config.rag_context_path.strip():
        rag_context, truncated = _read_manual_rag_context(config, project_root)
        trace = {
            "rag_mode": config.rag_mode,
            "rag_context_path": str(_resolve_manual_rag_context_path(config, project_root)),
            "rag_query": None,
            "rag_top_k": config.rag_top_k,
            "rag_corpus_size_before_filter": None,
            "rag_corpus_size_after_filter": None,
            "rag_global_items": [],
            "rag_all_scores": [],
            "rag_selected_items": [],
            "rag_context_chars": len(rag_context),
            "rag_context_truncated": truncated,
        }
    else:
        rag_context, trace = _build_retrieved_rag_context(config, project_root)

    if rag_context:
        os.environ["EOH_RAG_CONTEXT"] = rag_context
    else:
        os.environ.pop("EOH_RAG_CONTEXT", None)
    return trace

def run_v0_eoh(config: EOHConfig) -> dict[str, Any]:
    """
    Directly invoke Agent_EOH as a Python library rather than a subprocess.
    """
    # 1. Setup paths
    agent_root = os.path.abspath(config.agent_eoh_root)
    project_root = os.path.abspath(os.path.join(agent_root, ".."))
    src_path = os.path.join(agent_root, "eoh", "src")
    example_root = os.path.join(src_path, "eoh", "examples", "user_insertships_go")
    
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    if example_root not in sys.path:
        sys.path.insert(0, example_root)

    saved_env = {key: os.environ.get(key) for key in _RUNNER_ENV_KEYS}
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    rag_trace = None
        
    try:
        # 2. Imports from Agent_EOH
        from eoh import EVOL
        from eoh.utils.getParas import Paras
        import prob_insertships_go
        import importlib
        
        # 3. Setup Problem & Paras
        importlib.reload(prob_insertships_go)
        rag_trace = _set_rag_context_env(config, project_root)
        problem_instance = prob_insertships_go.Evaluation(
            sim_time_multi=config.sim_time_multi,
            max_instances=config.max_instances,
            dataset_density=config.dataset_density,
            sim_time_interval=config.sim_time_interval,
            arrival_scale=config.arrival_scale,
            use_density_source_dirs=config.use_density_source_dirs,
        )

        paras = Paras()
        exp_out = config.exp_output_path or os.path.join(example_root, "results_insertships_v0")
        paras.exp_output_path = exp_out

        if config.seed_path:
            seed_path = config.seed_path
        elif config.use_sa_seed_as_init:
            seed_path = _prepare_sa_seed(example_root, project_root)
        else:
            seed_path = os.path.join(example_root, "seeds_insertships_go.json")

        os.environ["EOH_OBJECTIVE_USE_COMPOSITE"] = "1" if config.objective_use_composite else "0"
        os.environ["EOH_RES_WEIGHT"] = str(config.objective_res_weight)
        os.environ["EOH_RUN_TIMEOUT_S"] = str(config.run_timeout_s)
        
        paras.set_paras(
            method="eoh",
            problem=problem_instance,
            llm_api_endpoint=config.deepseek_api_endpoint,
            llm_api_key=config.deepseek_api_key,
            llm_model=config.llm_model,
            ec_pop_size=config.ec_pop_size,
            ec_n_pop=config.ec_n_pop,
            ec_operators=config.ec_operators,
            exp_n_proc=4,
            exp_use_seed=True,
            exp_seed_path=seed_path,
            eva_timeout=config.eva_timeout,
            eva_numba_decorator=False,
        )

        # 4. Run Evolution
        start_time = datetime.now()
        evolution = EVOL(paras)
        evolution.run()
        end_time = datetime.now()
        
        # 5. Extract Results
        pop_dir = Path(exp_out) / "results" / "pops"
        pop_files = sorted(pop_dir.glob("population_generation_*.json"))
        latest_pop_file = pop_files[-1] if pop_files else None
        
        population = []
        if latest_pop_file and latest_pop_file.exists():
            try:
                population = json.loads(latest_pop_file.read_text(encoding="utf-8"))
            except Exception:
                pass
                
        return {
            "ok": True,
            "duration": (end_time - start_time).total_seconds(),
            "population_file": str(latest_pop_file) if latest_pop_file else None,
            "population_size": len(population),
            "population": population,
            "rag_trace": rag_trace,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "duration": 0,
            "population_file": None,
            "population_size": 0,
            "population": [],
            "rag_trace": rag_trace,
        }
    finally:
        _restore_env(saved_env)
