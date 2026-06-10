# 自动化实验报告：tocc_day2_tsp_tocc_gen4

本报告由 Auto Summarizer 自动生成。结论措辞遵循 exploratory 约束：
不写'已证明''稳定优于''sweet spot 已确定'等无统计支持的强结论。

## 汇总表

| problem | arm | gen | pop | best | norm | Δ% | valid | cards | status |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| tsp_construct | tocc_corrected | 4 | 4 | 7.32429 | - | - | 4/4 | tsp_regret_insertion, tsp_farthest_insertion | OK |
| tsp_construct | tocc_corrected | 4 | 4 | 6.39984 | - | - | 4/4 | tsp_regret_insertion, tsp_farthest_insertion | OK |
| tsp_construct | tocc_corrected | 4 | 4 | 6.50991 | - | - | 4/4 | tsp_regret_insertion, tsp_farthest_insertion | OK |

## 代码片段

### tsp_construct

**tocc_corrected** (gen=4, best=7.32429):
```python

    if len(unvisited_nodes) == 0:
        raise ValueError("No unvisited nodes")
    if len(unvisited_nodes) == 1:
        return unvisited_nodes[0]

    dist_from_current = distance_matrix[current_node][unvisited_nodes]
    dist_to_dest = distance_matrix[destination_node][unvisited_nodes]
```

**tocc_corrected** (gen=4, best=6.39984):
```python

    if len(unvisited_nodes) <= 2:
        return unvisited_nodes[np.argmin(distance_matrix[current_node][unvisited_nodes])]

    curr_dists = distance_matrix[current_node][unvisited_nodes]
    dest_dists = distance_matrix[destination_node][unvisited_nodes]

    scores = np.empty(len(unvisited_nodes), dtype=np.float64)
```

**tocc_corrected** (gen=4, best=6.50991):
```python

    if len(unvisited_nodes) == 0:
        raise ValueError("No unvisited nodes")
    
    cur_dists = distance_matrix[current_node][unvisited_nodes]
    nn_score = cur_dists / np.max(cur_dists) if np.max(cur_dists) > 0 else np.ones_like(cur_dists)
    
    dest_dists = distance_matrix[destination_node][unvisited_nodes]
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
| 2. Linkage (selected_card_ids 已注入 rag_trace) | 3 | 3 | 100.0% | |
| 3. Generation (valid ≥ ceil(0.5×pop), 无 valid collapse) | 3 | 3 | 100.0% | |
| 4. Objective (best 优于 pure baseline mean) | 0 | 0 | - | (insufficient data) |
| 5. Diagnosis (需 agent pipeline 数据, 当前未统计) | 0 | 0 | - | |