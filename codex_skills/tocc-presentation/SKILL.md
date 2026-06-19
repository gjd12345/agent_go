---
name: tocc-presentation
description: Use for creating TOCC/agent_go PPT decks, diagrams, architecture figures, experiment flowcharts, code-evolution visuals, and advisor-ready progress slides from repository reports.
---

# TOCC Presentation Skill

Use this skill when creating or editing PPT decks and diagrams for `agent_go`.

## Inputs

Prefer these current sources:

- `eoh_go_workspace/reports/auto_experiment_reports/tocc_current_progress_20260619.md`
- `eoh_go_workspace/reports/auto_experiment_reports/tocc_best_code_records.md`
- `eoh_go_workspace/reports/auto_experiment_reports/README.md`
- `.codex/goals/tocc_automation_framework.md`

Historical figures and old reports live under:

- `archived_experiments/reports_20260619/`

## Workflow

1. Draft the story in Chinese first: TOCC definition, workflow, evidence, limitations, next steps.
2. Use editable diagrams for system architecture and data flow.
3. Use PPT-native text/tables/shapes where possible; avoid full-slide screenshots as final slides.
4. Include concrete evolved code snippets when discussing code evolution.
5. Render or inspect the deck before delivery; fix unreadable text and cramped diagrams.

## Diagram Guidance

For architecture diagrams:

- Show `trace -> diagnosis -> card selection -> EOH run -> summary -> card memory`.
- Distinguish strategy cards, API constraints, failure warnings, and history cards.
- Keep labels large enough for advisor meetings.

For evolution diagrams:

- Plot generation or phase on the x-axis.
- Plot objective quality on the y-axis.
- Attach callouts with concrete code changes, not only strategy names.

## Output Locations

Use:

- PPTX: `eoh_go_workspace/reports/auto_experiment_reports/`
- Assets: sibling directory named `<deck_name>_assets/`

Keep scratch files outside the repository unless explicitly requested.
