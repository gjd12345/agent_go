# Literature/RAG Phase A-B-C Agent Record

Date: 2026-05-26

This note is an agent-side local record only. It is outside the `agent_go` repository and is not intended to be committed with the project.

## Context

The project goal is to test whether adding heuristic knowledge as prompt context can improve EOH-Go code generation for `InsertShips`.

The working hypothesis came from the advisor's direction:

- use existing pseudocode or algorithm knowledge from literature/books;
- provide it as input constraints/context to the LLM;
- compare generation quality with and without that context;
- do not train a model or introduce embedding infrastructure at this stage.

The work was split into Phase A, Phase B, and Phase C to keep implementation and experiment risk manageable.

## Phase A: Fixed Context Injection

Goal: prove the minimal context-injection path works before building retrieval.

Implemented behavior:

- Added `EOH_RAG_CONTEXT` prompt injection in `Agent_EOH/eoh/src/eoh/examples/user_insertships_go/prompts_insertships_go.py`.
- Added config switches in `eoh_go/eoh_runner/config.py`:
  - `use_rag_context`
  - `rag_context_path`
  - `rag_top_k`
  - `rag_query`
- Updated `eoh_go/eoh_runner/runner.py` to set or clear `EOH_RAG_CONTEXT` before `Evaluation(...)` is constructed.
- Added CLI pass-through and result-tracing fields in `eoh_go/experiments/eoh_arrival_grid.py`.
- Added manual context file under `eoh_go_workspace/rag/manual_contexts/insertships_v1.txt`.
- Added tests around empty/non-empty prompt context and runner timing.

Important constraints preserved:

- RAG context is wrapped as untrusted reference material.
- Generated context is inserted before EOH evolution starts.
- Existing prompt output constraints remain intact: return only Go code, no package/imports/explanations.
- RAG data stays under `eoh_go_workspace/rag/`.

Result:

- Phase A validated that prompt injection works and that the environment variable is visible at the right time.
- This established the baseline mechanism for later retrieval.

## Phase B: Corpus + Keyword Retrieval

Goal: replace the fixed manual context with automatic corpus loading, keyword retrieval, and prompt-context formatting.

Implemented modules under `eoh_go/rag/`:

- `schemas.py`: `CorpusItem` dataclass plus JSONL load/save.
- `build_corpus.py`: builds corpus files from existing project materials.
- `retriever.py`: deterministic keyword scoring retriever.
- `prompt_context.py`: formats retrieved items into bounded prompt context.

Corpus sources:

- `eoh_go_workspace/candidate_sources/*.go` -> `code_examples.jsonl`
- `seeds_insertships_go_sa.json` -> `algorithm_cards.jsonl`
- `main.go` API/interface details -> `api_constraints.jsonl`
- `candidate_guard.py` guard rules -> `failure_cases.jsonl`

Runner integration:

- `use_rag_context = False`: clear `EOH_RAG_CONTEXT`.
- `use_rag_context = True` and `rag_context_path` non-empty: use Phase A manual context path.
- Otherwise: auto-build/load corpus, generate query, retrieve top-k items, format context, set `EOH_RAG_CONTEXT`.

Retrieval behavior:

- Pure keyword scoring, no embedding/vector DB.
- Score uses title/tags/summary/constraints, not full code content.
- Deterministic ordering:
  - score descending;
  - kind priority;
  - id lexical order.

Tests added:

- schema round-trip and empty file behavior;
- deterministic retrieval;
- corpus build validity;
- context formatting and max character truncation;
- runner integration timing.

Result:

- Corpus grew to about 15 initial items.
- Retrieval and prompt construction worked.
- Main weakness found: the initial corpus was dominated by historical generated code, especially density-switch candidates. This limited retrieval diversity and made the "literature knowledge" claim weak.

## Phase C: Small Ablation Experiment

Goal: run a small experiment to test whether RAG context helps compared with no context.

Experiment matrix:

- problems: `rc101`, `rc102`, `rc103`
- densities: `d25`, `d50`, `d75`
- arrival scale: `1.0`
- generations: `1`
- population size: `4`
- groups:
  - baseline: no RAG context
  - RAG: automatic retrieval context

Total planned cells: `3 x 3 x 2 = 18` EOH runs.

Added experiment support:

- `--ablation-pair` mode in `eoh_go/experiments/eoh_arrival_grid.py`.
- `eoh_go/experiments/summarize_rag_ablation.py` to compare baseline vs RAG by cell key:
  - `problem`
  - `density`
  - `arrival_scale`
- Summary output under `eoh_go_workspace/reports/tables/rag_ablation_summary/`.

Core metrics:

- guard pass rate: `valid_candidates / population_size`
- bad candidate rate: suspicious + invalid candidates
- objective improvement: `delta_J = best_EOH_J - seed_J`
- response degradation: `best_EOH_Res / seed_Res`

Observed results:

- Some cells were incomplete, especially `rc103 d25` and `rc103 d50`, because SA baseline evaluation returned `seed_J = null`.
- Among complete cells, RAG showed positive signal but was not uniformly better.
- Strong positive case:
  - `rc102 d50`: baseline failed to beat seed, while RAG substantially improved `J` and guard pass rate.
- Negative cases:
  - `rc101 d50` and `rc101 d75`: RAG improved valid rate but worsened best `J`.

Interpretation:

- RAG is not random noise: bad-case analysis showed it consistently retrieved the same density/tightness switch family for some cells.
- The issue is context selection quality, not merely whether context exists.
- Same retrieved strategy can help one problem/density and hurt another.

## Issues Found

1. Initial corpus did not satisfy the advisor's intended source quality.

The first Phase B corpus mostly used historical generated Go code. That is useful as "history-RAG", but it is not the same as literature pseudocode from books or papers.

2. Retrieval query was too coarse.

The automatic query used density and arrival scale, but did not encode enough problem identity. This made rc101 and rc102 sometimes retrieve the same strategy even when their response differed.

3. EOH single-run variance is high.

The same `rc102 d50` cell can produce very different baseline results across runs. Single-run conclusions are unstable.

4. `rc103` baseline reliability is questionable.

`rc103 d25` and `rc103 d50` had null seed results. `rc103 d75` produced a very low seed value, so that cell should be treated with lower confidence unless the benchmark/evaluator path is checked.

5. Long context can hurt generation.

The later literature-RAG single-instance test showed a near-6000 character context. Generated candidates became longer and more failure-prone. This suggests context length and specificity need tuning.

## Follow-up Work

Recommended next steps:

1. Keep Phase A/B infrastructure; it is useful and mostly stable.
2. Split corpus types clearly:
   - history-RAG: generated code and guard experience;
   - literature-RAG: human algorithm pseudocode and constraints.
3. Improve retrieval query with problem-level signals, not only density.
4. For experiments, run repeated seeds or repeated runs per cell before drawing conclusions.
5. Shorten literature context, likely from `6000` chars to around `3000`, then retest.
6. Recheck `rc103` benchmark/evaluator behavior before including it in final analysis.

## Current Practical Takeaway

Phase A proved prompt injection. Phase B proved automatic retrieval and context formatting. Phase C showed that context can materially change generated code quality, but the effect depends on retrieval quality and problem match.

The pipeline is worth continuing, but the next bottleneck is corpus quality plus context selection, not the mechanics of injecting context.
