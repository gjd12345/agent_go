# HGS-CVRP: Hybrid Genetic Search for the CVRP 复现报告

## 论文基本信息

- 论文：Hybrid Genetic Search for the CVRP: Open-Source Implementation and SWAP* Neighborhood
- 论文链接：https://arxiv.org/abs/2012.10384
- 官方代码：https://github.com/vidalt/HGS-CVRP
- 任务：canonical CVRP
- 本地复现状态：`plan-only / local-run candidate`

## 研究问题

HGS-CVRP 不是神经方法，而是强经典启发式。论文目标是给 canonical CVRP 提供现代、开源、可复现实装，并包含 SWAP* 邻域。它回答的问题是：如何在工程上实现一个高质量、可公开对比的 CVRP 强基线。

## 算法原理

HGS 使用遗传搜索和局部搜索结合：

- 个体表示为 giant tour。
- Split 算法把 giant tour 切成多条可行路线。
- 交叉与变异产生新个体。
- 局部搜索改进路线。
- Diversity control 防止种群过早收敛。
- SWAP* 邻域在不同 route 间交换客户，提升改进能力。

## 核心实现与代码框架

官方 C++ 仓库包含：

- `Program/`：solver 主体。
- `Instances/`：示例实例。
- `make` 或 CMake 构建。
- CLI 参数：instance path、solution path、iteration、time limit、seed、vehicle count。

典型运行形式：

```bash
./hgs instancePath solPath -t 10 -seed 1
```

## 方法级伪代码

```text
Initialize population of giant tours

while time budget not exhausted:
    parent1, parent2 = select(population)
    child = crossover(parent1, parent2)
    routes = split(child)
    routes = local_search(routes, including SWAP*)
    insert child into population
    adjust penalties and diversity

return best feasible solution
```

## 数据集

HGS-CVRP 面向 CVRPLIB 等标准 `.vrp` 实例。复现时应记录：

- instance name。
- best known solution。
- time limit。
- seed。
- vehicle number 是否固定。
- distance rounding 规则。

## 论文实验结果

论文将 HGS-CVRP 作为强开源 CVRP solver 展示，重点不是训练收益，而是高质量解、可复现实现和 SWAP* 邻域效果。具体数值需要按论文表格和运行预算比较。

## 本地复现结果

本轮未运行 HGS-CVRP。建议最小复现：

```bash
git clone https://github.com/vidalt/HGS-CVRP
cd HGS-CVRP
make
./hgs Instances/CVRP/X-n101-k25.vrp out.sol -t 10 -seed 1
```

若仓库示例路径不同，以 README 为准。

## 图表复现

未重画图。后续可画 SA、HGS、Go Smart Operator 在同一转换实例上的 cost/runtime 对比。

## 差异分析

HGS 是静态 CVRP；我们的 Go 是动态调度。但 HGS 可作为 teacher、上界基线和局部搜索 move 来源。它比神经方法更适合先做工程基准。

## 复现结论

结论：`local-run candidate`。HGS-CVRP 是必须复现的强基线。它决定我们后续 agent 是否真的有优化价值。

## 下一步计划

1. 本地构建 HGS。
2. 跑 CVRPLIB 小实例。
3. 写 Go 动态实例到 CVRPLIB adapter。
4. 用 HGS 解作为 teacher 或 benchmark。
