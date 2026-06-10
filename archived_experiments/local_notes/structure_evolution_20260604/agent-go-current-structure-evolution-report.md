# agent_go 当前项目结构、数据流与代码演化记录

时间：2026-06-04

范围：只读整理当前 `agent_go` 的 Python harness、RAG corpus、official EoH TSP 实验结果和本地记录；不修改工程代码。

## 产物

- draw.io 源文件：`eoh_go_workspace/local_notes/structure_evolution_20260604/agent-go-structure-evolution.drawio`
- PNG 导出：`eoh_go_workspace/local_notes/structure_evolution_20260604/agent-go-structure-evolution.drawio.png`

## 当前最重要结论

TSP official benchmark 已经出现清晰的 targeted Literature-RAG 正向信号。默认 Literature-RAG 不提升，是因为检索选中了保守 nearest cards；targeted query 选中 `tsp_regret_insertion` + `tsp_farthest_insertion` 后，init-only 与 gen=4 都明显超过 pure EOH/API-only。

| setting | best objective | delta vs pure | valid/pop | selected cards |
|---|---:|---:|---:|---|
| `pure_eoh` | 6.83907 | +0.00000 | 4/4 | - |
| `api_only` | 6.78953 | -0.04954 | 4/4 | - |
| `literature_rag_default` | 6.83954 | +0.00047 | 4/4 | tsp_nearest_insertion, tsp_nearest_neighbor |
| `literature_rag_targeted_init` | 6.51118 | -0.32789 | 4/4 | tsp_regret_insertion, tsp_farthest_insertion |
| `targeted_gen4_pop8` | 6.28736 | -0.55171 | 8/8 | tsp_regret_insertion, tsp_farthest_insertion |

## 项目脚本结构表

| file | role |
|---|---|
| `eoh_go/__init__.py` | pipeline 基础模块 / CLI / store / router |
| `eoh_go/benchmark.py` | pipeline 基础模块 / CLI / store / router |
| `eoh_go/candidates.py` | pipeline 基础模块 / CLI / store / router |
| `eoh_go/cli.py` | pipeline 基础模块 / CLI / store / router |
| `eoh_go/efficiency_table.py` | pipeline 基础模块 / CLI / store / router |
| `eoh_go/eoh_runner/__init__.py` | EOH 控制面 / target registry / guard / RAG env 注入 |
| `eoh_go/eoh_runner/candidate_guard.py` | EOH 控制面 / target registry / guard / RAG env 注入 |
| `eoh_go/eoh_runner/config.py` | EOH 控制面 / target registry / guard / RAG env 注入 |
| `eoh_go/eoh_runner/problem_spec.py` | EOH 控制面 / target registry / guard / RAG env 注入 |
| `eoh_go/eoh_runner/registry.py` | EOH 控制面 / target registry / guard / RAG env 注入 |
| `eoh_go/eoh_runner/runner.py` | EOH 控制面 / target registry / guard / RAG env 注入 |
| `eoh_go/eoh_runner/target_spec.py` | EOH 控制面 / target registry / guard / RAG env 注入 |
| `eoh_go/evolution.py` | pipeline 基础模块 / CLI / store / router |
| `eoh_go/experiments/__init__.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/arrival_scale_table.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/build_full_paper_draft.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/build_paper_report.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/build_paper_style_table_image.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/build_valid_comparison_charts.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/dynamic_source_screen.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/efficiency_table.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/eight_problem_dt_tables.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/eoh_arrival_grid.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/eoh_obp_smoke.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/knapsack_smoke.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/mixer_split_smoke.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/official_eoh_run.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/official_eoh_smoke.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/policy_arrival_scale_table.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/router_probe.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/run_selected_repeats.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/summarize_eoh_grid_results.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/summarize_rag_ablation.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/summarize_selected_repeats.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/experiments/window_scale_table.py` | 实验入口、表格、报告、官方 EoH 对齐 runner |
| `eoh_go/memory.py` | pipeline 基础模块 / CLI / store / router |
| `eoh_go/paths.py` | pipeline 基础模块 / CLI / store / router |
| `eoh_go/rag/__init__.py` | RAG corpus/schema/retrieval/prompt formatting |
| `eoh_go/rag/build_corpus.py` | RAG corpus/schema/retrieval/prompt formatting |
| `eoh_go/rag/prompt_context.py` | RAG corpus/schema/retrieval/prompt formatting |
| `eoh_go/rag/retriever.py` | RAG corpus/schema/retrieval/prompt formatting |
| `eoh_go/rag/schemas.py` | RAG corpus/schema/retrieval/prompt formatting |
| `eoh_go/router_probe.py` | pipeline 基础模块 / CLI / store / router |
| `eoh_go/store.py` | pipeline 基础模块 / CLI / store / router |
| `eoh_go/strategy_router.py` | pipeline 基础模块 / CLI / store / router |

## 测试脚本表

| file | coverage intent |
|---|---|
| `tests/test_api_general_quota.py` | 单元测试 / regression gate |
| `tests/test_candidate_guard.py` | 单元测试 / regression gate |
| `tests/test_eoh_runner_specs.py` | 单元测试 / regression gate |
| `tests/test_official_eoh_run.py` | 单元测试 / regression gate |
| `tests/test_official_eoh_smoke.py` | 单元测试 / regression gate |
| `tests/test_rag_ablation_summary.py` | 单元测试 / regression gate |
| `tests/test_rag_build_corpus.py` | 单元测试 / regression gate |
| `tests/test_rag_context.py` | 单元测试 / regression gate |
| `tests/test_rag_prompt_context.py` | 单元测试 / regression gate |
| `tests/test_rag_retriever.py` | 单元测试 / regression gate |
| `tests/test_rag_runner_integration.py` | 单元测试 / regression gate |
| `tests/test_rag_schemas.py` | 单元测试 / regression gate |

## 数据流表

| stage | input | script/module | output | current evidence |
|---|---|---|---|---|
| Problem target | official EoH `tsp_construct` | `eoh_go/experiments/official_eoh_run.py` | `select_next_node(...)` prompt + evaluator | official root `/private/tmp/EoH-main` 已跑通 |
| RAG corpus | `algorithm_cards.jsonl`, `api_constraints.jsonl` | `eoh_go/rag/build_corpus.py` | 44 corpus items, problem-specific strategy pool | TSP top-k 可切换 nearest vs regret/farthest |
| Retrieval | query + strategy pool | `eoh_go/rag/retriever.py` | ranked cards + scores | targeted query selects `tsp_regret_insertion`, `tsp_farthest_insertion` |
| Prompt context | global API + selected cards | `eoh_go/rag/prompt_context.py` | two-section context | targeted context chars = 1917 |
| Evolution run | prompt + official evaluator | `official_eoh_run.py` calling official EoH | population_generation_N.json + samples_best.json | gen4 best = 6.28736 |
| Local record | summary JSON + best code | local note generator / manual aggregation | Chinese notes + diagram/report | this report + draw.io asset |

## 代码演化示例

### 1. Pure EOH baseline: progress-distance score

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

### 2. Targeted RAG init best: regret + farthest representative

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

### 3. Gen=4 best: isolation + regret score

```python
import numpy as np

def select_next_node(current_node: int, destination_node: int, unvisited_nodes: np.ndarray, distance_matrix: np.ndarray) -> int:
    """Select the next node to visit in a TSP greedy construction."""
    # Fallback to nearest neighbor if very few candidates remain
    if len(unvisited_nodes) <= 2:
        return unvisited_nodes[np.argmin(distance_matrix[current_node][unvisited_nodes])]

    # Compute centroid of unvisited nodes (including destination as part of context)
    relevant_nodes = np.append(unvisited_nodes, destination_node)
    centroid_x = np.mean(relevant_nodes)  # Using node indices as proxy positions; replace with real coords if available
    # Since we only have distance_matrix, we'll use average distance among unvisited as a spread measure
    # Compute mean distance between each unvisited node and all other unvisited+destination
    avg_distances = []
    for u in unvisited_nodes:
        others = np.setdiff1d(relevant_nodes, [u])
        avg_dist = np.mean([distance_matrix[u][o] for o in others])
        avg_distances.append(avg_dist)

    scores = []
    regrets = []

    # For each candidate, compute immediate cost and a simple 1‑step regret
    for i, cand in enumerate(unvisited_nodes):
        # Immediate cost
        d_current = distance_matrix[current_node][cand]

        # Isolation factor: higher avg distance means more isolated
        iso_factor = avg_distances[i]

        # Regret: difference between best direct link and best two‑hop via another unvisited
        # Best direct link from current to candidate is already d_current
        # Find best two‑hop: min over another unvisited k != cand of (dist[current][k] + dist[k][cand])
        two_hop_min = np.inf
        for j, k in enumerate(unvisited_nodes):
            if k == cand:
                continue
            two_hop = distance_matrix[current_node][k] + distance_matrix[k][cand]
            if two_hop < two_hop_min:
                two_hop_min = two_hop

        if two_hop_min == np.inf:  # only one candidate left
            regret_val = 0.0
        else:
            regret_val = max(0.0, two_hop_min - d_current)

        # Score combines inverse immediate cost, isolation, and regret
        # Weights tuned empirically: balance exploration vs exploitation
        w_iso = 0.4
        w_regret = 0.6
        # Normalize components relative to current best to keep scale stable
        scores.append((w_iso * iso_factor + w_regret * regret_val) / (d_current + 1e-9))
        regrets.append(regret_val)

    # If all regrets are zero (flat landscape), fall back to nearest neighbor with isolation tiebreak
    if np.max(regrets) == 0.0:
        best_idx = np.argmin(distance_matrix[current_node][unvisited_nodes])
        # Tiebreak toward more isolated node if equal distances occur
        min_dists = distance_matrix[current_node][unvisited_nodes]
        mask = min_dists == min_dists[best_idx]
        if np.sum(mask) > 1:
            tied_indices = np.where(mask)[0]
            best_tie_idx = tied_indices[np.argmax([avg_distances[t] for t in tied_indices])]
            return unvisited_nodes[best_tie_idx]
        return unvisited_nodes[best_idx]

    # Otherwise pick candidate with highest combined score
    best_score_idx = np.argmax(scores)
    return unvisited_nodes[best_score_idx]
```

## 进化轨迹

| phase | best objective | interpretation |
|---|---:|---|
| pure init | 6.83907 | 模型自然生成 progress/destination 族 |
| API-only init | 6.78953 | API 约束带来轻微信号 |
| default RAG init | 6.83954 | nearest cards 过于保守，未提升 |
| targeted RAG init | 6.51118 | regret/farthest cards 带来明显改善 |
| repeat best | 6.30547 | repeat=3 中最优，证明不是单次偶然 |
| gen4 best | 6.28736 | 深度进化最佳，出现 isolation + regret 组合 |
| gen8 plateau | 6.49327 | 更深迭代未继续改善 |

## 风险与下一步

- 当前正向信号集中在 TSP targeted RAG；BP 未拉开差距，CVRP 默认 cards 还需重写。
- 报告结论不能混淆 init-only、repeat、gen=4/8；需要保留 selected cards 和 best code。
- 下一步建议：把 TSP targeted RAG 作为主展示线，CVRP 先补 farthest/distance card 再复测。
