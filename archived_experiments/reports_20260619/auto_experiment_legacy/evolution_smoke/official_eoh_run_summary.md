# 官方 EoH LLM Evolution Smoke

本文记录官方 EoH benchmark 的最小 LLM evolution smoke。API key 不写入报告。

## 配置

- problem: `tsp_construct`
- arm: `literature_rag`
- pop_size: `4`
- generations: `1`
- operators: `e1,e2,m1,m2`
- use_official_seed: `False`
- run_dir: `/Users/guojiadong.9/agent_ad/agent_go/eoh_go_workspace/reports/auto_experiment_reports/evolution_smoke/tsp_construct/literature_rag/run_20260609_215558`
- api_key_present: `True`
- api_endpoint_present: `True`
- model_present: `True`

## 结果

- return_code: `0`
- failure_reason: `-`
- runtime_seconds: `1008.089`
- latest_generation: `1`
- population_size: `4`
- valid_candidates: `4`
- best_objective: `6.69203`

## 最优代码

```python
import numpy as np

def select_next_node(current_node: int, destination_node: int, unvisited_nodes: np.ndarray, distance_matrix: np.ndarray) -> int:
    """Select the next node to visit in a TSP greedy construction."""
    n = len(unvisited_nodes)
    if n == 1:
        return unvisited_nodes[0]
    
    # Direct distances from current node to each candidate
    direct = distance_matrix[current_node][unvisited_nodes]
    
    # Compute closeness centrality among unvisited subgraph for each candidate
    centralities = np.zeros(n)
    for idx, u in enumerate(unvisited_nodes):
        others = np.setdiff1d(unvisited_nodes, [u])
        if len(others) == 0:
            centralities[idx] = 0.0
        else:
            # Sum of distances from u to all other unvisited nodes
            dist_sum = np.sum(distance_matrix[u][others])
            centralities[idx] = dist_sum / len(others)
    
    # Normalize centralities to [0,1] relative to min/max among candidates
    c_min, c_max = centralities.min(), centralities.max()
    if c_max > c_min + 1e-12:
        norm_cent = (centralities - c_min) / (c_max - c_min)
    else:
        norm_cent = np.zeros_like(centralities)
    
    # Dynamic threshold: penalty decreases as more nodes are visited
    # Penalty factor increases with centrality to discourage visiting highly central nodes early
    # because they are easy to reach later; instead favor peripheral nodes first.
    penalty_factor = 0.7 * (n / max(len(distance_matrix), 1))
    adjusted_distance = direct + penalty_factor * (1.0 - norm_cent) * direct.std() if direct.std() > 1e-12 else direct
    
    # Choose the node with minimal adjusted distance
    return unvisited_nodes[np.argmin(adjusted_distance)]
```

## 最优算法描述

Use a dynamic thresholding rule that picks the node with the minimum adjusted distance, where adjustment is computed as the sum of the direct distance plus a penalty proportional to the node's closeness centrality among unvisited nodes, thereby favoring nodes that bridge remote clusters while avoiding excessive detours.
