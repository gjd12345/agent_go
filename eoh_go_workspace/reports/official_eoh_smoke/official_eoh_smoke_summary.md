# 官方 EoH Benchmark Seed/Evaluation Smoke

本文记录官方 EoH examples 的 evaluation-only smoke 结果，不包含 LLM 调用。

- official_root: `/private/tmp/EoH-main`
- python: `/private/tmp/eoh_official_venv/bin/python`
- generated_at: `2026-06-03 14:38:42`

## Summary

| Problem | OK | Metric | Objective | Target | Runtime | Failure |
|---|---:|---|---:|---|---:|---|
| bp_online | yes | avg_excess_percent | 1.796667 | score | 0.918 | - |
| tsp_construct | yes | avg_distance | 7.111000 | select_next_node | 0.592 | - |
| cvrp_construct | yes | avg_distance | 13.996400 | select_next_node | 0.103 | - |

## Official Seed Heuristic Code

### bp_online

```python
# example heuristic
# replace it with your own heuristic designed by EoH

def score(item, bins):
    scores = item - bins
    return scores
```

### tsp_construct

```python
# example heuristic
# replace it with your own heuristic designed by EoH
import numpy as np
def select_next_node(current_node, destination_node, unvisited_nodes, distance_matrix):
    next_node_id = np.argmin([distance_matrix[current_node][i] for i in unvisited_nodes if i != current_node])
    next_node = unvisited_nodes[next_node_id]
    return next_node
```

### cvrp_construct

```python
import numpy as np


def select_next_node(current_node, depot, unvisited_nodes, rest_capacity, demands, distance_matrix):
    """Nearest-feasible-neighbour baseline — replace with an EoH-designed heuristic."""
    return unvisited_nodes[np.argmin(distance_matrix[current_node][unvisited_nodes])]
```
