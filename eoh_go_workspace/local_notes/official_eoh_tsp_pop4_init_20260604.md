# Official EoH TSP pop4 init-only 记录

时间：2026-06-04

目的：在 `tsp_construct` 上比较 pure EOH、API-only、默认 Literature-RAG、targeted Literature-RAG 的 init-only 表现。

设置：

```text
problem = tsp_construct
pop_size = 4
generations = 0
operators = i1
n_processes = 1
eval_timeout_s = 40
llm_timeout_s = 180
```

## 结果表 (init-only 对照)

| arm | best objective | delta vs pure | delta vs API-only | valid/pop | runtime seconds | selected RAG cards |
|---|---|---|---|---:|---:|---:|---:|---|
| `pure_eoh` | 6.83907 | +0.00000 | +0.04954 | 4/4 | 1622.299 | - |
| `api_only` | 6.78953 | -0.04954 | +0.00000 | 4/4 | 1269.407 | - |
| `literature_rag_default` | 6.83954 | +0.00047 | +0.05001 | 4/4 | 612.678 | tsp_nearest_insertion, tsp_nearest_neighbor |
| `literature_rag_targeted_regret_farthest` | 6.51118 | -0.32789 | -0.27835 | 4/4 | 1211.348 | tsp_regret_insertion, tsp_farthest_insertion |

## repeat=3 验证 (init-only, same settings)

| repeat | best objective | delta vs pure | valid/pop | runtime |
|---|---:|---:|---:|---:|
| repeat 1 | **6.30547** | **-0.53360** | 4/4 | 1303s |
| repeat 2 | 6.50049 | -0.33858 | 4/4 | 1014s |
| repeat 3 | 6.73293 | -0.10614 | 4/4 | 615s |
| **median** | **6.50049** | | | |
| **min** | **6.30547** | | | |

## 深度进化 (gen > 0, same RAG query)

| config | best objective | delta vs pure | valid/pop | runtime | evolution trace |
|---|---:|---:|---:|---:|---|
| gen=1, pop=4 | 7.3266 | +0.48753 | 4/4 | 749s | init=7.33 → no gen1 improvement |
| gen=4, pop=8 | **6.28736** | **-0.55171** | 8/8 | 4601s | init=6.51 → gen2=6.32 → gen3=**6.29** |
| gen=8, pop=8 | 6.49327 | -0.34580 | 8/8 | 4473s | init=6.49, plateau across 8 gens |

## 结论

1. `api_only` 相对 `pure_eoh` 改善 `-0.04954`，说明 API/signature/contract 约束有轻微信号。
2. 默认 `literature_rag` 没有效果，原因是检索选中了 `tsp_nearest_insertion` + `tsp_nearest_neighbor`，与模型自然生成的 nearest/return-distance 族高度重合。
3. targeted Literature-RAG 明确有效：使用 regret/farthest query 后，top-2 变为 `tsp_regret_insertion` + `tsp_farthest_insertion`。
4. **repeat=3 验证**：3/3 全部低于 pure EOH (6.839) 和 API-only (6.790)。median=6.500，min=6.305。信号稳定，非单次波动。
5. **深度进化**：gen=4,pop=8 取得 **best=6.28736**（相对 pure 改善 -0.552），且进化轨迹清晰（init=6.51 → gen2=6.32 → gen3=6.29）。gen=8 进入 plateau，未进一步改善。
6. 下一步不应扩大默认 Literature-RAG，而应把 query/card selection 作为 RAG 的核心实验变量。

## RAG trace

### literature_rag_default

- query: `tsp construct select next node distance nearest insertion regret route length`
- global: `tsp_construct_api_skeleton`
- selected: `tsp_nearest_insertion, tsp_nearest_neighbor`
- context chars: `1800`
- scores:
  - `tsp_nearest_insertion`: 34
  - `tsp_nearest_neighbor`: 34
  - `tsp_regret_insertion`: 27
  - `tsp_farthest_insertion`: 19
  - `tsp_two_opt_awareness`: 16

### literature_rag_targeted_regret_farthest

- query: `tsp construct select next node regret farthest insertion lookahead second best global route length`
- global: `tsp_construct_api_skeleton`
- selected: `tsp_regret_insertion, tsp_farthest_insertion`
- context chars: `1917`
- scores:
  - `tsp_regret_insertion`: 29
  - `tsp_farthest_insertion`: 27
  - `tsp_nearest_insertion`: 23
  - `tsp_nearest_neighbor`: 23
  - `tsp_two_opt_awareness`: 16

## Best code

### pure_eoh

- best objective: `6.83907`
- valid/pop: `4/4`
- algorithm: The algorithm selects the next node by balancing proximity to the current node and alignment toward the final destination using a weighted score combining direct distance and directional deviation penalty, while prioritizing closer nodes if they also reduce detour from the ideal path toward the destination.

```python
import numpy as np

def select_next_node(current_node: int, destination_node: int, unvisited_nodes: np.ndarray, distance_matrix: np.ndarray) -> int:
    """Select the next node to visit in a TSP greedy construction.

    Args:
        current_node: ID of the current node
        destination_node: ID of the destination (return) node
        unvisited_nodes: array of unvisited node IDs
        distance_matrix: pairwise distance matrix between all nodes
    Returns:
        next_node: ID of the next node to visit
    """
    # If only one unvisited node remains, choose it
    if len(unvisited_nodes) == 1:
        return unvisited_nodes[0]

    # Extract distances from current node to all unvisited nodes
    dist_from_current = distance_matrix[current_node][unvisited_nodes]

    # Calculate "progress" scores: reduction in distance to destination via candidate
    # Defined as (dist_to_dest_direct - dist_via_candidate), but here we use a normalized measure
    dist_to_dest_direct = distance_matrix[current_node][destination_node]
    dist_via_candidate = dist_from_current + distance_matrix[unvisited_nodes][:, destination_node]
    progress_score = dist_to_dest_direct - dist_via_candidate  # positive means better progress

    # Normalize both distance and progress to [0,1] range within unvisited set
    min_dist, max_dist = dist_from_current.min(), dist_from_current.max()
    min_prog, max_prog = progress_score.min(), progress_score.max()

    norm_dist = (dist_from_current - min_dist) / (max_dist - min_dist + 1e-12)
    norm_prog = (progress_score - min_prog) / (max_prog - min_prog + 1e-12)

    # Combined score: lower is better; weight favors closeness (alpha=0.6) over progress (1-alpha=0.4)
    alpha = 0.6
    combined_score = alpha * norm_dist - (1 - alpha) * norm_prog  # minus because higher progress is better

    # Select candidate with minimum combined score
    best_idx = np.argmin(combined_score)
    return unvisited_nodes[best_idx]
```

### api_only

- best objective: `6.78953`
- valid/pop: `4/4`
- algorithm: Propose a hybrid heuristic that scores each unvisited node by combining its proximity to the current node, its remoteness from the centroid of unvisited nodes to encourage exploration, and a penalty for being far from the eventual destination, then selects the highest‑scoring candidate.

```python
import numpy as np

def select_next_node(current_node: int, destination_node: int, unvisited_nodes: np.ndarray, distance_matrix: np.ndarray) -> int:
    if len(unvisited_nodes) == 1:
        return unvisited_nodes[0]
    
    # 1) Nearest-neighbor score (normalized inverse distance)
    dist_from_current = distance_matrix[current_node][unvisited_nodes]
    inv_dist = 1.0 / (dist_from_current + 1e-10)
    nn_score = inv_dist / np.max(inv_dist)
    
    # 2) Exploration score based on centrality among unvisited nodes
    # Compute average distance from this unvisited node to all other unvisited nodes
    submatrix = distance_matrix[np.ix_(unvisited_nodes, unvisited_nodes)]
    avg_pairwise = submatrix.mean(axis=1)
    # Nodes farther from the "center" get higher exploration value
    exp_raw = avg_pairwise / np.max(avg_pairwise)
    exp_score = 1.0 - exp_raw  # invert so larger means more central; we actually want less central? Let's rethink:
    # We want to reward going toward clusters early, but penalize too isolated nodes late?
    # Instead, compute distance to the centroid of unvisited positions (but we don't have positions).
    # Use mean distance to others as proxy: low mean distance = central; high mean distance = outlier.
    # To encourage covering outliers earlier, use high mean distance = high score.
    # So keep exp_raw as defined (already normalized).
    exp_score = exp_raw
    
    # 3) Destination-awareness: penalty for moving away from destination
    # Only apply when few unvisited remain to avoid premature homing
    remaining_ratio = len(unvisited_nodes) / distance_matrix.shape[0]
    dest_penalty_factor = max(0, 1.5 - remaining_ratio * 2.0)  # grows when fewer left
    dist_to_dest = distance_matrix[destination_node][unvisited_nodes]
    dest_awareness = 1.0 / (dist_to_dest + 1e-10)
    dest_score = dest_awareness / np.max(dest_awareness)
    # Combine: final = nn_weighted + exp_weighted - dest_penalty_weighted*(when far from dest)
    w_nn = 0.6
    w_exp = 0.25
    w_dest = 0.15 * dest_penalty_factor
    
    total = w_nn * nn_score + w_exp * exp_score + w_dest * dest_score
    
    # Tie-breaker: smallest index (implicit via argmax on first occurrence)
    best_idx = np.argmax(total)
    return unvisited_nodes[best_idx]
```

### literature_rag_default

- best objective: `6.83954`
- valid/pop: `4/4`
- algorithm: My new algorithm selects the next node by minimizing the sum of the distance from the current node to the candidate and the estimated cost of returning from that candidate to the destination via a proxy using the average distance from all unvisited nodes to the destination, balancing immediate travel with future return proximity.

```python
import numpy as np

def select_next_node(current_node: int, destination_node: int, unvisited_nodes: np.ndarray, distance_matrix: np.ndarray) -> int:
    """Select the next node to visit in a TSP greedy construction.

    Args:
        current_node: ID of the current node
        destination_node: ID of the destination (return) node
        unvisited_nodes: array of unvisited node IDs
        distance_matrix: pairwise distance matrix between all nodes
    Returns:
        next_node: ID of the next node to visit
    """
    # Fallback to nearest neighbor if there is only one candidate
    if len(unvisited_nodes) == 1:
        return unvisited_nodes[0]

    # Compute forward distances from current node to each unvisited candidate
    dist_current_to_candidate = distance_matrix[current_node, unvisited_nodes]

    # Compute backward distances from each unvisited candidate to destination
    dist_candidate_to_destination = distance_matrix[unvisited_nodes, destination_node]

    # Estimate the "future integration cost" using the average distance 
    # from all unvisited nodes (excluding the candidate itself) to the destination.
    # This acts as a simple proxy for how well the candidate positions us for visiting the rest before returning.
    avg_remaining_to_dest = np.mean(distance_matrix[unvisited_nodes, destination_node])

    # Score = direct cost + adjusted return leg penalty
    # We penalize candidates whose direct distance to destination is far above the average,
    # encouraging moves that keep the return journey manageable after covering remaining nodes.
    adjusted_return_penalty = np.maximum(0, dist_candidate_to_destination - avg_remaining_to_dest)
    
    # Balance parameter alpha (fixed small value to avoid ties, emphasize forward progress slightly)
    alpha = 0.3
    
    # Combined score to minimize: forward distance + alpha * adjusted_return_penalty
    scores = dist_current_to_candidate + alpha * adjusted_return_penalty

    # Select candidate with minimum score
    best_index = np.argmin(scores)
    return unvisited_nodes[best_index]
```

### literature_rag_targeted_regret_farthest

- best objective: `6.51118`
- valid/pop: `4/4`
- algorithm: current_node, farthest_unvisited, destination_node

```python
import numpy as np

def select_next_node(current_node: int, destination_node: int, unvisited_nodes: np.ndarray, distance_matrix: np.ndarray) -> int:
    """Select the next node to visit in a TSP greedy construction."""
    n_unvisited = len(unvisited_nodes)
    if n_unvisited == 0:
        raise ValueError("No unvisited nodes.")
    if n_unvisited == 1:
        return unvisited_nodes[0]

    # Distances from current_node to each unvisited
    dist_from_current = distance_matrix[current_node][unvisited_nodes]

    # Identify a representative 'farthest' node among unvisited (approximate cluster seed)
    # Farthest from current_node within unvisited set
    farthest_idx_in_uv = np.argmax(dist_from_current)
    farthest_rep = unvisited_nodes[farthest_idx_in_uv]

    # Candidate endpoints for insertion consideration: current_node, farthest_rep, destination_node
    endpoints = [current_node, farthest_rep, destination_node]
    unique_endpoints = []
    seen = set()
    for ep in endpoints:
        if ep not in seen:
            seen.add(ep)
            unique_endpoints.append(ep)
    endpoints = unique_endpoints

    # For each unvisited node u, compute:
    #   1. regret_u = second_min_connection_cost(u) - min_connection_cost(u)
    #      where connection costs are distances to each distinct endpoint in endpoints list.
    #   2. cluster_penalty_u = distance(u, farthest_rep)
    #   3. current_dist_u = distance(current_node, u)

    regrets = np.zeros(n_unvisited, dtype=np.float64)
    cluster_dists = np.zeros(n_unvisited, dtype=np.float64)
    for i, u in enumerate(unvisited_nodes):
        # Connection costs to endpoints
        conn_costs = [distance_matrix[u][ep] for ep in endpoints]
        conn_costs.sort()
        min_conn = conn_costs[0]
        second_min = conn_costs[1] if len(conn_costs) > 1 else min_conn
        regrets[i] = second_min - min_conn
        cluster_dists[i] = distance_matrix[u][farthest_rep]

    current_dists = dist_from_current

    # Normalization (avoid division by zero)
    norm_regret = regrets / max(1e-12, regrets.max() - regrets.min()) if regrets.max() > regrets.min() else np.ones_like(regrets)
    norm_cluster = cluster_dists / max(1e-12, cluster_dists.max() - cluster_dists.min()) if cluster_dists.max() > cluster_dists.min() else np.ones_like(cluster_dists)
    norm_curdist = current_dists / max(1e-12, current_dists.max() - current_dists.min()) if current_dists.max() > current_dists.min() else np.ones_like(current_dists)

    # Combined score: regret + cluster_promotion - current_distance_bias (with equal weighting)
    # To balance, we use: score = w_r * norm_regret + w_c * norm_cluster + w_i * (1 - norm_curdist)
    w_r, w_c, w_i = 1.0, 1.0, 1.0
    scores = w_r * norm_regret + w_c * norm_cluster + w_i * (1 - norm_curdist)

    # Tie-breaker: raw regret
    best_score_idx = np.argmax(scores)
    best_score = scores[best_score_idx]
    candidates_mask = scores == best_score
    candidates_indices = np.where(candidates_mask)[0]
    if len(candidates_indices) > 1:
        # Among ties, pick highest raw regret
        tie_regrets = regrets[candidates_mask]
        best_tie_idx = candidates_indices[np.argmax(tie_regrets)]
        return unvisited_nodes[best_tie_idx]
    return unvisited_nodes[best_score_idx]
```
