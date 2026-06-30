# 自动化实验报告：tocc_day2_cvrp_real_evolution_gen4

本报告由 Auto Summarizer 自动生成。结论措辞遵循 exploratory 约束：
不写'已证明''稳定优于''sweet spot 已确定'等无统计支持的强结论。

## 汇总表

| problem | arm | gen | pop | best | norm | Δ% | valid | cards | status |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| cvrp_construct | pure_eoh | 4 | 4 | 13.57617 | 0.983 | +1.7% | 4/4 | - | OK |
| cvrp_construct | pure_eoh | 4 | 4 | 13.58669 | 0.982 | +1.8% | 4/4 | - | OK |
| cvrp_construct | pure_eoh | 4 | 4 | 13.23646 | 1.008 | -0.8% | 4/4 | - | OK |
| cvrp_construct | pure_eoh | 4 | 4 | 13.14576 | 1.015 | -1.5% | 4/4 | - | OK |
| cvrp_construct | pure_eoh | 4 | 4 | 13.17585 | 1.013 | -1.3% | 4/4 | - | OK |
| cvrp_construct | tocc_corrected | 4 | 4 | 12.9665 | 1.029 | -2.8% | 4/4 | cvrp_far_first, cvrp_regret_insertion | OK |
| cvrp_construct | tocc_corrected | 4 | 4 | 12.829 | 1.040 | -3.9% | 4/4 | cvrp_far_first, cvrp_regret_insertion | OK |
| cvrp_construct | tocc_corrected | 4 | 4 | 12.85606 | 1.038 | -3.7% | 4/4 | cvrp_far_first, cvrp_regret_insertion | OK |
| cvrp_construct | tocc_corrected | 4 | 4 | 12.829 | 1.040 | -3.9% | 4/4 | cvrp_far_first, cvrp_regret_insertion | OK |
| cvrp_construct | tocc_corrected | 4 | 4 | 12.70481 | 1.050 | -4.8% | 4/4 | cvrp_far_first, cvrp_regret_insertion | OK |

## 代码片段

### cvrp_construct

**pure_eoh** (gen=4, best=13.57617):
```python

                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    
    if len(unvisited_nodes) == 0:
        return depot
    
    distances = distance_matrix[current_node][unvisited_nodes]
```

**pure_eoh** (gen=4, best=13.58669):
```python

                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:

    Args:
        current_node:    index of the current node (0 = depot)
        depot:           index of the depot (always 0)
        unvisited_nodes: array of feasible unvisited customer indices
```

**pure_eoh** (gen=4, best=13.23646):
```python
                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    if len(unvisited_nodes) == 0:
        return depot
    current_to_depot = distance_matrix[current_node][depot]
    best_saving = -np.inf
    best_node = None
    for node in unvisited_nodes:
```

## 下一步建议

（由 TOCC controller 或人工审查后填入）

---

*本报告自动生成于 summarize_manifest_runs.py*

## Agent 成功率漏斗 (Success Funnel)

五层漏斗，与 HeuriGym (ICLR 2026) 四阶段错误分类对齐：

| 层级 | 通过 | 总数 | 通过率 | 说明 |
|---|---:|---:|---:|---|
| 1. Proposal Accept (gatekeeper 通过, 无 infra 失败) | 10 | 10 | 100.0% | |
| 2. Linkage (selected_card_ids 已注入 rag_trace) | 5 | 5 | 100.0% | |
| 3. Generation (valid ≥ ceil(0.5×pop), 无 valid collapse) | 10 | 10 | 100.0% | |
| 4. Objective (best 优于 pure baseline mean) | 8 | 10 | 80.0% | |
| 5. Diagnosis (需 agent pipeline 数据, 当前未统计) | 0 | 0 | - | |

**Pure baseline (mean):** cvrp_construct=13.344

**注意:** diagnosis_success 需 agent pipeline 数据（LLM 诊断是否引用 ≥3 项 trace 证据），当前 marked as unknown。仅 generation 和 objective 层可由 run_summary 自动计算。