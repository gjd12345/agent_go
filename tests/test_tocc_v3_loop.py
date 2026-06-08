"""Tests for TOCC V3 bounded auto-loop."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from eoh_go.experiments.tocc_v3_loop import run_v3_loop, MAX_ITERATIONS


class ToccV3LoopTests(unittest.TestCase):

    def setUp(self):
        self.problem = "tsp_construct"
        self.cards = ["tsp_regret_insertion", "tsp_farthest_insertion", "tsp_nearest_neighbor"]
        self.trace = "/fake/trace.json"
        self.output = tempfile.mkdtemp()

    def test_rejects_max_iterations_above_limit(self):
        with self.assertRaises(ValueError):
            run_v3_loop(self.trace, problem=self.problem, available_cards=self.cards,
                        output_dir=self.output, max_iterations=5)

    @patch("eoh_go.experiments.tocc_v3_loop.subprocess.run")
    def test_dry_run_no_cards_marks_rejected(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps({
            "diagnosis": "no_issue", "recommended_cards": [], "recommended_query": "",
        })
        mock_run.return_value = mock_proc

        history = run_v3_loop(self.trace, problem=self.problem, available_cards=self.cards,
                              output_dir=self.output, max_iterations=1, real_run=False)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["status"], "no_cards_recommended")

    @patch("eoh_go.experiments.tocc_v3_loop.subprocess.run")
    def test_dry_run_with_cards_accepted(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps({
            "diagnosis": "baseline_overlap",
            "recommended_cards": ["tsp_regret_insertion", "tsp_farthest_insertion"],
            "recommended_query": "tsp regret farthest",
        })
        mock_run.return_value = mock_proc

        history = run_v3_loop(self.trace, problem=self.problem, available_cards=self.cards,
                              output_dir=self.output, max_iterations=1, real_run=False)

        self.assertEqual(len(history), 1)
        self.assertTrue(history[0]["accepted"])
        self.assertEqual(history[0]["cards"], ["tsp_regret_insertion", "tsp_farthest_insertion"])

    @patch("eoh_go.experiments.tocc_v3_loop.subprocess.run")
    def test_real_run_uses_force(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps({
            "accepted": True,
            "safe_arm": {
                "runner_arm": "literature_rag", "context_strategy": "tocc_selected_cards",
                "rag_query": "tsp regret farthest",
                "selected_card_ids": ["tsp_regret_insertion", "tsp_farthest_insertion"],
            },
        })
        mock_run.return_value = mock_proc

        history = run_v3_loop(self.trace, problem=self.problem, available_cards=self.cards,
                              output_dir=self.output, max_iterations=1, real_run=True)

        self.assertEqual(len(history), 1)
        self.assertTrue(history[0]["accepted"])
        force_calls = [c for c in mock_run.call_args_list if "--force" in str(c)]
        self.assertTrue(len(force_calls) > 0, "real-run should pass --force to manifest runner")

    def test_prompt_contains_baseline_objectives(self):
        from eoh_go.experiments.tocc_agent import _flatten_trace, _build_user_prompt

        trace = {
            "problem": "cvrp_construct", "arm": "literature_rag",
            "rag_trace": {
                "rag_query": "cvrp regret savings",
                "rag_selected_items": [{"id": "cvrp_regret_insertion", "title": "R"}, {"id": "cvrp_savings", "title": "S"}],
                "rag_all_scores": [{"id": "cvrp_regret_insertion", "score": 23}, {"id": "cvrp_savings", "score": 20}],
                "rag_context_chars": 2000, "rag_max_chars": 2500, "rag_strategy_pool_size": 5,
            },
            "run_summary": {
                "ok": True, "best_objective": 13.230, "valid_candidates": 4, "population_size": 4,
                "best_code": "def select_next_node(): pass",
            },
            "runtime_seconds": 500,
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(trace, f)
            f.flush()
            flat = _flatten_trace(f.name)
            prompt = _build_user_prompt(flat)
            os.unlink(f.name)

        self.assertIn("13.207", prompt)
        self.assertIn("Historical Best Targeted", prompt)
        self.assertIn("12.821", prompt)
        self.assertIn("cvrp_far_first", prompt)


if __name__ == "__main__":
    unittest.main()
