# Learning to Delegate for Large-scale Vehicle Routing 复现报告

## 论文基本信息

- 论文：Learning to Delegate for Large-scale Vehicle Routing
- 论文链接：https://arxiv.org/abs/2107.04139
- 项目页：https://mit-wu-lab.github.io/learning-to-delegate/
- 官方代码：https://github.com/mit-wu-lab/learning-to-delegate
- 会议：NeurIPS 2021 Spotlight
- 任务：Large-scale CVRP、CVRPTW、VRPMPD
- 本地复现状态：`plan-only / local-partial candidate`

## 研究问题

大规模 VRP 中，直接全局求解代价高。很多神经方法只适合 100 节点以内。Learning to Delegate 的问题是：能否学习选择哪些局部子问题最值得交给强子求解器，从而加速大规模求解。

## 算法原理

该方法维护一个当前解，每轮构造一批候选子问题。模型预测哪个子问题交给 subsolver 后能带来最大改进，然后调用 LKH/HGS 等黑盒强求解器优化该子问题，再把改进合并回全局解。

关键是学习“选子问题”，不是学习完整解。

## 核心实现与代码框架

官方仓库包含：

- `generate_initial.py`：生成问题实例。
- `generate_multiprocess.py`：生成子问题选择轨迹。
- `preprocess*.py`：预处理训练数据。
- `supervised.py`：训练 regression/classification 模型并生成轨迹。
- `run_lkh.py` / `run_hgs.py`：调用子求解器。
- `lkh3/` 与 `hgs/`：外部 solver 依赖。

README 说明完整数据/模型 zip 约 10GB，这对本地完整复现是实际门槛。

## 方法级伪代码

```text
Input: large VRP instance I, initial solution S

for step = 1..T:
    candidate_subproblems = enumerate_local_subproblems(S)
    score = model(candidate_subproblems)
    selected = argmax(score)
    improved_subsolution = subsolver(selected)
    S = merge(S, improved_subsolution)

return S
```

## 数据集

论文覆盖 500、1000、2000、3000 节点的 Uniform CVRP，也包含 CVRPTW 和真实数据。复现必须记录：

- instance size。
- train/val/test split。
- 子求解器 LKH 或 HGS。
- CPU 线程数。
- 子问题大小。
- 是否使用官方 10GB 数据包。

## 论文实验结果

项目页称该方法在 500-3000 节点 VRP 上能加速强求解器，并且 learned selection 相比 random/heuristic selection 有额外 speedup。具体数字需按论文表格与项目日志复核。

## 本地复现结果

本轮未运行。建议先只做小规模生成和单次子求解器调用：

```bash
git clone https://github.com/mit-wu-lab/learning-to-delegate
cd learning-to-delegate
# 编译 LKH-3 或 HGS 后，生成极小 N_INSTANCES 的 CVRP 数据
```

不建议默认下载 10GB 数据包或跑完整训练。

## 图表复现

未重画图。后续应画 runtime-to-quality 曲线和 learned vs random 子问题选择对比。

## 差异分析

这篇对 Go 后续 agent 最关键：我们的动态调度天然是局部变化问题。Agent 不应每次全局重写策略，而应选择“受影响的局部子问题”，交给 SA/HGS/FILO/模板修复。

## 复现结论

结论：`local-partial candidate`。完整复现资源重，但方法路线非常适合我们的 Go agent。

## 下一步计划

1. 先跑 HGS 子求解器。
2. 设计 Go 子问题抽取器。
3. 收集 evaluator 轨迹，训练一个子问题选择模型。
4. 将 ReAct 用于解释和调参，而不是直接生成代码。
