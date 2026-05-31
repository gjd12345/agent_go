# InsertShips Code Evolution (gen=8 baseline)

Source run: `eoh_go_workspace/reports/tables/gen8_explore_20260527/baseline/run_20260527_210925/`

This report extracts the best population item from each generation and summarizes semantic strategy changes. It is generated from existing `pops_best/population_generation_N.json` files; no new LLM calls or evaluator runs were used.

Important: per-generation population objectives are internal EOH selection signals and are not treated as verified final solutions here. The only performance numbers retained are the guarded external evaluations from `eoh_arrival_grid_results.json`.

## Summary

| Cell | seed_J | verified best_EOH_J | Selected Gen | Lines | Selected Strategy |
|---|---:|---:|---:|---:|---|
| rc101_d50_t1p0 | 713.52 | 274.90 | - | - | - |
| rc101_d75_t1p0 | 549.48 | 393.30 | 8 | 143 | weighted best-delta |

## Reading Guide

- `first-feasible`: inserts into the first feasible Assign and stops.
- `trial-all`: tries multiple Assigns and rolls back trial insertions.
- `best-delta`: chooses the Assign with the smallest cost increase.
- `fallback-new-assign`: creates/uses a new Assign when existing vehicles fail.
- `weighted-scoring`: adds explicit score/slack/penalty terms beyond pure cost delta.

## rc101_d50_t1p0

Verified final result from grid row: seed_J=713.52, best_EOH_J=274.90, selected candidate=eoh_arrival_d50_t1p0_rc101_d50_t1p0_20260527_210925。

| Gen | Lines | Strategy | First introduced | Features |
|---:|---:|---|---|---|
| 1 | 59 | first-feasible | first-feasible, fallback-new-assign, renew-total-cost, rollback-remove | first-feasible, fallback-new-assign, renew-total-cost, rollback-remove |
| 2 | 59 | first-feasible | no semantic change | first-feasible, fallback-new-assign, renew-total-cost, rollback-remove |
| 3 | 64 | trial-all + delta | trial-all, best-delta | trial-all, best-delta, renew-total-cost, rollback-remove |
| 4 | 50 | trial-all + delta | no semantic change | trial-all, best-delta, renew-total-cost, rollback-remove |
| 5 | 63 | best-delta + fallback | no semantic change | trial-all, best-delta, fallback-new-assign, renew-total-cost, rollback-remove |
| 6 | 63 | best-delta + fallback | no semantic change | trial-all, best-delta, fallback-new-assign, renew-total-cost, rollback-remove |
| 7 | 63 | best-delta + fallback | no semantic change | trial-all, best-delta, fallback-new-assign, renew-total-cost, rollback-remove |
| 8 | 63 | best-delta + fallback | no semantic change | trial-all, best-delta, fallback-new-assign, renew-total-cost, rollback-remove |

## rc101_d75_t1p0

Verified final result from grid row: seed_J=549.48, best_EOH_J=393.30, selected candidate=eoh_arrival_d75_t1p0_rc101_d75_t1p0_20260527_210925。

| Gen | Lines | Strategy | First introduced | Features |
|---:|---:|---|---|---|
| 1 | 108 | best-delta + fallback | trial-all, best-delta, fallback-new-assign, renew-total-cost, rollback-remove | trial-all, best-delta, fallback-new-assign, renew-total-cost, rollback-remove |
| 2 | 108 | best-delta + fallback | no semantic change | trial-all, best-delta, fallback-new-assign, renew-total-cost, rollback-remove |
| 3 | 108 | best-delta + fallback | no semantic change | trial-all, best-delta, fallback-new-assign, renew-total-cost, rollback-remove |
| 4 | 108 | best-delta + fallback | no semantic change | trial-all, best-delta, fallback-new-assign, renew-total-cost, rollback-remove |
| 5 | 108 | best-delta + fallback | no semantic change | trial-all, best-delta, fallback-new-assign, renew-total-cost, rollback-remove |
| 6 | 143 | weighted best-delta | weighted-scoring | trial-all, best-delta, fallback-new-assign, weighted-scoring, renew-total-cost, rollback-remove |
| 7 | 143 | weighted best-delta | no semantic change | trial-all, best-delta, fallback-new-assign, weighted-scoring, renew-total-cost, rollback-remove |
| 8 | 143 | weighted best-delta | no semantic change | trial-all, best-delta, fallback-new-assign, weighted-scoring, renew-total-cost, rollback-remove |

## Interpretation

The d50 trajectory converges toward a compact trial-all/best-delta insertion operator with explicit rollback and fallback. The d75 trajectory introduces heavier weighted scoring, which matches the existing observation that denser instances require richer route-capacity/time-window context. This is L-layer evidence: deeper evolution changes code structure, not only objective values.
