# SGBS: Simulation-guided Beam Search 复现报告

## 论文基本信息

- 论文：Simulation-guided Beam Search for Neural Combinatorial Optimization
- 任务：TSP、CVRP、FFSP
- 论文链接：https://arxiv.org/abs/2207.06190
- 官方代码：https://github.com/yd-kwon/SGBS
- 本地复现状态：`plan-only / local-run candidate`

## 研究问题

POMO 等神经构造式模型在贪心解码时容易早期选错，sampling 虽能扩大搜索但计算预算不可控。SGBS 的问题是：能否在固定 beam 宽度下，把神经策略和快速 simulation/rollout 结合，稳定提升解质量。

对 CVRP 来说，搜索树节点是 partial route 状态，动作是下一个访问客户或 depot。SGBS 通过 beam 保留多个 partial solution，避免单一路径贪心。

## 算法原理

SGBS 在每个扩展步骤同时使用两类信号：

- neural policy：给出动作概率，表示模型认为哪些下一个节点更合理。
- simulation score：对候选分支做快速 rollout 或估计，判断后续可能质量。

搜索保留固定宽度的 beam。每次扩展时，从当前 beam 的所有候选后继中选出综合分数较好的若干 partial solution，继续向下搜索直到构造完整解。

## 核心实现与代码框架

官方仓库按问题拆分目录，CVRP 重点在：

- `CVRP/1_pre_trained_model`：预训练模型相关资源。
- `CVRP/2_SGBS/test.py`：SGBS 推理入口。
- mode 参数：`greedy`、`sampling`、`obs`、`sgbs` 等。
- EAS 组合：仓库支持和 Efficient Active Search 类方法结合。

## 方法级伪代码

```text
Input: CVRP instance I, pretrained policy pi, beam width B
beam = {empty_state}

while not complete:
    candidates = []
    for state in beam:
        probs = pi(state)
        for action in top_actions(probs):
            next_state = step(state, action)
            sim = rollout_or_simulate(next_state)
            score = combine(log_prob, sim)
            candidates.append((next_state, score))
    beam = select_top_B(candidates)

return best complete solution in beam
```

## 数据集

SGBS 继承神经 CO 常用随机 Euclidean CVRP 数据，也可测试标准 benchmark。复现时必须记录：

- problem size，例如 CVRP100。
- 是否开启 augmentation。
- beam width / simulation budget。
- episode 数量。
- 是否使用 EAS。

这些参数直接影响 cost 和 runtime。

## 论文实验结果

论文声称 SGBS 在 TSP/CVRP 上显著强于单纯 greedy、sampling 和普通 beam search，尤其在固定搜索预算下能更好利用神经 policy。具体数值要按仓库配置和论文表格复核。

## 本地复现结果

本轮未执行官方代码。建议最小复现：

```bash
git clone https://github.com/yd-kwon/SGBS
cd SGBS/CVRP/2_SGBS
python3 test.py -disable_aug --mode greedy --ep 10
python3 test.py -disable_aug --mode sgbs --ep 10
```

本地报告状态为 `plan-only`，但仓库命令清晰，应优先升级为 `local-run`。

## 图表复现

未重画图。建议先做同一 10 episode 下 greedy vs sgbs 的 cost/runtime 表，再画柱状图。

## 差异分析

SGBS 和当前 Go 项目的相似度高于纯训练方法。Go 里已有 evaluator，缺的是候选搜索预算管理。SGBS 的 beam 可以直接启发 `InsertShips` 候选队列。

## 复现结论

结论：`local-run candidate`。SGBS 是最适合接入 Go evaluator 的神经搜索论文。优先级与 POMO 同级，甚至对工程落地更直接。

## 下一步计划

1. 跑 `greedy` 和 `sgbs` 小样本对比。
2. 记录 beam/search 参数。
3. 把 Go `InsertShips` 改造成 beam-style candidate expansion。
4. 让后续 agent 只调 beam width、simulation budget 和 fallback。
