from __future__ import annotations

import re
import sys
import os
import unittest
from pathlib import Path

from eoh_go.eoh_runner.registry import PROBLEM_SPECS, TARGET_SPECS, get_problem_spec, get_target_spec


class TestEOHRunnerSpecs(unittest.TestCase):
    def test_registered_targets_exist(self) -> None:
        self.assertEqual({"InsertShips", "Optimization", "SelectItems", "SplitOrders"}, set(TARGET_SPECS))
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
        mixer = PROBLEM_SPECS["mixer_split"]
        mixer_paths = mixer.resolve_source_files(root)
        self.assertTrue(all(path.exists() for path in mixer_paths), mixer_paths)

    def test_go_regexes_match_current_sources(self) -> None:
        root = Path(__file__).resolve().parents[1]
        main_text = (root / "main.go").read_text(encoding="utf-8")
        self.assertIsNotNone(re.search(TARGET_SPECS["InsertShips"].extract_regex, main_text))
        self.assertIsNotNone(re.search(TARGET_SPECS["Optimization"].extract_regex, main_text))
        knapsack_text = (root / "eoh_go_workspace" / "problems" / "knapsack" / "knapsack_solver.go").read_text(
            encoding="utf-8"
        )
        self.assertIsNotNone(re.search(TARGET_SPECS["SelectItems"].extract_regex, knapsack_text))
        mixer_text = (root / "eoh_go_workspace" / "problems" / "mixer_split" / "mixer_split_solver.go").read_text(
            encoding="utf-8"
        )
        self.assertIsNotNone(re.search(TARGET_SPECS["SplitOrders"].extract_regex, mixer_text))

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

    def test_mixer_split_seed_evaluator_runs(self) -> None:
        root = Path(__file__).resolve().parents[1]
        example_root = root / "Agent_EOH" / "eoh" / "src" / "eoh" / "examples" / "user_mixer_split_go"
        sys.path.insert(0, str(example_root))
        try:
            import json
            from prob_mixer_split_go import Evaluation

            seed = json.loads((example_root / "seeds_mixer_split_go.json").read_text(encoding="utf-8"))[0]["code"]
            objective = Evaluation().evaluate(seed)
            self.assertLess(objective, 1e8)
        finally:
            try:
                sys.path.remove(str(example_root))
            except ValueError:
                pass

    def test_knapsack_evaluator_scrubs_secret_env(self) -> None:
        root = Path(__file__).resolve().parents[1]
        example_root = root / "Agent_EOH" / "eoh" / "src" / "eoh" / "examples" / "user_knapsack_go"
        sys.path.insert(0, str(example_root))
        old_secret = os.environ.get("DEEPSEEK_API_KEY")
        os.environ["DEEPSEEK_API_KEY"] = "LEAK_TEST_SECRET"
        try:
            from prob_knapsack_go import Evaluation

            code = """func SelectItems(items []Item, capacity int) []bool {
    fmt.Println(os.Getenv("DEEPSEEK_API_KEY"))
    return make([]bool, len(items))
}"""
            ev = Evaluation()
            ev.evaluate(code)
            self.assertNotIn("LEAK_TEST_SECRET", ev._last_traceback or "")
        finally:
            if old_secret is None:
                os.environ.pop("DEEPSEEK_API_KEY", None)
            else:
                os.environ["DEEPSEEK_API_KEY"] = old_secret
            try:
                sys.path.remove(str(example_root))
            except ValueError:
                pass

    def test_mixer_split_rejects_unknown_vehicle_capacity(self) -> None:
        root = Path(__file__).resolve().parents[1]
        example_root = root / "Agent_EOH" / "eoh" / "src" / "eoh" / "examples" / "user_mixer_split_go"
        sys.path.insert(0, str(example_root))
        try:
            from prob_mixer_split_go import Evaluation

            code = """func SplitOrders(orders []Order, vehicles []Vehicle, workHours float64) []SubOrder {
    out := make([]SubOrder, 0, len(orders))
    for _, order := range orders {
        out = append(out, SubOrder{OrderID: order.ID, Volume: order.Volume, VehicleCapacity: 999999})
    }
    return out
}"""
            objective = Evaluation().evaluate(code)
            self.assertGreaterEqual(objective, 1e8)
        finally:
            try:
                sys.path.remove(str(example_root))
            except ValueError:
                pass


if __name__ == "__main__":
    unittest.main()
