---
name: eoh-experiment
description: Use for EOH and TOCC-RAG experiment work in this repo: manifest dry-runs, pre-LLM smoke checks, paid smoke planning, Phase 5 ablations, candidate_card_ids transport, outcome/population signal validation, and official_eoh_run_summary trace inspection. Prefer this over old Solomon/grid experiment templates.
---

# EOH / TOCC-RAG Experiment

Use the current pipeline:

```text
manifest.json
  -> python -m eoh_go.experiments.batch_runner
  -> python -m eoh_go.experiments.eoh_single_runner
  -> official_eoh_run_summary.json
  -> python -m eoh_go.experiments.reports.run_summarizer
```

Legacy `eoh_arrival_grid` / Solomon templates are not the default for TOCC-RAG.

## Safety

- Never print API keys or full auth headers.
- Do not run paid LLM calls unless the user confirms API readiness.
- For non-paid checks, clear `DEEPSEEK_API_KEY` so the runner stops after RAG trace construction.
- Do not commit raw run outputs, generated `_run_official_eoh.py`, population JSONs, temporary outcome files, API logs, or local summaries.

## Field Contract

- `arm.candidate_card_ids` is the canonical candidate pool field.
- `selected_card_ids` and `cards` are legacy fallbacks only.
- CLI transport still uses `--selected-card-ids`; treat it as a candidate allowlist.
- Include `--candidate-card-source candidate_card_ids` when the manifest source is `candidate_card_ids`.
- `manifest.rag.prev_run_dir` and `manifest.rag.outcome_file` are global/batch signals; split manifests if arms need different signals.

## Non-Paid Linkage Check

Run manifest dry-run:

```powershell
python -m eoh_go.experiments.batch_runner `
  --manifest eoh_go_workspace/experiments/manifests/tocc_rag_linkage_validation.json `
  --output-dir eoh_go_workspace/reports/auto_experiment_reports `
  --dry-run
```

Then run pre-LLM smoke with API key cleared:

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

Expected non-paid result:

```text
failure_reason == "missing_env_DEEPSEEK_API_KEY"
official_eoh_run_summary.json exists
rag_trace is populated
```

## Trace Fields To Check

```text
rag_candidate_card_ids
rag_candidate_card_source
rag_candidate_pool_size_after_filter
rag_selection_space_warning
candidate_cards_with_zero_keyword_score
candidate_cards_dropped_by_zero_keyword_score
rag_candidate_zero_score_warning
rag_rerank_scores[].selected
rag_outcome_summary_count
rag_population_feature_count
```

Do not use the obsolete name `rag_candidate_zero_score_items`.

## Paid Smoke Scope

After API is provided, keep the first paid smoke tiny:

```text
problem: tsp_construct
arms: keyword_rag, outcome_population_rag
generations: [0]
pop_size: 4
repeats: 1
top_k: 2
```

This validates real run output only. It does not prove performance improvement.
