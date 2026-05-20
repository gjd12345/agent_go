# Hybrid Learning and Optimization Methods for Solving CVRP 复现报告

## 论文基本信息

- 论文：Hybrid Learning and Optimization methods for solving Capacitated Vehicle Routing Problem
- 作者：Monit Sharma, Hoong Chuin Lau
- arXiv：2509.15262，提交时间 2025-09-18
- 出版信息：SMU InK 页面显示为 2026 年 QC+AI 会议 accepted version，Springer DOI: 10.1007/978-3-032-17625-7_2
- 官方代码：https://github.com/SMU-Quantum/adaptive_quantum_cvrp
- 本地代码路径：`/Users/guojiadong.9/paper_reproductions/adaptive_quantum_cvrp`
- 本地 commit：`fa35bcc863e5daf48bb4fec5295a2dba33d3c3a0`
- 复现状态：`local-partial / warn`

## 研究问题

论文研究 Capacitated Vehicle Routing Problem (CVRP) 中约束优化参数难调的问题。核心问题是：能否把 Augmented Lagrangian Method (ALM) 与 reinforcement learning、quantum VQE 子问题求解结合起来，让 RL 自动选择 ALM penalty 参数，从而提升可行性、解质量和收敛效率。

论文比较四类方法：

- `C-ALM`：classical Augmented Lagrangian Method，使用 classical heuristic 子问题求解器。
- `RL-C-ALM`：使用 Soft Actor-Critic (SAC) 为 classical ALM 选择 penalty 初始化。
- `Q-ALM`：将 ALM 子问题映射为 QUBO，并用 VQE 求解。
- `RL-Q-ALM`：SAC 选择 quantum ALM 的 penalty 参数。

## 算法原理

CVRP 输入为 depot、客户集合、需求、车辆容量和距离矩阵。目标是所有客户恰好访问一次、每条 route 不超过容量，并最小化总路线成本。

论文的 ALM 主循环把 visit constraint 和 capacity violation 转为 Lagrangian multiplier 与 penalty 项。每轮先根据当前 multiplier 构造 route generation 子问题，然后生成当前解、评估可行性、更新最优可行解，再依据约束违反程度更新 multiplier 与 penalty。

RL 部分使用 SAC。状态包括实例特征与约束违反信息；动作是 penalty 参数；奖励鼓励更低成本、更高可行性和更少 ALM 迭代。论文描述的 RL-C-ALM/RL-Q-ALM 关键点是：SAC policy 在每个 CVRP instance 上给出 penalty 初始化，之后 ALM 主过程按确定性方式执行。

Quantum 部分将子问题构造为 QUBO，再映射到 Ising Hamiltonian，用 Qiskit VQE 与浅层 EfficientSU2 ansatz 求近似最优 bitstring，最后 decode 为 route。

## 核心实现与代码框架

官方仓库核心文件：

- `run_experiment.py`：实验入口，读取 YAML config，构建 solver 和 environment。
- `src/adaptive_quantum_cvrp/common/cvrp_instance.py`：解析 `.vrp` CVRP 实例。
- `src/adaptive_quantum_cvrp/common/evaluator.py`：计算路线成本和可行性。
- `src/adaptive_quantum_cvrp/alm/optimizer.py`：ALM 主循环。
- `src/adaptive_quantum_cvrp/alm/classical_solver.py`：classical greedy subproblem solver。
- `src/adaptive_quantum_cvrp/rl/environment.py`：Gymnasium 环境，动作是 penalty `mu`。
- `src/adaptive_quantum_cvrp/rl/agent.py`：SAC actor/critic。
- `src/adaptive_quantum_cvrp/quantum/solver.py`：QUBO/VQE quantum solver wrapper。

仓库检查结果保存于：

- `repro_inspection.json`
- `reproduction_artifacts/local_smoke_results.json`
- `reproduction_artifacts/metric_comparison.json`

## 方法级伪代码

### C-ALM / RL-C-ALM 主流程

```text
Input: CVRP instance I, max iterations T, initial penalty mu
Initialize lambda_j = 0 for every customer j
best_solution = None

for t = 1..T:
    rewards_j = -lambda_j
    routes = SubproblemSolver(I, rewards, mu)
    solution = CVRPSolution(routes)
    cost = route_cost(solution)
    feasible, violations = check_feasibility(solution)

    if feasible and cost improves best:
        best_solution = solution

    for each customer j:
        g_j = visit_count(j, solution) - 1
        lambda_j = lambda_j + (1 / mu) * g_j

return best_solution
```

### SAC penalty tuning

```text
for each training episode:
    sample or reset one CVRP instance
    observe instance features and previous violation features
    action = SAC_policy(state)
    map action to penalty parameter(s)
    run one or more ALM steps with selected penalty
    reward = -solution_cost - infeasibility_penalty - iteration_penalty
    store transition in replay buffer
    update SAC actor, critics, and entropy temperature
```

### RL-Q-ALM

```text
for each CVRP instance:
    SAC predicts penalty parameters
    for each ALM iteration:
        construct QUBO subproblem using travel costs and multiplier-derived rewards
        map QUBO to Ising Hamiltonian
        run VQE with shallow EfficientSU2 ansatz
        decode bitstring to routes
        evaluate solution and update multipliers
return best feasible solution
```

## 数据集

论文报告三类数据：

- light：50 个小实例，客户数约 5-8，用于 quantum/VQE 可承受规模。
- synthetic：35 个中等实例，客户数约 10-40，只评估 classical 方法。
- CVRPLIB benchmark：14 个标准实例，包含 `E-n13-k4`、`A-n32-k5`、`B-n34-k5` 等。

官方仓库包含：

- `data/cvrplib_instances/*.vrp`
- `data/cvrplib_instances_eval/*.vrp`
- `data/cvrplib_instances_train/*.vrp`
- `data/quantum_data/C-n3-k2_inst1.vrp`
- `data/processed/*.sol`

本地数据集根目录：

```text
/Users/guojiadong.9/paper_reproductions/adaptive_quantum_cvrp/data
```

主要子目录含义如下：

| 路径 | 用途 | 示例文件 |
|---|---|---|
| `data/cvrplib_instances/` | 小规模/通用 CVRPLIB 实例 | `mini-n7-k2.vrp`, `E-n13-k4.vrp`, `B-n34-k5.vrp` |
| `data/cvrplib_instances_eval/` | 官方默认 classical/RL eval 配置使用的数据 | `A-n32-k5.vrp`, `E-n13-k4.vrp` |
| `data/cvrplib_instances_train/` | 官方默认 train 数据 | `mini-n7-k2.vrp`, `E-n22-k4.vrp`, `E-n31-k7.vrp` |
| `data/quantum_data/` | quantum/VQE 小实例 | `C-n3-k2_inst1.vrp` |
| `data/raw/` | 更多 CVRPLIB 原始实例 | `A-n33-k5.vrp` 等 |
| `data/processed/` | `.sol` 参考解/最优解文件 | `A-n32-k5.sol` 等 |

查看本地数据文件可运行：

```bash
cd /Users/guojiadong.9/paper_reproductions/adaptive_quantum_cvrp
find data -maxdepth 2 -type f | sort
```

## 论文实验结果

论文表 1 报告 aggregate 结果：

- light：C-ALM 和 RL-C-ALM feasibility 均为 100%，classical runtime 小于 1 秒；Q-ALM 和 RL-Q-ALM feasibility 也为 100%，但 quantum 平均 runtime 为数百秒。
- synthetic：C-ALM feasibility 98%、optimality 70%、runtime 868.5s；RL-C-ALM feasibility 98%、optimality 78%、runtime 775.68s。

论文表 2 报告 CVRPLIB gap/runtime。关键例子：

- `E-n13-k4`：C-ALM gap 0.00%，time 7.48s；RL-C-ALM gap 0.00%，time 6.68s；Q-ALM gap 14.17%；RL-Q-ALM gap 4.04%。
- `A-n32-k5`：C-ALM gap 17.09%，RL-C-ALM gap 16.58%。
- `A-n33-k6`：C-ALM gap 14.42%，RL-C-ALM gap 4.98%。

论文结论称 RL tuning 通常提升 ALM 的解质量和收敛速度，但 quantum 方法受 qubit count、VQE runtime 和 QUBO decoding 限制，当前只适合小规模实例。

## 本地复现结果

### 环境与依赖

- Python：3.9.6
- 未安装：`torch`、`gymnasium`、`qiskit`、`qiskit-optimization`、`qiskit-algorithms`、`qiskit-aer`、`scipy`
- 因为这些依赖下载体积较大，且 quantum/RL full run 计算耗时较高，本次未执行完整依赖安装、SAC 训练或 VQE 训练。

### 训练计算资源估计

论文代码的训练分为 classical RL-C-ALM 和 quantum RL-Q-ALM。训练对象不是 CVRP solver 本体，而是一个 SAC agent；agent 在 ALM 每一步输出 penalty 参数 `mu`，然后由 classical 或 quantum subproblem solver 产生解并返回 reward。

资源需求大致分三档：

| 训练档位 | 典型配置 | CPU/GPU | 内存 | 时间估计 | 用途 |
|---|---|---|---|---|---|
| classical smoke | `num_episodes=5-100`, `max_alm_steps=5-20` | CPU 即可，无需 GPU | 通常 `<2GB` | 几秒到几分钟 | 验证训练 loop、reward、日志和模型保存 |
| 官方 classical | `num_episodes=1000`, `max_alm_steps=50`, `batch_size=256` | CPU 可跑，GPU非必需 | 约 `2-4GB` | 约 30-60 分钟，取决于机器 | 复现官方 classical/RL classical 配置 |
| quantum RL-Q-ALM | `num_episodes=10`, `max_alm_steps=10`, `VQE maxiter=50` | CPU 模拟器可跑但慢；GPU不一定有帮助 | 建议 `4-8GB+` | 小实例数分钟到数十分钟；稍大实例可能数小时 | 只适合极小实例的 quantum smoke |

官方仓库日志提供了两个参考：

- `results/rl_classical_run_1/experiment.log` 显示，`A-n32-k5` 和 `E-n13-k4` 的 1000 episode classical RL 训练曾在 CPU 量级时间内完成。
- `results/rl_quantum_run_1/experiment.log` 显示，`C-n3-k2_inst1` 的 10 episode quantum run 从 17:15:52 到 17:22:40，约 6 分 48 秒。

建议训练顺序：

1. 先跑 classical smoke：5-20 episodes、5-10 ALM steps、1-2 个小实例。
2. 确认 SAC loop 正常后，增加模型保存逻辑，保存 actor/critic。
3. 再跑 100 episodes 的 `mini-n7-k2` / `E-n13-k4`。
4. 最后才考虑官方 1000 episodes。
5. quantum 只建议在 `data/quantum_data/C-n3-k2_inst1.vrp` 上做 1 episode smoke，不建议默认跑完整论文级实验。

### 仓库测试

首次运行：

```bash
python3 -m pytest -q
```

结果：4 error, 3 passed。失败原因是测试构造 `CVRPInstance` 时没有传 `num_vehicles`，但构造器要求该参数。

本地最小兼容补丁：

```python
def __init__(..., demands: np.ndarray, num_vehicles: int = 0, ...)
```

补丁后：

```bash
python3 -m pytest -q
```

结果：`7 passed in 0.10s`。

### Classical ALM smoke test

直接调用 classical core，绕开 `run_experiment.py` 顶层 quantum/RL import：

```bash
python3 -c '... CVRPInstance -> ClassicalSolver -> ALMOptimizer ...'
```

结果保存于 `reproduction_artifacts/local_smoke_results.json`。

| Instance | Iter. | Best Cost | Feasible | Routes |
|---|---:|---:|---|---|
| `mini-n7-k2` | 10 | 160.0 | true | `[[1,6,2],[4,3,5]]` |
| `E-n13-k4` | 10 | 380.0 | true | `[[1,12,2,5],[6,10,11,7],[3,9,8],[4]]` |

额外检查：`E-n13-k4.vrp` 文件注释写明 optimal value 为 247；本地 classical smoke cost=380，对应 gap 约 53.85%，没有复现论文表 2 的 C-ALM/RL-C-ALM 0.00% gap。

仓库自带的 `results/rl_classical_run_1/E-n13-k4/solution.json` 也保存为 cost=380.0，和本地 direct smoke 一致，但与论文表 2 不一致。

使用技能脚本 `paper_repro.py compare` 对论文表 2 的 `E-n13-k4 C-ALM gap (%)` 与本地结果比较，状态为 `fail`：

| Metric | Paper Expected | Local Actual | Tolerance | Status |
|---|---:|---:|---:|---|
| `E-n13-k4 C-ALM gap (%)` | 0.0 | 53.846 | 1.0 | fail |

## 图表复现

本次未重画论文图 1-3。原因：

- 官方代码没有提供直接复现论文图的脚本。
- 当前 safe local run 未复现论文表 2 指标，因此直接重画图会放大不一致结果。

建议后续先修复 metric/code mismatch，再画：

- A-n32-k5 known optimal vs C-ALM/RL-C-ALM route 对比图。
- E-n13-k4 gap/runtime bar chart。
- light/synthetic aggregate feasibility/optimality/runtime table。

## 差异分析

1. **官方代码和论文方法有差异。**
   论文描述 SAC 动作为 `[rho, sigma]` penalty 初始化；当前 `ALMPenaltyEnv` 的 action space 是单维 `mu`。论文 Algorithm 1 也包含 visit 与 capacity 两类 penalty/multiplier，而当前 classical `ALMOptimizer` 主要更新 visit constraint multiplier。

2. **`run_experiment.py` 顶层依赖过重。**
   即使只运行 classical ALM，也会 import `SACAgent`、`ALMPenaltyEnv`、`QuantumSolver`，因此没有安装 torch/gym/qiskit 时无法使用官方入口。

3. **仓库自带测试存在接口漂移。**
   测试没有传 `num_vehicles`，而 `CVRPInstance` 需要该参数。本地补丁只修兼容性，不影响求解逻辑。

4. **本地结果与论文表 2 不一致。**
   `E-n13-k4` 官方实例注释 optimal=247，论文表 2 称 C-ALM/RL-C-ALM gap 0%，但当前代码与仓库保存结果均为 cost=380。该差异需要作者代码版本、随机种子、配置、预处理或结果生成脚本进一步核查。

5. **完整 RL/Quantum 复现成本较高。**
   论文表 2 的 quantum runtime 动辄数千秒；仓库日志显示 `C-n3-k2_inst1` 的 10 episode quantum run 约 6 分 48 秒。因此本次不把 quantum full run 作为安全默认复现。

## 复现结论

结论：`local-partial / warn`。

可以确认：

- 官方仓库可克隆、结构完整、包含数据、模型、配置和结果文件。
- classical core 在不安装 RL/Quantum 大依赖的情况下可运行。
- 本地 smoke test 能输出 feasible CVRP routes。
- 仓库测试在一个小兼容补丁后全部通过。

不能确认：

- 当前官方代码无法在轻量 classical run 中复现论文表 2 的 `E-n13-k4` 0% gap。
- 由于未安装 torch/qiskit 并未跑 full SAC training 或 VQE quantum experiments，不能声称复现了 RL-C-ALM / RL-Q-ALM 的论文指标。

因此，本次复现应作为代码可运行性与部分算法链路验证，而不是论文结果完全复现。

## 下一步计划

1. 新建轻量配置，只跑 `mini-n7-k2` 和 `E-n13-k4`，并把 `run_experiment.py` 的 quantum/RL import 改为 lazy import，使 classical entrypoint 不依赖 qiskit/torch。
2. 解析 `data/processed/*.sol` 中 BKS route，统一 evaluator 的 cost/gap 计算。
3. 复查论文表 2 所用实例文件和本仓库 `data/cvrplib_instances` 是否完全一致。
4. 安装依赖前先确认下载体积；若允许，建 venv 后安装 `torch/gymnasium/qiskit`，运行 1-3 episode 的 RL classical smoke。
5. 若 RL smoke 成功，再尝试 `data/quantum_data/C-n3-k2_inst1.vrp` 的 1 episode quantum smoke，不跑完整 10 episode 或表 2 级别实验。
