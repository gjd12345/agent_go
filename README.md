# EOH-RAG: Trace-Conditioned Small-Model Controllers for Heuristic Evolution

Research workspace for training small models to select strategy cards (RAG reranker) and generate/repair heuristic code, using traces from LLM-driven evolutionary optimization experiments.

## Current Research Direction

1. **Batch data collection**: Island Model parallel experiments (gen=8/16, shared pool, 3 problems)
2. **RAG reranker small model**: Learn strategy-card selection from experiment traces
3. **Code gen/repair small model**: Learn heuristic code generation from successful evolution trajectories

## Active Pipeline

```
eoh_go/experiments/      — batch_runner, eoh_single_runner, rag_context_builder
eoh_go/rag/              — retriever, reranker, llm_reranker, card_outcomes, features, card_synthesis
eoh_go/tocc/             — agent, gatekeeper, pipeline, controller
eoh_go/llm/              — LLM client (JoyAI / OpenCode)
eoh_go_workspace/        — corpus, manifests, reports, shared_pool
```

## Problems (Official EOH Benchmarks)

| Problem | Type | Best Result | vs Baseline |
|---------|------|------------|-------------|
| `tsp_construct` | TSP50, 8 instances | 6.004 | +8.5% |
| `cvrp_construct` | CVRP50, 16 instances | 12.423 | +8.1% |
| `bp_online` | Online Bin Packing | 0.00674 | +83.1% |

## Quick Start

```bash
# Run batch experiment with shared pool (island model)
export $(grep -v '^#' ~/.config/agent_go/opencode.env | xargs)
python3 -m eoh_go.experiments.batch_runner \
  --manifest eoh_go_workspace/experiments/manifests/high_gen_tsp_construct.json \
  --force --shared-pool-dir eoh_go_workspace/shared_pool

# Run tests
python3 -m pytest tests/ -q
```

## Repository Structure

```
eoh_go/                  — Python experiment framework (active)
eoh_go_workspace/        — Data: corpus, manifests, reports, shared pool
scripts/                 — Launch scripts for parallel experiments
docs/                    — Architecture docs, cleanup plan, isolation contract
tests/                   — Test suite (284 pass)
legacy/                  — Archived: InsertShips v0, old grids, old reports
main.go, routing.go      — Go dispatch solver (frozen, historical)
```

## Key Design Decisions

- **Island Model**: 15+ parallel processes share best-code pool, outcome memory, failure patterns
- **Go/Python isolation**: Go solver frozen as evaluator, Python is research layer (see `docs/ISOLATION.md`)
- **Shared pool**: Cross-process elite sharing via `--shared-pool-dir` (see `docs/CLEANUP_PLAN.md`)
- **Baselines fixed**: TSP=6.560, CVRP=13.519, BP=0.0398 (Round 1 A_pure median, never re-run)
