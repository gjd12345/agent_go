# Legacy Assets

This directory contains code and data from earlier research phases that are no longer
on the active mainline but preserved for reference and reproducibility.

## Contents

- `insertships_eoh_v0/` — Go InsertShips solver evolution framework (cli, evolution, benchmark, grids, candidates)
- `corpus_insertships/` — InsertShips Go code examples corpus (not used by current RAG)
- `manifests_tocc/` — Early TOCC experiment manifests (day1/day2/stabilization)

## Current Mainline

The active research direction is **Trace-Conditioned Small-Model Controllers**:
- RAG reranker small model (strategy card selection from traces)
- Code gen/repair small model (heuristic generation from feedback)
- Data flywheel: batch EOH experiments → training data → small model → improved EOH

See `docs/CLEANUP_PLAN.md` for the full migration plan.

## When to Reference

- If reproducing InsertShips / Solomon benchmark results from Phase 0
- If comparing against the original Go-based EoH v0 baseline
- If auditing historical TOCC experiment configurations
