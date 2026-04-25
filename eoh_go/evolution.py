from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .benchmark import build_go_binary, parse_numeric_cost, run_subprocess, run_test
from .candidates import add_candidate, load_candidate, register_candidate_result
from .memory import append_research_note
from .paths import EOHGoPaths, ensure_workspace
from .store import read_json, write_json
from .eoh_runner import EOHConfig, run_v0_eoh


DEFAULT_PROBLEMS = [f"rc10{i}.json" for i in range(1, 9)]
DEFAULT_DATASETS = [
    r"C:\Users\24294\.trae\Archive_2\Archive_0422\solomon_benchmark_d25",
]
BASELINE_SOLVER_NAME = "sa_baseline"
BASELINE_SOLVER_PATH = "mainbin_sa.exe"


def _root(paths: EOHGoPaths) -> Path:
    return paths.root


def _agent_eoh_example_root(paths: EOHGoPaths) -> Path:
    return _root(paths) / "Agent_EOH" / "eoh" / "src" / "eoh" / "examples" / "user_insertships_go"


def _agent_eoh_runner_script(paths: EOHGoPaths) -> Path:
    return _agent_eoh_example_root(paths) / "v0_baseline" / "runEoH_insertships_go.py"


def _agent_eoh_population_dir(paths: EOHGoPaths) -> Path:
    return _agent_eoh_example_root(paths) / "results_insertships_v0" / "results" / "pops"


def _agent_eoh_seed_file(paths: EOHGoPaths) -> Path:
    return _agent_eoh_example_root(paths) / "seeds_insertships_go.json"


def _discover_default_datasets(paths: EOHGoPaths) -> list[str]:
    candidates = [
        _root(paths) / "solomon_benchmark",
        _root(paths) / "solomon_benchmark_d25",
        _root(paths) / "solomon_benchmark_t25",
    ]
    out: list[str] = []
    for item in candidates:
        if item.exists():
            out.append(str(item))
    return out or DEFAULT_DATASETS


def _replace_insertships(main_go_text: str, insertships_method_go: str) -> str:
    pat = r"func\s+InsertShips\s*\(\s*dispatch\s+Dispatch\s*,\s*oris\s*,\s*dess\s*\[\]Station\s*,\s*total_ship\s+int\s*\)\s*Dispatch\s*\{[\s\S]*?\n\}"
    matched = re.search(pat, main_go_text)
    if not matched:
        raise ValueError("InsertShips method not found in main.go")
    patched = main_go_text[: matched.start()] + insertships_method_go.strip() + "\n" + main_go_text[matched.end() :]
    if "sort.Sort" in insertships_method_go:
        patched = _ensure_go_import(patched, "sort")
    if "SortManager" in insertships_method_go and not re.search(r"type\s+SortManager\s+struct\s*\{", patched):
        patched = _inject_sort_manager_definition(patched)
    return patched


def _ensure_go_import(go_text: str, pkg_name: str) -> str:
    import_block = re.search(r"import\s*\(([^)]*)\)", go_text, flags=re.DOTALL)
    if not import_block:
        return go_text
    body = import_block.group(1)
    if re.search(rf'^\s*"{re.escape(pkg_name)}"\s*$', body, flags=re.MULTILINE):
        return go_text
    updated_body = body.rstrip() + f'\n    "{pkg_name}"\n'
    return go_text[: import_block.start(1)] + updated_body + go_text[import_block.end(1) :]


def _inject_sort_manager_definition(go_text: str) -> str:
    insert_pos = go_text.find("func InsertShips(")
    if insert_pos < 0:
        return go_text
    sort_manager_block = (
        "type SortManager struct {\n"
        "    inds []int\n"
        "    values []float64\n"
        "}\n\n"
        "func (sm *SortManager) Len() int {\n"
        "    return len(sm.inds)\n"
        "}\n\n"
        "func (sm *SortManager) Swap(i, j int) {\n"
        "    sm.inds[i], sm.inds[j] = sm.inds[j], sm.inds[i]\n"
        "}\n\n"
        "func (sm *SortManager) Less(i, j int) bool {\n"
        "    return sm.values[sm.inds[i]] < sm.values[sm.inds[j]]\n"
        "}\n\n"
    )
    return go_text[:insert_pos] + sort_manager_block + go_text[insert_pos:]


def _candidate_templates(paths: EOHGoPaths) -> list[dict[str, Any]]:
    root = _root(paths)
    return [
        {
            "candidate_id": "eoh_seed_random_insert",
            "label": "random_insert",
            "algorithm": "eoh_seed",
            "target_file": "main.go",
            "source_main": str(root / "main.go"),
            "rationale": "以当前 SA 主程序的随机插入逻辑作为 EOH 种子。",
            "metadata": {"origin": "main.go", "strategy_family": "insertships", "code_mode": "full_main"},
        },
        {
            "candidate_id": "eoh_seed_nearest_insert",
            "label": "nearest_insert",
            "algorithm": "eoh_seed",
            "target_file": "main.go",
            "source_main": str(root / "nearist" / "main.go"),
            "rationale": "以最近邻插入逻辑作为 EOH 候选。",
            "metadata": {"origin": "nearist/main.go", "strategy_family": "insertships", "code_mode": "full_main"},
        },
        {
            "candidate_id": "eoh_seed_empty_insert",
            "label": "empty_insert",
            "algorithm": "eoh_seed",
            "target_file": "main.go",
            "source_main": str(root / "empty" / "main.go"),
            "rationale": "以优先扩车的朴素插入逻辑作为 EOH 候选。",
            "metadata": {"origin": "empty/main.go", "strategy_family": "insertships", "code_mode": "full_main"},
        },
        {
            "candidate_id": "eoh_seed_regret_insert",
            "label": "regret_insert",
            "algorithm": "eoh_seed",
            "target_file": "main.go",
            "source_main": str(root / "0422" / "main.go"),
            "rationale": "以 regret 风格插入逻辑作为 EOH 候选。",
            "metadata": {"origin": "0422/main.go", "strategy_family": "insertships", "code_mode": "full_main"},
        },
        {
            "candidate_id": "eoh_seed_adaptive_ts",
            "label": "adaptive_ts_insert",
            "algorithm": "eoh_seed",
            "target_file": "main.go",
            "source_main": str(root / "0422_adaptive_ts" / "main.go"),
            "rationale": "以自适应时间尺度版本作为 EOH 候选。",
            "metadata": {
                "origin": "0422_adaptive_ts/main.go",
                "strategy_family": "insertships",
                "code_mode": "full_main",
            },
        },
    ]


def get_round_mode(mode: str) -> dict[str, Any]:
    return {
        "description": "EOH 自动代码进化回合",
        "baseline_solver": "SA",
        "mode": mode,
    }


def initialize_workspace(paths: EOHGoPaths) -> None:
    ensure_workspace(paths)
    if not paths.plan_path.exists():
        paths.plan_path.write_text("# PLAN\n\n## Current Goal\n构建 EOH 风格自动代码进化闭环。\n", encoding="utf-8")
    if not paths.memory_path.exists():
        paths.memory_path.write_text("# MEMORY\n\n## Facts\n- 当前 baseline 为 SA。\n", encoding="utf-8")
    if not paths.research_notes_path.exists():
        paths.research_notes_path.write_text("# Research Notes\n", encoding="utf-8")
    if not paths.registry_path.exists():
        write_json(paths.registry_path, [])
    if not paths.run_index_path.exists():
        write_json(paths.run_index_path, [])


def dataset_name(dataset_path: str) -> str:
    return Path(dataset_path).name


def _safe_float_avg(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def build_improvement_rows(
    results: list[dict[str, Any]],
    baseline_solver: str = BASELINE_SOLVER_NAME,
    target_strategy_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    indexed = defaultdict(dict)
    for item in results:
        key = (item["dataset"], item["problem"])
        indexed[key][item["strategy_name"]] = item

    rows = []
    for (dataset, problem), by_strategy in sorted(indexed.items()):
        if baseline_solver not in by_strategy:
            continue
        baseline_result = by_strategy[baseline_solver]
        baseline_cost_num = parse_numeric_cost(baseline_result["cost"])
        baseline_time = baseline_result["response_time"]

        candidate_names = target_strategy_names or [name for name in by_strategy if name != baseline_solver]
        for target_name in candidate_names:
            target_result = by_strategy.get(target_name)
            if not target_result:
                continue

            target_cost_num = parse_numeric_cost(target_result["cost"])
            target_time = target_result["response_time"]

            cost_improvement_pct = None
            if baseline_cost_num is not None and target_cost_num is not None and baseline_cost_num != 0:
                cost_improvement_pct = (baseline_cost_num - target_cost_num) / baseline_cost_num * 100.0

            time_improvement_pct = None
            if baseline_time is not None and target_time is not None and baseline_time != 0:
                time_improvement_pct = (baseline_time - target_time) / baseline_time * 100.0

            rows.append(
                {
                    "dataset": dataset,
                    "problem": problem,
                    "baseline_strategy": baseline_solver,
                    "target_strategy": target_name,
                    "target_cost": target_result["cost"],
                    "baseline_cost": baseline_result["cost"],
                    "target_response_time": round(target_time, 6) if target_time is not None else None,
                    "baseline_response_time": round(baseline_time, 6) if baseline_time is not None else None,
                    "cost_improvement_pct": round(cost_improvement_pct, 4) if cost_improvement_pct is not None else None,
                    "response_time_improvement_pct": round(time_improvement_pct, 4) if time_improvement_pct is not None else None,
                    "candidate_id": target_result.get("candidate_id"),
                    "candidate_label": target_result.get("candidate_label"),
                    "candidate_origin": target_result.get("candidate_origin"),
                }
            )
    return rows


def classify_strategy(cost_values: list[float], time_values: list[float]) -> str:
    avg_cost = sum(cost_values) / len(cost_values) if cost_values else 0.0
    avg_time = sum(time_values) / len(time_values) if time_values else 0.0
    if avg_cost > 0 and avg_time > 0:
        return "balanced"
    if avg_cost > 0 and avg_time <= 0:
        return "cost_focused"
    if avg_cost <= 0 and avg_time > 0:
        return "speed_focused"
    return "exploratory"


def build_summary(improvement_rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "cost": [],
            "time": [],
            "wins_cost": 0,
            "wins_time": 0,
            "count_cost": 0,
            "count_time": 0,
        }
    )

    for row in improvement_rows:
        target = row["target_strategy"]
        if row["cost_improvement_pct"] is not None:
            grouped[target]["cost"].append(row["cost_improvement_pct"])
            grouped[target]["count_cost"] += 1
            if row["cost_improvement_pct"] > 0:
                grouped[target]["wins_cost"] += 1
        if row["response_time_improvement_pct"] is not None:
            grouped[target]["time"].append(row["response_time_improvement_pct"])
            grouped[target]["count_time"] += 1
            if row["response_time_improvement_pct"] > 0:
                grouped[target]["wins_time"] += 1

    out = {}
    for target, values in grouped.items():
        count_cost = values["count_cost"]
        count_time = values["count_time"]
        out[target] = {
            "avg_cost_improvement_pct": _safe_float_avg(values["cost"]),
            "avg_response_time_improvement_pct": _safe_float_avg(values["time"]),
            "count_cost": count_cost,
            "count_time": count_time,
            "win_rate_cost": round(values["wins_cost"] / count_cost, 4) if count_cost else None,
            "win_rate_time": round(values["wins_time"] / count_time, 4) if count_time else None,
            "dominance_tag": classify_strategy(values["cost"], values["time"]),
        }
    return out


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        shutil.copy2(src, dst)


def _candidate_project_dir(paths: EOHGoPaths, candidate_id: str) -> Path:
    return paths.generated_projects_dir / candidate_id


def _candidate_bin_path(paths: EOHGoPaths, candidate_id: str) -> Path:
    return paths.generated_bins_dir / f"{candidate_id}.exe"


def _prepare_candidate_project(paths: EOHGoPaths, candidate: dict[str, Any]) -> dict[str, Any]:
    candidate_id = candidate["candidate_id"]
    project_dir = _candidate_project_dir(paths, candidate_id)
    if project_dir.exists():
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)

    root = _root(paths)
    candidate_meta = candidate.get("metadata", {})
    if candidate_meta.get("code_mode") == "insertships_only":
        base_main_text = (root / "main.go").read_text(encoding="utf-8")
        patched = _replace_insertships(base_main_text, candidate.get("code", ""))
        (project_dir / "main.go").write_text(patched, encoding="utf-8")
    else:
        source_main = Path(candidate_meta["source_main"])
        shutil.copy2(source_main, project_dir / "main.go")
    _copy_if_exists(root / "routing.go", project_dir / "routing.go")
    _copy_if_exists(root / "go.mod", project_dir / "go.mod")
    _copy_if_exists(root / "go.sum", project_dir / "go.sum")

    output_bin = _candidate_bin_path(paths, candidate_id)
    build_result = build_go_binary(project_dir, output_bin)
    return {
        "candidate_id": candidate_id,
        "project_dir": str(project_dir),
        "bin_path": str(output_bin),
        "build_ok": build_result["ok"],
        "build_return_code": build_result["return_code"],
        "build_stdout": build_result["stdout"],
        "build_stderr": build_result["stderr"],
        "build_duration": round(build_result["duration"], 6),
        "algorithm": candidate.get("algorithm"),
        "target_file": candidate.get("target_file"),
        "candidate_label": candidate.get("metadata", {}).get("label", candidate_id),
        "candidate_origin": candidate.get("metadata", {}).get("origin"),
        "rationale": candidate.get("rationale", ""),
    }


def _write_pre_execution_report(paths: EOHGoPaths, content: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = paths.reports_dir / f"pre_execution_report_{timestamp}.md"
    report_path.write_text(content, encoding="utf-8")
    return report_path


def _latest_population_file(pop_dir: Path) -> Path | None:
    files = sorted(pop_dir.glob("population_generation_*.json"))
    return files[-1] if files else None


def _ensure_agent_eoh_dataset(paths: EOHGoPaths) -> dict[str, Any]:
    agent_root = _root(paths) / "Agent_EOH"
    target_dir = agent_root / "solomon_benchmark"
    source_candidates = [
        _root(paths) / "solomon_benchmark",
        _root(paths) / "solomon_benchmark_d25",
    ]
    source_dir = next((item for item in source_candidates if item.exists()), None)
    if source_dir is None:
        return {
            "ok": False,
            "reason": "source_dataset_not_found",
            "source": None,
            "target": str(target_dir),
            "copied": 0,
        }

    target_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for file in source_dir.glob("*.json"):
        dst = target_dir / file.name
        if not dst.exists():
            shutil.copy2(file, dst)
            copied += 1

    return {
        "ok": True,
        "source": str(source_dir),
        "target": str(target_dir),
        "copied": copied,
    }


def run_agent_eoh_generation(
    paths: EOHGoPaths,
    loops: int = 1,
    gens: int = 0,
    sim_time_multi: int = 10,
    max_instances: int = 1,
    seed_path: str | None = None,
    dataset_density: str = "d25",
    sim_time_interval: int = 1,
    arrival_scale: float = 1.0,
    use_density_source_dirs: bool = False,
) -> dict[str, Any]:
    dataset_info = _ensure_agent_eoh_dataset(paths)
    
    agent_root = str(_root(paths) / "Agent_EOH")
    exp_out = str(_agent_eoh_example_root(paths) / "results_insertships_v0")
    
    config = EOHConfig(
        ec_n_pop=max(1, gens),
        sim_time_multi=sim_time_multi,
        max_instances=max_instances,
        seed_path=seed_path,
        exp_output_path=exp_out,
        agent_eoh_root=agent_root,
        dataset_density=dataset_density,
        sim_time_interval=sim_time_interval,
        arrival_scale=arrival_scale,
        use_density_source_dirs=use_density_source_dirs,
    )
    
    start_time = datetime.now()
    runner_result = run_v0_eoh(config)
    end_time = datetime.now()
    
    population = runner_result.get("population", [])
    if not population:
        seed_file = _agent_eoh_seed_file(paths)
        if seed_file.exists():
            try:
                seed_loaded = json.loads(seed_file.read_text(encoding="utf-8"))
                if isinstance(seed_loaded, list):
                    population = seed_loaded
            except Exception:
                population = []

    return {
        "executed": True,
        "command": ["run_v0_eoh_library"],
        "cwd": agent_root,
        "ok": runner_result.get("ok", False),
        "return_code": 0 if runner_result.get("ok", False) else 1,
        "stdout": "",
        "stderr": runner_result.get("error", ""),
        "duration": runner_result.get("duration", (end_time - start_time).total_seconds()),
        "population_file": runner_result.get("population_file"),
        "population_size": len(population),
        "population": population,
        "dataset_info": dataset_info,
        "seed_file": str(_agent_eoh_seed_file(paths)),
        "eoh_config": {
            "dataset_density": dataset_density,
            "sim_time_interval": sim_time_interval,
            "arrival_scale": arrival_scale,
            "use_density_source_dirs": use_density_source_dirs,
            "sim_time_multi": sim_time_multi,
            "max_instances": max_instances,
        },
    }


def ensure_agent_eoh_candidates(
    paths: EOHGoPaths,
    limit: int | None = None,
    dataset_density: str = "d25",
    sim_time_interval: int = 1,
    arrival_scale: float = 1.0,
    use_density_source_dirs: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = []
    eoh_result = run_agent_eoh_generation(
        paths,
        dataset_density=dataset_density,
        sim_time_interval=sim_time_interval,
        arrival_scale=arrival_scale,
        use_density_source_dirs=use_density_source_dirs,
    )
    population = eoh_result.get("population") if isinstance(eoh_result, dict) else []
    if not isinstance(population, list):
        population = []
    if limit is not None:
        population = population[:limit]

    for idx, item in enumerate(population):
        code = item.get("code")
        if not isinstance(code, str) or "func InsertShips" not in code:
            continue
        candidate_id = f"agent_eoh_insertships_{idx+1:03d}"
        metadata = {
            "origin": "Agent_EOH:user_insertships_go",
            "strategy_family": "insertships",
            "code_mode": "insertships_only",
            "objective": item.get("objective"),
            "algorithm_text": item.get("algorithm"),
            "population_file": eoh_result.get("population_file"),
            "eoh_return_code": eoh_result.get("return_code"),
        }
        add_candidate(
            paths,
            candidate_id=candidate_id,
            algorithm="agent_eoh",
            target_file="main.go",
            code=code,
            rationale="由 Agent_EOH 的 EOH 流程自动生成 InsertShips 代码",
            metadata=metadata,
        )
        loaded = load_candidate(paths, candidate_id)
        if loaded:
            generated.append(loaded)
    return generated, eoh_result


def ensure_eoh_seed_candidates(paths: EOHGoPaths, limit: int | None = None) -> list[dict[str, Any]]:
    initialize_workspace(paths)
    generated: list[dict[str, Any]] = []
    templates = _candidate_templates(paths)
    if limit is not None:
        templates = templates[:limit]

    for item in templates:
        source_main = Path(item["source_main"])
        if not source_main.exists():
            continue
        code = source_main.read_text(encoding="utf-8")
        metadata = dict(item.get("metadata", {}))
        metadata["source_main"] = str(source_main)
        metadata["label"] = item["label"]
        add_candidate(
            paths,
            candidate_id=item["candidate_id"],
            algorithm=item["algorithm"],
            target_file=item["target_file"],
            code=code,
            rationale=item["rationale"],
            metadata=metadata,
        )
        loaded = load_candidate(paths, item["candidate_id"])
        if loaded:
            generated.append(loaded)
    return generated


def build_eoh_candidate_pool(
    paths: EOHGoPaths,
    limit: int | None = None,
    generator: str = "agent_eoh",
    include_seed: bool = True,
    dataset_density: str = "d25",
    sim_time_interval: int = 1,
    arrival_scale: float = 1.0,
    use_density_source_dirs: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generation_trace: dict[str, Any] = {
        "generator": generator,
        "agent_eoh": None,
        "candidate_sources": [],
    }

    seed_candidates: list[dict[str, Any]] = []
    if generator == "agent_eoh":
        agent_candidates, eoh_result = ensure_agent_eoh_candidates(
            paths,
            limit=limit,
            dataset_density=dataset_density,
            sim_time_interval=sim_time_interval,
            arrival_scale=arrival_scale,
            use_density_source_dirs=use_density_source_dirs,
        )
        if agent_candidates:
            seed_candidates.extend(agent_candidates)
            generation_trace["candidate_sources"].append("agent_eoh")
        generation_trace["agent_eoh"] = {
            "candidate_count": len(agent_candidates),
            "executed": bool(eoh_result.get("executed")) if isinstance(eoh_result, dict) else True,
            "ok": eoh_result.get("ok") if isinstance(eoh_result, dict) else None,
            "return_code": eoh_result.get("return_code") if isinstance(eoh_result, dict) else None,
            "population_file": eoh_result.get("population_file") if isinstance(eoh_result, dict) else None,
        }

    if include_seed or not seed_candidates:
        local_seed_candidates = ensure_eoh_seed_candidates(paths, limit=limit)
        seed_candidates.extend(local_seed_candidates)
        generation_trace["candidate_sources"].append("local_seed")

    if limit is not None:
        seed_candidates = seed_candidates[:limit]

    built_candidates: list[dict[str, Any]] = []
    for candidate in seed_candidates:
        build_info = _prepare_candidate_project(paths, candidate)
        register_candidate_result(
            paths,
            {
                "candidate_id": build_info["candidate_id"],
                "algorithm": build_info["algorithm"],
                "target_file": build_info["target_file"],
                "candidate_path": str(paths.candidates_dir / f"{build_info['candidate_id']}.json"),
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "metadata": {
                    "project_dir": build_info["project_dir"],
                    "bin_path": build_info["bin_path"],
                    "build_ok": build_info["build_ok"],
                    "build_duration": build_info["build_duration"],
                    "origin": build_info["candidate_origin"],
                    "label": build_info["candidate_label"],
                },
                "build_ok": build_info["build_ok"],
            },
        )
        built_candidates.append(build_info)
    return built_candidates, generation_trace


def execute_strategy(strategy_cfg: dict[str, Any], data_path: str, fixed_t: int) -> dict[str, Any]:
    run_out = run_test(strategy_cfg["solver_path"], data_path, fixed_t, extra_args=strategy_cfg.get("extra_args", []))
    return {
        "strategy_name": strategy_cfg["name"],
        "strategy_type": strategy_cfg.get("strategy_type", "direct_optimizer"),
        "solver_path": strategy_cfg["solver_path"],
        "cost": run_out["cost"],
        "response_time": run_out["response_time"],
        "return_code": run_out["return_code"],
        "candidate_id": strategy_cfg.get("candidate_id"),
        "candidate_label": strategy_cfg.get("candidate_label"),
        "candidate_origin": strategy_cfg.get("candidate_origin"),
    }


def _baseline_strategy(paths: EOHGoPaths) -> dict[str, Any]:
    return {
        "name": BASELINE_SOLVER_NAME,
        "strategy_type": "baseline_producer",
        "solver_path": str((_root(paths) / BASELINE_SOLVER_PATH).resolve()),
        "extra_args": [],
    }


def _candidate_strategy_configs(paths: EOHGoPaths, built_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for item in built_candidates:
        if not item["build_ok"]:
            continue
        out.append(
            {
                "name": item["candidate_id"],
                "strategy_type": "eoh_candidate",
                "solver_path": item["bin_path"],
                "extra_args": [],
                "candidate_id": item["candidate_id"],
                "candidate_label": item["candidate_label"],
                "candidate_origin": item["candidate_origin"],
            }
        )
    return out


def _write_markdown_report(run_dir: Path, run_payload: dict[str, Any]) -> str:
    lines = [
        f"# EOH Evolution Report {run_payload['run_id']}",
        "",
        "## Summary",
        f"- mode: {run_payload['mode']}",
        f"- baseline: {run_payload['baseline_solver']}",
        f"- datasets: {', '.join(run_payload['datasets'])}",
        f"- problems: {', '.join(run_payload['problems'])}",
        f"- result_count: {run_payload['result_count']}",
        "",
        "## Candidate Build Status",
    ]
    for item in run_payload["candidate_builds"]:
        lines.append(
            f"- {item['candidate_id']}: build_ok={item['build_ok']}, origin={item['candidate_origin']}, duration={item['build_duration']}"
        )
    lines.append("")
    lines.append("## Improvement Summary")
    for name, metrics in run_payload["summary"].items():
        lines.append(
            f"- {name}: avg_cost={metrics.get('avg_cost_improvement_pct')}, avg_time={metrics.get('avg_response_time_improvement_pct')}, win_rate_cost={metrics.get('win_rate_cost')}, win_rate_time={metrics.get('win_rate_time')}, tag={metrics.get('dominance_tag')}"
        )
    report = "\n".join(lines) + "\n"
    (run_dir / "eoh_evolution_report.md").write_text(report, encoding="utf-8")
    return report


def run_round(
    paths: EOHGoPaths,
    datasets: list[str] | None = None,
    problems: list[str] | None = None,
    strategy_configs: list[dict[str, Any]] | None = None,
    fixed_t: int = 1,
    mode: str = "eoh_auto",
    generation_size: int = 5,
    generator: str = "agent_eoh",
    include_seed: bool = True,
    dataset_density: str = "d25",
    sim_time_interval: int = 1,
    arrival_scale: float = 1.0,
    use_density_source_dirs: bool = False,
) -> dict[str, Any]:
    initialize_workspace(paths)
    datasets = datasets or _discover_default_datasets(paths)
    problems = problems or DEFAULT_PROBLEMS

    pre_report_content = "\n".join(
        [
            "# Pre-Execution Report",
            "",
            "- objective: 使用 Agent_EOH/EOH 真实生成候选，并与 SA 基线对比",
            f"- mode: {mode}",
            f"- generator: {generator}",
            f"- include_seed: {include_seed}",
            f"- generation_size: {generation_size}",
            f"- dataset_density: {dataset_density}",
            f"- sim_time_interval: {sim_time_interval}",
            f"- arrival_scale: {arrival_scale}",
            f"- use_density_source_dirs: {use_density_source_dirs}",
            f"- datasets: {', '.join(datasets)}",
            f"- problems: {', '.join(problems)}",
        ]
    )
    pre_report_path = _write_pre_execution_report(paths, pre_report_content)

    candidate_builds, generation_trace = build_eoh_candidate_pool(
        paths,
        limit=generation_size,
        generator=generator,
        include_seed=include_seed,
        dataset_density=dataset_density,
        sim_time_interval=sim_time_interval,
        arrival_scale=arrival_scale,
        use_density_source_dirs=use_density_source_dirs,
    )
    baseline = _baseline_strategy(paths)
    auto_candidate_strategies = _candidate_strategy_configs(paths, candidate_builds)
    strategy_configs = strategy_configs or [baseline, *auto_candidate_strategies]

    results = []
    for strategy_cfg in strategy_configs:
        for ds in datasets:
            ds_name = dataset_name(ds)
            for prob in problems:
                data_path = str(Path(ds) / prob)
                if not Path(data_path).exists():
                    continue
                result = execute_strategy(strategy_cfg, data_path, fixed_t)
                result.update(
                    {
                        "dataset": ds_name,
                        "dataset_path": ds,
                        "problem": prob,
                        "t": fixed_t,
                    }
                )
                results.append(result)

    improvement_rows = build_improvement_rows(
        results,
        baseline_solver=BASELINE_SOLVER_NAME,
        target_strategy_names=[cfg["name"] for cfg in strategy_configs if cfg["name"] != BASELINE_SOLVER_NAME],
    )
    summary = build_summary(improvement_rows)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = paths.runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    best_target = None
    best_cost = None
    for target, metrics in summary.items():
        score = metrics.get("avg_cost_improvement_pct")
        if score is None:
            continue
        if best_cost is None or score > best_cost:
            best_cost = score
            best_target = target

    run_payload = {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "mode": mode,
        "baseline_solver": "SA",
        "datasets": datasets,
        "problems": problems,
        "fixed_t": fixed_t,
        "eoh_eval_config": {
            "dataset_density": dataset_density,
            "sim_time_interval": sim_time_interval,
            "arrival_scale": arrival_scale,
            "use_density_source_dirs": use_density_source_dirs,
        },
        "strategy_names": [cfg["name"] for cfg in strategy_configs],
        "candidate_builds": candidate_builds,
        "summary": summary,
        "best_target": best_target,
        "result_count": len(results),
        "pre_execution_report": str(pre_report_path),
        "generation_trace": generation_trace,
    }

    write_json(run_dir / "full_benchmark_results.json", results)
    write_json(run_dir / "improvement_vs_SA.json", improvement_rows)
    write_json(run_dir / "summary.json", summary)
    write_json(run_dir / "candidate_builds.json", candidate_builds)
    write_json(run_dir / "run_manifest.json", run_payload)
    report_text = _write_markdown_report(run_dir, run_payload)

    append_research_note(
        paths.research_notes_path,
        f"EOH run {run_id}",
        report_text,
    )

    run_index = read_json(paths.run_index_path, [])
    if not isinstance(run_index, list):
        run_index = []
    run_index.append(
        {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "mode": mode,
            "baseline_solver": "SA",
            "strategy_names": [cfg["name"] for cfg in strategy_configs],
            "candidate_count": len(auto_candidate_strategies),
            "generator": generator,
            "eoh_eval_config": {
                "dataset_density": dataset_density,
                "sim_time_interval": sim_time_interval,
                "arrival_scale": arrival_scale,
                "use_density_source_dirs": use_density_source_dirs,
            },
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    write_json(paths.run_index_path, run_index)

    return run_payload


def analyze_latest_run(paths: EOHGoPaths) -> dict[str, Any]:
    initialize_workspace(paths)
    run_index = read_json(paths.run_index_path, [])
    if not isinstance(run_index, list) or not run_index:
        return {"run_id": None, "summary": {}, "best_target": None}

    latest = run_index[-1]
    run_dir = Path(latest["run_dir"])
    summary = read_json(run_dir / "summary.json", {})
    candidate_builds = read_json(run_dir / "candidate_builds.json", [])

    best_target = None
    best_cost = None
    if isinstance(summary, dict):
        for target, metrics in summary.items():
            score = metrics.get("avg_cost_improvement_pct")
            if score is None:
                continue
            if best_cost is None or score > best_cost:
                best_cost = score
                best_target = target

    return {
        "run_id": latest.get("run_id"),
        "run_dir": latest.get("run_dir"),
        "summary": summary,
        "best_target": best_target,
        "candidate_builds": candidate_builds,
    }
