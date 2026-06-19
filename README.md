# agent_go

Research workspace for LLM-based heuristic evolution and TOCC (Trace-Conditioned Operator-Card Controller).

The current codebase is organized around two layers:

- Go dynamic dispatch solver: `main.go`, `routing.go`, `go.mod`, `go.sum`
- Python experiment/control layer: `eoh_go/`
- Patched Agent_EOH core and Go `InsertShips` example: `Agent_EOH/eoh/src/eoh/`
- Dynamic Solomon-style source data for RC101-RC105: `solomon_benchmark_d25/`, `solomon_benchmark_d50/`, `solomon_benchmark_d75/`
- Candidate Go heuristics used during the EOH-Go experiments: `eoh_go_workspace/candidate_sources/`
- Current TOCC reports and decks: `eoh_go_workspace/reports/auto_experiment_reports/`
- Paper notes and related-work drafts: `eoh_go_workspace/reports/paper_notes/`
- Historical reports and figures: `archived_experiments/reports_20260619/`

## Main Artifacts

- Current TOCC progress report: `eoh_go_workspace/reports/auto_experiment_reports/tocc_current_progress_20260619.md`
- Current TOCC progress deck: `eoh_go_workspace/reports/auto_experiment_reports/tocc_current_progress_20260619.pptx`
- Best evolved code records: `eoh_go_workspace/reports/auto_experiment_reports/tocc_best_code_records.md`
- Current auto-experiment report index: `eoh_go_workspace/reports/auto_experiment_reports/README.md`
- Reports layout guide: `eoh_go_workspace/reports/README.md`
- Historical Guarded EOH-Go tables, figures, and paper drafts: `archived_experiments/reports_20260619/`
- Phase summary: `eoh_go/eoh_go_phase0_summary.md`

## Quick Checks

```powershell
go build -o mainbin_sa.exe .
python -m pytest tests/ -q
python -m unittest discover -s tests -q
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
  --output-dir eoh_go_workspace/reports/auto_experiment_reports/manual_eoh_arrival_grid `
  --generations 1 `
  --pop-size 4 `
  --eva-timeout 120 `
  --run-timeout-s 60 `
  --objective-res-weight 0.2
```

## Development Workflow

### Build

```bash
go build -o mainbin_sa.exe .
```

Or use the Makefile:

```bash
make build          # build the main solver
```

### Run tests

**Python unit tests (guard, operator, templates):**

```bash
python -m pytest tests/ -q
```

**Go benchmark integration tests (requires solomon_benchmark data):**

```bash
make test           # run SA solver benchmarks
```

### Code quality

The project currently has no automated Go linting or formatting hooks. When contributing:

- Ensure `go build .` succeeds with no errors.
- Run `python -m pytest tests/ -q` and confirm all tests pass.
- Keep Python imports clean; the project uses `pytest` and `unittest`.

## Notes

The private reference PDF is not included. The report cites it as the local reference manuscript and aligns the experiments with its `Res.`/`J` evaluation style.
