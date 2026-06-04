# 官方 EoH LLM Evolution Smoke

本文记录官方 EoH benchmark 的最小 LLM evolution smoke。API key 不写入报告。

## 配置

- problem: `cvrp_construct`
- arm: `pure_eoh`
- pop_size: `2`
- generations: `1`
- operators: `i1`
- use_official_seed: `False`
- run_dir: `/Users/guojiadong.9/agent_ad/agent_go/eoh_go_workspace/reports/official_eoh_runs/cvrp_construct/pure_eoh/run_20260604_114042`
- api_key_present: `True`
- api_endpoint_present: `True`
- model_present: `True`

## 结果

- return_code: `None`
- failure_reason: `timeout`
- runtime_seconds: `1200.173`
- latest_generation: `0`
- population_size: `2`
- valid_candidates: `2`
- best_objective: `13.05982`

## 最优代码

```python
import numpy as np

def select_next_node(current_node: int, depot: int, unvisited_nodes: np.ndarray,
                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    """Select the next node to visit in a CVRP greedy construction.

    Args:
        current_node:    index of the current node (0 = depot)
        depot:           index of the depot (always 0)
        unvisited_nodes: array of feasible unvisited customer indices
                         (already filtered to satisfy remaining capacity)
        rest_capacity:   remaining vehicle capacity
        demands:         demand of every node (index 0 = depot demand = 0)
        distance_matrix: pairwise Euclidean distance matrix
    Returns:
        Index of the next node to visit, or 0 to return to the depot early.
    """
    if len(unvisited_nodes) == 0:
        return depot
    
    # Calculate distances from current node to all feasible unvisited nodes
    dists = distance_matrix[current_node][unvisited_nodes]
    
    # Compute savings based on proximity to depot vs current location
    depot_dists = distance_matrix[depot][unvisited_nodes]
    # Preference metric: closer to current but penalize if very far from depot
    # This balances route compactness with future accessibility
    scores = dists - 0.3 * depot_dists
    
    # Also consider demand density: prefer higher demand within remaining capacity
    # Normalize by max demand among feasible nodes
    max_demand_feasible = np.max(demands[unvisited_nodes])
    if max_demand_feasible > 0:
        normalized_demands = demands[unvisited_nodes] / max_demand_feasible
        # Add small penalty for picking low-demand nodes when capacity is limited
        scores += 0.1 * (1 - normalized_demands) * (rest_capacity < 0.5 * np.sum(demands[unvisited_nodes]))
    
    # If current node is depot, use farthest insertion among feasible to seed routes better
    if current_node == depot:
        # Choose farthest feasible node from depot to start new route
        chosen_idx = np.argmax(depot_dists)
    else:
        chosen_idx = np.argmin(scores)
    
    return unvisited_nodes[chosen_idx]
```

## 最优算法描述

A nearest-neighbor heuristic that prioritizes closest feasible customers but switches to a farthest-first criterion when the remaining capacity drops below a threshold, otherwise returning to depot if no feasible nodes remain.
