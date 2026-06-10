# 自动化实验报告：tocc_day2_tsp_gen1_outlier

本报告由 Auto Summarizer 自动生成。结论措辞遵循 exploratory 约束：
不写'已证明''稳定优于''sweet spot 已确定'等无统计支持的强结论。

## 汇总表

| problem | arm | gen | pop | best | norm | Δ% | valid | cards | status |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| tsp_construct | tocc_corrected | 1 | 4 | 6.55479 | - | - | 4/4 | tsp_regret_insertion, tsp_farthest_insertion | OK |
| tsp_construct | tocc_corrected | 1 | 4 | 7.45222 | - | - | 4/4 | tsp_regret_insertion, tsp_farthest_insertion | OK |

## 代码片段

### tsp_construct

**tocc_corrected** (gen=1, best=6.55479):
```python

    n = len(unvisited_nodes)
    if n == 0:
        raise ValueError("No unvisited nodes available.")
    if n == 1:
        return unvisited_nodes[0]

    MAX_CANDIDATES_FOR_REGRET = 50
```

**tocc_corrected** (gen=1, best=7.45222):
```python

    if len(unvisited_nodes) == 0:
        raise ValueError("No unvisited nodes")
    
    dist_from_current = distance_matrix[current_node, unvisited_nodes]
    
    nn_scores = dist_from_current
    
```

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