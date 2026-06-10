# TOCC Day观察笔记 / Observation Notes

日期：2026-06-09

## 1. CVRP n=8 数据分析

- pure_eoh: n=8, mean=13.540, range=[13.279, 13.611]
- tocc_corrected: n=8, mean=12.975, range=[12.713, 13.283]
- tocc 8/8 less than pure mean → improvement 4.2%
- success funnel: 8/8 proposal_accept, 8/8 linkage, 8/8 generation, 8/8 objective

**趋势**: tocc 的 8 个值中 2 个等于 13.283（与 default_rag degenerate 值相同），但仍有 6/8 显著低于 pure。best=12.713 是 init-only 新低。

**代码特征**: 最佳和最差 tocc 代码都有 `regret + farthest + nearest + depot + distance` 特征——card set 稳定引导到同一策略族。最差代码（13.283）更倾回 nearest，最好代码（12.713）更倾向 farthest clustering。

## 2. TSP Outlier 诊断

stabilization 3 个 tocc runs：
- r1: 9.656（outlier）——代码有 nearest + regret + farthest 特征，但 objective 极差
- r2: 7.010
- r3: 6.189（极佳）

三者的代码特征完全相同（nearest, regret, farthest, distance, destination），但 objective 差异巨大。根因不是 cards 问题，而是 TSP init-only 本身方差大——LLM 每次 init 生成 8 个候选然后选 4 个 survivor，随机波动很大。

**修正建议**: TSP 不宜做 init-only repeat。应该用 gen=1 压制随机性。

## 3. 夜间 batch 准备

优先级 per goal：
1. CVRP repeat 已充足（n=8），暂不追加
2. TSP gen=1 repeat=2 用 tocc_corrected cards 压制方差
3. Mixer/Knapsack smoke 暂缓
