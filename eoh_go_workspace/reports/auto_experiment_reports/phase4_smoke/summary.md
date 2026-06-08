# 自动化实验报告：phase4_smoke

本报告由 Auto Summarizer 自动生成。结论措辞遵循 exploratory 约束：
不写'已证明''稳定优于''sweet spot 已确定'等无统计支持的强结论。

## 汇总表

| problem | arm | gen | pop | best | valid | cards | status |
|---|---|---:|---:|---:|---|---|---|
| cvrp_construct | targeted_cvrp | 0 | 4 | 13.07835 | 4/4 | cvrp_regret_insertion, cvrp_far_first | OK |
| tsp_construct | targeted_tsp | 0 | 4 | 6.47488 | 4/4 | tsp_regret_insertion, tsp_farthest_insertion | OK |

## 代码片段

### cvrp_construct

**targeted_cvrp** (gen=0, best=13.07835):
```python

                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    if len(unvisited_nodes) == 0:
        return depot
    
    dist_from_current = distance_matrix[current_node][unvisited_nodes]
    
```

### tsp_construct

**targeted_tsp** (gen=0, best=6.47488):
```python

    if len(unvisited_nodes) == 1:
        return unvisited_nodes[0]
    
    dist_from_current = distance_matrix[current_node][unvisited_nodes]
    
    min_dist_idx = np.argmin(dist_from_current)
    nearest_neighbor = unvisited_nodes[min_dist_idx]
```

## 下一步建议

（由 TOCC controller 或人工审查后填入）

---

*本报告自动生成于 summarize_manifest_runs.py*