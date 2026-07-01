# Legacy: EOH Runner v0 (InsertShips)

This directory archives the **legacy InsertShips v0 RAG runner**. It is **not**
used by the current BP / TSP / CVRP official EOH-RAG mainline.

## What's here

| File | Role |
| --- | --- |
| `runner.py` | v0 RAG runner: `run_v0_eoh`, `_set_rag_context_env`, `_build_retrieved_rag_context`, manual/auto RAG context assembly for the InsertShips Go problem. |
| `config.py` | `EOHConfig` dataclass consumed only by `runner.py`. |
| `tests/` | Integration/context tests that protect the v0 runner. Not collected by the mainline `pytest tests/` run. |

## Current mainline RAG path (use this instead)

```
eoh_rag/experiments/rag_context_builder.py::build_official_rag_context
```

`batch_runner.py` routes the `history_rag` / `literature_rag` / `mixed_rag` arms
to that builder. The mainline "history card" concept is an `algorithm_card`
whose id starts with `history_` (see `eoh_rag/rag/build_corpus.py::_is_history_card`).

## Why archived, not deleted

The v0 runner still imports mainline infra that remains in `eoh_rag/`:
`eoh_rag.eoh_runner.registry` (problem/target specs) and `eoh_rag.rag.*`
(corpus / retriever). Keeping the runner runnable documents the v0 behavior and
lets its tests verify it if anyone revisits the InsertShips path.

## Running the legacy tests

```bash
python3 -m pytest legacy/eoh_runner_v0/tests/ -q
```

(The mainline `python3 -m pytest tests/` does not collect this directory.)
