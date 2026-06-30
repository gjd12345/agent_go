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
- gen=4 已完成同口径 repeat，对比见下一节。gen=0 不作为主要 evidence。

## TSP gen=4（更新，2026-06-18）

| arm | n | mean | min | max | spread |
|---|---:|---:|---:|---:|---:|
| pure_eoh gen=0 | 3 | 6.751 | 6.590 | 7.057 | 0.467 |
| tocc_corrected gen=0 | 5 | 7.372 | 6.189 | 9.656 | 3.467 |
| **pure_eoh gen=4** | **3** | **6.548** | **6.430** | **6.608** | **0.178** |
| **tocc_corrected gen=4** | **3** | **6.456** | **6.292** | **6.615** | **0.323** |

### TSP 结论

1. **gen=4 本身带来明显改善。** pure gen=0→gen=4 改善约 -3.0%（6.751→6.548）。进化深度是此前被低估的关键变量。

2. **TOCC gen=4 有 exploratory 正向信号。** 同口径 gen=4 pop=4 repeat=3 下，tocc_corrected mean=6.456，相比 pure mean=6.548 改善约 -1.4%；3 次中 2 次优于 pure mean。

3. **不能写成稳定证明。** tocc_corrected r2=6.615 劣于 pure mean，说明仍有生成方差。当前可写为“gen=4 下 TOCC 方向从 gen=0 的不稳定转为小幅正向信号”，不能写“稳定优于”。

4. **TOCC 价值区间更清楚。** CVRP 上 TOCC 主要解决错误 card 导致的 valid collapse；TSP 上 TOCC 主要在足够进化深度下提供方向偏置，效果较小但可观察。

### TSP gen=4 Success Funnel

| 层级 | 通过 | 总数 | 率 |
|---|---:|---:|---:|
| Proposal Accept | 6 | 6 | 100% |
| Linkage (RAG arms) | 3 | 3 | 100% |
| Generation | 6 | 6 | 100% |
| Objective | 3 | 6 | 50% |

注：Objective 层按“是否优于 pure gen=4 mean=6.548”逐 run 计算；pure 自身也参与该层统计，因此 6 次中 3 次通过。

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

*本报告由 summarize_manifest_runs.py 结果人工汇总更新，更新时间 2026-06-18*
