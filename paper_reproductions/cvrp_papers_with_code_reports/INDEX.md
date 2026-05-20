# CVRP Papers with Code 可复现性筛选报告

生成日期：2026-05-20

本目录收集了一批带公开代码的 CVRP/VRP 论文与项目，目标是服务两件事：

1. 判断哪些论文值得继续做完整复现。
2. 判断哪些方法可以迁移到当前 `agent_ad` / Go 动态调度代码中。

这里的报告是“复现前筛选报告”，不是完整训练复现结论。状态含义：

- `local-run`：仓库给出清晰命令、数据/模型可用，优先尝试本地小规模跑通。
- `local-partial`：代码可用，但依赖、模型、数据或算力有明显门槛，适合先跑最小 smoke test。
- `plan-only`：论文/代码有价值，但完整复现成本较高，先做方法迁移设计。

## 候选优先级

| Rank | 报告 | 方法家族 | 代码 | 复现状态 | 对 Go 项目价值 |
|---:|---|---|---|---|---|
| 1 | [POMO](reports/01_pomo_policy_optimization_multiple_optima.md) | 神经构造式 RL | https://github.com/yd-kwon/POMO | local-run | 多起点/多候选生成，可改造成 InsertShips 候选排序器 |
| 2 | [SGBS](reports/02_sgbs_simulation_guided_beam_search.md) | 神经策略 + 搜索 | https://github.com/yd-kwon/SGBS | local-run | beam/search budget 思路最适合接入当前 evaluator |
| 3 | [EAS](reports/03_eas_efficient_active_search.md) | 推理时实例自适应 | https://github.com/ahottung/EAS | local-partial | 可借鉴“单实例在线调参”，不一定训练大模型 |
| 4 | [NLNS](reports/04_nlns_neural_large_neighborhood_search.md) | 神经 LNS | https://github.com/ahottung/NLNS | local-partial | destroy/repair 框架可替代盲目改 InsertShips |
| 5 | [HGS-CVRP](reports/05_hgs_cvrp_hybrid_genetic_search.md) | 经典 HGS + SWAP* | https://github.com/vidalt/HGS-CVRP | local-run | 最强工程基线之一，适合做 Go 结果上界/teacher |
| 6 | [FILO](reports/06_filo_fast_iterated_local_search.md) | 大规模局部搜索 | https://github.com/acco93/filo | local-run | 可提供高质量局部搜索 move 设计 |
| 7 | [Sym-NCO](reports/07_sym_nco_symmetricity_regularization.md) | 对称性正则 RL | https://github.com/alstn12088/Sym-NCO | local-partial | 训练思想有价值，短期不如 POMO/SGBS 直接 |
| 8 | [COMPASS](reports/08_compass_policy_adaptation_latent_search.md) | 潜空间策略自适应 | https://github.com/instadeepai/compass | local-partial | 对“策略族选择器”有启发，依赖栈较重 |
| 9 | [Omni-VRP](reports/09_omni_vrp_omni_generalizable.md) | 多 VRP 泛化模型 | https://github.com/RoyalSkye/Omni-VRP | plan-only | 适合长期做多约束/多任务统一表示 |
| 10 | [Learning to Delegate](reports/10_learning_to_delegate_large_scale_vrp.md) | 学习式大规模分解 | https://github.com/mit-wu-lab/learning-to-delegate | local-partial | 对大规模实例分解、局部重优化很有价值 |

## 建议复现顺序

第一批先跑 `POMO -> SGBS -> HGS-CVRP`。这三类覆盖“神经构造式、多候选搜索、经典强基线”，对我们当前 Go 管线最有直接帮助。

第二批跑 `EAS -> NLNS -> FILO`。这批更接近“在当前解附近改进”，适合下一步把 ReAct/Smart Operator 从“改代码”转成“选策略 + 调参数 + 局部修复”。

第三批作为方法储备：`Sym-NCO -> COMPASS -> Omni-VRP -> Learning to Delegate`。它们适合做更长线的训练或统一策略表示。

## 和当前 Go 项目的结合方向

短期不要再让 LLM 随机重写 `InsertShips`。更稳的路线是：

1. 保留 SA/当前 InsertShips 作为可靠 baseline。
2. 加一个候选策略层：POMO/SGBS/HGS/FILO 的思想都输出候选路线或候选插入顺序。
3. 用 Go evaluator 做真实打分，把 ReAct 用在“选择策略、调 search budget、分析失败原因”，而不是直接生成整段 Go。
4. 把失败记忆从 compile/runtime 扩展到算法行为：超时、负成本、过度保守、过度复杂、容量边界错误、只改善局部不改善全局。

## 主要来源

- Papers with Code: https://paperswithcode.com/
- POMO: https://github.com/yd-kwon/POMO
- SGBS: https://github.com/yd-kwon/SGBS
- EAS: https://github.com/ahottung/EAS
- NLNS: https://github.com/ahottung/NLNS
- HGS-CVRP: https://github.com/vidalt/HGS-CVRP
- FILO: https://acco93.github.io/filo/
- Sym-NCO: https://paperswithcode.com/paper/sym-nco-leveraging-symmetricity-for-neural
- COMPASS: https://github.com/instadeepai/compass
- Omni-VRP: https://arxiv.org/abs/2305.19587
- Learning to Delegate: https://github.com/mit-wu-lab/learning-to-delegate
