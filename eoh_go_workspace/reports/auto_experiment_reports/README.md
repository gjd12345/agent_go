# Auto Experiment Reports

This directory contains the current TOCC evidence set. It should contain summaries, compact JSON/Markdown tables, decks, and code records only.

## Core files

- `tocc_current_progress_20260619.md`: current Chinese progress report.
- `tocc_current_progress_20260619.pptx`: current progress deck.
- `tocc_current_progress_20260619_assets/`: editable/rendered assets for the deck.
- `tocc_best_code_records.md`: best evolved code snippets and verified scores.
- `tocc_stabilization_report.md`: stabilization summary.

## Current experiment summaries

- `tocc_stabilization_repeats/`
- `tocc_day1_cvrp_repeat5/`
- `tocc_day2_cvrp_real_evolution_gen4/`
- `tocc_day2_tsp_pure_gen4/`
- `tocc_day2_tsp_tocc_gen4/`
- `tocc_day2_tsp_real_evolution_gen4/`
- `tocc_history_card_audit_20260619/`
- `tocc_history_mixed_cvrp_smoke/`
- `tocc_split_history_cvrp_smoke/`

Each experiment directory should keep only `summary.*`, `success_funnel.*`, `run_index.json`, card decisions, and other compact evidence files.

Raw `run_*` directories are intentionally excluded from this tree and from git. They are archived locally under:

- `archived_experiments/raw_runs_20260619/eoh_go_workspace/reports/auto_experiment_reports/`
