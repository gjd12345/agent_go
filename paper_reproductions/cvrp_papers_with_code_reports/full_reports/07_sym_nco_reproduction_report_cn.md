# Sym-NCO: Leveraging Symmetricity for Neural CO 复现报告

## 论文基本信息

- 论文：Sym-NCO: Leveraging Symmetricity for Neural Combinatorial Optimization
- 论文链接：https://arxiv.org/abs/2205.13209
- 官方代码：https://github.com/alstn12088/Sym-NCO
- 任务：TSP、CVRP、PCTSP、OP
- 本地复现状态：`plan-only / local-partial candidate`

## 研究问题

神经组合优化模型经常对等价变换不稳定。例如坐标旋转、反射、起点变化不应改变问题本质，但模型输出可能明显变化。Sym-NCO 研究如何利用问题对称性提升训练和泛化。

## 算法原理

Sym-NCO 是训练正则化框架，而不是单独的 CVRP solver。它对同一实例做对称变换，要求模型在变换前后保持一致或获得一致质量。通过对称增强和正则项，模型学习到更稳定的表示。

对 CVRP，典型对称性包括坐标旋转/反射、客户排列等。在不改变距离结构和需求约束的前提下，解的成本应保持一致。

## 核心实现与代码框架

官方仓库实现 Sym-NCO 训练框架，通常包含：

- 多问题环境：TSP/CVRP/PCTSP/OP。
- 模型训练脚本。
- 对称变换和增强逻辑。
- 评估脚本。

复现重点是先跑 CVRP 小规模训练或评估，而不是直接全表复现。

## 方法级伪代码

```text
for each instance I:
    transformed_instances = symmetry_transforms(I)
    solutions = policy(transformed_instances)
    rewards = evaluate(solutions)
    rl_loss = policy_gradient(rewards)
    symmetry_loss = inconsistency_penalty(solutions/rewards)
    update model with rl_loss + lambda * symmetry_loss
```

## 数据集

Sym-NCO 使用神经 CO 常见随机生成数据。CVRP 复现需要确认：

- problem size。
- demand/capacity 生成规则。
- symmetry augmentation 数量。
- base model 是 AM、POMO 还是其他结构。

## 论文实验结果

论文声称对称性正则能提升多个组合优化任务的神经模型表现。CVRP 具体收益需要按论文表格和仓库配置提取。

## 本地复现结果

本轮未运行官方代码。建议先做最小训练/评估：

```bash
git clone https://github.com/alstn12088/Sym-NCO
cd Sym-NCO
# 按 README 选择 CVRP small config
```

## 图表复现

未重画图。可重画 augmentation 数量 vs cost/gap。

## 差异分析

Sym-NCO 对当前 Go 的直接价值小于 HGS/SGBS/NLNS，但它适合做 agent 策略稳定性测试：同一实例经过坐标变换后，Go 策略不应产生异常差异。

## 复现结论

结论：`local-partial candidate`。适合在 POMO 跑通后作为训练增强，不适合作为第一批工程落地。

## 下一步计划

1. 跑 CVRP small config。
2. 提取对称变换测试。
3. 给 Go evaluator 增加坐标旋转/反射一致性检查。
