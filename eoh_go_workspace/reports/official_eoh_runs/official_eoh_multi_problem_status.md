# 官方 EoH 多问题最小闭环状态

本文记录当前官方 EoH benchmark 对齐进展。所有实验都调用 `/private/tmp/EoH-main` 官方 EoH core；raw run 目录不入仓。

## 总览

| Problem | Arm | Status | Latest gen | Best objective | Valid | Samples | RAG context |
|---|---|---|---:|---:|---:|---:|---|
| `bp_online` | `pure_eoh` | completed | 1 | 0.03984 | 2/2 | 6 | - |
| `bp_online` | `api_only` | completed | 1 | 0.03984 | 2/2 | 6 | - |
| `bp_online` | `literature_rag_default` | completed | 1 | 0.03984 | 1/1 | 6 | obp_best_fit, obp_first_fit (truncated) |
| `bp_online` | `literature_rag_targeted_residual` | timeout_after_init | 0 | 0.03984 | 2/2 | 4 | obp_eoh_util_sqrt_exp, obp_funsearch_residual_poly (truncated) |
| `tsp_construct` | `pure_eoh` | timeout_after_init | 0 | 6.74626 | 2/2 | 4 | - |
| `cvrp_construct` | `pure_eoh` | timeout_after_init | 0 | 13.05982 | 2/2 | 4 | - |

## 结论

- `bp_online`：pure/API-only/default Literature-RAG 都完整跑完 gen=1；targeted residual RAG 完成 init 后超时。当前未观察到 RAG 优于 pure EOH，主要因为 best-fit/tight-fit 已是强基线，且 targeted context 仍截断。
- `tsp_construct`：init 阶段完整跑通，4/4 evaluated，best objective 6.74626；Gen 1 在 20 分钟预算内未完成。说明官方 TSP target 已可生成和评估，但需要调整预算或先采用 init-only 展示。
- `cvrp_construct`：init 阶段完整跑通，4/4 evaluated，best objective 13.05982；Gen 1 同样超时。说明官方 CVRP target 也已可迁移。
- 下一步优先级：先把 official runner 支持 init-only 模式或提高总 timeout，再补 TSP/CVRP 的 API-only/RAG 小对照；BP 不宜作为正向收益主证据，可作为“官方对齐 + RAG 检索诊断”案例。

## bp_online / pure_eoh 最优代码

Assign the item to the bin whose remaining capacity after placement is closest to zero without going negative, prioritizing tighter fits to reduce wasted space and thus the total number of bins needed.

```python
import numpy as np

def score(item: int, bins: np.ndarray) -> np.ndarray:
    """Score each bin for assigning the current item. Higher score = preferred bin.

    Args:
        item: size of the current item to assign
        bins: remaining capacities of feasible bins (all >= item size)
    Returns:
        scores: priority scores for each bin
    """
    # Remaining capacity if item is placed in each bin
    remaining_after_placement = bins - item
    # We want smaller remaining capacities to have higher scores.
    # Use negative remaining capacity so that max score picks smallest remainder.
    # Add 1/(bins+1) term to break ties in favor of larger original bin capacity,
    # which helps utilize partially filled bins more effectively.
    tie_breaker = 1.0 / (bins + 1)
    scores = -remaining_after_placement + tie_breaker
    return scores
```

## bp_online / api_only 最优代码

Maximize utilization by scoring bins based on how close their remaining capacity is to the item size after placement, preferring bins where the leftover space is minimized but still non-negative, while also prioritizing tighter fits to reduce fragmentation and thus total bins used.

```python
import numpy as np

def score(item: int, bins: np.ndarray) -> np.ndarray:
    """Score each bin for assigning the current item. Higher score = preferred bin.

    Args:
        item: size of the current item to assign
        bins: remaining capacities of feasible bins (all >= item size)
    Returns:
        scores: priority scores for each bin
    """
    # After placing the item, the leftover space is (bins - item).
    # We want to maximize the negative of leftover space (i.e., minimize leftover),
    # so we can use (bins - item) directly but invert sign because higher leftover means lower preference.
    # However, to strictly prefer smaller leftovers, we take negative of leftover.
    # To handle exact fits best (leftover = 0), we add a small bonus for exact fits.
    # But simpler: score = -(bins - item) = item - bins? Wait, that's negative if bins > item.
    # Actually, we want larger score when leftover is smaller, so score = - (bins - item) = item - bins.
    # That gives highest score when bins == item (score = 0?), let's check:
    # If bins == item: leftover = 0, score = item - bins = 0.
    # If bins > item: leftover positive, score negative → worse than exact fit.
    # But all bins have bins >= item, so smallest leftover gives least negative (or zero).
    # So we can just use negative leftover: score = - (bins - item) = item - bins.
    # Since item is constant across bins, this is equivalent to using -bins.
    # But using -bins alone would rank same as minimizing bins, which isn't exactly our goal.
    # Better: score = 1 / (bins - item + epsilon) to heavily favor smaller leftover.
    # This gives huge scores for near-exact fits.
    
    # Add tiny epsilon to avoid division by zero when bins == item.
    eps = 1e-9
    leftover = bins - item
    # Use reciprocal to strongly prioritize smaller leftover.
    scores = 1.0 / (leftover + eps)
    return scores
```

## bp_online / literature_rag_default 最优代码

New algorithm: Hybrid Residual-Aware Gap Minimization (HRAGM) — prioritize bins whose post-assignment residual creates the smallest potential future waste relative to both their absolute residual and their contribution to lowering the global lower-bound gap, while strongly favoring tighter fits on larger items to delay new-bin openings.

```python
import numpy as np

def score(item: int, bins: np.ndarray) -> np.ndarray:
    """Score each bin for assigning the current item. Higher score = preferred bin."""
    # Post-assignment residual for each feasible bin
    residuals = bins - item
    
    # Absolute tightness: smaller residual is better → invert for scoring
    tightness = 1.0 / (residuals + 1e-9)
    
    # Global incentive: penalize bins whose residual is far from zero but also far from being useless
    # Use normalized residual to avoid scale bias
    max_residual = np.max(residuals) if len(residuals) > 0 else 1
    norm_residuals = residuals / (max_residual + 1e-9)
    # Prefer small normalized residuals (tighter fit)
    fit_quality = 1.0 - norm_residuals
    
    # Item-size awareness: for larger items, prioritize even more aggressive tightness
    # because wasting space on big items is costly
    item_factor = 1.0 + (item / (np.mean(bins) + 1e-9)) * 0.5
    
    # Combine: primary weight on tightness, secondary on fit_quality, modulated by item factor
    scores = tightness * (1.0 + fit_quality * 0.3) * item_factor
    
    # Fallback deterministic tie-break via tiny index-based perturbation
    indices = np.arange(len(bins))
    epsilon = 1e-12
    scores += indices * epsilon
    
    return scores.astype(np.float64)
```

## bp_online / literature_rag_targeted_residual 最优代码

Score bins by combining a strong preference for minimizing leftover space after placement with a secondary preference for using already highly-utilized bins, implemented via a normalized best-fit term and a utilization bonus that avoids extreme penalties to keep all scores finite.

```python
import numpy as np

def score(item: int, bins: np.ndarray) -> np.ndarray:
    residuals = bins - item
    min_r = np.min(residuals)
    max_r = np.max(residuals)
    
    # Primary term: best-fit preference (normalized, higher when residual is smaller)
    if max_r > min_r:
        primary = 1.0 - (residuals - min_r) / (max_r - min_r + 1e-12)
    else:
        primary = np.ones_like(residuals, dtype=float)
    
    # Secondary term: utilization bonus based on original remaining capacity before placing item
    # We want to slightly favor bins that are more filled, but avoid extreme values.
    # Use a gentle linear scaling from empty (bonus ~0) to full (bonus ~1).
    capacity_approx = bins.max() + item  # rough estimate of bin capacity, works if at least one bin can hold item+something
    util_bonus = 1.0 - bins / (capacity_approx + 1e-12)
    
    # Combine: primary dominates, secondary adds tie-breaking towards higher utilization.
    scores = primary * 10.0 + util_bonus
    
    return scores.astype(float)
```

## tsp_construct / pure_eoh 最优代码

Hybridize nearest-neighbor selection with a regret-based look-ahead that penalizes choices which isolate distant clusters of unvisited nodes from the eventual return path to the destination.

```python
import numpy as np

def select_next_node(current_node: int, destination_node: int, unvisited_nodes: np.ndarray, distance_matrix: np.ndarray) -> int:
    if len(unvisited_nodes) == 1:
        return unvisited_nodes[0]

    # Step 1: Compute direct distances from current to each unvisited candidate
    direct_distances = distance_matrix[current_node][unvisited_nodes]

    # Step 2: For each candidate, compute the "isolation cost":
    #   the increase in total detour if we go to candidate now vs. visiting it later via another unvisited node,
    #   approximated by the difference between (current->candidate + candidate->destination)
    #   and the minimum of (current->other + other->candidate) for other in remaining_unvisited\{candidate}.
    #   Also include a cluster-awareness term: the maximum distance from candidate to any other unvisited node,
    #   scaled to avoid isolating far-away groups.
    scores = np.zeros_like(direct_distances, dtype=float)

    for i, cand in enumerate(unvisited_nodes):
        # Remaining unvisited excluding this candidate
        others = np.setdiff1d(unvisited_nodes, [cand])
        if len(others) > 0:
            # Detour if visited now directly: current->cand->dest
            direct_detour = distance_matrix[current_node, cand] + distance_matrix[cand, destination_node]

            # Alternative: go through another unvisited first, then to candidate later
            # Approximate minimal two-hop path: current->other + other->cand for some other
            alt_paths = distance_matrix[current_node, others] + distance_matrix[others, cand]
            best_alt = np.min(alt_paths) + distance_matrix[cand, destination_node]  # still need to reach dest eventually

            # Regret-like penalty for choosing now if alternative is much shorter overall
            regret = max(0, direct_detour - best_alt)

            # Cluster penalty: how isolated is 'cand' from the rest of unvisited?
            # Measured as max distance from cand to any other unvisited node
            cluster_penalty = np.max(distance_matrix[cand, others])

            # Combined score: primary weight on nearest neighbor, but adjusted by regret and cluster isolation
            # Normalize factors roughly
            scores[i] = direct_distances[i] + 0.3 * regret + 0.15 * cluster_penalty / (np.max(distance_matrix) + 1e-10)
        else:
            scores[i] = direct_distances[i]

    return unvisited_nodes[np.argmin(scores)]
```

## cvrp_construct / pure_eoh 最优代码

A nearest-neighbor heuristic that prioritizes closest feasible customers but switches to a farthest-first criterion when the remaining capacity drops below a threshold, otherwise returning to depot if no feasible nodes remain.

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
