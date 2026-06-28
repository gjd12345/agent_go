# TOCC-RAG Skills

This folder preserves reusable TOCC-RAG workflows as local Codex skills.

The skills are intentionally small and operational. They are for keeping the
project from re-learning the same experiment, trace, card, and review routines
after every refactor.

## Core Skills

```text
eoh-experiment            current EOH / TOCC-RAG experiment runner workflow
experiment-planner        convert hypotheses into bounded manifests and gates
trace-reviewer            inspect official_eoh_run_summary.json for validity
paper-to-card             turn papers or abstracts into grounded card drafts
outcome-memory-auditor    audit card_outcomes.jsonl evidence
population-feature-auditor audit population feature extraction and overlap
refactor-reviewer         review diffs against TOCC-RAG refactor contracts
```

## Project Position

TOCC-RAG is not an end-to-end paper-writing system. Treat it as:

```text
a controllable, auditable, ablation-friendly EOH enhancement platform
```

The core loop is:

```text
paper / prior run
  -> strategy card / outcome memory / population features
  -> candidate_card_ids
  -> keyword retrieve
  -> outcome/population rerank
  -> final injected cards
  -> trace and outcome feedback
```

## Guardrail

Do not mix these into the first Phase 5 ablation unless explicitly requested:

```text
embedding retrieval
hybrid retrieval
LLM rerank
operator-aware injection
rerank multiplier tuning
outcome threshold tuning
AI-Scientist-style end-to-end paper automation
```
