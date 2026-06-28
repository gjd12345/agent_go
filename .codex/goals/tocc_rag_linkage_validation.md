# TOCC-RAG Linkage Validation

Status: active

Freeze point:

```text
tocc-rag-refactor-v1 -> main@ed2731a
local verification at freeze: 316 passed, 5 subtests passed; compileall passed
remote CI: not verified
```

## Purpose

Validate that the TOCC-RAG chain is connected before any paid smoke or Phase 5 ablation:

```text
arm.candidate_card_ids
  -> legacy CLI transport via --selected-card-ids
  -> --candidate-card-source candidate_card_ids
  -> RAG context build
  -> keyword retrieve / rerank trace
  -> optional outcome memory
  -> optional population features
  -> official_eoh_run_summary.json
```

This goal does not validate performance and does not start Phase 5 ablation.

## Non-Paid Step 1: Manifest Dry-Run

Run from repo root:

```powershell
python -m eoh_go.experiments.batch_runner `
  --manifest eoh_go_workspace/experiments/manifests/tocc_rag_linkage_validation.json `
  --output-dir eoh_go_workspace/reports/auto_experiment_reports `
  --dry-run
```

Expected command evidence:

```text
--selected-card-ids tsp_regret_insertion,tsp_farthest_insertion,tsp_two_opt_awareness,tsp_nearest_insertion
--candidate-card-source candidate_card_ids
--rag-top-k 2
--rag-max-chars 2500
```

Notes:

- `candidate_card_ids` must live on the arm, not under `manifest.rag`.
- `--selected-card-ids` is a legacy CLI transport name; it means candidate allowlist here.
- Current `batch_runner` treats `manifest.rag.prev_run_dir` and `manifest.rag.outcome_file` as global signals. If only one arm should receive population/outcome signals, use a separate manifest or direct `eoh_single_runner` call.

## Non-Paid Step 2: Pre-LLM Smoke

Directly call `eoh_single_runner` with API key cleared. The runner should build RAG context and write summary, then stop at the API environment gate:

```powershell
$env:DEEPSEEK_API_KEY=''
python -m eoh_go.experiments.eoh_single_runner `
  --problem tsp_construct `
  --arm literature_rag `
  --pop-size 4 `
  --generations 0 `
  --rag-top-k 2 `
  --rag-max-chars 2500 `
  --rag-query "tsp regret farthest insertion avoid nearest repetition" `
  --selected-card-ids "tsp_regret_insertion,tsp_farthest_insertion,tsp_two_opt_awareness,tsp_nearest_insertion" `
  --candidate-card-source candidate_card_ids `
  --prev-run-dir eoh_go_workspace/reports/official_eoh_runs/linkage_validation_prev `
  --output-dir eoh_go_workspace/reports/official_eoh_runs/linkage_validation_pre_llm
```

Expected summary evidence:

```text
official_eoh_run_summary.json exists
failure_reason == "missing_env_DEEPSEEK_API_KEY"
rag_trace.rag_candidate_card_ids is non-empty
rag_trace.rag_candidate_card_source == "candidate_card_ids"
rag_trace.candidate_cards_with_zero_keyword_score exists
rag_trace.candidate_cards_dropped_by_zero_keyword_score exists
rag_trace.rag_candidate_zero_score_warning exists
rag_trace.rag_rerank_scores[].selected exists
rag_trace.rag_population_feature_count > 0 when the scratch prev population is present
```

This is a successful linkage validation, not a failed paid experiment.

## Outcome Memory Gate

Preferred synced file:

```text
eoh_go_workspace/rag/corpus/card_outcomes.jsonl
```

Before passing `--outcome-file`, verify:

```powershell
python -c "from pathlib import Path; from eoh_go.rag.card_outcomes import load_outcomes, summarize_all_cards; p=Path('eoh_go_workspace/rag/corpus/card_outcomes.jsonl'); records=load_outcomes(p); summary=summarize_all_cards(records); print({'records': len(records), 'summaries': len(summary)})"
```

Acceptance:

```text
file exists
load_outcomes() succeeds
summarize_all_cards() is non-empty
pre-LLM rag_trace.rag_outcome_summary_count > 0
```

If the file is missing, do not fake outcome memory. Record:

```text
rag_outcome_summary_count == 0
outcome memory missing in this environment
rerun after sync
```

## Explicit Non-Goals

- Do not run paid LLM calls in this goal.
- Do not claim Phase 5 ablation is complete.
- Do not claim performance improvement.
- Do not add embedding, hybrid retrieval, LLM rerank, operator-aware injection, rerank multiplier tuning, or outcome threshold tuning.
- Do not commit raw run outputs, generated runner files, population JSONs, temporary outcome files, API logs, or local summaries.

## Required Verification

After repo edits:

```powershell
python -m compileall -q eoh_go
python -m pytest tests/test_experiment_manifest_runner.py tests/test_official_eoh_run.py tests/test_tocc_v3_loop.py -q
```

After linkage checks:

```text
dry-run command transport is correct
pre-LLM summary exists
RAG trace fields are complete
no API key path stops only after RAG/context construction
```

## Verification Log

2026-06-28 local non-paid validation:

```text
branch: codex/tocc-rag-linkage-validation
base: ed2731a / tocc-rag-refactor-v1
compileall: passed
targeted tests: 45 passed
manifest dry-run: passed
pre-LLM smoke: passed
paid LLM call: not run
```

Dry-run evidence:

```text
printed 2 runs for tsp_construct:
- keyword_rag
- outcome_population_rag

both commands included:
--selected-card-ids tsp_regret_insertion,tsp_farthest_insertion,tsp_two_opt_awareness,tsp_nearest_insertion
--candidate-card-source candidate_card_ids
--rag-top-k 2
--rag-max-chars 2500
```

Pre-LLM smoke evidence:

```text
summary path:
eoh_go_workspace/reports/official_eoh_runs/linkage_validation_pre_llm/official_eoh_run_summary.json

failure_reason: missing_env_DEEPSEEK_API_KEY
rag_candidate_card_source: candidate_card_ids
candidate count: 4
rerank score rows: 4
rerank selected flags: [true, true, false, false]
rag_population_feature_count: 5
rag_outcome_summary_count: 0
```

Outcome memory gate:

```text
eoh_go_workspace/rag/corpus/card_outcomes.jsonl: missing in this environment
status: not a linkage failure; rerun outcome gate after syncing the file
```
