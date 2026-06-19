# 自动化实验报告：phase4_cvrp_targeted_repeat3

本报告由 Auto Summarizer 自动生成。结论措辞遵循 exploratory 约束：
不写'已证明''稳定优于''sweet spot 已确定'等无统计支持的强结论。

## 汇总表

| problem | arm | gen | pop | best | norm | Δ% | valid | cards | status |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| cvrp_construct | pure_eoh | 0 | 4 | 13.56507 | 1.002 | -0.2% | 4/4 | - | OK |
| cvrp_construct | pure_eoh | 0 | 4 | 13.61078 | 0.998 | +0.2% | 4/4 | - | OK |
| cvrp_construct | default_rag | 0 | 4 | 13.28321 | 1.023 | -2.2% | 1/1 | cvrp_far_first, cvrp_nearest_capacity | OK |
| cvrp_construct | default_rag | 0 | 4 | 13.28321 | 1.023 | -2.2% | 1/1 | cvrp_far_first, cvrp_nearest_capacity | OK |
| cvrp_construct | targeted_tocc | 0 | 4 | 12.886 | 1.054 | -5.2% | 4/4 | cvrp_regret_insertion, cvrp_far_first | OK |
| cvrp_construct | targeted_tocc | 0 | 4 | 12.92217 | 1.052 | -4.9% | 4/4 | cvrp_regret_insertion, cvrp_far_first | OK |

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

**default_rag** (gen=0, best=13.28321):
```python

                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    if len(unvisited_nodes) == 0:
        return depot
    
    if current_node == depot:
        dist_from_depot = distance_matrix[depot][unvisited_nodes]
```

## 下一步建议

（由 TOCC controller 或人工审查后填入）

---

*本报告自动生成于 summarize_manifest_runs.py*

## Agent 成功率漏斗 (Success Funnel)

五层漏斗，与 HeuriGym (ICLR 2026) 四阶段错误分类对齐：

| 层级 | 通过 | 总数 | 通过率 | 说明 |
|---|---:|---:|---:|---|
| 1. Proposal Accept (gatekeeper 通过, 无 infra 失败) | 6 | 6 | 100.0% | |
| 2. Linkage (selected_card_ids 已注入 rag_trace) | 4 | 4 | 100.0% | |
| 3. Generation (valid ≥ ceil(0.5×pop), 无 valid collapse) | 4 | 6 | 66.7% | |
| 4. Objective (best 优于 pure baseline mean) | 5 | 6 | 83.3% | |
| 5. Diagnosis (需 agent pipeline 数据, 当前未统计) | 0 | 0 | - | |

**Pure baseline (mean):** cvrp_construct=13.588

**注意:** diagnosis_success 需 agent pipeline 数据（LLM 诊断是否引用 ≥3 项 trace 证据），当前 marked as unknown。仅 generation 和 objective 层可由 run_summary 自动计算。