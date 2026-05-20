# EAS: Efficient Active Search 复现报告

## 论文基本信息

- 论文：Efficient Active Search for Combinatorial Optimization Problems
- 论文链接：https://openreview.net/forum?id=nO5caZwFwYu
- 官方代码：https://github.com/ahottung/EAS
- 任务：TSP、CVRP、JSSP
- 本地复现状态：`plan-only / local-partial candidate`

## 研究问题

传统神经求解器训练好后参数固定，对分布外实例表现不稳。Active Search 会在测试实例上继续优化模型，但代价较高。EAS 研究的问题是：能否在推理时只更新少量参数，让模型快速适应单个实例。

## 算法原理

EAS 基于预训练策略，在测试时加入可更新的小参数集合。常见形式包括：

- EAS-Emb：更新 embedding 相关参数。
- EAS-Lay：在模型中加入小层，只更新该层。
- EAS-Tab：使用 tabular 参数调节动作偏好。

每个测试实例上，EAS 反复采样解、计算 cost、用 policy gradient 更新这些小参数。由于不更新完整模型，搜索速度比原始 Active Search 更可控。

## 核心实现与代码框架

官方仓库基于 POMO 风格模型，包含：

- `run_search.py`：active search 入口。
- `instances/`：论文实例。
- `trained_models/`：预训练模型。
- method 参数：选择 EAS-Emb、EAS-Lay、EAS-Tab 或 sampling。

复现关键是明确 `problem`、`method`、`model_path`、`instances_path`、`max_iter`、`batch_size`。

## 方法级伪代码

```text
Input: instance I, pretrained policy pi, adaptation parameters phi
freeze pi base parameters
initialize phi

for iter = 1..T:
    solutions = sample(pi_phi, I)
    costs = evaluate(solutions)
    reward = -costs
    baseline = mean(reward)
    loss = -sum((reward - baseline) * log_prob)
    update only phi

return best solution sampled during adaptation
```

## 数据集

EAS 可用于随机 TSP/CVRP，也包含论文实例和预训练模型。CVRP 复现需确认：

- CVRP100 或 XE benchmark 的实例路径。
- 模型是否与实例规模匹配。
- 是否开启 augmentation。
- max search iteration。

## 论文实验结果

论文报告 EAS 在 TSP、CVRP、JSSP 上优于普通 greedy/sampling，并显著降低传统 Active Search 的推理时训练成本。CVRP 指标需按表格复核，不能仅凭 README 断言具体 gap。

## 本地复现结果

本轮未运行 EAS。建议最小复现：

```bash
git clone https://github.com/ahottung/EAS
cd EAS
python3 run_search.py -problem CVRP -method eas-tab -max_iter 20 -batch_size 16
```

实际需要补充模型路径和实例路径。若无 GPU，应把 batch 和迭代数压低。

## 图表复现

未重画图。后续可以画 `sampling vs EAS-Tab vs EAS-Lay` 的 cost/runtime 曲线。

## 差异分析

EAS 的训练对象不是通用 solver，而是单实例推理时参数。它对我们 Go 更有参考价值：可以把 `InsertShips` 的若干权重作为可更新参数，不让 LLM 重写代码。

## 复现结论

结论：`local-partial candidate`。方法价值高，但完整实验依赖预训练模型和 GPU。短期应只跑 EAS-Tab 小迭代 smoke。

## 下一步计划

1. 确认 CVRP checkpoint 与实例路径。
2. 跑 20 iter 小样本。
3. 抽象出 Go 参数向量：距离权重、容量权重、等待权重、风险权重。
4. 用 evaluator 做 EAS-style online tuning。
