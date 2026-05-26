import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EOHConfig:
    deepseek_api_key: str = os.environ.get("DEEPSEEK_API_KEY", "")
    deepseek_api_endpoint: str = os.environ.get("DEEPSEEK_API_ENDPOINT", "api.deepseek.com")
    llm_model: str = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
    moonshot_api_key: str = os.environ.get("MOONSHOT_API_KEY", "")
    tavily_api_key: str = os.environ.get("TAVILY_API_KEY", "")
    
    ec_pop_size: int = 4
    ec_n_pop: int = 1
    ec_operators: list[str] = field(default_factory=lambda: ["m1", "m2"])
    
    sim_time_multi: int = 10
    max_instances: int = 1
    eva_timeout: int = 120
    run_timeout_s: int = 60
    objective_res_weight: float = 0.2
    objective_use_composite: bool = True
    dataset_density: str = "d25"
    sim_time_interval: int = 1
    arrival_scale: float = 1.0
    use_density_source_dirs: bool = False
    
    seed_path: Optional[str] = None
    exp_output_path: str = ""
    agent_eoh_root: str = ""
    use_sa_seed_as_init: bool = True

    use_rag_context: bool = False
    rag_context_path: str = ""
    rag_mode: str = "mixed"
    rag_top_k: int = 3
    rag_query: str = ""
    rag_corpus_dir: str = ""
    rag_max_chars: int = 6000
