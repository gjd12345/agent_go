# SGBS：Simulation-guided Beam Search for Neural CO

状态：`local-run`  
代码：https://github.com/yd-kwon/SGBS  
论文：https://arxiv.org/abs/2207.06190  
任务：TSP / CVRP / FFSP

## 论文基本信息

SGBS 是 NeurIPS 2022 的神经组合优化搜索增强方法。官方仓库说明其包含 TSP、CVRP、FFSP，并给出 CVRP 目录下的直接测试命令。它不是重新训练一个完全新模型，而是在已有神经策略上加 beam search、simulation/rollout 指引和 EAS 组合。

## 方法要点

- 神经策略给出候选动作概率。
- Beam search 保留多个前缀解，避免贪心早期选错。
- Simulation 指引对候选分支做快速估计。
- 可选择 greedy、sampling、original beam search、MCTS、SGBS 等推理模式。

## 代码与数据可用性

GitHub README 明确给出 CVRP 推理命令：

```bash
cd ./CVRP/2_SGBS
python3 test.py
python3 test.py -disable_aug --mode greedy --ep 10
python3 test.py -disable_aug --mode sgbs --ep 10
```

仓库标注语言版本为 Python 3.8.6、torch 1.11.0。可复现性较高，尤其适合先跑少量 episode。

## 最小复现路线

```bash
git clone https://github.com/yd-kwon/SGBS
cd SGBS/CVRP/2_SGBS
python3 test.py -disable_aug --mode greedy --ep 10
python3 test.py -disable_aug --mode sgbs --ep 10
```

建议先比较 greedy 与 sgbs 在同一小样本上的 cost 与耗时，再决定是否扩大 episode 或启用 augmentation。

## 对 Go 项目的价值

SGBS 比 POMO 更接近我们当前需求。Go 管线已经有真实 evaluator，缺的是在固定预算内探索多个候选策略。可以迁移成：

1. `InsertShips` 不直接返回唯一方案，而是暴露候选插入动作。
2. Beam 宽度作为参数，例如 2、4、8。
3. 每个候选用轻量模拟估分，再把少数高分候选交给真实 evaluator。
4. ReAct 负责动态调 `beam_width`、`rollout_budget`、`timeout`。

## 风险

- 如果直接接神经模型，需要解决静态 CVRP 到动态调度的状态映射。
- SGBS 搜索预算变大后容易耗时，需要强 timeout。
- MCTS 模式官方也提醒更慢，不适合先接入。

## 结论

这是最值得立刻复现的小项目之一。它给我们一个清晰方向：把 ReAct 从“写 Go 代码”改为“在候选搜索空间里调度预算”。
