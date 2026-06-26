import unittest


class RagRetrieverTests(unittest.TestCase):
    def _item(self, item_id: str, kind: str, summary: str, tags=None):
        from eoh_go.rag.schemas import CorpusItem

        return CorpusItem(
            id=item_id,
            kind=kind,
            title=item_id.replace("_", " "),
            tags=tags or ["insertships"],
            source_path="source",
            summary=summary,
            constraints=["avoid timeout", "safe rollback"],
            content="content",
        )

    def test_retrieve_is_deterministic_with_kind_priority_tiebreak(self) -> None:
        from eoh_go.rag.retriever import retrieve

        corpus = [
            self._item("z_code", "code_example", "dynamic insertion heuristic"),
            self._item("a_failure", "failure_case", "dynamic insertion heuristic"),
            self._item("m_algorithm", "algorithm_card", "dynamic insertion heuristic"),
            self._item("b_api", "api_constraint", "dynamic insertion heuristic"),
        ]

        first = retrieve("dynamic insertion heuristic", corpus, top_k=4)
        second = retrieve("dynamic insertion heuristic", corpus, top_k=4)

        self.assertEqual([item.id for item in first], [item.id for item in second])
        self.assertEqual([item.kind for item in first], ["algorithm_card", "failure_case", "api_constraint", "code_example"])

    def test_empty_corpus_and_top_k_are_respected(self) -> None:
        from eoh_go.rag.retriever import retrieve

        corpus = [
            self._item("a", "algorithm_card", "delta insertion"),
            self._item("b", "failure_case", "delta insertion"),
        ]

        self.assertEqual(retrieve("delta", [], top_k=3), [])
        self.assertEqual(retrieve("delta", corpus, top_k=1), [corpus[0]])
        self.assertEqual(retrieve("delta", corpus, top_k=0), [])

    # ── Phase 4a: retrieve_with_rerank tests ──

    def test_rerank_without_signals_matches_retrieve(self) -> None:
        from eoh_go.rag.retriever import retrieve, retrieve_with_rerank

        corpus = [
            self._item("regret_insertion", "algorithm_card", "regret insertion heuristic"),
            self._item("far_first", "algorithm_card", "far first insertion"),
            self._item("nearest_neighbor", "algorithm_card", "nearest neighbor greedy"),
        ]
        query = "insertion heuristic"

        plain = retrieve(query, corpus, top_k=2)
        reranked = retrieve_with_rerank(query, corpus, top_k=2)

        self.assertEqual([i.id for i in plain], [i.id for i in reranked])

    def test_outcome_boost_promotes_item(self) -> None:
        from eoh_go.rag.retriever import retrieve_with_rerank
        from types import SimpleNamespace

        corpus = [
            self._item("high_score_card", "algorithm_card", "regret insertion heuristic"),
            self._item("low_score_card", "algorithm_card", "regret insertion"),
        ]
        query = "regret insertion heuristic"

        without = retrieve_with_rerank(query, corpus, top_k=2)
        self.assertEqual(without[0].id, "high_score_card")

        outcome_summaries = {
            "low_score_card": SimpleNamespace(decision="boost"),
            "high_score_card": SimpleNamespace(decision="suppress"),
        }
        with_boost = retrieve_with_rerank(
            query, corpus, top_k=2, outcome_summaries=outcome_summaries
        )
        self.assertEqual(with_boost[0].id, "low_score_card")

    def test_outcome_suppress_demotes_item(self) -> None:
        from eoh_go.rag.retriever import retrieve_with_rerank
        from types import SimpleNamespace

        corpus = [
            self._item("strong_card", "algorithm_card", "regret insertion heuristic"),
            self._item("weak_card", "algorithm_card", "regret insertion"),
        ]
        query = "regret insertion heuristic"

        without = retrieve_with_rerank(query, corpus, top_k=2)
        self.assertEqual(without[0].id, "strong_card")

        outcome_summaries = {
            "strong_card": SimpleNamespace(decision="suppress"),
        }
        with_suppress = retrieve_with_rerank(
            query, corpus, top_k=2, outcome_summaries=outcome_summaries
        )
        self.assertEqual(with_suppress[0].id, "weak_card")

    def test_population_overlap_penalty_demotes_redundant_card(self) -> None:
        from eoh_go.rag.retriever import retrieve_with_rerank

        corpus = [
            self._item("greedy_nearest", "algorithm_card", "nearest neighbor greedy",
                       tags=["nearest", "greedy", "simple"]),
            self._item("regret_based", "algorithm_card", "regret based insertion",
                       tags=["regret", "lookahead", "optimal"]),
        ]
        query = "insertion strategy"

        population_features = {"nearest", "greedy", "simple"}
        result = retrieve_with_rerank(
            query, corpus, top_k=2, population_features=population_features
        )
        self.assertEqual(result[0].id, "regret_based")

    def test_candidate_k_expands_rerank_pool(self) -> None:
        from eoh_go.rag.retriever import RerankConfig, retrieve_with_rerank
        from types import SimpleNamespace

        corpus = [
            self._item(f"card_{i}", "algorithm_card", f"insertion strategy variant {i}")
            for i in range(12)
        ]
        query = "insertion strategy"

        outcome_summaries = {"card_11": SimpleNamespace(decision="boost")}
        config = RerankConfig(candidate_k=12)
        result = retrieve_with_rerank(
            query, corpus, top_k=3,
            outcome_summaries=outcome_summaries, config=config,
        )
        self.assertIn("card_11", [i.id for i in result])

    def test_extract_card_features_filters_stopwords(self) -> None:
        from eoh_go.rag.retriever import _extract_card_features

        item = self._item(
            "history_tsp_regret_abc",
            "algorithm_card",
            "regret insertion",
            tags=["tsp", "regret", "lookahead"],
        )
        features = _extract_card_features(item)
        self.assertIn("regret", features)
        self.assertIn("lookahead", features)
        self.assertNotIn("tsp", features)
        self.assertNotIn("algorithm", features)

    def test_rerank_empty_corpus_returns_empty(self) -> None:
        from eoh_go.rag.retriever import retrieve_with_rerank
        from types import SimpleNamespace

        result = retrieve_with_rerank(
            "test", [], top_k=3,
            outcome_summaries={"x": SimpleNamespace(decision="boost")},
        )
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
