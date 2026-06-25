from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from argparse import Namespace
from unittest import mock


def _row(
    problem: str,
    density: str,
    *,
    population_size: int = 4,
    valid_candidates: int = 2,
    suspicious_candidates: int = 1,
    invalid_candidates: int = 1,
    seed_j: float | None = 100.0,
    best_j: float | None = 95.0,
    seed_res: float | None = 10.0,
    best_res: float | None = 9.0,
    build_ok: bool = True,
    selected_status: str | None = "valid",
) -> dict:
    return {
        "problem": problem,
        "density": density,
        "arrival_scale": 1.0,
        "population_size": population_size,
        "valid_candidates": valid_candidates,
        "suspicious_candidates": suspicious_candidates,
        "invalid_candidates": invalid_candidates,
        "seed_J": seed_j,
        "best_EOH_J": best_j,
        "seed_Res": seed_res,
        "best_EOH_Res": best_res,
        "best_build_ok": build_ok,
        "selected_best_status_after_eval": selected_status,
    }


def _payload(rows: list[dict]) -> dict:
    return {"output_dir": "fake", "rows": rows}


class RagAblationSummaryTests(unittest.TestCase):
    def _write_payload(self, root: Path, name: str, rows: list[dict]) -> Path:
        path = root / f"{name}.json"
        path.write_text(json.dumps(_payload(rows), ensure_ascii=False), encoding="utf-8")
        return path

    def test_summarize_pairs_rows_by_problem_density_and_arrival_scale(self) -> None:
        from eoh_go.experiments.reports.summarize_rag_ablation import summarize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = self._write_payload(
                root,
                "baseline",
                [
                    _row("rc102.json", "d50", valid_candidates=1, best_j=120.0, best_res=12.0),
                    _row("rc101.json", "d25", valid_candidates=2, best_j=95.0, best_res=9.0),
                ],
            )
            rag = self._write_payload(
                root,
                "rag",
                [
                    _row("rc101.json", "d25", valid_candidates=3, best_j=90.0, best_res=8.0),
                    _row("rc102.json", "d50", valid_candidates=2, best_j=110.0, best_res=15.0),
                ],
            )

            summary = summarize(str(baseline), str(rag), str(root / "out"))

        paired = summary["paired_cells"]
        self.assertEqual([cell["key"] for cell in paired], [["rc101.json", "d25", 1.0], ["rc102.json", "d50", 1.0]])
        self.assertEqual(paired[0]["delta_valid_rate"], 0.25)
        self.assertEqual(paired[0]["delta_J"], -5.0)
        self.assertEqual(paired[0]["res_ratio_rag"], 0.8)
        self.assertEqual(summary["stats"]["rag_j_improved"], 2)

    def test_unpaired_rows_are_reported_without_crashing(self) -> None:
        from eoh_go.experiments.reports.summarize_rag_ablation import summarize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = self._write_payload(root, "baseline", [_row("rc101.json", "d25"), _row("rc103.json", "d75")])
            rag = self._write_payload(root, "rag", [_row("rc101.json", "d25"), _row("rc102.json", "d50")])

            summary = summarize(str(baseline), str(rag), str(root / "out"))

        self.assertEqual(summary["stats"]["paired_count"], 1)
        self.assertEqual(summary["stats"]["unpaired_count"], 2)
        self.assertEqual({cell["side"] for cell in summary["unpaired_cells"]}, {"baseline", "rag"})

    def test_incomplete_cells_handle_zero_population_and_null_metrics(self) -> None:
        from eoh_go.experiments.reports.summarize_rag_ablation import summarize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = self._write_payload(
                root,
                "baseline",
                [_row("rc101.json", "d25", population_size=0, valid_candidates=0, seed_j=None, best_j=None)],
            )
            rag = self._write_payload(root, "rag", [_row("rc101.json", "d25", best_j=None)])

            summary = summarize(str(baseline), str(rag), str(root / "out"))

        cell = summary["paired_cells"][0]
        self.assertFalse(cell["complete"])
        self.assertIsNone(cell["baseline"]["valid_rate"])
        self.assertIsNone(cell["delta_J"])
        self.assertIn("no_population", cell["notes"])
        self.assertIn("missing_j", cell["notes"])
        self.assertEqual(summary["stats"]["complete_count"], 0)
        self.assertEqual(summary["stats"]["rag_j_improved"], 0)

    def test_res_ratio_direction_labels_are_reported(self) -> None:
        from eoh_go.experiments.reports.summarize_rag_ablation import summarize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = self._write_payload(root, "baseline", [_row("rc101.json", "d25", best_res=12.0)])
            rag = self._write_payload(root, "rag", [_row("rc101.json", "d25", best_res=8.0)])

            summary = summarize(str(baseline), str(rag), str(root / "out"))

        cell = summary["paired_cells"][0]
        self.assertEqual(cell["res_direction_baseline"], "slower")
        self.assertEqual(cell["res_direction_rag"], "faster")

    def test_seed_mismatch_notes_use_relative_threshold_without_blocking_complete_cell(self) -> None:
        from eoh_go.experiments.reports.summarize_rag_ablation import summarize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = self._write_payload(root, "baseline", [_row("rc101.json", "d25", seed_j=100.0, seed_res=10.0)])
            rag = self._write_payload(root, "rag", [_row("rc101.json", "d25", seed_j=106.0, seed_res=10.4)])

            summary = summarize(str(baseline), str(rag), str(root / "out"))

        cell = summary["paired_cells"][0]
        self.assertTrue(cell["complete"])
        self.assertIn("seed_j_mismatch", cell["notes"])
        self.assertNotIn("seed_res_mismatch", cell["notes"])
        self.assertEqual(summary["stats"]["seed_j_mismatch_count"], 1)
        self.assertEqual(summary["stats"]["seed_res_mismatch_count"], 0)

    def test_empty_inputs_write_reports_and_do_not_crash(self) -> None:
        from eoh_go.experiments.reports.summarize_rag_ablation import summarize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = self._write_payload(root, "baseline", [])
            rag = self._write_payload(root, "rag", [])
            out = root / "out"

            summary = summarize(str(baseline), str(rag), str(out))

            self.assertTrue((out / "rag_ablation_summary.md").exists())
            self.assertTrue((out / "rag_ablation_summary.json").exists())
        self.assertEqual(summary["stats"]["paired_count"], 0)

    def test_run_ablation_pair_reuses_grid_with_baseline_and_auto_rag_variants(self) -> None:
        from eoh_go.experiments.grids.eoh_arrival_grid import run_ablation_pair

        args = Namespace(
            root="/repo",
            output_dir="eoh_go_workspace/reports/tables/rag_ablation",
            ablation_pair=True,
            use_rag_context=False,
            rag_context_path="manual.txt",
        )

        def fake_run_grid(run_args: Namespace) -> dict:
            suffix = "rag" if run_args.use_rag_context else "baseline"
            return {"output_dir": f"/tmp/{suffix}"}

        with mock.patch("eoh_go.experiments.grids.eoh_arrival_grid.run_grid", side_effect=fake_run_grid) as run_grid:
            with mock.patch("eoh_go.experiments.grids.eoh_arrival_grid.summarize_rag_ablation", return_value={"stats": {}}) as summarize:
                result = run_ablation_pair(args)

        baseline_args = run_grid.call_args_list[0].args[0]
        rag_args = run_grid.call_args_list[1].args[0]
        self.assertFalse(baseline_args.use_rag_context)
        self.assertTrue(rag_args.use_rag_context)
        self.assertEqual(rag_args.rag_context_path, "")
        self.assertTrue(str(baseline_args.output_dir).endswith("rag_ablation/baseline"))
        self.assertTrue(str(rag_args.output_dir).endswith("rag_ablation/rag"))
        summarize.assert_called_once_with(
            "/tmp/baseline/eoh_arrival_grid_results.json",
            "/tmp/rag/eoh_arrival_grid_results.json",
            "/repo/eoh_go_workspace/reports/tables/rag_ablation_summary",
        )
        self.assertEqual(result["summary_output_dir"], "/repo/eoh_go_workspace/reports/tables/rag_ablation_summary")


if __name__ == "__main__":
    unittest.main()
