# Agent Governance Rules

## Purpose

Use subagents to prevent uncontrolled code growth, untested changes, and unsafe generated-code execution.

## Agent Roles

**Core (always available):**

- `scout`: read-only. Maps affected files, defines scope, identifies test gaps. Merges repo_mapper + architect + test_designer.
- `implementer`: workspace-write. Only agent allowed to edit files.
- `gatekeeper`: read-only. Reviews correctness, security, test coverage, maintainability, delivery readiness. Merges reviewer + security_auditor + quality_supervisor.
- `verifier`: read-only. Runs tests and smoke checks, reports command evidence.

**On-demand:**

- `rag_researcher`: read-only. Researches RAG, papers, external repos. Enable only for tasks involving retrieval, literature, or external knowledge.
- `exploration_analyst`: read-only. Monitors TOCC/EoH live experiments. Reads run_index, traces, valid rate, best score, cards, failure_reason. Recommends stop/resume/change_cards/change_query/reduce_budget. Never edits files or executes runs. Used for E2-E5 runs.

## Task Tiers

| Tier | Scope | Agents |
|------|-------|--------|
| **S** | docs, config, small fixes | scout → implementer → verifier |
| **M** | feature, refactor, code change | scout → implementer → gatekeeper → verifier |
| **L** | RAG, sandbox, auth, security boundary, core architecture | scout → rag_researcher? → implementer → gatekeeper → verifier |

**Escalation rule:** If the change touches auth, sandbox, permissions, external calls, data deletion, secrets, RAG retrieval, eval logic, eval-guard, or test infrastructure, the workflow MUST use L tier. For L tasks, gatekeeper may request an extra focused security or test-design pass.

## Experiment Tiers

EOH/RAG work is a research workflow. Use the engineering tier (S/M/L) together with an experiment tier (E0-E5).

| Exp Tier | Scope | Execution rule | Required review |
|----------|-------|----------------|-----------------|
| **E0** | read-only analysis, report cleanup, best-code/card-decision records | may run automatically | verifier |
| **E1** | `--dry-run`, `--no-run`, manifest validation, summary regeneration | may run automatically | verifier |
| **E2** | smoke run: `gen <= 1` and `runs <= 2` | may run after local safety checks; user confirmation preferred for paid APIs | exploration_analyst → verifier |
| **E3** | repeat check: `runs 3-20` and `gen <= 1` | requires explicit user confirmation | exploration_analyst → gatekeeper → verifier |
| **E4** | deep evolution: `gen > 1` or `runs > 20` | requires explicit plan, background monitoring, and user confirmation | scout → exploration_analyst → gatekeeper → verifier |
| **E5** | paper-level matrix: multi-problem, multi-arm, multi-repeat | split into staged batches with milestone reviews | full L workflow + milestone gatekeeper |

### Exploration vs. Paper Evidence

Early-stage exploration should not spend large repeat budgets before a direction is validated.

| Stage | Purpose | Repeat policy | Claim allowed |
|-------|---------|---------------|---------------|
| Exploration | find promising cards/problems and failure modes | 1 smoke or 2-3 repeats | "positive/negative best-score signal" |
| Stabilization | check whether a signal repeats | 3-5 repeats | "repeat-level signal" |
| Paper evidence | support thesis claims | 5-10+ repeats per arm, budget-aligned | "stable improvement" only with statistics |

Do not require heavy repeat for every exploratory idea. Do require repeat before writing stable-effect claims.

### Exploration Analyst Rules

Use `exploration_analyst` for E2-E5 runs and for long background experiments. It is a read-only, in-process advisor, not an implementer.

It should inspect:

- `run_index.json`
- `official_eoh_run_summary.json`
- `rag_trace.rag_selected_items`
- `rag_trace.rag_all_scores`
- `rag_trace.rag_context_chars`
- `run_summary.best_objective`
- `run_summary.valid_candidates / population_size`
- `failure_reason`, timeout, API failure, valid collapse
- best-code structure changes

It should recommend one of:

- `continue`: signal is promising and run health is good
- `stop`: no new information, repeated failures, or budget mismatch
- `resume`: incomplete run can safely continue
- `reduce_budget`: context too long, valid collapse, or high failure rate
- `change_cards`: selected cards overlap baseline or point in wrong direction
- `change_query`: cards are close but retrieval ranking is wrong
- `switch_problem`: current target has low information gain
- `write_report`: result is an inflection point worth documenting

It must distinguish:

- smoke vs repeat vs deep evolution
- historical best vs current-suite best
- best-score signal vs statistically stable improvement
- selected_card_ids requested vs rag_trace.rag_selected_items actually injected

It must not:

- edit files
- execute commands
- read or print API keys
- approve its own recommendations
- convert exploratory signals into stable claims

## Write Discipline

Only `implementer` may edit files.

Do not spawn multiple write-capable agents. Do not allow parallel edits.

Implementation begins only after scout returns its report.

## Subagent Output Contract

- **PASS**: Return only the verdict line. Do not write a report.
- **WARNING or FAIL**: Return verdict + findings (P0/P1/P2/P3) + evidence (file:line) + recommended action.

## Merge Gate

The task is not complete if `gatekeeper` or `verifier` returns FAIL.

P0/P1 findings block completion.

`implementer` cannot self-approve.

## Conflict Resolution

1. Correctness beats style.
2. Security beats convenience.
3. Tests beat assumptions.
4. Existing architecture beats speculative redesign.
5. Runtime evidence beats static speculation.
6. If unresolved, choose the lower-risk option and document the tradeoff.

## Project: EOH-VRP / TOCC

Evolutionary optimization with Trace-Conditioned Operator-Card Controller (TOCC).
Current phase: V2 agent assisted controller, preparing V3 bounded auto-loop.

### TOCC V2 Agent Pipeline

```
trace -> LLM proposer -> proposal JSON -> rule gatekeeper -> manifest -> runner -> new trace -> summarizer
```

V2 agent role: **LLM as trace-conditioned proposer**, NOT autonomous agent.
Gatekeeper enforces: cards exist, problem prefix matches, no forbidden fields.

### Key Paths

| Path | Purpose |
|------|---------|
| `eoh_go/experiments/official_eoh_run.py` | Official EOH benchmark runner |
| `eoh_go/experiments/operator_card_controller.py` | V1 rule-based TOCC controller |
| `eoh_go/experiments/tocc_agent.py` | V2 LLM proposer (trace → proposal) |
| `eoh_go/experiments/tocc_gatekeeper.py` | V2 rule validator (R1-R11, alias support) |
| `eoh_go/experiments/tocc_v2_pipeline.py` | V2 orchestrator (agent → gatekeeper) |
| `eoh_go/experiments/run_experiment_manifest.py` | Manifest-driven experiment runner |
| `eoh_go/experiments/summarize_manifest_runs.py` | Auto summarizer (tables + code + report) |
| `eoh_go/rag/build_corpus.py` | Corpus building + mode filtering |
| `eoh_go/rag/retriever.py` | Keyword-weighted retrieval |
| `eoh_go/rag/prompt_context.py` | Prompt formatting (API RULES + STRATEGY CARDS) |
| `eoh_go_workspace/experiments/manifests/*.json` | Experiment manifests |
| `eoh_go_workspace/experiments/card_memory/` | Card outcome records (research asset) |
| `eoh_go_workspace/reports/auto_experiment_reports/` | Suite-level summaries, proposals, reports |
| `eoh_go_workspace/rag/corpus/` | RAG corpus JSONL files |
| `~/.config/agent_go/chatrhino.env` | API credentials (never echo) |

### Architecture Rule

When the codebase architecture changes (new modules, pipeline refactors, RAG flow modifications), draw an architecture diagram with version suffix:

```
eoh_go_workspace/reports/figures/architecture_v{1,2,3...}.drawio
```

Labels: RAG Pipeline, EOH Evolution Loop, Experiment Flow, Module Dependencies.

### Evolution Retention Rule

After every evolution run (gen >= 3 or best_J significantly below seed), save the best
candidate to `eoh_go_workspace/candidate_sources/` and rebuild the corpus.

**Admission criteria**: only candidates with `best_build_ok=true` AND
`selected_best_status_after_eval=valid` AND `best_EOH_J` not null.
Move candidates from build-failed runs to `candidate_sources/quarantine/`.

```bash
# Save best candidate from last generation
python3 -c "
import json, os, glob
# Find pop best from last gen, copy code to candidate_sources/
..."

# Rebuild corpus
python3 -c "from eoh_go.rag.build_corpus import build_all_corpora; build_all_corpora('.')"
```

This creates a positive feedback loop: evolution discovers strategies → corpus grows
→ history-RAG retrieves proven patterns → future runs benefit.

### Documentation Milestones

Proactively suggest updating `eoh_go_workspace/reports/tables/rag_experiments_report.md`
when a **genuine inflection point** is reached. Do NOT suggest for routine runs.

**Trigger (suggest):**
- A new experiment completes that shifts a finding from tentative → confirmed
- A bug is found and verified (e.g. history-RAG strategy_pool was broken)
- A parameter/methodology decision that changes future direction (e.g. "switch from gen=1 to gen=8 exploration")
- A new cell or RAG mode shows a result that contradicts or extends previous claims

**Don't trigger for:**
- Routine experiment runs, repeat completions, parameter tweaks
- Slides or diagrams (those have their own rules)

**Format:** one-line suggestion before taking action, e.g. "Worth adding this to the report?"
Wait for user nod before writing. Keep updates targeted — don't rewrite the whole file.

### Skills

| Skill | Trigger | Use |
|-------|---------|-----|
| `drawio` | diagram, flowchart, architecture, draw.io | Draw/update architecture diagrams |
| `pptx` | slides, presentation, deck | Generate meeting/presentation slides |
| `eoh-experiment` | run experiment, ablation, grid search | Run EOH experiments with correct params |
| `eoh-analyze` | analyze results, compare, delta J, summary | Compute median ΔJ, valid rates, seed checks |

### Commands Quick Reference

```bash
# Source API key
export $(grep -v '^#' ~/.config/agent_go/chatrhino.env | xargs)

# Run ablation pair
python3 -m eoh_go.experiments.eoh_arrival_grid \
  --root . --problem rc101.json rc102.json --density d50 d75 \
  --arrival-scale 1.0 --pop-size 8 --generations 1 \
  --rag-mode literature --rag-top-k 0 --rag-max-chars 2500 \
  --llm-model JoyAI-LLM-Pro \
  --output-dir eoh_go_workspace/reports/tables/<exp> \
  --ablation-pair --use-density-source-dirs --source-dir solomon_benchmark

# Deep evolution
--pop-size 4 --generations 8  # gen > pop for exploration depth

# Resume
--resume --output-dir <existing_run_dir>
```

## Safety Rules

Generated candidate code must run only through guarded evaluator paths.
Do not execute generated Python or Go directly in the main process.
RAG code must live under `eoh_go/rag/`; generated artifacts and reports stay under `eoh_go_workspace/`.
API credentials must never be printed or echoed.

## Completion Requirements

Final response must include:

- files changed
- commands run
- test results
- subagent verdicts
- unresolved risks
- merge recommendation
