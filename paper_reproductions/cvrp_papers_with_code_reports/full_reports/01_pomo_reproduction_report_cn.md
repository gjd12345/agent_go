# POMO: Policy Optimization with Multiple Optima 复现报告

## 论文基本信息

- 论文：POMO: Policy Optimization with Multiple Optima for Reinforcement Learning
- 任务：TSP、CVRP、0-1 Knapsack
- 论文链接：https://arxiv.org/abs/2010.16011
- 官方代码：https://github.com/yd-kwon/POMO
- Papers with Code/论文页面：NeurIPS 2020 论文与官方代码互相引用
- 本地复现状态：`plan-only / local-run candidate`

## 研究问题

POMO 解决的是神经组合优化中 policy gradient 训练不稳定、同一实例只采样单一路径导致方差较大的问题。对 CVRP 来说，模型需要逐步选择下一个客户或 depot，满足车辆容量约束并最小化总路线长度。

论文关键假设是：很多组合优化问题存在多个等价最优解。例如 TSP 可以从任意城市作为起点，CVRP 中也可以用多个 rollout 起点得到不同但等价或近似等价的构造轨迹。POMO 利用这些多重最优结构训练策略，使模型一次对同一实例产生多个候选解。

## 算法原理

POMO 是构造式神经求解器。模型从当前 partial solution、客户坐标、需求、车辆剩余容量等状态出发，逐步输出下一个访问节点。与普通 REINFORCE 不同，POMO 对每个训练实例并行启动多个 rollout，每个 rollout 对应一个不同的起点或初始动作。

训练时，多个 rollout 的 reward 形成组内 baseline。某个 rollout 的优势值不是相对全局 moving average，而是相对同一实例其他 rollout 的平均表现。这能降低梯度方差，并鼓励模型保留多个优质候选路径。

## 核心实现与代码框架

官方仓库包含新版 Python 代码和旧版 notebook。CVRP 部分通常位于 `NEW_py_ver/CVRP`。核心模块可按如下理解：

- `CVRPEnv`：生成 CVRP 实例、维护 depot/customer、需求、容量、visited mask。
- `CVRPModel`：attention-based policy，输出下一个节点概率。
- `train.py`：POMO policy gradient 训练入口。
- `test.py`：加载 checkpoint 或模型配置做推理评估。
- `utils` / tester / trainer：记录日志、批量评估、augmentation。

## 方法级伪代码

```text
Input: batch of CVRP instances, POMO size K
Initialize K parallel rollouts per instance

while not all routes complete:
    state = env.get_state()
    prob = policy(state)
    action = sample_or_greedy(prob, feasible_mask)
    env.step(action)

cost[k] = route_length(rollout_k)
reward[k] = -cost[k]
baseline = mean(reward[1..K])
loss = -sum_k((reward[k] - baseline) * log_prob[k])
update policy parameters
```

## 数据集

POMO 通常使用随机生成的 Euclidean CVRP 实例，节点坐标在单位正方形内采样，客户需求离散采样，车辆容量随 problem size 设定。复现时应区分：

- 随机生成测试集：用于论文式神经 CO 对比。
- CVRPLIB 标准实例：更接近传统 OR benchmark，但不一定是 POMO 原始主要评估集。
- 我们 Go 项目的 Solomon/d25/d50/d75 动态实例：不是静态 CVRP，需要额外 adapter。

## 论文实验结果

论文声称 POMO 在 TSP、CVRP、KP 上优于或接近当时神经基线，核心收益来自多起点 rollout 与组内 baseline。CVRP 结果通常要看 problem size、是否使用 sampling/augmentation、解码预算和 checkpoint。

## 本地复现结果

本轮未克隆并执行 POMO。原因是当前任务要求先输出十篇报告；未进行依赖安装、checkpoint 下载或训练。复现状态标为 `plan-only / local-run candidate`。

建议最小命令：

```bash
git clone https://github.com/yd-kwon/POMO
cd POMO/NEW_py_ver/CVRP
python3 test.py
```

若默认命令依赖 GPU 或 checkpoint，先把 batch、episode、problem size 降到最小，只验证 env、model forward、cost 计算和 feasibility mask。

## 图表复现

未重画图。后续应优先复现 CVRP test cost/gap 表格，再画 baseline vs POMO 的 cost/runtime 对比。

## 差异分析

POMO 是静态 CVRP 构造器；当前 Go 代码是动态调度/插入式 `InsertShips`。直接把模型接进 Go 不现实，但“多候选起点 + 组内比较”的训练思想可以迁移。

## 复现结论

结论：`local-run candidate`。这是十篇里最适合作为神经 CVRP 起点的论文。优先级高，但完整训练需要 PyTorch 环境和 GPU；CPU 上只建议 smoke test。

## 下一步计划

1. 克隆官方仓库并记录 commit。
2. 跑 CVRP 最小 test。
3. 若有 checkpoint，先做 inference；没有 checkpoint 再跑 1 epoch smoke。
4. 把 POMO 多 rollout 思路转为 Go 中的多候选插入排序器。
