# 自动化实验报告：tocc_day2_tsp_pure_gen4

本报告由 Auto Summarizer 自动生成。结论措辞遵循 exploratory 约束：
不写'已证明''稳定优于''sweet spot 已确定'等无统计支持的强结论。

## 汇总表

| problem | arm | gen | pop | best | norm | Δ% | valid | cards | status |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| tsp_construct | pure_eoh | 4 | 4 | 6.26884 | 1.032 | -3.1% | 4/4 | - | OK |
| tsp_construct | pure_eoh | 4 | 4 | 6.46162 | 1.001 | -0.1% | 4/4 | - | OK |
| tsp_construct | pure_eoh | 4 | 4 | 6.67754 | 0.969 | +3.2% | 4/4 | - | OK |

## 代码片段

### tsp_construct

**pure_eoh** (gen=4, best=6.26884):
```python

    if len(unvisited_nodes) == 1:
        return unvisited_nodes[0]
    
    dist_from_current = distance_matrix[current_node, unvisited_nodes]
    dist_to_dest = distance_matrix[unvisited_nodes, destination_node]
    
    max_fwd = np.max(dist_from_current)
```

**pure_eoh** (gen=4, best=6.46162):
```python


    Args:
        current_node: ID of the current node
        destination_node: ID of the destination (return) node
        unvisited_nodes: array of unvisited node IDs
        distance_matrix: pairwise distance matrix between all nodes
    Returns:
```

**pure_eoh** (gen=4, best=6.67754):
```python

    if len(unvisited_nodes) == 1:
        return unvisited_nodes[0]

        n = len(nodes)
        if n <= 1:
            return 0.0
        included = [False] * n
```

## 下一步建议

（由 TOCC controller 或人工审查后填入）

---

*本报告自动生成于 summarize_manifest_runs.py*

## Agent 成功率漏斗 (Success Funnel)

五层漏斗，与 HeuriGym (ICLR 2026) 四阶段错误分类对齐：

| 层级 | 通过 | 总数 | 通过率 | 说明 |
|---|---:|---:|---:|---|
| 1. Proposal Accept (gatekeeper 通过, 无 infra 失败) | 3 | 3 | 100.0% | |
| 2. Linkage (selected_card_ids 已注入 rag_trace) | 0 | 0 | - | (insufficient data) |
| 3. Generation (valid ≥ ceil(0.5×pop), 无 valid collapse) | 3 | 3 | 100.0% | |
| 4. Objective (best 优于 pure baseline mean) | 2 | 3 | 66.7% | |
| 5. Diagnosis (需 agent pipeline 数据, 当前未统计) | 0 | 0 | - | |

**Pure baseline (mean):** tsp_construct=6.469

**注意:** diagnosis_success 需 agent pipeline 数据（LLM 诊断是否引用 ≥3 项 trace 证据），当前 marked as unknown。仅 generation 和 objective 层可由 run_summary 自动计算。