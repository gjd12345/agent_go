# 自动化实验报告：v2_agent_real_run_validation

本报告由 Auto Summarizer 自动生成。结论措辞遵循 exploratory 约束：
不写'已证明''稳定优于''sweet spot 已确定'等无统计支持的强结论。

## 汇总表

| problem | arm | gen | pop | best | valid | cards | status |
|---|---|---:|---:|---:|---|---|---|
| cvrp_construct | v2_agent_targeted_cvrp_regret_savings | 0 | 4 | 13.2301 | 4/4 | cvrp_regret_insertion, cvrp_savings | OK |
| cvrp_construct | v2_agent_targeted_cvrp_regret_savings_v2 | 0 | 4 | 13.23646 | 4/4 | cvrp_regret_insertion, cvrp_savings | OK |
| tsp_construct | v2_agent_targeted_tsp | 0 | 4 | 6.21694 | 4/4 | tsp_regret_insertion, tsp_farthest_insertion | OK |

## 代码片段

### cvrp_construct

**v2_agent_targeted_cvrp_regret_savings** (gen=0, best=13.2301):
```python

                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    if len(unvisited_nodes) == 0:
        return depot

    dist_from_current = distance_matrix[current_node, unvisited_nodes]
    dist_from_depot = distance_matrix[depot, unvisited_nodes]
```

**v2_agent_targeted_cvrp_regret_savings_v2** (gen=0, best=13.23646):
```python

                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:

    Args:
        current_node:    index of the current node (0 = depot)
        depot:           index of the depot (always 0)
        unvisited_nodes: array of feasible unvisited customer indices
```

### tsp_construct

**v2_agent_targeted_tsp** (gen=0, best=6.21694):
```python

    if len(unvisited_nodes) == 1:
        return unvisited_nodes[0]

    curr_dists = distance_matrix[current_node][unvisited_nodes]

    regret_vals = np.zeros(len(unvisited_nodes))
    for i, u in enumerate(unvisited_nodes):
```

## 下一步建议

（由 TOCC controller 或人工审查后填入）

---

*本报告自动生成于 summarize_manifest_runs.py*