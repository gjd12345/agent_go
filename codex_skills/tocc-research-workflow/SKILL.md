---
name: tocc-research-workflow
description: Use for agent_go TOCC research tasks: planning experiments, running manifests, reading traces, selecting operator cards, updating goals, summarizing results, and preserving best evolved code with verified scores.
---

# TOCC Research Workflow

Use this skill inside the `agent_go` repository for TOCC / EOH research work.

## Core Rule

Treat TOCC as a trace-conditioned search-steering controller:

1. Read existing run summaries and traces.
2. Diagnose search bias, invalid-rate, candidate success rate, and card overlap.
3. Select or propose operator cards.
4. Run a small manifest or smoke test only when needed.
5. Record selected cards, rationale, best verified score, and best generated code.

Do not treat a single run as stable evidence. Mark it as smoke, pilot, or repeat evidence.

## Required Files To Check

- `.codex/goals/tocc_automation_framework.md`
- `AGENTS.md`
- `eoh_go_workspace/reports/auto_experiment_reports/README.md`
- `eoh_go_workspace/reports/auto_experiment_reports/tocc_best_code_records.md`
- `eoh_go/experiments/run_experiment_manifest.py`
- `eoh_go/experiments/summarize_manifest_runs.py`
- `eoh_go/experiments/operator_card_controller.py`

## Standard Commands

Run tests before reporting implementation work:

```bash
PYTHONPATH=. python3 -m pytest tests -q
python3 -m compileall -q eoh_go
go build -o /tmp/eoh_go_mainbin .
```

For manifest dry-runs:

```bash
PYTHONPATH=. python3 -m eoh_go.experiments.manifest_runner \
  --manifest <manifest.json> \
  --output-dir eoh_go_workspace/reports/auto_experiment_reports \
  --dry-run
```

For real overnight experiments, use `caffeinate` and keep raw `run_*` directories out of git.

## Reporting Contract

Every experiment report must include:

- Problem, target function, model, generations, pop size, repeats.
- Selected card IDs and how they were selected.
- Candidate success rate and valid-rate.
- Best verified score, not only population objective.
- Best evolved code snippet.
- Whether evidence is smoke, repeat, or stable.

Write user-facing reports in Chinese unless asked otherwise.
