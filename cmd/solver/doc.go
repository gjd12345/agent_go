// Package main provides a stable CLI entry point for the Go dispatch solver.
//
// This is a thin wrapper around the existing solver logic in main.go/routing.go.
// Python experiment code should call this binary via eoh_go/solver_adapter/.
//
// Usage:
//   agent-go-solver --input input.json --output result.json [--multi 1]
//
// TODO: migrate from os.Args[1] style to flag-based CLI.
// For now this is a placeholder documenting the intended interface.
package main

// NOTE: The actual solver entry point is currently in the root main.go.
// This file documents the target architecture. Migration will happen
// incrementally once the JSON contract is stabilized.
//
// Target CLI:
//   --input <path>    Input JSON with batches, load_cap, vehicle_num
//   --output <path>   Output JSON with objective, res, j, runtime_ms
//   --multi <int>     Vehicle multiplier (default 1)
//   --seed <int>      Random seed for reproducibility
//   --timeout <int>   Max runtime in seconds
