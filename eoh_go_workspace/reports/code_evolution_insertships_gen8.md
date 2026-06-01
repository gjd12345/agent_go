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

## Representative Code Snippets

These snippets are copied from the actual `pops_best/population_generation_N.json` files. They show the concrete code shape behind the strategy labels above.

### rc101 d50 Gen 1: first feasible insertion

```go
for jj := range oris {
    for _, ii := range rand_range {
        if !dispatch.Assigns[ii].AddShip(total_ship+jj, oris[jj], dess[jj]) {
            dispatch.Assigns[ii].Cost = -1
        } else {
            dispatch.Assigns[ii].GenRoute()
        }
        if dispatch.Assigns[ii].Cost < 0 {
            dispatch.Assigns[ii].RemoveShip(total_ship + jj)
            dispatch.Assigns[ii].GenRoute()
        } else {
            if ii >= dispatch.AssignsLen {
                dispatch.AssignsLen += 1
            }
            break
        }
    }
}
```

### rc101 d50 Gen 4: trial all Assigns and rollback

```go
for _, idx := range assignIndices {
    origCost := dispatch.Assigns[idx].Cost
    ok := dispatch.Assigns[idx].AddShip(shipId, ori, des)
    if ok {
        dispatch.Assigns[idx].GenRoute()
        newCost := dispatch.Assigns[idx].Cost
        deltaCost := newCost - origCost
        if deltaCost >= 0 || bestAssignIdx == -1 || deltaCost < bestDeltaCost {
            bestDeltaCost = deltaCost
            bestAssignIdx = idx
        }
        dispatch.Assigns[idx].RemoveShip(shipId)
        dispatch.Assigns[idx].GenRoute()
    }
}
```

### rc101 d50 Gen 8: best-delta commit and fallback

```go
for aIdx := 0; aIdx < dispatch.AssignsLen; aIdx++ {
    assign := &dispatch.Assigns[aIdx]
    origCost := assign.Cost
    trialOk := assign.AddShip(shipId, ori, des)
    if trialOk {
        assign.GenRoute()
        deltaCost := assign.Cost - origCost
        if deltaCost < bestDeltaCost {
            bestDeltaCost = deltaCost
            bestAssignIdx = aIdx
        }
        assign.RemoveShip(shipId)
        assign.GenRoute()
    }
}
if bestAssignIdx != -1 {
    finalAssign := &dispatch.Assigns[bestAssignIdx]
    if finalAssign.AddShip(shipId, ori, des) {
        finalAssign.GenRoute()
        inserted = true
    }
}
if !inserted && dispatch.AssignsLen < MAXASSIGNS {
    nextIdx := dispatch.AssignsLen
    if dispatch.Assigns[nextIdx].AddShip(shipId, ori, des) {
        dispatch.Assigns[nextIdx].GenRoute()
        dispatch.AssignsLen++
    }
}
dispatch.RenewnTotalCost()
```

### rc101 d75 Gen 8: weighted best-delta

```go
delta := newCost - prevCost
normDelta := delta / normalizeBase
timeSlack := float64(des.TimeEnd - des.TimeStart)
if timeSlack < minSlackThresh {
    timeSlack = minSlackThresh
}
score := costWeight*normDelta + slackWeight*(normalizeBase/timeSlack)
if score < bestScore {
    bestScore = score
    bestIdx = ii
    bestDelta = delta
}
dispatch.Assigns[ii].RemoveShip(shipID)
dispatch.Assigns[ii].GenRoute()
```
