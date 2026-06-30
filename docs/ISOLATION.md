# Go/Python Isolation Contract

## Architecture

```
                Python side (experiment controller)
        eoh_go/ TOCC / RAG / batch_runner
                     |
                     | CLI + JSON contract
                     v
              bin/agent-go-solver (or Go binary)
                     |
                     v
              Go solver side (dispatch / routing / simulation)
```

## Boundary Rules

### Go side MUST NOT:
- Read Python experiment directories (eoh_go_workspace/, reports/, rag/)
- Know about RAG cards, TOCC proposals, LLM endpoints
- Import Python modules or call Python scripts
- Contain experiment-specific logic (generations, arms, repeats)

### Python side MUST NOT:
- Depend on Go internal struct fields (Assign.StaIndexesLen, Route[0].CurTime)
- Directly modify main.go or routing.go
- Assume Go binary location — always use solver_adapter

### Communication contract: CLI + JSON

**Input:**
```json
{
  "instance_id": "rc101_d25_seed1",
  "load_cap": 100,
  "vehicle_num": 25,
  "batches": [...],
  "solver_params": {"memory_size": 16, "sa_steps": 32, "seed": 42}
}
```

**Output:**
```json
{
  "ok": true,
  "objective": 1234.56,
  "res": 0.82,
  "j": 0.91,
  "runtime_ms": 182,
  "vehicle_count": 12,
  "error": null
}
```

## Current State

The Go solver (`main.go`, `routing.go`) remains unchanged for now.
Python accesses Go through `eoh_go/solver_adapter/go_solver.py`.
EOH experiment runner (`eoh_single_runner.py`) uses official EoH's Python wrapper,
not the Go solver directly — they solve different problem types.

## Future Migration

1. Wrap Go solver in `cmd/solver/main.go` with stable CLI flags
2. All Python-Go interaction through `solver_adapter.run_go_solver()`
3. Once stable, consider extracting Go solver into separate repo/submodule
