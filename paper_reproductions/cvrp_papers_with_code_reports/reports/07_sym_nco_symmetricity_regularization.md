# Sym-NCO：Leveraging Symmetricity for Neural CO

状态：`local-partial`  
Papers with Code：https://paperswithcode.com/paper/sym-nco-leveraging-symmetricity-for-neural  
代码：https://github.com/alstn12088/Sym-NCO  
论文：https://arxiv.org/abs/2205.13209  
任务：TSP / CVRP / PCTSP / OP

## 论文基本信息

Sym-NCO 是一个通用训练 scheme，利用组合优化问题中的旋转、反射等对称性提升神经求解器泛化。Papers with Code 页面明确写到其实验覆盖 TSP、CVRP、PCTSP、OP，并给出官方代码仓库。

## 方法要点

- 不只是一个 CVRP solver，而是训练正则化方法。
- 通过对称变换增强状态/解的一致性。
- 目标是提升 DRL-NCO 在不同问题上的泛化。
- 可以叠加在已有神经构造式方法上。

## 代码与数据可用性

官方 GitHub 存在，但相比 POMO/SGBS，复现链路更偏训练侧。若只想验证 CVRP 指标，需要确认仓库里的 CVRP 配置、预训练权重和测试脚本。

可复现性：中等。适合在 POMO 跑通后继续。

## 最小复现路线

```bash
git clone https://github.com/alstn12088/Sym-NCO
cd Sym-NCO
# 先阅读 README 中 CVRP 配置，再运行最小测试或训练
```

建议先不做完整训练，只检查是否能生成 CVRP 实例、模型 forward 和 cost。

## 对 Go 项目的价值

Sym-NCO 对 Go 的直接帮助小于 POMO/SGBS，但训练思想有价值：

1. 对称数据增强：同一实例做旋转/镜像，策略输出应等价。
2. 策略评估时加入增强平均，降低偶然性。
3. 对 LLM 生成策略也可以做“坐标变换一致性”测试。

## 风险

- 需要训练才能体现论文主贡献。
- 对当前动态调度的迁移不是直接可用。
- 环境和配置可能比 POMO 更复杂。

## 结论

作为第二梯队复现。先跑 POMO/SGBS，再用 Sym-NCO 验证对称增强是否能提升泛化。
