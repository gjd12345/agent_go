import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import EOHConfig


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

    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
        
    try:
        # 2. Imports from Agent_EOH
        from eoh import EVOL
        from eoh.utils.getParas import Paras
        import prob_insertships_go
        import importlib
        
        # 3. Setup Problem & Paras
        importlib.reload(prob_insertships_go)
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
        }
