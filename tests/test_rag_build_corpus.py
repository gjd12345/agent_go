import json
import tempfile
import unittest
from pathlib import Path


class RagBuildCorpusTests(unittest.TestCase):
    def test_build_all_corpora_writes_expected_jsonl_files_from_local_sources(self) -> None:
        from eoh_go.rag.build_corpus import build_all_corpora, load_all_corpora, resolve_corpus_dir

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "eoh_go_workspace" / "candidate_sources").mkdir(parents=True)
            (root / "eoh_go_workspace" / "candidate_sources" / "topk_delta.go").write_text(
                "func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch { return dispatch }\n",
                encoding="utf-8",
            )
            seed_dir = root / "Agent_EOH" / "eoh" / "src" / "eoh" / "examples" / "user_insertships_go"
            seed_dir.mkdir(parents=True)
            (seed_dir / "seeds_insertships_go_sa.json").write_text(
                json.dumps([{"algorithm": "SA fallback", "code": "func InsertShips(...)"}]),
                encoding="utf-8",
            )
            (root / "main.go").write_text("type Dispatch struct{}\nfunc InsertShips() {}\n", encoding="utf-8")
            guard_dir = root / "eoh_go" / "eoh_runner"
            guard_dir.mkdir(parents=True)
            (guard_dir / "candidate_guard.py").write_text("suspicious low negative timeout missing result\n", encoding="utf-8")

            written = build_all_corpora(root)
            corpus_dir = resolve_corpus_dir(root, "")
            loaded = load_all_corpora(root)

            self.assertEqual(set(path.name for path in written), {"code_examples.jsonl", "algorithm_cards.jsonl", "api_constraints.jsonl", "failure_cases.jsonl"})
            self.assertTrue((corpus_dir / "code_examples.jsonl").exists())
            self.assertEqual({"code_example", "algorithm_card", "api_constraint", "failure_case"}, {item.kind for item in loaded})
            self.assertTrue(any(item.source_path.endswith("topk_delta.go") for item in loaded))

    def test_resolve_corpus_dir_rejects_paths_outside_workspace_corpus(self) -> None:
        from eoh_go.rag.build_corpus import resolve_corpus_dir

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                resolve_corpus_dir(root, "../../../outside")


if __name__ == "__main__":
    unittest.main()
