# Memory Pool Spec

## Purpose

PoolAPI is the unified interface for all cross-process shared state in EOH-RAG experiments.
It replaces the previous scattered `shared_pool_*` functions.

## Record Types

| Type | File | Schema |
|------|------|--------|
| run | pool_index.jsonl | `{problem, run_dir, objective, ts}` |
| code | best_codes_{problem}.jsonl | `{code, objective, ts}` |
| operator | operator_stats_{problem}.jsonl | `{operator, improved, delta, ts}` |
| failure | failures_{problem}.jsonl | `{failure_type, pattern_hint, code_hash, ts}` |

## Public API

```python
class PoolAPI:
    def __init__(self, pool_dir: str | Path)

    # Run records
    def register_run(self, problem: str, run_dir: str, objective: float, **meta) -> None
    def best_run(self, problem: str) -> str
    def list_runs(self, problem: str | None = None) -> list[dict]

    # Elite code
    def register_code(self, problem: str, code: str, objective: float, **meta) -> None
    def best_codes(self, problem: str, top_k: int = 3) -> list[dict]

    # Operator stats
    def register_operator_stat(self, problem: str, operator: str, improved: bool, delta: float) -> None
    def operator_weights(self, problem: str) -> dict[str, float]

    # Failure patterns
    def register_failure(self, problem: str, code: str, failure_type: str, pattern_hint: str = "") -> None
    def failure_hints(self, problem: str, top_k: int = 5) -> list[str]
```

## Concurrency

All writes use `fcntl.flock` (POSIX file locking).
Reads do not lock (eventual consistency is acceptable).
Multiple processes can safely write to the same pool_dir simultaneously.

## Storage Layout

```
shared_pool/
├── pool_index.jsonl
├── best_codes_bp_online.jsonl
├── best_codes_tsp_construct.jsonl
├── best_codes_cvrp_construct.jsonl
├── operator_stats_bp_online.jsonl
├── operator_stats_tsp_construct.jsonl
├── operator_stats_cvrp_construct.jsonl
├── failures_bp_online.jsonl
├── failures_tsp_construct.jsonl
├── failures_cvrp_construct.jsonl
└── dynamic_config.json
```

## Invariants

1. PoolAPI is the ONLY writer to these files (no direct file I/O elsewhere)
2. Reads return data sorted by objective (best first for codes)
3. Duplicate entries are filtered by dedup key (objective value for codes)
4. File paths are relative to pool_dir (portable)
