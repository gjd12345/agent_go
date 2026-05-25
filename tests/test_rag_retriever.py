import unittest


class RagRetrieverTests(unittest.TestCase):
    def _item(self, item_id: str, kind: str, summary: str):
        from eoh_go.rag.schemas import CorpusItem

        return CorpusItem(
            id=item_id,
            kind=kind,
            title=item_id.replace("_", " "),
            tags=["insertships"],
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


if __name__ == "__main__":
    unittest.main()
