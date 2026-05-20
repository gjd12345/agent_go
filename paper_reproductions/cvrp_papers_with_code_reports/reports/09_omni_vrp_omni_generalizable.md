# Omni-VRP：Towards Omni-generalizable Neural Methods for VRP

状态：`plan-only`  
代码：https://github.com/RoyalSkye/Omni-VRP  
论文：https://arxiv.org/abs/2305.19587  
任务：TSP / CVRP / 多 VRP 变体

## 论文基本信息

Omni-VRP 目标是训练更泛化的神经 VRP 方法。arXiv 摘要说明其实验覆盖 TSP 和 CVRP，并给出代码仓库。它关心跨问题、跨规模或跨分布泛化，比单一 CVRP 复现更复杂。

## 方法要点

- 多任务/多分布训练。
- 追求 VRP 家族上的泛化，而不是只在一个固定规模上拟合。
- 对真实业务多约束场景更有理论吸引力。

## 代码与数据可用性

代码仓库公开，但完整复现需要确认：

- 是否提供预训练模型。
- 是否提供 CVRP 单任务测试入口。
- 多任务配置是否容易缩小。
- 依赖版本和数据生成方式。

## 最小复现路线

```bash
git clone https://github.com/RoyalSkye/Omni-VRP
cd Omni-VRP
# 先寻找 CVRP-only eval 或 small training config
```

建议先做代码结构审计，不直接完整训练。

## 对 Go 项目的价值

Omni-VRP 对当前 Go 最有价值的地方是“统一表示”：

1. 我们的动态 dispatch 比标准 CVRP 更复杂。
2. 如果以后要覆盖 CVRP、CVRPTW、动态到达、容量、触发机制，需要统一 state/action schema。
3. Omni-VRP 可作为 schema 设计参考。

## 风险

- 复现成本高，不适合作为第一批。
- 论文收益可能体现在泛化实验，而不是单个 CVRP benchmark。
- 迁移到 Go 需要大量表示层改造。

## 结论

先作为架构参考，不作为近期主复现对象。等 POMO/SGBS/HGS 跑通后，再判断是否值得投入训练资源。
