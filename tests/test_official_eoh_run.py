from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from eoh_go.experiments.eoh_single_runner import (
    _runner_script,
    _tail_text,
    build_official_rag_context,
    history_card_gate_reasons,
    normalize_api_endpoint,
    redact_log_tail,
    run_official_eoh,
    summarize_run,
)
from eoh_go.rag.card_synthesis import synthesize_card


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
        text = "LLM @ https://api.example.com/v1/chat endpoint=api.example.com Bearer TOKEN"
        redacted = redact_log_tail(text)
        self.assertNotIn("api.example.com", redacted)
        self.assertNotIn("TOKEN", redacted)
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

    def test_build_tsp_and_cvrp_literature_context_use_problem_cards(self) -> None:
        tsp_context, tsp_trace = build_official_rag_context(Path.cwd(), "tsp_construct", "literature_rag", top_k=2, max_chars=1800)
        cvrp_context, cvrp_trace = build_official_rag_context(Path.cwd(), "cvrp_construct", "literature_rag", top_k=2, max_chars=1800)

        self.assertTrue(all(item["id"].startswith("tsp_") for item in tsp_trace["rag_selected_items"]))
        self.assertTrue(all(not item["id"].startswith("history_") for item in tsp_trace["rag_selected_items"]))
        self.assertEqual(["tsp_construct_api_skeleton"], [item["id"] for item in tsp_trace["rag_global_items"]])
        self.assertIn("API RULES", tsp_context)
        self.assertNotIn("obp_", tsp_context)

        self.assertTrue(all(item["id"].startswith("cvrp_") for item in cvrp_trace["rag_selected_items"]))
        self.assertTrue(all(not item["id"].startswith("history_") for item in cvrp_trace["rag_selected_items"]))
        self.assertEqual(["cvrp_construct_api_skeleton"], [item["id"] for item in cvrp_trace["rag_global_items"]])
        self.assertIn("API RULES", cvrp_context)
        self.assertNotIn("obp_", cvrp_context)

    def test_build_history_rag_context_uses_synthesized_history_cards(self) -> None:
        context, trace = build_official_rag_context(
            Path.cwd(),
            "tsp_construct",
            "history_rag",
            top_k=2,
            max_chars=1800,
            query="tsp construct evolved adaptive destination centrality",
        )
        selected_ids = [item["id"] for item in trace["rag_selected_items"]]

        self.assertTrue(all(item_id.startswith("history_tsp_construct_") for item_id in selected_ids))
        self.assertEqual(trace["rag_strategy_pool_size"], len(trace["rag_all_scores"]))
        self.assertGreater(trace["rag_history_pool_size_before_gate"], 0)
        self.assertEqual(trace["rag_history_pool_size_after_gate"], len(selected_ids))
        self.assertTrue(trace["rag_blocked_history_items"])
        self.assertIn("API RULES", context)

    def test_build_mixed_rag_context_blocks_overcompound_history_cards(self) -> None:
        from eoh_go.rag.build_corpus import _is_history_card, load_all_corpora

        history_id = next(
            item.id
            for item in load_all_corpora(Path.cwd())
            if _is_history_card(item) and item.id.startswith("history_tsp_construct_")
        )
        with self.assertRaisesRegex(ValueError, "failed gate"):
            build_official_rag_context(
                Path.cwd(),
                "tsp_construct",
                "mixed_rag",
                top_k=2,
                max_chars=1800,
                query="tsp construct regret evolved",
                selected_card_ids=[
                    "tsp_regret_insertion",
                    history_id,
                ],
            )

    def test_build_mixed_rag_context_can_use_split_history_but_not_blocked_history(self) -> None:
        context, trace = build_official_rag_context(
            Path.cwd(),
            "cvrp_construct",
            "mixed_rag",
            top_k=5,
            max_chars=1800,
            query="cvrp construct regret evolved farthest",
        )
        selected_ids = [item["id"] for item in trace["rag_selected_items"]]
        blocked_ids = {item["id"] for item in trace["rag_blocked_history_items"]}

        self.assertTrue(selected_ids)
        self.assertTrue(any(item_id.startswith("history_") for item_id in selected_ids))
        self.assertTrue(all(item_id not in blocked_ids for item_id in selected_ids))
        self.assertGreater(trace["rag_history_pool_size_before_gate"], 0)
        self.assertGreater(trace["rag_history_pool_size_after_gate"], 0)
        self.assertTrue(trace["rag_blocked_history_items"])
        self.assertIn("RETRIEVED STRATEGY CARDS", context)

    def test_newly_synthesized_history_card_passes_gate(self) -> None:
        code = "regret = second_best - best; dest = distance_matrix[u, destination]; alpha = remaining_ratio; capacity = rest_capacity"
        card = synthesize_card("cvrp_construct", code)
        self.assertEqual([], history_card_gate_reasons(card))

    def test_split_history_cards_can_be_selected_explicitly(self) -> None:
        selected = [
            "history_cvrp_far_destination_seed",
            "history_cvrp_capacity_feasible_filter",
            "cvrp_regret_insertion",
        ]
        context, trace = build_official_rag_context(
            Path.cwd(),
            "cvrp_construct",
            "mixed_rag",
            top_k=3,
            max_chars=3000,
            query="cvrp construct far capacity regret",
            selected_card_ids=selected,
        )
        selected_ids = {item["id"] for item in trace["rag_selected_items"]}

        self.assertEqual(set(selected), selected_ids)
        self.assertEqual(3, trace["rag_history_pool_size_after_gate"])
        self.assertIn("history_cvrp_far_destination_seed", context)

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
                    "eoh_go.experiments.eoh_single_runner.subprocess.run",
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

    def test_build_rag_trace_includes_audit_fields(self) -> None:
        """Trace from build_official_rag_context includes injection audit."""
        _, trace = build_official_rag_context(
            Path.cwd(), "tsp_construct", "literature_rag", top_k=3, max_chars=3000
        )

        self.assertIn("rag_injected_items", trace)
        self.assertIn("rag_omitted_items", trace)
        self.assertIn("rag_truncated_item_id", trace)
        self.assertIn("rag_context_truncated", trace)
        self.assertIn("rag_context_sections_chars", trace)

        for entry in trace["rag_injected_items"]:
            self.assertIn("id", entry)
            self.assertIn("section", entry)
            self.assertIn("status", entry)
            self.assertIn("chars", entry)
            self.assertIn(entry["section"], ("api_rules", "warnings", "strategy"))
            self.assertIn(entry["status"], ("full", "truncated"))
            self.assertGreater(entry["chars"], 0)

        sections = trace["rag_context_sections_chars"]
        self.assertIn("total", sections)
        self.assertEqual(sections["total"], trace["rag_context_chars"])

    def test_build_rag_trace_truncation_marks_correct_item(self) -> None:
        """With very tight max_chars, some items should be omitted/truncated."""
        _, trace = build_official_rag_context(
            Path.cwd(), "tsp_construct", "literature_rag", top_k=5, max_chars=800
        )

        if trace["rag_context_truncated"]:
            self.assertTrue(
                trace["rag_truncated_item_id"] is not None
                or len(trace["rag_omitted_items"]) > 0
            )


if __name__ == "__main__":
    unittest.main()
