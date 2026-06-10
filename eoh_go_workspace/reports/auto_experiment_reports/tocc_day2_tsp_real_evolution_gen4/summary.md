# 自动化实验报告：tocc_day2_tsp_real_evolution_gen4

本报告由 Auto Summarizer 自动生成。结论措辞遵循 exploratory 约束：
不写'已证明''稳定优于''sweet spot 已确定'等无统计支持的强结论。

## 汇总表

| problem | arm | gen | pop | best | norm | Δ% | valid | cards | status |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| tsp_construct | pure_eoh | 4 | 4 | 6.60788 | 0.991 | +0.9% | 4/4 | - | OK |
| tsp_construct | pure_eoh | 4 | 4 | 6.60788 | 0.991 | +0.9% | 4/4 | - | OK |
| tsp_construct | pure_eoh | 4 | 4 | 6.42951 | 1.018 | -1.8% | 4/4 | - | OK |
| tsp_construct | tocc_corrected | 4 | 4 | 6.29166 | 1.041 | -3.9% | 4/4 | tsp_regret_insertion, tsp_farthest_insertion | OK |
| tsp_construct | tocc_corrected | 4 | 4 | 6.61498 | 0.990 | +1.0% | 4/4 | tsp_regret_insertion, tsp_farthest_insertion | OK |
| tsp_construct | tocc_corrected | 4 | 4 | 6.45989 | 1.014 | -1.4% | 4/4 | tsp_regret_insertion, tsp_farthest_insertion | OK |

## 代码片段

### tsp_construct

**pure_eoh** (gen=4, best=6.60788):
```python


    Args:
        current_node: ID of the current node
        destination_node: ID of the destination (return) node
        unvisited_nodes: array of unvisited node IDs
        distance_matrix: pairwise distance matrix between all nodes
    Returns:
```

**pure_eoh** (gen=4, best=6.60788):
```python

    if len(unvisited_nodes) == 1:
        return unvisited_nodes[0]

    n_unvisited = len(unvisited_nodes)
    sub_indices = list(unvisited_nodes)
    idx_map = {node: i for i, node in enumerate(sub_indices)}
    
```

**pure_eoh** (gen=4, best=6.42951):
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
| 1. Proposal Accept (gatekeeper 通过, 无 infra 失败) | 6 | 6 | 100.0% | |
| 2. Linkage (selected_card_ids 已注入 rag_trace) | 3 | 3 | 100.0% | |
| 3. Generation (valid ≥ ceil(0.5×pop), 无 valid collapse) | 6 | 6 | 100.0% | |
| 4. Objective (best 优于 pure baseline mean) | 3 | 6 | 50.0% | |
| 5. Diagnosis (需 agent pipeline 数据, 当前未统计) | 0 | 0 | - | |

**Pure baseline (mean):** tsp_construct=6.548

**注意:** diagnosis_success 需 agent pipeline 数据（LLM 诊断是否引用 ≥3 项 trace 证据），当前 marked as unknown。仅 generation 和 objective 层可由 run_summary 自动计算。