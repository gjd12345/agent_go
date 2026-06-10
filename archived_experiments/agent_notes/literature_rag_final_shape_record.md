# Literature-RAG Final Shape Record

Date: 2026-05-26
Repo: /Users/guojiadong.9/agent_ad/agent_go
Scope: agent record only; not part of project source.

## Objective

Finalize Literature-RAG infrastructure so prompt context is built from short executable instruction cards instead of long reference documents or generated code.

The key design correction was classification:

- algorithm_card: strategy selection cards that compete in retrieval top-k.
- api_constraint: fixed API and safety rules that are always injected before strategy cards.
- failure_case: short warning summaries; source content is never dumped into prompt context.

## Problem Fixed

The previous corpus shape mixed unrelated content types:

- sa_seed_1 was stored as an algorithm_card even though it is an API usage skeleton.
- api_constraints.jsonl contained a large main.go excerpt.
- failure_case entries contained candidate_guard.py source text.
- prompt_context.py emitted one repeated block format, so API rules, strategy cards, and failure cases were all treated alike.

This caused context bloat and poorer retrieval: non-strategy material competed with literature strategy cards.

## Final Data Shape

algorithm_cards.jsonl now contains exactly five curated literature strategy cards:

- nearest_insertion
- farthest_insertion
- solomon_i1
- regret2_insertion
- cw_savings

Each card is a short Skill/When/Do/Fallback/Safety instruction card. Content is ASCII-only and <=450 chars.

api_constraints.jsonl now contains:

- insertships_api_skeleton

This is a short API rule card, <=400 chars, source_path=curated, with no Go source code.

sa_seed_1 no longer appears in algorithm_cards and does not participate in literature top-k retrieval.

## Code Changes

build_corpus.py:

- build_algorithm_cards() is now manual-only and returns [].
- build_api_constraints() generates the fixed insertships_api_skeleton instead of reading main.go.
- filter_corpus_by_mode("literature") includes literature IDs, api_constraint, and failure_case, but not sa_seed_1.
- build_all_corpora() preserves curated algorithm_cards.jsonl when it exists and does not overwrite it.

prompt_context.py:

- format_prompt_context() now supports global_items.
- Output is two-section:
  - GLOBAL SAFETY / API RULES
  - RETRIEVED STRATEGY CARDS
- Global section does not contain "Retrieved item".
- failure_case strategy entries output title, summary, and first two constraints only; content is skipped.

runner.py:

- API constraints are split into rag_global_items and excluded from the retrieval pool.
- Retrieval runs only over strategy_pool.
- rag_trace now records rag_global_items and rag_selected_items separately.

eoh_arrival_grid.py:

- Carries rag_mode and trace-derived fields into result rows.

Tests:

- Added/updated coverage for curated corpus preservation.
- Added no-sa_seed_1 assertions.
- Added API skeleton size/source checks.
- Added two-section prompt checks.
- Added failure_case no-content-leak checks.
- Added api_constraint-not-in-retrieval-pool checks.

## Verification

Commands run:

```text
PYTHONPATH=. python3 -m unittest discover -s tests -q
python3 -m compileall -q eoh_go
go build -o /tmp/eoh_go_mainbin .
git diff --check
```

Results:

- 39 tests passed.
- Python compileall passed.
- Go build passed.
- diff whitespace check passed.

Inline specification check passed:

- algorithm_cards contains exactly five LITERATURE_IDS.
- sa_seed_1 is not in algorithm_cards.
- insertships_api_skeleton exists, <=400 chars, no Go source code.
- all literature skill card content <=450 chars and ASCII.
- literature mode excludes sa_seed_1.
- api_constraint is not in retrieval results.
- prompt context has GLOBAL before RETRIEVED.
- final literature context was 2413 chars.
- no package main or func InsertShips leaked into context.
- failure_case content did not leak into context.

Observed retrieved top-k in final check:

```text
farthest_insertion
nearest_insertion
negative_or_missing_result
```

## Governance Notes

Subagent workflow:

- scout: identified remaining classification and two-section prompt gaps.
- implementer: applied the final shape.
- gatekeeper: found two P2 issues.
- implementer fix: preserved section headers under tight budgets and changed API skeleton source_path to curated.
- verifier: full tests and inline checks passed.

No real LLM experiments were run. No API key was read or printed.

## Remaining Non-Task Workspace State

The repo still has unrelated pre-existing experimental artifacts not included in the intended RAG infrastructure commit:

- eoh_go_workspace/reports/tables/rag_ablation_summary/rag_ablation_summary.json
- eoh_go_workspace/reports/tables/rag_ablation_summary/rag_ablation_summary.md
- eoh_go_workspace/candidate_registry.json
- eoh_go_workspace/reports/tables/rag_ablation_smoke/
- eoh_go_workspace/reports/tables/rag_literature_rc102d50/

These should not be included in the Literature-RAG infrastructure commit unless explicitly requested.
