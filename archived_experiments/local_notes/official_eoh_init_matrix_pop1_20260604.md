# Official EoH TSP/CVRP init-only pop1 诊断记录

时间：2026-06-04

目的：在 BP online 没拉开差距后，先用官方 `tsp_construct` / `cvrp_construct` 做最小 init-only 诊断，确认 RAG 是否在更大启发式空间中出现初始信号。

重要限制：本轮是 `pop_size=1, generations=0`，每臂只有 2 个 init samples，survivor population 只有 1 个。因此只能用于判断链路和早期信号，不能作为最终性能结论。

## 结果表

| problem | arm | return | best objective | valid/pop | selected RAG cards |
|---|---|---:|---:|---:|---|
| tsp_construct | pure_eoh | 0 | 6.83907 | 1/1 | - |
| tsp_construct | api_only | 0 | 6.86186 | 1/1 | - |
| tsp_construct | literature_rag | 0 | 6.83907 | 1/1 | tsp_nearest_insertion, tsp_nearest_neighbor |
| cvrp_construct | pure_eoh | 0 | 13.20696 | 1/1 | - |
| cvrp_construct | api_only | 0 | 13.41247 | 1/1 | - |
| cvrp_construct | literature_rag | 0 | 14.49387 | 1/1 | cvrp_nearest_capacity, cvrp_capacity_slack |

## 诊断判断

1. `tsp_construct`：Literature-RAG 与 pure EOH 打平（6.83907），API-only 略差（6.86186）。说明 TSP cards 没有破坏生成，但 pop1 下还没有证明提升。
2. `cvrp_construct`：pure EOH 最好（13.20696），API-only 次之（13.41247），Literature-RAG 更差（14.49387）。当前 CVRP cards 可能引导模型过度关注 capacity slack，导致路线距离变差。
3. `bp_online`、`tsp_construct`、`cvrp_construct` 三者共同说明：当前 RAG 链路能生效，但短 skill cards 是否产生收益高度依赖 target；不能只靠单次 pop1 下结论。
4. 下一步不应扩大所有 arm。优先挑 `tsp_construct` 做 `pop_size=4, generations=0` 的三臂重复；CVRP 先审查 cards，尤其 `cvrp_capacity_slack` 是否过强。

## Best code

### tsp_construct / pure_eoh

- best objective: `6.83907`
- valid/pop: `1/1`
- algorithm: The proposed algorithm selects the next node by balancing proximity to the current node and angular alignment toward the final destination, using a weighted score of inverse normalized distance and cosine similarity between the vectors from current to candidate and from current to destination.

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
    if len(unvisited_nodes) == 0:
        return destination_node
    
    # Extract distances from current node to each unvisited node
    dists = distance_matrix[current_node, unvisited_nodes]
    
    # If only one unvisited node left, choose it
    if len(unvisited_nodes) == 1:
        return unvisited_nodes[0]
    
    # Normalize distances to [0,1] range among candidates
    min_dist = np.min(dists)
    max_dist = np.max(dists)
    if max_dist > min_dist:
        norm_dists = (dists - min_dist) / (max_dist - min_dist)
    else:
        norm_dists = np.zeros_like(dists)
    
    # Compute direction scores: cosine similarity between 
    # vector (current → candidate) and vector (current → destination)
    # We approximate direction via inverse distance differences? 
    # But we don't have coordinates, only distance matrix.
    # Use triangle inequality insight: prefer nodes that make detour smaller relative to direct path to destination.
    # Define a proxy for "alignment": how much visiting the candidate increases total tour length compared to going directly to destination.
    # Score = (distance to dest if we go via candidate) / (direct to dest + small epsilon)
    # Actually: direct = d_cd (current to destination)
    #           via_candidate = d_cu + d_ud (current to unvisited + unvisited to destination)
    # We want to minimize detour_ratio = (d_cu + d_ud) / d_cd
    # Lower ratio means candidate lies roughly on the way to destination.
    
    d_current_to_dest = distance_matrix[current_node, destination_node]
    
    # For numerical stability when d_current_to_dest is zero (shouldn't happen for distinct nodes)
    eps = 1e-10
    detour_ratios = []
    for i, u in enumerate(unvisited_nodes):
        d_cu = distance_matrix[current_node, u]
        d_ud = distance_matrix[u, destination_node]
        detour = d_cu + d_ud
        ratio = detour / (d_current_to_dest + eps)
        detour_ratios.append(ratio)
    
    detour_ratios = np.array(detour_ratios)
    # Normalize ratios to [0,1] where lower is better
    min_ratio = np.min(detour_ratios)
    max_ratio = np.max(detour_ratios)
    if max_ratio > min_ratio:
        norm_ratios = (detour_ratios - min_ratio) / (max_ratio - min_ratio)
    else:
        norm_ratios = np.zeros_like(detour_ratios)
    
    # Combine: higher preference for short distance AND low detour ratio.
    # Since both norm_dists and norm_ratios are normalized to [0,1], 
    # we can use a weighted sum where we invert so that larger score is better.
    alpha = 0.6  # weight for distance (short distance preferred)
    beta = 0.4   # weight for directional alignment (low detour preferred)
    
    # Invert norms so that shorter distance gives higher score
    inv_norm_dists = 1.0 - norm_dists
    inv_norm_ratios = 1.0 - norm_ratios
    
    scores = alpha * inv_norm_dists + beta * inv_norm_ratios
    
    # Choose candidate with highest combined score
    best_idx = np.argmax(scores)
    return unvisited_nodes[best_idx]
```

### tsp_construct / api_only

- best objective: `6.86186`
- valid/pop: `1/1`
- algorithm: The algorithm selects the next node by balancing proximity to the current node and future potential via a heuristic that combines nearest‑neighbor distance with an urgency term based on remaining detour cost toward the mandatory return to the destination node.

```python
import numpy as np

def select_next_node(current_node: int, destination_node: int, unvisited_nodes: np.ndarray, distance_matrix: np.ndarray) -> int:
    if len(unvisited_nodes) == 0:
        raise ValueError("No unvisited nodes available.")
    
    # Heuristic weighting factor (can be tuned; here fixed at 1.5)
    alpha = 1.5
    
    # Current distances to all unvisited nodes
    cur_dists = distance_matrix[current_node, unvisited_nodes]
    
    # Minimum distance from each unvisited candidate to the destination node,
    # considering only unvisited nodes left after choosing it (approximated by direct distance to destination).
    dest_dists = distance_matrix[destination_node, unvisited_nodes]
    
    # Urgency term: how much longer would it be to go from candidate → destination later?
    # We compare (candidate→destination) vs (current→destination) but since we will eventually
    # visit other nodes, we use a simpler proxy: penalize candidates far from destination.
    # To avoid over-penalizing early choices, we scale by number of remaining nodes.
    n_remaining = len(unvisited_nodes)
    # Score = distance to candidate + alpha * (distance from candidate to destination) / sqrt(n_remaining)
    scores = cur_dists + alpha * dest_dists / np.sqrt(max(1, n_remaining))
    
    # In case of ties, prefer smaller index for determinism (argmin returns first occurrence)
    chosen_index = np.argmin(scores)
    return unvisited_nodes[chosen_index]
```

### tsp_construct / literature_rag

- best objective: `6.83907`
- valid/pop: `1/1`
- algorithm: The algorithm selects the next node by minimizing the sum of the distance from the current node to the candidate and the distance from the candidate back to the destination, normalized by the maximum such sum among candidates to also consider proximity to the destination while avoiding premature long detours.

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
    # Compute raw scores: d(current -> u) + d(u -> destination)
    forward_dists = distance_matrix[current_node][unvisited_nodes]
    return_dists = distance_matrix[unvisited_nodes, destination_node]
    raw_scores = forward_dists + return_dists
    
    # Normalize to [0,1] range relative to min/max among candidates
    max_score = np.max(raw_scores)
    min_score = np.min(raw_scores)
    
    if max_score > min_score:
        norm_scores = (raw_scores - min_score) / (max_score - min_score)
    else:
        norm_scores = np.zeros_like(raw_scores)
    
    # Also consider pure proximity to current (nearest‑neighbor fallback effect)
    # Normalize forward distances similarly
    max_forward = np.max(forward_dists)
    min_forward = np.min(forward_dists)
    if max_forward > min_forward:
        norm_forward = (forward_dists - min_forward) / (max_forward - min_forward)
    else:
        norm_forward = np.zeros_like(forward_dists)
    
    # Combined weighted score: emphasize staying near current early,
    # but gradually shift toward considering the return leg.
    # Simple fixed weighting works well; here we use 0.6*norm_forward + 0.4*norm_scores.
    combined = 0.6 * norm_forward + 0.4 * norm_scores
    
    # Choose the candidate with the smallest combined score
    best_idx = np.argmin(combined)
    return unvisited_nodes[best_idx]
```

### cvrp_construct / pure_eoh

- best objective: `13.20696`
- valid/pop: `1/1`
- algorithm: At each step, choose the nearest feasible customer weighted by an inverse squared-distance urgency penalty that prioritizes distant clusters when near the depot but switches to pure nearest-neighbor once en route, returning to the depot only when no customer fits capacity.

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
    
    # If currently at depot, use a savings-inspired composite score:
    # favor nodes that are far from depot but close to current position (depot),
    # blended with nearest-neighbor tendency.
    if current_node == depot:
        dist_from_depot = distance_matrix[depot, unvisited_nodes]
        max_depot_dist = np.max(dist_from_depot)
        if max_depot_dist > 0:
            # Normalize distances from depot to [0,1] range relative to farthest feasible
            norm_far = dist_from_depot / max_depot_dist
        else:
            norm_far = np.zeros_like(dist_from_depot)
        # Nearest neighbor component from depot
        nn_score = distance_matrix[current_node, unvisited_nodes]
        # Composite: prioritize farther customers (to avoid leaving outliers late)
        # while still respecting proximity.
        alpha = 0.7  # weight for 'far first' component
        scores = alpha * (1 - norm_far) + (1 - alpha) * (nn_score / (np.max(nn_score) + 1e-10))
        best_idx = np.argmin(scores)
        return unvisited_nodes[best_idx]
    
    # Otherwise (en route), use modified nearest neighbor with a slight push
    # toward customers whose demand better fills the vehicle.
    direct_dists = distance_matrix[current_node, unvisited_nodes]
    # Favor higher demand if it helps fill capacity without being too far
    demand_frac = demands[unvisited_nodes] / rest_capacity
    # Penalize distance more strongly than reward for filling; 
    # simple combined metric: distance adjusted by small demand factor.
    # Use inverse so that larger demand slightly reduces effective distance.
    adj_factor = 1.0 - 0.3 * demand_frac  # up to 30% reduction for high-demand fit
    scores = direct_dists * adj_factor
    best_idx = np.argmin(scores)
    return unvisited_nodes[best_idx]
```

### cvrp_construct / api_only

- best objective: `13.41247`
- valid/pop: `1/1`
- algorithm: A nearest-neighbor heuristic that at each step selects the closest feasible unvisited customer; if no such customer exists within a relaxed feasibility window (considering a safety margin on capacity), it returns to the depot early to avoid long detours for marginal gains.

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
    # If there are no unvisited nodes (should not happen given filtering), return to depot
    if len(unvisited_nodes) == 0:
        return depot
    
    # Compute distances from current node to all feasible unvisited nodes
    distances = distance_matrix[current_node, unvisited_nodes]
    
    # Find the nearest feasible node (greedy nearest neighbor)
    nearest_idx = np.argmin(distances)
    nearest_node = unvisited_nodes[nearest_idx]
    
    # Early termination condition: 
    # If returning to depot now is cheaper than going to the nearest node plus from that node back to depot,
    # and the remaining capacity is relatively low (less than half of average remaining demand per feasible node),
    # then end the route early.
    avg_remaining_demand = np.mean(demands[unvisited_nodes])
    dist_to_depot_from_current = distance_matrix[current_node, depot]
    dist_nearest_to_depot = distance_matrix[nearest_node, depot]
    
    # Heuristic threshold: end route if the detour via nearest node is longer than direct return
    # scaled by a factor reflecting low remaining capacity utility.
    if (dist_to_depot_from_current < distances[nearest_idx] + dist_nearest_to_depot - 1e-9) and \
       (rest_capacity < 1.5 * avg_remaining_demand):
        return depot
    
    # Otherwise proceed to the nearest feasible customer
    return nearest_node
```

### cvrp_construct / literature_rag

- best objective: `14.49387`
- valid/pop: `1/1`
- algorithm: A hybrid nearest-capacity heuristic that scores each feasible customer by a weighted combination of normalized distance from the current node and normalized capacity slack (remaining capacity minus customer demand), selecting the highest‑score customer unless a penalty threshold suggests closing the route early.

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
    # If no feasible customers remain, return to depot
    if len(unvisited_nodes) == 0:
        return depot
    
    # Extract distances from current_node to each candidate
    dists = distance_matrix[current_node][unvisited_nodes]
    
    # Normalized distance component (lower is better)
    d_min = np.min(dists)
    d_max = np.max(dists)
    if d_max > d_min:
        norm_dist = (dists - d_min) / (d_max - d_min + 1e-12)
    else:
        norm_dist = np.zeros_like(dists)
    
    # Capacity slack: rest_capacity - demand (higher slack means more leftover capacity after serving)
    slacks = rest_capacity - demands[unvisited_nodes]
    # Normalize slack to [0,1] where higher slack is better (but we want to *use* capacity efficiently,
    # so we actually prefer smaller positive slack → less leftover waste).
    s_max = np.max(slacks)
    s_min = np.min(slacks)
    if s_max > s_min:
        # Invert so that lower slack gives higher score (using capacity well)
        norm_slack = 1.0 - (slacks - s_min) / (s_max - s_min + 1e-12)
    else:
        norm_slack = np.ones_like(slacks) * 0.5
    
    # Weighted combined score: alpha favors proximity, (1-alpha) favors tight capacity fit
    alpha = 0.7
    scores = alpha * (1.0 - norm_dist) + (1.0 - alpha) * norm_slack
    
    best_idx = np.argmax(scores)
    best_customer = unvisited_nodes[best_idx]
    
    # Early return penalty: if the best candidate's distance exceeds a threshold relative to
    # the nearest possible customer, consider closing the route.
    # Threshold: if the selected customer's distance is > 1.5 × min_distance among candidates,
    # it's relatively far and might indicate a poor insertion; however, since we already
    # filter by capacity feasibility, we only close early if there is *no* attractive move.
    # Here we simply always choose the best scored customer; the API expects depot return
    # only when voluntarily ending a route. We do not force an early return in this deterministic
    # version because the problem states unvisited_nodes are already capacity‑feasible.
    # Thus we always pick a customer unless the list is empty (handled above).
    return best_customer
```
