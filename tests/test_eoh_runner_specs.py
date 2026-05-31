from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

from eoh_go.eoh_runner.registry import PROBLEM_SPECS, TARGET_SPECS, get_problem_spec, get_target_spec


class TestEOHRunnerSpecs(unittest.TestCase):
    def test_registered_targets_exist(self) -> None:
        self.assertEqual({"InsertShips", "Optimization", "SelectItems"}, set(TARGET_SPECS))
        self.assertEqual("vrp_insertships", get_problem_spec("vrp_insertships").name)
        self.assertEqual("Optimization", get_target_spec("Optimization").function_name)

    def test_vrp_problem_sources_resolve(self) -> None:
        root = Path(__file__).resolve().parents[1]
        spec = PROBLEM_SPECS["vrp_insertships"]
        paths = spec.resolve_source_files(root)
        self.assertTrue(all(path.exists() for path in paths), paths)
        knapsack = PROBLEM_SPECS["knapsack"]
        knapsack_paths = knapsack.resolve_source_files(root)
        self.assertTrue(all(path.exists() for path in knapsack_paths), knapsack_paths)

    def test_go_regexes_match_current_sources(self) -> None:
        root = Path(__file__).resolve().parents[1]
        main_text = (root / "main.go").read_text(encoding="utf-8")
        self.assertIsNotNone(re.search(TARGET_SPECS["InsertShips"].extract_regex, main_text))
        self.assertIsNotNone(re.search(TARGET_SPECS["Optimization"].extract_regex, main_text))
        knapsack_text = (root / "eoh_go_workspace" / "problems" / "knapsack" / "knapsack_solver.go").read_text(
            encoding="utf-8"
        )
        self.assertIsNotNone(re.search(TARGET_SPECS["SelectItems"].extract_regex, knapsack_text))

    def test_unknown_specs_raise_value_error(self) -> None:
        with self.assertRaises(ValueError):
            get_target_spec("MissingTarget")
        with self.assertRaises(ValueError):
            get_problem_spec("missing_problem")

    def test_knapsack_seed_evaluator_runs(self) -> None:
        root = Path(__file__).resolve().parents[1]
        example_root = root / "Agent_EOH" / "eoh" / "src" / "eoh" / "examples" / "user_knapsack_go"
        sys.path.insert(0, str(example_root))
        try:
            import json
            from prob_knapsack_go import Evaluation

            seed = json.loads((example_root / "seeds_knapsack_go.json").read_text(encoding="utf-8"))[0]["code"]
            objective = Evaluation().evaluate(seed)
            self.assertLess(objective, 0)
        finally:
            try:
                sys.path.remove(str(example_root))
            except ValueError:
                pass


if __name__ == "__main__":
    unittest.main()
