# History/Mixed RAG Routing Smoke（2026-06-18）

目的：验证 best-code memory 生成的 `history_*` cards 已经不是“只写入 corpus”，而是能被 official EoH runner 的 `history_rag` / `mixed_rag` 路径实际检索并注入。

本 smoke 不调用 LLM，不读取 API key，只调用：

```text
build_official_rag_context(project_root, problem, mode, top_k=5, max_chars=2500, query=...)
```

## TSP

query:

```text
tsp construct regret evolved adaptive destination centrality farthest route length
```

| mode | strategy pool | context chars | selected ids |
|---|---:|---:|---|
| literature_rag | 5 | 2500 | `tsp_farthest_insertion`, `tsp_regret_insertion`, `tsp_nearest_insertion`, `tsp_two_opt_awareness`, `tsp_nearest_neighbor` |
| history_rag | 3 | 2500 | `history_tsp_construct_centrality_destination_farthest_5f1a3e`, `history_tsp_construct_adaptive_weights_centrality_destination_1e25e5`, `history_tsp_construct_adaptive_weights_destination_forward_score_4cb543` |
| mixed_rag | 8 | 2500 | `history_tsp_construct_centrality_destination_farthest_5f1a3e`, `history_tsp_construct_adaptive_weights_centrality_destination_1e25e5`, `history_tsp_construct_adaptive_weights_destination_forward_score_4cb543`, `tsp_farthest_insertion`, `tsp_regret_insertion` |

结论：

- `literature_rag` 保持纯 literature cards。
- `history_rag` 只返回 `history_tsp_construct_*`。
- `mixed_rag` 能同时返回 history + literature cards。

## CVRP

query:

```text
cvrp construct regret evolved capacity destination savings farthest route depot
```

| mode | strategy pool | context chars | selected ids |
|---|---:|---:|---|
| literature_rag | 5 | 2500 | `cvrp_savings`, `cvrp_nearest_capacity`, `cvrp_regret_insertion`, `cvrp_far_first`, `cvrp_sweep` |
| history_rag | 8 | 2500 | `history_cvrp_construct_adaptive_weights_capacity_destination_9df661`, `history_cvrp_construct_capacity_clustering_destination_5656e1`, `history_cvrp_construct_adaptive_weights_capacity_destination_d7206c`, `history_cvrp_construct_capacity_clustering_destination_1acd4f`, `history_cvrp_construct_capacity_destination_farthest_085049` |
| mixed_rag | 13 | 2500 | `history_cvrp_construct_adaptive_weights_capacity_destination_9df661`, `history_cvrp_construct_capacity_clustering_destination_5656e1`, `history_cvrp_construct_adaptive_weights_capacity_destination_d7206c`, `history_cvrp_construct_capacity_clustering_destination_1acd4f`, `history_cvrp_construct_capacity_destination_farthest_085049` |

结论：

- `history_rag` 已可消费 CVRP best-code memory。
- 当前 query 下，`mixed_rag` top-5 被 history cards 占满，文献卡没有进入 prompt。
- 后续如果要测试“history + literature 组合”，不应只用默认 mixed retrieval；应使用 `selected_card_ids` 强制控制组合比例。

## 后续实验建议

最小真实 LLM smoke 不建议直接跑大矩阵，建议两组即可。已落地为 manifest：

```text
eoh_go_workspace/experiments/manifests/tocc_history_mixed_cvrp_smoke.json
```

dry-run 已验证会展开 2 个 run：

```text
run_cvrp_construct_literature_regret_far_g0_r1
run_cvrp_construct_mixed_history_far_regret_g0_r1
```

selected-card linkage 已验证：

| arm | runner_arm | selected ids | context chars |
|---|---|---|---:|
| literature_regret_far | literature_rag | `cvrp_regret_insertion`, `cvrp_far_first` | 2122 |
| mixed_history_far_regret | mixed_rag | `history_cvrp_construct_capacity_destination_farthest_085049`, `cvrp_regret_insertion` | 2500 |

真实实验配置：

```text
problem: cvrp_construct
generations: 0
pop_size: 4
repeat: 1

arm A: literature_rag selected_card_ids=cvrp_regret_insertion,cvrp_far_first
arm B: mixed_rag selected_card_ids=history_cvrp_construct_capacity_destination_farthest_085049,cvrp_regret_insertion
```

判定标准：

```text
linkage_success: selected_card_ids == rag_trace.rag_selected_items
generation_success: valid_candidates >= 2
objective_signal: best_objective < pure_baseline_mean
```

注意：这个 smoke 只能验证 best-code memory 是否可用，不能证明 history cards 优于 literature cards。
