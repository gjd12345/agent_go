# 自动化实验报告：tocc_history_mixed_cvrp_smoke

本报告由 Auto Summarizer 自动生成。结论措辞遵循 exploratory 约束：
不写'已证明''稳定优于''sweet spot 已确定'等无统计支持的强结论。

## 汇总表

| problem | arm | gen | pop | best | norm | Δ% | valid | card_source | cards | status |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| cvrp_construct | literature_regret_far | 0 | 4 | 13.09441 | - | - | 4/4 | literature | cvrp_regret_insertion, cvrp_far_first | OK |
| cvrp_construct | mixed_history_far_regret | 0 | 4 | 14.20996 | - | - | 4/4 | mixed | history_cvrp_construct_capacity_destination_farthest_085049, cvrp_regret_insertion | OK |

## 代码片段

### cvrp_construct

**literature_regret_far** (gen=0, best=13.09441):
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
    if current_node == depot:
        depot_distances = distance_matrix[depot][feasible_nodes]
        return feasible_nodes[np.argmax(depot_distances)]
```

**mixed_history_far_regret** (gen=0, best=14.20996):
```python
def select_next_node(current_node: int, depot: int, unvisited_nodes: np.ndarray,
                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    if len(unvisited_nodes) == 0:
        return depot
    feasible_mask = demands[unvisited_nodes] <= rest_capacity + 1e-9
    feasible = unvisited_nodes[feasible_mask]
    if len(feasible) == 0:
        return depot
    n_remaining = len(unvisited_nodes)
    alpha = min(2.0, 0.5 + 1.5 * (n_remaining / max(len(demands) - 1, 1)))
    base_scores = distance_matrix[current_node, feasible] + alpha * distance_matrix[feasible, depot]
```

## Card-memory / 选卡记录

| problem | arm | gen | card_source | selected_card_ids | history_card_ids | best_code_record_id | synthesized_card_id |
|---|---|---:|---|---|---|---|---|
| cvrp_construct | literature_regret_far | 0 | literature | cvrp_regret_insertion, cvrp_far_first | - | cvrp_construct:literature_regret_far:g0:r1 | - |
| cvrp_construct | mixed_history_far_regret | 0 | mixed | history_cvrp_construct_capacity_destination_farthest_085049, cvrp_regret_insertion | history_cvrp_construct_capacity_destination_farthest_085049 | cvrp_construct:mixed_history_far_regret:g0:r1 | - |

## 下一步建议

（由 TOCC controller 或人工审查后填入）

---

*本报告自动生成于 summarize_manifest_runs.py*

## Agent 成功率漏斗 (Success Funnel)

五层漏斗，与 HeuriGym (ICLR 2026) 四阶段错误分类对齐：

| 层级 | 通过 | 总数 | 通过率 | 说明 |
|---|---:|---:|---:|---|
| 1. Proposal Accept (gatekeeper 通过, 无 infra 失败) | 2 | 2 | 100.0% | |
| 2. Linkage (selected_card_ids 已注入 rag_trace) | 2 | 2 | 100.0% | |
| 3. Generation (valid ≥ ceil(0.5×pop), 无 valid collapse) | 2 | 2 | 100.0% | |
| 4. Objective (best 优于 pure baseline mean) | 0 | 0 | - | (insufficient data) |
| 5. Diagnosis (需 agent pipeline 数据, 当前未统计) | 0 | 0 | - | |