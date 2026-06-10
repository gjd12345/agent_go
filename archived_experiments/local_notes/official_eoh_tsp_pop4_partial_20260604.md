# Official EoH TSP pop4 init-only 部分记录

时间：2026-06-04

目的：在 pop1 诊断后，将 `tsp_construct` 放大到 `pop_size=4, generations=0`，先跑三臂对照。当前只完成 `pure_eoh`，`api_only` 和 `literature_rag` 因 Codex 审批/额度限制待恢复后继续。

## 已完成结果

| problem | arm | pop_size | generations | return | runtime_seconds | best objective | valid/pop |
|---|---|---:|---:|---:|---:|---:|---:|
| tsp_construct | pure_eoh | 4 | 0 | 0 | 1622.299 | 6.83907 | 4/4 |

stdout 关键事实：init 8/8 evaluated，survivor pop=4，best=6.83907，耗时约 26.7 分钟。

## 当前解释

1. `pure_eoh pop4` 与此前 `pure_eoh pop1` 的 best 都是 `6.83907`，说明该 strong baseline 在 init 阶段已经稳定出现。
2. 这也意味着后续 `api_only` / `literature_rag` 至少要低于 `6.83907`，才算在 TSP 上出现正向 signal。
3. 当前不能比较三臂，因为 `api_only` / `literature_rag` 尚未完成。

## 待继续

额度/审批恢复后继续运行：

```text
tsp_construct / api_only / pop_size=4 / generations=0
tsp_construct / literature_rag / pop_size=4 / generations=0 / rag_top_k=2 / rag_max_chars=1800
```

## Best code

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
