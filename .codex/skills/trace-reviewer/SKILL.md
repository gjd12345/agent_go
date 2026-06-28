---
name: trace-reviewer
description: Use to audit official_eoh_run_summary.json, rag_trace, run_index.json, or TOCC-RAG smoke outputs. Trigger whenever the user asks whether a run is trustworthy, whether rerank/outcome/population actually connected, or whether a trace can support an ablation claim.
---

# TOCC-RAG Trace Reviewer

Review traces as evidence. Passing code is not enough; verify the run measured what it claims.

## Input

Primary file:

```text
official_eoh_run_summary.json
```

Optional:

```text
run_index.json
population_generation_*.json
card_outcomes.jsonl
```

## Checks

Inspect:

```text
failure_reason
run_summary.ok
run_summary.valid_candidates
run_summary.best_objective
rag_trace.rag_candidate_card_ids
rag_trace.rag_candidate_card_source
rag_trace.rag_candidate_pool_size_after_filter
rag_trace.rag_selection_space_warning
rag_trace.rag_rerank_enabled
rag_trace.rag_rerank_scores[].selected
rag_trace.rag_outcome_summary_count
rag_trace.rag_population_feature_count
rag_trace.candidate_cards_with_zero_keyword_score
rag_trace.candidate_cards_dropped_by_zero_keyword_score
rag_trace.rag_candidate_zero_score_warning
```

Flag risks:

```text
candidate pool size <= top_k
rerank enabled but no choice space
outcome summary count == 0 for outcome arm
population feature count == 0 for population arm
all selected cards are the old baseline family
selected_card_ids / candidate_card_ids semantics are mixed
```

## Verdict Labels

Use one:

```text
linkage_valid
paid_smoke_valid
ablation_usable
inconclusive
invalid_for_claim
```

Never call a run performance-valid when only linkage was tested.

## Output

Return concise evidence:

```text
verdict
what is proven
what is not proven
blocking trace gaps
next rerun command or required artifact
```
