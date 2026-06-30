# TRD: EOH-RAG System Architecture

## System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Experiment Control Layer                   │
│  batch_runner → eoh_single_runner → official EoH subprocess  │
├─────────────────────────────────────────────────────────────┤
│                    RAG / Selection Layer                      │
│  rag_context_builder → reranker / llm_reranker → cards       │
├─────────────────────────────────────────────────────────────┤
│                    Memory / Pool Layer                        │
│  PoolAPI → best_codes / outcomes / failures / operator_stats │
├─────────────────────────────────────────────────────────────┤
│                    Evaluation Layer                           │
│  evaluator → baselines → adaptive_target                     │
├─────────────────────────────────────────────────────────────┤
│                    Evidence / Tracking Layer                  │
│  RunTracker → evidence/ → reports/                           │
└─────────────────────────────────────────────────────────────┘
```

## Module Responsibilities

| Module | Owns | Does NOT Own |
|--------|------|-------------|
| `batch_runner.py` | Execution scheduling, manifest parsing | Evaluation logic, pool storage |
| `eoh_single_runner.py` | Single run lifecycle, subprocess mgmt | Card selection, outcome writing |
| `rag_context_builder.py` | Prompt assembly, card filtering | LLM calls, pool reads |
| `pool_api.py` | All shared pool read/write | Evaluation decisions |
| `evaluator.py` | Baseline comparison, pass/fail | Pool writes, config changes |
| `hooks.py` | Post-run feedback (pool/card/outcome) | Execution control |
| `run_tracker.py` | Run metadata, directory layout | Summary generation |

## Data Flow

```
manifest.json
    ↓
batch_runner (expands matrix, schedules)
    ↓
eoh_single_runner (RAG context → subprocess → summary)
    ↓
hooks.on_run_success/failure
    ├→ PoolAPI.register_run/code/operator/failure
    ├→ evaluator.evaluate_run
    └→ RunTracker.save_*
```

## Key Data Schemas

### pool_index.jsonl
```json
{"problem": "bp_online", "run_dir": "...", "objective": 0.00674, "ts": 123456}
```

### best_codes_*.jsonl
```json
{"code": "def score(...)...", "objective": 0.00674, "ts": 123456}
```

### eval_result.json
```json
{"problem": "...", "objective": ..., "baseline": ..., "improvement": ..., "passed": true, "decision": "archive"}
```

## Invariants

1. All pool writes go through PoolAPI (never direct file I/O from batch_runner)
2. Evaluation decisions are deterministic (no LLM in evaluator)
3. LLM calls only happen in: llm_reranker, card_synthesis, eoh subprocess
4. Baselines are fixed constants, never recomputed from data
5. Evidence directories are immutable once created (append-only)
