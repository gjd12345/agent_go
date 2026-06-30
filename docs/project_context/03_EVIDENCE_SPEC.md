# Evidence Spec

## What Counts as Evidence

Evidence = frozen, reproducible experimental result that can be cited in papers.

Every evidence directory MUST contain:
```
evidence/<name>/
├── README.md            # What this evidence shows, how to cite it
├── REPRODUCE.md         # Exact steps to reproduce (commit, env, commands)
├── commit_hash.txt      # Git commit that produced this result
├── best_code.py         # The actual code (if applicable)
├── result.json          # Machine-readable result summary
└── ...                  # Additional supporting files
```

## Evidence Types

| Type | When to Create |
|------|---------------|
| `final_batch_*` | After a major batch experiment completes |
| `bp_interpretability` | BP formula analysis (replay, ablation, plots) |
| `noisy_context_ablation` | Controlled noise vs clean RAG comparison |
| `small_model_eval` | After training and evaluating a small model |

## Immutability

Once evidence is committed, it MUST NOT be modified.
If new results supersede old ones, create a new evidence directory.

## Result JSON Schema

```json
{
  "problem": "bp_online",
  "objective": 0.00674,
  "baseline": 0.0398,
  "improvement": 0.831,
  "metric": "excess_ratio_over_lower_bound",
  "evaluator": "official EoH ICML 2024",
  "distribution": "Weibull(3.0, 45)",
  "capacity": 100,
  "replayed": true,
  "replay_mean": 0.00674,
  "replay_std": 0.0,
  "n_seeds": 1
}
```

## Baselines (Fixed, Never Recomputed)

```json
{
  "bp_online": 0.0398,
  "tsp_construct": 6.560,
  "cvrp_construct": 13.519
}
```

Source: Phase 4a Round 1 A_pure median (3 repeats each).
