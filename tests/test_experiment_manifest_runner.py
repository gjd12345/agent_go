from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from eoh_go.experiments.batch_runner import _build_cmd, _validate_manifest, main


class ExperimentManifestRunnerTests(unittest.TestCase):
    def _write_manifest(self, root: Path, manifest: dict) -> Path:
        path = root / "manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def _minimal_manifest(self) -> dict:
        return {
            "suite": "test_suite",
            "problems": ["tsp_construct"],
            "arms": [
                {
                    "name": "targeted_tsp",
                    "runner_arm": "literature_rag",
                    "context_strategy": "tocc_selected_cards",
                    "rag_query": "tsp regret farthest route length",
                    "selected_card_ids": ["tsp_regret_insertion", "tsp_farthest_insertion"],
                    "problems": ["tsp_construct"],
                }
            ],
            "generations": [0],
            "pop_size": 4,
            "repeats": 1,
            "max_runs": 1,
            "require_confirm_for_real_run": True,
        }

    def test_build_cmd_passes_selected_card_ids(self) -> None:
        manifest = self._minimal_manifest()
        arm = manifest["arms"][0]
        cmd = _build_cmd(manifest, "tsp_construct", arm, 0, 1, "/tmp/out")

        self.assertIn("--selected-card-ids", cmd)
        self.assertIn("tsp_regret_insertion,tsp_farthest_insertion", cmd)
        self.assertIn("--candidate-card-source", cmd)
        self.assertIn("selected_card_ids", cmd)
        self.assertIn("--rag-query", cmd)

    def test_build_cmd_prefers_candidate_card_ids(self) -> None:
        manifest = self._minimal_manifest()
        arm = manifest["arms"][0]
        arm["candidate_card_ids"] = ["tsp_nearest_insertion", "tsp_two_opt_awareness"]
        cmd = _build_cmd(manifest, "tsp_construct", arm, 0, 1, "/tmp/out")

        self.assertIn("--selected-card-ids", cmd)
        self.assertIn("tsp_nearest_insertion,tsp_two_opt_awareness", cmd)
        self.assertIn("--candidate-card-source", cmd)
        self.assertIn("candidate_card_ids", cmd)

    def test_validate_manifest_accepts_canonical_and_legacy_context_strategies(self) -> None:
        for strategy in ("tocc_candidate_pool", "tocc_selected_cards"):
            manifest = self._minimal_manifest()
            manifest["arms"][0]["context_strategy"] = strategy
            self.assertEqual([], _validate_manifest(manifest))

    def test_no_run_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = self._write_manifest(root, self._minimal_manifest())
            output_dir = root / "out"

            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "eoh_go.experiments.batch_runner",
                    "--manifest",
                    str(manifest_path),
                    "--output-dir",
                    str(output_dir),
                    "--no-run",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertFalse(output_dir.exists())

    def test_real_run_requires_force_when_manifest_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = self._write_manifest(root, self._minimal_manifest())
            output_dir = root / "out"

            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "eoh_go.experiments.batch_runner",
                    "--manifest",
                    str(manifest_path),
                    "--output-dir",
                    str(output_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("--force", proc.stdout + proc.stderr)
            self.assertFalse(output_dir.exists())

    def test_validate_manifest_lists_all_supported_card_fields_for_tocc_strategy(self) -> None:
        manifest = self._minimal_manifest()
        manifest["arms"][0]["selected_card_ids"] = []

        errors = _validate_manifest(manifest)

        self.assertTrue(
            any(
                "tocc_* strategy requires candidate_card_ids, selected_card_ids, or cards" in error
                for error in errors
            )
        )

    def test_validate_manifest_accepts_candidate_card_ids_for_tocc_strategy(self) -> None:
        manifest = self._minimal_manifest()
        manifest["arms"][0]["selected_card_ids"] = []
        manifest["arms"][0]["candidate_card_ids"] = ["tsp_regret_insertion", "tsp_farthest_insertion"]

        errors = _validate_manifest(manifest)

        self.assertEqual([], errors)

    def test_build_cmd_passes_prev_run_dir_when_provided(self) -> None:
        manifest = self._minimal_manifest()
        arm = manifest["arms"][0]
        cmd = _build_cmd(manifest, "tsp_construct", arm, 0, 2, "/tmp/out_r2", prev_run_dir="/tmp/out_r1")

        self.assertIn("--prev-run-dir", cmd)
        self.assertIn("/tmp/out_r1", cmd)

    def test_build_cmd_omits_prev_run_dir_when_empty(self) -> None:
        manifest = self._minimal_manifest()
        arm = manifest["arms"][0]
        cmd = _build_cmd(manifest, "tsp_construct", arm, 0, 1, "/tmp/out_r1", prev_run_dir="")

        self.assertNotIn("--prev-run-dir", cmd)

    def test_build_cmd_reads_prev_run_dir_from_manifest_rag(self) -> None:
        manifest = self._minimal_manifest()
        manifest["rag"] = {"top_k": 2, "max_chars": 2500, "prev_run_dir": "/tmp/prev_iter"}
        arm = manifest["arms"][0]
        cmd = _build_cmd(manifest, "tsp_construct", arm, 0, 1, "/tmp/out_r1", prev_run_dir="")

        self.assertIn("--prev-run-dir", cmd)
        self.assertIn("/tmp/prev_iter", cmd)

    def test_build_cmd_arg_prev_run_dir_overrides_manifest(self) -> None:
        manifest = self._minimal_manifest()
        manifest["rag"] = {"top_k": 2, "max_chars": 2500, "prev_run_dir": "/tmp/manifest_prev"}
        arm = manifest["arms"][0]
        cmd = _build_cmd(manifest, "tsp_construct", arm, 0, 1, "/tmp/out_r2", prev_run_dir="/tmp/arg_prev")

        self.assertIn("/tmp/arg_prev", cmd)
        self.assertNotIn("/tmp/manifest_prev", cmd)

    def test_build_cmd_passes_outcome_file_from_manifest_rag(self) -> None:
        manifest = self._minimal_manifest()
        manifest["rag"] = {"top_k": 2, "max_chars": 2500, "outcome_file": "/tmp/card_outcomes.jsonl"}
        arm = manifest["arms"][0]
        cmd = _build_cmd(manifest, "tsp_construct", arm, 0, 1, "/tmp/out")

        self.assertIn("--outcome-file", cmd)
        self.assertIn("/tmp/card_outcomes.jsonl", cmd)

    def test_dry_run_applies_arm_rag_override_and_only_chains_population_arm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._minimal_manifest()
            manifest.update(
                {
                    "suite": "four_arm_dry_run",
                    "repeats": 2,
                    "max_runs": 6,
                    "rag": {"top_k": 2, "max_chars": 2500},
                    "arms": [
                        {
                            "name": "B_keyword",
                            "runner_arm": "literature_rag",
                            "context_strategy": "tocc_candidate_pool",
                            "candidate_card_ids": ["tsp_regret_insertion", "tsp_farthest_insertion"],
                        },
                        {
                            "name": "C_keyword_outcome",
                            "runner_arm": "literature_rag",
                            "context_strategy": "tocc_candidate_pool",
                            "candidate_card_ids": ["tsp_regret_insertion", "tsp_farthest_insertion"],
                            "rag": {"outcome_file": "card_outcomes.jsonl"},
                        },
                        {
                            "name": "D_keyword_outcome_pop",
                            "runner_arm": "literature_rag",
                            "context_strategy": "tocc_candidate_pool",
                            "candidate_card_ids": ["tsp_regret_insertion", "tsp_farthest_insertion"],
                            "rag": {
                                "outcome_file": "card_outcomes.jsonl",
                                "use_prev_run_dir_chain": True,
                            },
                        },
                    ],
                }
            )
            manifest_path = self._write_manifest(root, manifest)

            with mock.patch.object(
                sys,
                "argv",
                [
                    "batch_runner",
                    "--manifest",
                    str(manifest_path),
                    "--output-dir",
                    str(root / "out"),
                    "--dry-run",
                ],
            ), mock.patch("builtins.print") as print_mock:
                main()

            output = "\n".join(" ".join(str(arg) for arg in call.args) for call in print_mock.call_args_list)
            b_lines = [
                line for line in output.splitlines()
                if "run_tsp_construct_B_keyword_" in line and "--problem" in line
            ]
            c_lines = [
                line for line in output.splitlines()
                if "run_tsp_construct_C_keyword_outcome_" in line and "--problem" in line
            ]
            d_lines = [
                line for line in output.splitlines()
                if "run_tsp_construct_D_keyword_outcome_pop_" in line and "--problem" in line
            ]
            self.assertTrue(all("--outcome-file" not in line for line in b_lines))
            self.assertTrue(all("--prev-run-dir" not in line for line in b_lines))
            self.assertTrue(all("--outcome-file card_outcomes.jsonl" in line for line in c_lines))
            self.assertTrue(all("--prev-run-dir" not in line for line in c_lines))
            self.assertIn("--outcome-file card_outcomes.jsonl", d_lines[0])
            self.assertNotIn("--prev-run-dir", d_lines[0])
            self.assertIn("--prev-run-dir", d_lines[1])

    def test_population_chain_skips_immediately_after_failed_repeat(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._minimal_manifest()
            manifest.update(
                {
                    "suite": "population_chain_failure",
                    "repeats": 3,
                    "max_runs": 3,
                    "require_confirm_for_real_run": False,
                    "rag": {"top_k": 2, "max_chars": 2500},
                    "arms": [
                        {
                            "name": "D_keyword_outcome_pop",
                            "runner_arm": "literature_rag",
                            "context_strategy": "tocc_candidate_pool",
                            "candidate_card_ids": ["tsp_regret_insertion", "tsp_farthest_insertion"],
                            "rag": {
                                "outcome_file": "card_outcomes.jsonl",
                                "use_prev_run_dir_chain": True,
                            },
                        }
                    ],
                }
            )
            manifest_path = self._write_manifest(root, manifest)
            commands: list[list[str]] = []

            def fake_run(cmd, **_kwargs):
                commands.append(cmd)
                output_dir = Path(cmd[cmd.index("--output-dir") + 1])
                output_dir.mkdir(parents=True, exist_ok=True)
                repeat = len(commands)
                failed = repeat == 2
                (output_dir / "official_eoh_run_summary.json").write_text(
                    json.dumps(
                        {
                            "failure_reason": "return_code_1" if failed else None,
                            "run_summary": {
                                "ok": not failed,
                                "best_objective": None if failed else 1.0,
                                "valid_candidates": 0 if failed else 4,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=1 if failed else 0, stdout="", stderr="")

            with mock.patch.object(
                sys,
                "argv",
                [
                    "batch_runner",
                    "--manifest",
                    str(manifest_path),
                    "--output-dir",
                    str(root / "out"),
                    "--force",
                ],
            ), mock.patch("eoh_go.experiments.batch_runner.subprocess.run", side_effect=fake_run):
                main()

            self.assertNotIn("--prev-run-dir", commands[0])
            self.assertIn("--prev-run-dir", commands[1])
            self.assertNotIn("--prev-run-dir", commands[2])
            run_index = json.loads(
                (root / "out" / "population_chain_failure" / "run_index.json").read_text(encoding="utf-8")
            )
            self.assertTrue(run_index[2]["population_chain_skipped_previous_failed"])

    def test_run_index_is_persisted_before_a_later_run_is_interrupted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._minimal_manifest()
            manifest.update(
                {
                    "suite": "incremental_index",
                    "repeats": 2,
                    "max_runs": 2,
                    "require_confirm_for_real_run": False,
                }
            )
            manifest_path = self._write_manifest(root, manifest)
            calls = 0

            def fake_run(cmd, **_kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise KeyboardInterrupt
                output_dir = Path(cmd[cmd.index("--output-dir") + 1])
                output_dir.mkdir(parents=True, exist_ok=True)
                (output_dir / "official_eoh_run_summary.json").write_text(
                    json.dumps(
                        {
                            "failure_reason": None,
                            "run_summary": {
                                "ok": True,
                                "best_objective": 1.0,
                                "valid_candidates": 4,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with mock.patch.object(
                sys,
                "argv",
                [
                    "batch_runner",
                    "--manifest",
                    str(manifest_path),
                    "--output-dir",
                    str(root / "out"),
                    "--force",
                ],
            ), mock.patch("eoh_go.experiments.batch_runner.subprocess.run", side_effect=fake_run):
                with self.assertRaises(KeyboardInterrupt):
                    main()

            index_path = root / "out" / "incremental_index" / "run_index.json"
            self.assertTrue(index_path.exists())
            run_index = json.loads(index_path.read_text(encoding="utf-8"))
            self.assertEqual(1, len(run_index))
            self.assertEqual("run_tsp_construct_targeted_tsp_g0_r1", run_index[0]["tag"])

    def test_resume_rebuilds_index_with_existing_successful_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._minimal_manifest()
            manifest.update(
                {
                    "suite": "resume_index",
                    "repeats": 2,
                    "max_runs": 2,
                    "require_confirm_for_real_run": False,
                }
            )
            manifest_path = self._write_manifest(root, manifest)
            suite_root = root / "out" / "resume_index"
            first_run = suite_root / "run_tsp_construct_targeted_tsp_g0_r1"
            first_run.mkdir(parents=True)
            (first_run / "official_eoh_run_summary.json").write_text(
                json.dumps(
                    {
                        "failure_reason": None,
                        "runtime_seconds": 12.5,
                        "run_summary": {
                            "ok": True,
                            "best_objective": 1.25,
                            "valid_candidates": 4,
                        },
                    }
                ),
                encoding="utf-8",
            )

            def fake_run(cmd, **_kwargs):
                output_dir = Path(cmd[cmd.index("--output-dir") + 1])
                output_dir.mkdir(parents=True, exist_ok=True)
                (output_dir / "official_eoh_run_summary.json").write_text(
                    json.dumps(
                        {
                            "failure_reason": None,
                            "run_summary": {
                                "ok": True,
                                "best_objective": 1.0,
                                "valid_candidates": 4,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with mock.patch.object(
                sys,
                "argv",
                [
                    "batch_runner",
                    "--manifest",
                    str(manifest_path),
                    "--output-dir",
                    str(root / "out"),
                    "--resume",
                    "--force",
                ],
            ), mock.patch("eoh_go.experiments.batch_runner.subprocess.run", side_effect=fake_run):
                main()

            run_index = json.loads((suite_root / "run_index.json").read_text(encoding="utf-8"))
            self.assertEqual(2, len(run_index))
            self.assertTrue(run_index[0]["resumed_existing"])
            self.assertEqual(1.25, run_index[0]["best_objective"])

    def test_consecutive_failure_limit_stops_remaining_paid_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._minimal_manifest()
            manifest.update(
                {
                    "suite": "failure_circuit_breaker",
                    "repeats": 6,
                    "max_runs": 6,
                    "max_consecutive_failures": 5,
                    "require_confirm_for_real_run": False,
                }
            )
            manifest_path = self._write_manifest(root, manifest)
            commands: list[list[str]] = []

            def fake_run(cmd, **_kwargs):
                commands.append(cmd)
                output_dir = Path(cmd[cmd.index("--output-dir") + 1])
                output_dir.mkdir(parents=True, exist_ok=True)
                (output_dir / "official_eoh_run_summary.json").write_text(
                    json.dumps(
                        {
                            "failure_reason": "return_code_1",
                            "run_summary": {
                                "ok": False,
                                "best_objective": None,
                                "valid_candidates": 0,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=1, stdout="", stderr="generated code failed")

            with mock.patch.object(
                sys,
                "argv",
                [
                    "batch_runner",
                    "--manifest",
                    str(manifest_path),
                    "--output-dir",
                    str(root / "out"),
                    "--force",
                ],
            ), mock.patch("eoh_go.experiments.batch_runner.subprocess.run", side_effect=fake_run):
                with self.assertRaisesRegex(SystemExit, "consecutive run failures"):
                    main()

            self.assertEqual(5, len(commands))
            run_index = json.loads(
                (root / "out" / "failure_circuit_breaker" / "run_index.json").read_text(encoding="utf-8")
            )
            self.assertEqual(5, len(run_index))


if __name__ == "__main__":
    unittest.main()
