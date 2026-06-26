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

    def test_outcome_summaries_supports_dict(self) -> None:
        from eoh_go.rag.retriever import retrieve_with_rerank

        corpus = [
            self._item("strong_card", "algorithm_card", "regret insertion heuristic"),
            self._item("weak_card", "algorithm_card", "regret insertion"),
        ]
        query = "regret insertion heuristic"

        outcome_summaries = {
            "strong_card": {"decision": "suppress"},
        }
        result = retrieve_with_rerank(
            query, corpus, top_k=2, outcome_summaries=outcome_summaries
        )
        self.assertEqual(result[0].id, "weak_card")

    def test_extract_features_prefers_tags_over_text(self) -> None:
        from eoh_go.rag.retriever import _extract_card_features

        item = self._item(
            "regret_insertion_card",
            "algorithm_card",
            "far first nearest neighbor greedy approach",
            tags=["regret", "lookahead"],
        )
        features = _extract_card_features(item)
        self.assertEqual(features, {"regret", "lookahead"})
        self.assertNotIn("nearest", features)
        self.assertNotIn("greedy", features)

    def test_score_corpus_with_rerank_returns_debug_info(self) -> None:
        from eoh_go.rag.retriever import score_corpus_with_rerank

        corpus = [
            self._item("card_a", "algorithm_card", "regret insertion"),
            self._item("card_b", "algorithm_card", "regret heuristic"),
        ]
        result = score_corpus_with_rerank(
            "regret insertion", corpus,
            outcome_summaries={"card_a": {"decision": "suppress"}},
        )
        self.assertTrue(len(result) >= 1)
        first = result[0]
        self.assertIn("base_score", first)
        self.assertIn("outcome_decision", first)
        self.assertIn("multiplier", first)
        self.assertIn("final_score", first)
        suppressed = next(r for r in result if r["id"] == "card_a")
        self.assertEqual(suppressed["outcome_decision"], "suppress")
        self.assertLess(suppressed["multiplier"], 1.0)

    def test_extract_code_features_from_go_code(self) -> None:
        from eoh_go.rag.retriever import extract_code_features

        code = """func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
    bestDelta := math.MaxFloat64
    for candidate := range unassigned {
        distPenalty := CalcDistance(oris[candidate], dess[candidate])
        if distPenalty < bestDelta {
            bestDelta = distPenalty
        }
    }
    return dispatch
}"""
        features = extract_code_features(code)
        self.assertIn("bestdelta", features)
        self.assertIn("distpenalty", features)
        self.assertIn("calcdistance", features)
        self.assertIn("dispatch", features)
        self.assertNotIn("func", features)
        self.assertNotIn("return", features)
        self.assertNotIn("for", features)

    def test_load_population_features_from_individuals(self) -> None:
        from eoh_go.rag.retriever import load_population_features

        population = [
            {"code": "func InsertShips() { bestDelta := 1.0 }", "objective": 100.5},
            {"code": "func InsertShips() { nearestCost := 2.0 }", "objective": 98.2},
            {"code": "", "objective": None},
            "invalid_entry",
        ]
        features = load_population_features(population)
        self.assertIn("bestdelta", features)
        self.assertIn("nearestcost", features)
        self.assertNotIn("func", features)

    def test_load_population_features_empty_population(self) -> None:
        from eoh_go.rag.retriever import load_population_features

        self.assertEqual(load_population_features([]), set())


if __name__ == "__main__":
    unittest.main()
