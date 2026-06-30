# 自动化实验报告：tocc_split_history_cvrp_smoke

本报告由 Auto Summarizer 自动生成。结论措辞遵循 exploratory 约束：
不写'已证明''稳定优于''sweet spot 已确定'等无统计支持的强结论。

## 汇总表

| problem | arm | gen | pop | best | norm | Δ% | valid | card_source | cards | status |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| cvrp_construct | literature_regret_far | 0 | 4 | 12.72795 | - | - | 4/4 | literature | cvrp_regret_insertion, cvrp_far_first | OK |
| cvrp_construct | split_far_seed_regret | 0 | 4 | 13.00458 | - | - | 4/4 | mixed | history_cvrp_far_destination_seed, cvrp_regret_insertion | OK |
| cvrp_construct | split_capacity_filter_regret | 0 | 4 | 13.23646 | - | - | 4/4 | mixed | history_cvrp_capacity_feasible_filter, cvrp_regret_insertion | OK |
| cvrp_construct | split_remaining_alpha_far | 0 | 4 | 12.96129 | - | - | 4/4 | mixed | history_cvrp_remaining_aware_alpha, cvrp_far_first | OK |

## 代码片段

### cvrp_construct

**literature_regret_far** (gen=0, best=12.72795):
```python
def select_next_node(current_node: int, depot: int, unvisited_nodes: np.ndarray,
                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    if len(unvisited_nodes) == 0:
        return depot
    dist_from_current = distance_matrix[current_node, unvisited_nodes]
    dist_from_depot = distance_matrix[depot, unvisited_nodes]
    max_curr_dist = np.max(dist_from_current) if len(dist_from_current) > 0 else 1.0
    min_curr_dist = np.min(dist_from_current) if len(dist_from_current) > 0 else 0.0
    range_curr = max_curr_dist - min_curr_dist
    if range_curr == 0:
        range_curr = 1.0
```

**split_remaining_alpha_far** (gen=0, best=12.96129):
```python
def select_next_node(current_node: int, depot: int, unvisited_nodes: np.ndarray,
                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    if len(unvisited_nodes) == 0:
        return depot
    total_customers = len(demands) - 1  # exclude depot
    remaining_ratio = len(unvisited_nodes) / total_customers if total_customers > 0 else 0.5
    alpha = min(1.0, max(0.0, remaining_ratio))
    if current_node == depot:
        dist_from_depot = distance_matrix[depot][unvisited_nodes]
        median_dist = np.median(dist_from_depot)
        far_candidates = unvisited_nodes[dist_from_depot >= median_dist]
```

**split_far_seed_regret** (gen=0, best=13.00458):
```python
def select_next_node(current_node: int, depot: int, unvisited_nodes: np.ndarray,
                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    if len(unvisited_nodes) == 0:
        return depot
    if current_node == depot:
        distances_from_depot = distance_matrix[depot][unvisited_nodes]
        farthest_idx = np.argmax(distances_from_depot)
        return unvisited_nodes[farthest_idx]
    n_candidates = len(unvisited_nodes)
    if n_candidates == 1:
        return unvisited_nodes[0]
```

**split_capacity_filter_regret** (gen=0, best=13.23646):
```python
def select_next_node(current_node: int, depot: int, unvisited_nodes: np.ndarray,
                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    if len(unvisited_nodes) == 0:
        return depot
    feasible_mask = demands[unvisited_nodes] <= rest_capacity + 1e-9
    feasible_nodes = unvisited_nodes[feasible_mask]
    if len(feasible_nodes) == 0:
        return depot
    dist_from_current = distance_matrix[current_node][feasible_nodes]
    nearest_idx = np.argmin(dist_from_current)
    nearest_dist = dist_from_current[nearest_idx]
```

## Card-memory / 选卡记录

| problem | arm | gen | card_source | selected_card_ids | history_card_ids | best_code_record_id | synthesized_card_id |
|---|---|---:|---|---|---|---|---|
| cvrp_construct | literature_regret_far | 0 | literature | cvrp_regret_insertion, cvrp_far_first | - | cvrp_construct:literature_regret_far:g0:r1 | - |
| cvrp_construct | split_far_seed_regret | 0 | mixed | history_cvrp_far_destination_seed, cvrp_regret_insertion | history_cvrp_far_destination_seed | cvrp_construct:split_far_seed_regret:g0:r1 | - |
| cvrp_construct | split_capacity_filter_regret | 0 | mixed | history_cvrp_capacity_feasible_filter, cvrp_regret_insertion | history_cvrp_capacity_feasible_filter | cvrp_construct:split_capacity_filter_regret:g0:r1 | - |
| cvrp_construct | split_remaining_alpha_far | 0 | mixed | history_cvrp_remaining_aware_alpha, cvrp_far_first | history_cvrp_remaining_aware_alpha | cvrp_construct:split_remaining_alpha_far:g0:r1 | - |

## 下一步建议

（由 TOCC controller 或人工审查后填入）

---

*本报告自动生成于 summarize_manifest_runs.py*

## Agent 成功率漏斗 (Success Funnel)

五层漏斗，与 HeuriGym (ICLR 2026) 四阶段错误分类对齐：

| 层级 | 通过 | 总数 | 通过率 | 说明 |
|---|---:|---:|---:|---|
| 1. Proposal Accept (gatekeeper 通过, 无 infra 失败) | 4 | 4 | 100.0% | |
| 2. Linkage (selected_card_ids 已注入 rag_trace) | 4 | 4 | 100.0% | |
| 3. Generation (valid ≥ ceil(0.5×pop), 无 valid collapse) | 4 | 4 | 100.0% | |
| 4. Objective (best 优于 pure baseline mean) | 0 | 0 | - | (insufficient data) |
| 5. Diagnosis (需 agent pipeline 数据, 当前未统计) | 0 | 0 | - | |