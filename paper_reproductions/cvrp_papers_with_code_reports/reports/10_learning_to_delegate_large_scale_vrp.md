# Learning to Delegate for Large-scale Vehicle Routing

状态：`local-partial`  
代码：https://github.com/mit-wu-lab/learning-to-delegate  
论文：https://arxiv.org/abs/2107.04139  
任务：Large-scale CVRP / CVRPTW / VRPMPD

## 论文基本信息

Learning to Delegate 是 NeurIPS 2021 Spotlight，目标是大规模 VRP 的学习增强局部搜索。官方仓库说明包含代码、数据、模型，可生成 CVRP、CVRPTW、VRPMPD 实例，并结合 LKH-3/HGS 等子求解器运行基线、训练和评估子问题模型。

## 方法要点

- 大规模问题不一次性全局求解。
- 学习选择值得重优化的子问题。
- 把子问题交给强子求解器。
- 迭代式框架持续改善整体解。

## 代码与数据可用性

仓库公开代码、数据和模型，但依赖外部求解器和数据生成流程。完整复现比 POMO/SGBS 更工程化，适合在 HGS 跑通后继续。

## 最小复现路线

```bash
git clone https://github.com/mit-wu-lab/learning-to-delegate
cd learning-to-delegate
# 先按 README 配置小规模 CVRP 数据与 HGS/LKH 子求解器
```

建议先跑作者提供的小样例或 plotting/analysis，再跑完整训练。

## 对 Go 项目的价值

这个方法对我们的动态调度非常有价值，因为当前 Go 问题天然适合“局部重优化”：

1. 每次触发不必重排全部车辆。
2. 学习选择受影响最大的 ship/customer 子集。
3. 子问题用 SA/HGS/FILO/模板策略求解。
4. ReAct 负责解释为什么选择这些子问题，并调节子问题大小。

## 风险

- 依赖链更重，可能要配置 HGS/LKH。
- 完整训练面向大规模，资源和时间都高。
- 与当前 Go 数据结构对接需要额外 adapter。

## 结论

非常适合做中期迁移路线。短期先复现 HGS，再参考 Learning to Delegate 设计 Go 的“受影响区域选择器”。
