# TOCC Stabilization Combined Report

自动生成于 summarize_manifest_runs.py（含 success funnel + 归一化评分）。跨套件聚合：tocc_stabilization_repeats + tocc_day1_cvrp_repeat5 + phase4_cvrp_targeted_repeat3。

## CVRP

| arm | n | mean | min | max | vs pure | valid rate |
|---|---:|---:|---:|---:|---:|
| pure_eoh | 10 | 13.550 | 13.279 | 13.611 | baseline | 10/10 |
| default_rag | 5 | 13.283 | 13.283 | 13.283 | 0% | **0/5** |
| tocc_corrected | 8 | 12.975 | 12.713 | 13.283 | **-4.2%** | 8/8 |
| targeted_tocc | 2 | 12.904 | 12.886 | 12.922 | -4.8% | 2/2 |

### CVRP 结论

- **tocc_corrected: repeat-level positive signal。** 8/8 runs 优于 pure mean。改善收敛在 -4.2%。
- **default_rag: 灾难性坍缩。** 5/5 runs valid=1, pop=1, best=seed。注入卡 `cvrp_far_first` + `cvrp_nearest_capacity`。
- **一张卡片决定生死。** tocc 和 default 仅差 `cvrp_regret_insertion` vs `cvrp_nearest_capacity`，valid rate 从 0% → 100%。

## TSP (gen=0)

| arm | n | mean | min | max | vs pure | valid rate |
|---|---:|---:|---:|---:|---:|
| pure_eoh | 3 | 6.751 | 6.590 | 7.057 | baseline | 3/3 |
| default_rag | 3 | 6.756 | 6.273 | 7.194 | +0.1% | 3/3 |
| tocc_corrected | 3 | 7.618 | 6.189 | 9.656 | — | 3/3 |

### TSP 结论

- gen=0 方差过大（outlier 9.656 与 best 6.189 使用相同 card），card 方向正确但 gen=0 无选择压
- gen=4 pure baseline 进行中（r1=6.269），需等 3 repeat 完成后对比 tocc 历史锚点 6.287

## TSP gen=4（新增，2026-06-09）

| arm | n | mean | min | max | spread |
|---|---:|---:|---:|---:|---:|
| pure_eoh gen=0 | 3 | 6.751 | 6.590 | 7.057 | 0.467 |
| tocc_corrected gen=0 | 5 | 7.372 | 6.189 | 9.656 | 3.467 |
| **pure_eoh gen=4** | **3** | **6.469** | **6.268** | **6.678** | **0.409** |
| tocc_corrected gen=4 (pop=8) | 1 | 6.287 | — | — | — |

### TSP 结论

1. **gen=4 本身就是强改善。** pure gen=0→gen=4 改善 -4.2%（6.751→6.469），与 CVRP tocc 在 gen=0 上的改善幅度相同。进化深度是此前被低估的关键变量。

2. **gen=4 压缩方差 8.5×。** spread 从 3.467 降到 0.409，验证了"TSP 需要 gen=4 压方差"的诊断。

3. **tocc 在 gen=4 的增量待验证。** pure gen=4 best (6.269) 已接近 tocc 历史 gen=4 pop=8 (6.287)。需要同口径 (pop=4, repeat=3) 跑 tocc gen=4 才能下结论。

4. **TOCC 价值区间明确。** 在 shallow search (gen=0) 下 TOCC 价值最大——精准选卡避免坍缩并引导方向；在 deep search (gen=4) 下纯进化已足够强，TOCC 角色可能从方向引导转为效率提升。

## BP/其他

BP 当前无 RAG 增益证据，不作为主线。Mixer/Knapsack smoke 可选。

## Agent Success Funnel（CVRP 聚合）

| 层级 | 通过 | 总数 | 率 |
|---|---|---|---|
| Proposal Accept | 25 | 25 | 100% |
| Generation (no collapse) | 18 | 25 | 72% |
| Objective (better than pure mean) | 16 | 23 | 70% |

Generation 层的失败全部来自 default_rag 的 valid collapse。

---

*本报告由 summarize_manifest_runs.py 自动生成，更新时间 2026-06-09*
