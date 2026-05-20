# POMO：Policy Optimization with Multiple Optima for RL

状态：`local-run`  
代码：https://github.com/yd-kwon/POMO  
论文：https://arxiv.org/abs/2010.16011  
任务：TSP / CVRP / Knapsack

## 论文基本信息

POMO 是神经组合优化里最适合作为 CVRP 入门复现的项目之一。官方仓库说明它包含 NeurIPS 2020 论文代码，并同时保留原始 notebook 版本和 2021 年整理后的 Python 版本。论文核心是利用同一个问题的多个等价最优起点，让策略一次产生多个轨迹，降低单一路径采样带来的不稳定。

## 方法要点

- 构造式策略：逐步选择下一个客户节点，直到形成完整路线。
- 多起点 rollout：同一个实例从多个初始选择出发，得到一组候选解。
- 强化学习训练：用 route cost 作为 reward，不依赖最优标签。
- CVRP 约束：通过剩余容量、depot 回退等状态变量控制可行动作。

## 代码与数据可用性

仓库包含 `NEW_py_ver` 和 `OLD_ipynb_ver`。GitHub 页面标明 `NEW_py_ver` 是更适合服务器运行的 Python 结构化版本，`OLD_ipynb_ver` 是论文原始交互代码。

可复现性判断：高。理由是仓库结构清楚、论文任务与 CVRP 直接相关、POMO 后续大量方法复用了它的模型和数据格式。

## 最小复现路线

建议先不训练，先跑小规模推理或 1-2 epoch 训练 smoke test：

```bash
git clone https://github.com/yd-kwon/POMO
cd POMO/NEW_py_ver/CVRP
python3 train.py
python3 test.py
```

实际命令需要根据仓库 README 与本机 PyTorch/CUDA 版本微调。若本机无 GPU，先把 batch、epoch、problem size 降到很小，只验证数据生成、模型 forward、cost 计算和可行性检查。

## 对 Go 项目的价值

POMO 最值得迁移的是“多候选生成”而不是整套训练。当前 Go 里 LLM 改 `InsertShips` 容易保守或超时，可以改成：

1. InsertShips 保持 baseline 可行逻辑。
2. 在每次派车时生成多个候选插入顺序。
3. 用 POMO 式多起点思想做候选多样性。
4. 用现有 evaluator 选择最优，而不是信任单个启发式。

## 风险

- 完整训练需要 GPU；CPU 只适合 smoke test。
- POMO 主要面向静态 CVRP，直接迁移到动态调度需要重新定义状态。
- 神经模型输出的是路线构造策略，不是 Go 插入函数代码。

## 结论

优先级最高。POMO 是 CVRP 神经构造式方法的基础复现对象，也最适合给我们的 Smart Operator 提供“候选集生成”范式。
