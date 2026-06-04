from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from eoh_go.experiments.official_eoh_run import (
    _runner_script,
    _tail_text,
    build_official_rag_context,
    normalize_api_endpoint,
    redact_log_tail,
    run_official_eoh,
    summarize_run,
)


class OfficialEohRunTests(unittest.TestCase):
    def test_normalize_api_endpoint_strips_scheme_and_path(self) -> None:
        self.assertEqual(normalize_api_endpoint("https://api.example.com/v1/chat/completions"), "api.example.com")
        self.assertEqual(normalize_api_endpoint("http://api.example.com"), "api.example.com")
        self.assertEqual(normalize_api_endpoint("api.example.com/v1"), "api.example.com")

    def test_generated_runner_script_compiles(self) -> None:
        script = _runner_script()
        compile(script, "_run_official_eoh.py", "exec")
        self.assertIn("install_api_url_patch", script)
        self.assertIn("api_url(self.api_endpoint)", script)

    def test_redact_log_tail_removes_endpoint_and_bearer_token(self) -> None:
        text = "LLM @ https://api.example.com/v1/chat endpoint=api.example.com Bearer SECRET_TOKEN"
        redacted = redact_log_tail(text)
        self.assertNotIn("api.example.com", redacted)
        self.assertNotIn("SECRET_TOKEN", redacted)
        self.assertIn("[api-endpoint-redacted]", redacted)
        self.assertIn("[api-key-redacted]", redacted)

    def test_tail_text_accepts_bytes_from_timeout_expired(self) -> None:
        self.assertEqual(_tail_text(b"a\nb\nc", max_lines=2), "b\nc")

    def test_summarize_run_reads_latest_population_and_best_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            pop_dir = run_dir / "results" / "pops"
            pop_dir.mkdir(parents=True)
            (pop_dir / "population_generation_0.json").write_text(
                json.dumps([{"algorithm": "seed", "code": "def score(): pass", "objective": 3.0}]),
                encoding="utf-8",
            )
            (pop_dir / "population_generation_1.json").write_text(
                json.dumps(
                    [
                        {"algorithm": "bad", "code": "bad", "objective": None},
                        {"algorithm": "good", "code": "def score(item, bins): return bins", "objective": 1.5},
                    ]
                ),
                encoding="utf-8",
            )

            summary = summarize_run(run_dir)

        self.assertTrue(summary["ok"])
        self.assertEqual(summary["latest_generation"], 1)
        self.assertEqual(summary["population_size"], 2)
        self.assertEqual(summary["valid_candidates"], 1)
        self.assertEqual(summary["best_objective"], 1.5)
        self.assertIn("return bins", summary["best_code"])

    def test_summarize_run_reports_missing_population(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = summarize_run(Path(tmp))
        self.assertFalse(summary["ok"])
        self.assertEqual(summary["failure_reason"], "missing_population")

    def test_build_bp_online_literature_rag_context_uses_obp_cards_only(self) -> None:
        context, trace = build_official_rag_context(Path.cwd(), "bp_online", "literature_rag", top_k=2, max_chars=1800)
        selected_ids = [item["id"] for item in trace["rag_selected_items"]]
        self.assertTrue(selected_ids)
        self.assertTrue(all(item_id.startswith("obp_") for item_id in selected_ids))
        self.assertEqual(["obp_api_skeleton"], [item["id"] for item in trace["rag_global_items"]])
        self.assertLessEqual(len(context), 1800)
        self.assertIn("API RULES", context)
        self.assertNotIn("InsertShips", context)

    def test_run_official_eoh_timeout_reports_without_key_value(self) -> None:
        old_key = os.environ.get("TEST_OFFICIAL_KEY")
        old_endpoint = os.environ.get("TEST_OFFICIAL_ENDPOINT")
        old_model = os.environ.get("TEST_OFFICIAL_MODEL")
        os.environ["TEST_OFFICIAL_KEY"] = "SECRET_SHOULD_NOT_APPEAR"
        os.environ["TEST_OFFICIAL_ENDPOINT"] = "https://api.example.com/v1"
        os.environ["TEST_OFFICIAL_MODEL"] = "test-model"
        try:
            with tempfile.TemporaryDirectory() as tmp:
                args = Namespace(
                    official_root=tmp,
                    python="/bin/python3",
                    output_dir=str(Path(tmp) / "out"),
                    problem="bp_online",
                    arm="pure_eoh",
                    context_file="",
                    pop_size=2,
                    generations=1,
                    operators="i1",
                    n_processes=1,
                    eval_timeout_s=1,
                    llm_timeout_s=1,
                    run_timeout_s=1,
                    use_official_seed=False,
                    api_key_env="TEST_OFFICIAL_KEY",
                    api_endpoint_env="TEST_OFFICIAL_ENDPOINT",
                    model_env="TEST_OFFICIAL_MODEL",
                    llm_model="",
                    rag_top_k=2,
                    rag_max_chars=1800,
                    rag_query="",
                )
                with patch(
                    "eoh_go.experiments.official_eoh_run.subprocess.run",
                    side_effect=subprocess.TimeoutExpired(cmd=["python"], timeout=1, output=b"", stderr=b""),
                ):
                    payload = run_official_eoh(args)
                encoded = json.dumps(payload, ensure_ascii=True)
        finally:
            if old_key is None:
                os.environ.pop("TEST_OFFICIAL_KEY", None)
            else:
                os.environ["TEST_OFFICIAL_KEY"] = old_key
            if old_endpoint is None:
                os.environ.pop("TEST_OFFICIAL_ENDPOINT", None)
            else:
                os.environ["TEST_OFFICIAL_ENDPOINT"] = old_endpoint
            if old_model is None:
                os.environ.pop("TEST_OFFICIAL_MODEL", None)
            else:
                os.environ["TEST_OFFICIAL_MODEL"] = old_model

        self.assertEqual(payload["failure_reason"], "timeout")
        self.assertTrue(payload["api_key_present"])
        self.assertNotIn("SECRET_SHOULD_NOT_APPEAR", encoded)


if __name__ == "__main__":
    unittest.main()
