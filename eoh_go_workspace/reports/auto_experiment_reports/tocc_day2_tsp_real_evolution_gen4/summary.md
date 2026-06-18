# 自动化实验报告：tocc_day2_tsp_real_evolution_gen4

本报告由 Auto Summarizer 自动生成。结论措辞遵循 exploratory 约束：
不写'已证明''稳定优于''sweet spot 已确定'等无统计支持的强结论。

## 汇总表

| problem | arm | gen | pop | best | norm | Δ% | valid | card_source | cards | status |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| tsp_construct | pure_eoh | 4 | 4 | 6.60788 | 0.991 | +0.9% | 4/4 | none | - | OK |
| tsp_construct | pure_eoh | 4 | 4 | 6.60788 | 0.991 | +0.9% | 4/4 | none | - | OK |
| tsp_construct | pure_eoh | 4 | 4 | 6.42951 | 1.018 | -1.8% | 4/4 | none | - | OK |
| tsp_construct | tocc_corrected | 4 | 4 | 6.29166 | 1.041 | -3.9% | 4/4 | literature | tsp_regret_insertion, tsp_farthest_insertion | OK |
| tsp_construct | tocc_corrected | 4 | 4 | 6.61498 | 0.990 | +1.0% | 4/4 | literature | tsp_regret_insertion, tsp_farthest_insertion | OK |
| tsp_construct | tocc_corrected | 4 | 4 | 6.45989 | 1.014 | -1.4% | 4/4 | literature | tsp_regret_insertion, tsp_farthest_insertion | OK |

## 代码片段

### tsp_construct

**tocc_corrected** (gen=4, best=6.29166):
```python
def select_next_node(current_node: int, destination_node: int, unvisited_nodes: np.ndarray, distance_matrix: np.ndarray) -> int:
    n_unvisited = len(unvisited_nodes)
    if n_unvisited <= 2:
        return unvisited_nodes[np.argmin(distance_matrix[current_node][unvisited_nodes])]
    dist_from_current = distance_matrix[current_node][unvisited_nodes]
    dist_to_dest = distance_matrix[destination_node][unvisited_nodes]
    regrets = []
    for i, u in enumerate(unvisited_nodes):
        d_curr = dist_from_current[i]
        d_dest = dist_to_dest[i]
        others = np.concatenate([unvisited_nodes[:i], unvisited_nodes[i+1:]])
        avg_dist_to_others = np.mean(distance_matrix[u][others])
```

**pure_eoh** (gen=4, best=6.42951):
```python
def select_next_node(current_node: int, destination_node: int, unvisited_nodes: np.ndarray, distance_matrix: np.ndarray) -> int:
    if len(unvisited_nodes) == 0:
        return destination_node
    if len(unvisited_nodes) == 1:
        return unvisited_nodes[0]
    idx = unvisited_nodes
    curr_dist = distance_matrix[current_node, idx]
    alpha = 0.8          # weight for forward progress vs. exploration
    beta = 0.5           # sensitivity to local sparsity
    gamma = 0.3          # influence of angular separation
    eps = 1e-12
    d_min = np.min(curr_dist)
```

## Card-memory / 选卡记录

| problem | arm | gen | card_source | selected_card_ids | history_card_ids | best_code_record_id | synthesized_card_id |
|---|---|---:|---|---|---|---|---|
| tsp_construct | pure_eoh | 4 | none | - | - | tsp_construct:pure_eoh:g4:r1 | - |
| tsp_construct | pure_eoh | 4 | none | - | - | tsp_construct:pure_eoh:g4:r2 | - |
| tsp_construct | pure_eoh | 4 | none | - | - | tsp_construct:pure_eoh:g4:r3 | - |
| tsp_construct | tocc_corrected | 4 | literature | tsp_regret_insertion, tsp_farthest_insertion | - | tsp_construct:tocc_corrected:g4:r1 | - |
| tsp_construct | tocc_corrected | 4 | literature | tsp_regret_insertion, tsp_farthest_insertion | - | tsp_construct:tocc_corrected:g4:r2 | - |
| tsp_construct | tocc_corrected | 4 | literature | tsp_regret_insertion, tsp_farthest_insertion | - | tsp_construct:tocc_corrected:g4:r3 | - |

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