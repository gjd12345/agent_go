# COMPASS: Policy Adaptation with Latent Space Search 复现报告

## 论文基本信息

- 论文/项目：COMPASS: Combinatorial Optimization with Policy Adaptation using Latent Space Search
- 论文链接：https://arxiv.org/abs/2310.01510
- 官方代码：https://github.com/instadeepai/compass
- 任务：TSP、CVRP、JSSP
- 本地复现状态：`plan-only / local-partial candidate`

## 研究问题

固定神经策略对不同实例分布适应性弱。COMPASS 的问题是：能否学习一个由 latent condition 控制的策略族，并在推理时搜索 latent，使策略适配当前实例。

## 算法原理

COMPASS 不只输出一个 policy，而是学习 conditioned policy。latent 向量控制策略行为；推理时不改完整模型，而是在 latent space 中搜索，让同一模型表现出不同启发式偏好。

这相当于把“训练一个 solver”改为“训练一个可调 solver family”。

## 核心实现与代码框架

官方仓库说明实现基于 JAX，包含 TSP、CVRP、JSSP。典型入口：

- `experiments/train.py`
- `config_exp_cvrp.yaml`
- `validate.py`
- latent search / slow RL validate 相关脚本

## 方法级伪代码

```text
Train:
    sample instance I and latent z
    solution = policy(I, z)
    reward = -cost(solution)
    update conditioned policy

Inference:
    initialize latent candidates
    for search step:
        evaluate policy(I, z)
        update/search z
    return best solution found
```

## 数据集

COMPASS 使用随机生成或 benchmark 的 TSP/CVRP/JSSP 配置。CVRP 复现需记录：

- config 文件。
- JAX/Jaxlib 版本。
- 是否使用 GPU。
- latent search budget。
- validation instance distribution。

## 论文实验结果

论文报告 COMPASS 在多个组合优化任务上通过 latent adaptation 提升泛化。CVRP 指标依赖搜索预算和配置。

## 本地复现结果

本轮未运行。建议最小复现：

```bash
git clone https://github.com/instadeepai/compass
cd compass
pip install -e .
python experiments/train.py --config-name config_exp_cvrp.yaml
```

需要先确认 JAX 环境，CPU-only 可能可跑 smoke，但速度有限。

## 图表复现

未重画图。后续可画 latent search step vs cost。

## 差异分析

COMPASS 对 Go 的价值是策略族设计。当前 `strategy_templates.py` 已经有多个 bounded family，可以看成手写 latent strategy space。下一步可训练一个小模型或 bandit 来选 family/knobs。

## 复现结论

结论：`local-partial candidate`。训练栈较重，短期以思想迁移为主。

## 下一步计划

1. 确认 JAX 环境。
2. 跑 CVRP config 的 1-2 step smoke。
3. 把 Go template family 映射成离散 latent。
4. 训练选择器而不是训练完整 neural solver。
