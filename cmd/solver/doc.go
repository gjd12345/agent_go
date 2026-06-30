// Package solver documents the target CLI contract for the Go dispatch solver.
//
// This is a design placeholder. The actual solver entry point is in the root main.go.
// Migration to a stable CLI (--input/--output/--config) will happen incrementally.
//
// Target CLI:
//   agent-go-solver --input <path> --output <path> [--multi 1] [--seed 42] [--timeout 120]
//
// Input JSON contract:
//   {"instance_id": "...", "load_cap": 100, "vehicle_num": 25, "batches": [...], "solver_params": {...}}
//
// Output JSON contract:
//   {"ok": true, "objective": 1234.56, "res": 0.82, "j": 0.91, "runtime_ms": 182, "error": null}
package solver
