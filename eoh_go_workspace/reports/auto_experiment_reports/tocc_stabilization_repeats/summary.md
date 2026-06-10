# 自动化实验报告：tocc_stabilization_repeats

本报告由 Auto Summarizer 自动生成。结论措辞遵循 exploratory 约束：
不写'已证明''稳定优于''sweet spot 已确定'等无统计支持的强结论。

## 汇总表

| problem | arm | gen | pop | best | norm | Δ% | valid | cards | status |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| cvrp_construct | pure_eoh | 0 | 4 | 13.56507 | 1.002 | -0.2% | 3/3 | - | OK |
| cvrp_construct | pure_eoh | 0 | 4 | 13.61078 | 0.999 | +0.1% | 4/4 | - | OK |
| cvrp_construct | pure_eoh | 0 | 4 | 13.61078 | 0.999 | +0.1% | 4/4 | - | OK |
| cvrp_construct | default_rag | 0 | 4 | 13.28321 | 1.024 | -2.3% | 1/1 | cvrp_far_first, cvrp_nearest_capacity | OK |
| cvrp_construct | default_rag | 0 | 4 | 13.28321 | 1.024 | -2.3% | 1/1 | cvrp_far_first, cvrp_nearest_capacity | OK |
| cvrp_construct | default_rag | 0 | 4 | 13.28321 | 1.024 | -2.3% | 1/1 | cvrp_far_first, cvrp_nearest_capacity | OK |
| cvrp_construct | tocc_corrected | 0 | 4 | 12.7382 | 1.067 | -6.3% | 4/4 | cvrp_regret_insertion, cvrp_far_first | OK |
| cvrp_construct | tocc_corrected | 0 | 4 | 12.88776 | 1.055 | -5.2% | 4/4 | cvrp_regret_insertion, cvrp_far_first | OK |
| cvrp_construct | tocc_corrected | 0 | 4 | 13.28321 | 1.024 | -2.3% | 4/4 | cvrp_regret_insertion, cvrp_far_first | OK |
| tsp_construct | pure_eoh | 0 | 4 | 6.60788 | 1.022 | -2.1% | 4/4 | - | OK |
| tsp_construct | pure_eoh | 0 | 4 | 7.05664 | 0.957 | +4.5% | 4/4 | - | OK |
| tsp_construct | pure_eoh | 0 | 4 | 6.5898 | 1.024 | -2.4% | 4/4 | - | OK |
| tsp_construct | default_rag | 0 | 4 | 6.27344 | 1.076 | -7.1% | 4/4 | tsp_nearest_insertion, tsp_nearest_neighbor | OK |
| tsp_construct | default_rag | 0 | 4 | 7.19415 | 0.939 | +6.6% | 4/4 | tsp_nearest_insertion, tsp_nearest_neighbor | OK |
| tsp_construct | default_rag | 0 | 4 | 6.79914 | 0.993 | +0.7% | 4/4 | tsp_nearest_insertion, tsp_nearest_neighbor | OK |
| tsp_construct | tocc_corrected | 0 | 4 | 9.6561 | 0.699 | +43.0% | 4/4 | tsp_regret_insertion, tsp_farthest_insertion | OK |
| tsp_construct | tocc_corrected | 0 | 4 | 7.01002 | 0.963 | +3.8% | 4/4 | tsp_regret_insertion, tsp_farthest_insertion | OK |
| tsp_construct | tocc_corrected | 0 | 4 | 6.18855 | 1.091 | -8.3% | 4/4 | tsp_regret_insertion, tsp_farthest_insertion | OK |

## 代码片段

### cvrp_construct

**pure_eoh** (gen=0, best=13.56507):
```python

                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:

    Args:
        current_node:    index of the current node (0 = depot)
        depot:           index of the depot (always 0)
        unvisited_nodes: array of feasible unvisited customer indices
```

**pure_eoh** (gen=0, best=13.61078):
```python

                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:

    Args:
        current_node:    index of the current node (0 = depot)
        depot:           index of the depot (always 0)
        unvisited_nodes: array of feasible unvisited customer indices
```

**pure_eoh** (gen=0, best=13.61078):
```python

                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    if len(unvisited_nodes) == 0:
        return depot
    distances = distance_matrix[current_node][unvisited_nodes]
    nearest_idx = np.argmin(distances)
    nearest_node = unvisited_nodes[nearest_idx]
```

### tsp_construct

**pure_eoh** (gen=0, best=6.60788):
```python

    if len(unvisited_nodes) == 0:
        raise ValueError("No unvisited nodes left.")
    dist_to_current = distance_matrix[current_node, unvisited_nodes]
    if len(unvisited_nodes) == 1:
        dist_closest_other = distance_matrix[destination_node, unvisited_nodes]
    else:
        cand_indices = {node: i for i, node in enumerate(unvisited_nodes)}
```

**pure_eoh** (gen=0, best=7.05664):
```python

    if len(unvisited_nodes) == 0:
        raise ValueError("No unvisited nodes left")
    
    if len(unvisited_nodes) == 1:
        return unvisited_nodes[0]
    
    dists = distance_matrix[current_node][unvisited_nodes]
```

**pure_eoh** (gen=0, best=6.5898):
```python


    Args:
        current_node: ID of the current node
        destination_node: ID of the destination (return) node
        unvisited_nodes: array of unvisited node IDs
        distance_matrix: pairwise distance matrix between all nodes
    Returns:
```

## 下一步建议

（由 TOCC controller 或人工审查后填入）

---

*本报告自动生成于 summarize_manifest_runs.py*

## Agent 成功率漏斗 (Success Funnel)

五层漏斗，与 HeuriGym (ICLR 2026) 四阶段错误分类对齐：

| 层级 | 通过 | 总数 | 通过率 | 说明 |
|---|---:|---:|---:|---|
| 1. Proposal Accept (gatekeeper 通过, 无 infra 失败) | 18 | 18 | 100.0% | |
| 2. Linkage (selected_card_ids 已注入 rag_trace) | 12 | 12 | 100.0% | |
| 3. Generation (valid ≥ ceil(0.5×pop), 无 valid collapse) | 15 | 18 | 83.3% | |
| 4. Objective (best 优于 pure baseline mean) | 11 | 18 | 61.1% | |
| 5. Diagnosis (需 agent pipeline 数据, 当前未统计) | 0 | 0 | - | |

**Pure baseline (mean):** tsp_construct=6.751, cvrp_construct=13.596

**注意:** diagnosis_success 需 agent pipeline 数据（LLM 诊断是否引用 ≥3 项 trace 证据），当前 marked as unknown。仅 generation 和 objective 层可由 run_summary 自动计算。