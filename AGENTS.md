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

## Task Tiers

| Tier | Scope | Agents |
|------|-------|--------|
| **S** | docs, config, small fixes | scout → implementer → verifier |
| **M** | feature, refactor, code change | scout → implementer → gatekeeper → verifier |
| **L** | RAG, sandbox, auth, security boundary, core architecture | scout → rag_researcher? → implementer → gatekeeper → verifier |

**Escalation rule:** If the change touches auth, sandbox, permissions, external calls, data deletion, secrets, RAG retrieval, eval logic, eval-guard, or test infrastructure, the workflow MUST use L tier. For L tasks, gatekeeper may request an extra focused security or test-design pass.

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

## Project: EOH-VRP

Evolutionary optimization of InsertShips heuristics for VRPTW with RAG context injection.

### Key Paths

| Path | Purpose |
|------|---------|
| `eoh_go/experiments/eoh_arrival_grid.py` | Main experiment runner (grid + ablation pair) |
| `eoh_go/eoh_runner/runner.py` | EOH config + RAG context injection |
| `eoh_go/rag/build_corpus.py` | Corpus building + mode filtering |
| `eoh_go/rag/retriever.py` | Keyword-weighted retrieval |
| `eoh_go/rag/prompt_context.py` | Prompt formatting with max_chars limit |
| `eoh_go_workspace/reports/tables/` | Experiment results |
| `eoh_go_workspace/reports/figures/` | Diagrams + slides |
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
