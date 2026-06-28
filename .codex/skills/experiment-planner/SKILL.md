---
name: experiment-planner
description: Use when turning a TOCC-RAG hypothesis into a bounded experiment manifest or ablation plan. Triggers include Phase 5 ablation, paid smoke, non-paid dry-run, candidate pool validation, outcome/population comparisons, and requests to avoid over-expanding experiments.
---

# TOCC-RAG Experiment Planner

Convert a hypothesis into the smallest manifest that can answer it.

## Inputs

Look for:

```text
hypothesis
problem
arms
generations
pop_size
repeats
top_k
candidate_card_ids
required prev_run_dir
required outcome_file
```

If an outcome file is required, prefer:

```text
eoh_go_workspace/rag/corpus/card_outcomes.jsonl
```

If it is missing, mark outcome signal as unavailable instead of inventing evidence.

## Planning Rules

- Put `candidate_card_ids` on each arm.
- Keep `rag.top_k` and `rag.max_chars` in `manifest.rag`.
- Remember `manifest.rag.prev_run_dir` and `manifest.rag.outcome_file` are global/batch signals.
- Split manifests when one arm needs outcome/population signals and another must stay keyword-only.
- Estimate matrix size before any real run.
- Keep first paid smoke to `generations=[0]`, `pop_size=4`, `repeats=1`.

## First Phase 5 Matrix

Only start with:

```text
A. pure_eoh
B. keyword_rag
C. keyword_rag + outcome
D. keyword_rag + outcome + population
```

Do not add embedding, hybrid retrieval, LLM rerank, operator-aware injection, threshold tuning, or multiplier tuning to the first ablation.

## Output

Return:

```text
manifest path or manifest JSON
commands to dry-run
commands to run
expected trace fields
acceptance criteria
known environment gaps
```

Label results carefully:

```text
linkage validated
paid smoke pending
exploratory
performance not validated
```
