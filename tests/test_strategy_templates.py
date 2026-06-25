import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eoh_go.operator.strategy_templates import (
    BoundedReactPlanner,
    StrategySpec,
    generate_template_candidates,
    normalize_strategy_spec,
    render_strategy,
)


def test_normalize_rejects_unknown_family_with_sa_fallback():
    spec = normalize_strategy_spec({"family": "invented", "top_k": 99})

    assert spec.family == "sa_exact"
    assert spec.top_k == 4
    assert spec.fallback == "sa_exact"


def test_normalize_clamps_top_k_and_weight():
    spec = normalize_strategy_spec(
        {"family": "balanced_delta", "top_k": 99, "pickup_weight": -2}
    )

    assert spec.family == "balanced_delta"
    assert spec.top_k == 6
    assert spec.pickup_weight == 0.0


@pytest.mark.parametrize(
    "family",
    ["sa_exact", "fast_nearest", "balanced_delta", "global_delta", "robust_first_feasible"],
)
def test_render_strategy_returns_bounded_insertships(family):
    code = render_strategy(StrategySpec(family=family, top_k=3))

    assert code.startswith("func InsertShips")
    assert "dispatch.RenewnTotalCost()" in code
    assert "return dispatch" in code
    assert "MAXASSIGNS" in code
    assert "func " not in code[len("func InsertShips"):]


def test_planner_avoids_complex_strategy_after_timeouts():
    planner = BoundedReactPlanner()
    spec = planner.decide(
        {
            "density": "d25",
            "arrival_scale": 1.0,
            "active_failure_patterns": ["timeout"],
            "best_cost": None,
            "baseline_cost": 664.12,
        }
    )

    assert spec.family == "fast_nearest"
    assert spec.top_k == 2
    assert "timeout" in spec.rationale.lower()


def test_planner_uses_robust_strategy_for_high_density():
    planner = BoundedReactPlanner()
    spec = planner.decide(
        {
            "density": "d75",
            "arrival_scale": 0.7,
            "active_failure_patterns": [],
            "best_cost": None,
            "baseline_cost": 310.78,
        }
    )

    assert spec.family == "robust_first_feasible"


def test_planner_uses_global_delta_for_guard_validated_d25_cases():
    planner = BoundedReactPlanner()
    spec = planner.decide(
        {
            "density": "d25",
            "arrival_scale": 1.0,
            "active_failure_patterns": [],
            "best_cost": None,
            "baseline_cost": 664.12,
        }
    )

    assert spec.family == "global_delta"
    assert spec.pickup_weight == 0.5


def test_global_delta_template_scans_all_existing_assigns():
    code = render_strategy(StrategySpec(family="global_delta", pickup_weight=0.5))

    assert "const pickupWeight = 0.5" in code
    assert "for ii := 0; ii < dispatch.AssignsLen; ii++" in code
    assert "score := (newCost - oldCost) + pickupWeight*distPenalty" in code


def test_generate_template_candidates_deduplicates_and_limits():
    candidates = generate_template_candidates(
        {
            "density": "d50",
            "arrival_scale": 1.0,
            "active_failure_patterns": [],
            "best_cost": None,
            "baseline_cost": 500.0,
        },
        count=3,
    )

    assert len(candidates) == 3
    assert len(set(candidates)) == 3
    assert all("func InsertShips" in code for code in candidates)


def test_d25_global_delta_is_kept_even_with_stale_failures():
    candidates = generate_template_candidates(
        {
            "density": "d25",
            "arrival_scale": 1.0,
            "active_failure_patterns": ["timeout"],
            "best_cost": None,
            "baseline_cost": 664.12,
        },
        count=4,
    )

    assert any("const pickupWeight = 0.5" in code for code in candidates)


def test_smart_operator_template_mode_generates_without_api(tmp_path):
    from eoh_go.operator.agent_controller import SmartOperator

    project = tmp_path / "project"
    project.mkdir()
    (project / "main.go").write_text(
        "package main\n\nfunc InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {\n\treturn dispatch\n}\n"
    )

    op = SmartOperator(
        project_root=str(project),
        api_key="",
        pop_size=2,
        generations=1,
        dataset_density="d25",
        mutation_mode="templates",
    )

    candidates = op._generate_candidates(
        parent_code="func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {\n\treturn dispatch\n}",
        overall_best_cost=None,
        failure_keys=["timeout"],
        failure_constraints="",
    )

    assert len(candidates) == 2
    assert "const topK = 2" in candidates[0]


def test_template_mode_estimates_zero_llm_calls():
    from eoh_go.experiments.grids.smart_operator_grid import _estimate_cost

    est = _estimate_cost(cells=5, generations=2, pop_size=3, mutation_mode="templates")

    assert est["est_llm_calls"] == 0


def test_summary_markdown_uses_generation_counts():
    from eoh_go.experiments.grids.smart_operator_grid import build_summary_markdown

    args = SimpleNamespace(generations=1, pop_size=2, llm_model="test-model")
    md = build_summary_markdown(
        [
            {
                "problem": "rc101.json",
                "density": "d25",
                "arrival_scale": 1.0,
                "seed_J": 664.12,
                "best_cost": 664.12,
                "improvement_pct": 0.0,
                "best_generation": 1,
                "cell_elapsed_s": 17,
                "memory_total_attempts": 99,
                "memory_total_failures": 88,
                "gen1_compiled_ok": 2,
                "gen1_eval_ok": 2,
                "gen1_repairs": 0,
            }
        ],
        args,
    )

    assert "| RC101 | d25 | 1.0 | 664.12 | 664.12 | +0.00 | +0.0% | 1 | 17s | 2 | 2 | 0 |" in md
