from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from eoh_go.experiments.batch_runner import _build_cmd, _validate_manifest


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
        self.assertIn("--rag-query", cmd)

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

    def test_validate_manifest_rejects_missing_selected_cards_for_tocc_strategy(self) -> None:
        manifest = self._minimal_manifest()
        manifest["arms"][0]["selected_card_ids"] = []

        errors = _validate_manifest(manifest)

        self.assertTrue(any("selected_card_ids" in error for error in errors))

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


if __name__ == "__main__":
    unittest.main()
