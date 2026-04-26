# agent_go

Minimal EOH-Go workspace for evolving Go insertion heuristics in a dynamic dispatch benchmark.

This repository contains the smallest publishable subset of the local experiment:

- Go dynamic dispatch solver: `main.go`, `routing.go`, `go.mod`, `go.sum`
- EOH-Go experiment wrapper: `eoh_go/`
- Patched Agent_EOH core and Go `InsertShips` example: `Agent_EOH/eoh/src/eoh/`
- Dynamic Solomon-style source data for RC101-RC105: `solomon_benchmark_d25/`, `solomon_benchmark_d50/`, `solomon_benchmark_d75/`
- Cleaned experiment tables and repeat validation: `eoh_go_workspace/reports/tables/`
- Candidate Go heuristics used during the EOH-Go experiments: `eoh_go_workspace/candidate_sources/`
- Paper-style figures and comparison charts: `eoh_go_workspace/reports/figures/`
- Full Chinese LaTeX draft and compiled PDF: `eoh_go_workspace/reports/paper_draft_full_20260426/`

## Main Artifacts

- Full Chinese draft PDF: `eoh_go_workspace/reports/paper_draft_full_20260426/build/guarded_eoh_go_full_draft_cn.pdf`
- Full Chinese draft source: `eoh_go_workspace/reports/paper_draft_full_20260426/guarded_eoh_go_full_draft_cn.tex`
- Paper-style comparison tables: `eoh_go_workspace/reports/figures/paper_style_tables_20260426/`
- Valid comparison charts: `eoh_go_workspace/reports/figures/valid_comparison_charts_20260426/`
- Cleaned RC101-RC105 summary: `eoh_go_workspace/reports/tables/eoh_grid_cleaned_summary_rc101_105/clean_summary.md`
- Repeat validation summary: `eoh_go_workspace/reports/tables/eoh_selected_repeats_summary_20260426/selected_repeat_summary.md`
- Phase summary: `eoh_go/eoh_go_phase0_summary.md`

## Quick Checks

```powershell
go build -o mainbin_sa.exe .
python -m pytest tests/test_candidate_guard.py -q
python -m eoh_go.experiments.build_paper_style_table_image
python -m eoh_go.experiments.build_paper_style_table_image --repeat-only
python -m eoh_go.experiments.build_full_paper_draft
```

To run a small EOH grid, configure the DeepSeek/OpenAI-compatible API key in your environment first, then use:

```powershell
python -m eoh_go.experiments.eoh_arrival_grid `
  --root "." `
  --problem rc101.json `
  --density d25 --density d50 --density d75 `
  --arrival-scale 1.0 --arrival-scale 0.9 --arrival-scale 0.8 --arrival-scale 0.7 --arrival-scale 0.6 `
  --use-density-source-dirs `
  --llm-model deepseek-v4-flash `
  --output-dir eoh_go_workspace/reports/tables/eoh_arrival_grid_flash_dynamic_full `
  --generations 1 `
  --pop-size 4 `
  --eva-timeout 120 `
  --run-timeout-s 60 `
  --objective-res-weight 0.2
```

## Notes

The private reference PDF is not included. The report cites it as the local reference manuscript and aligns the experiments with its `Res.`/`J` evaluation style.
