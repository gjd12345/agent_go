# Go 求解器与 ReAct Agent 后续指导意见

## 结论先行

当前不建议继续让 LLM 大段重写 `InsertShips`。这条路线已经暴露两个问题：

- 可靠性问题：生成代码容易编译失败、超时、负成本或破坏可行性。
- 优化问题：即使编译通过，LLM 往往只做保守改动，效果持平 SA；大胆改动又容易变慢或失效。

后续正确路线是：

1. 保留 SA / 当前 `InsertShips` 作为稳定 baseline。
2. 把 ReAct agent 的动作空间限制在“选策略、调参数、选局部子问题、调搜索预算”。
3. 用 Go evaluator 做唯一裁判。
4. 训练目标先从“训练完整 neural solver”降级为“训练策略选择器/局部重优化选择器”。
5. HGS、SGBS、NLNS、Learning to Delegate 是最值得迁移的四类思想。

## 当前 Go 代码状态判断

当前 Go/EOH 管线已经有几个有价值的基础模块：

- `main.go` / SA baseline：稳定、可运行，是所有新方法的参照。
- `eoh_go/operator/agent_controller.py`：负责 candidate 生成、编译、自修复、评估、guard、报告。
- `eoh_go/operator/failure_memory.py`：记录 timeout、negative cost、compile failure 等失败模式。
- `eoh_go/operator/self_repair.py`：编译失败时尝试修复。
- `eoh_go/operator/directed_mutate.py`：LLM 变异入口。
- `eoh_go/operator/strategy_templates.py`：当前最重要的方向，已经把策略限制为 bounded templates。
- `eoh_go/experiments/smart_operator_grid.py`：可以跑 problem × density × arrival_scale grid。

这说明工程方向应该从“生成代码”转向“受控策略搜索”。

## 是否继续改 SA

短期不要直接重写 SA 主体。SA 的价值是稳定 baseline、fallback 和 teacher。应该做三件事：

1. **冻结 SA 行为**  
   保留原始 SA 作为 `sa_exact`，每次实验都记录 SA cost、runtime、可行性。

2. **外包增量改进**  
   新方法不要替代 SA，而是在 SA 前后加层：
   - 前处理：候选任务排序、车辆排序、局部子问题抽取。
   - 后处理：局部搜索、destroy/repair、route swap。
   - 并行候选：多个策略生成多个 dispatch，再用 evaluator 选最优。

3. **把 SA 变成 teacher**  
   训练数据可以记录：在哪类实例上 SA 选择了什么插入、什么局部 move 有效、什么 move 导致超时。

结论：SA 不应被替换，应被包装、对照和蒸馏。

## 是否继续改 InsertShips

可以改，但必须从“自由文本改代码”改成“受控策略族”。

建议将 `InsertShips` 拆成三层：

```text
InsertShips(dispatch, oris, dess, total_ship)
    -> build_candidate_actions(...)
    -> score_actions(strategy_spec, action_features)
    -> apply_best_or_fallback(...)
```

### 第一层：候选动作生成

候选动作只做有限集合：

- 把新 ship 插入已有 assign。
- 新建 assign。
- 在已有 route 中交换局部顺序。
- 移除 k 个任务后重新插入。

### 第二层：动作打分

打分函数先手写，不训练大模型：

```text
score =
  w_delta_cost * estimated_delta_cost
  + w_capacity * capacity_risk
  + w_route_len * route_length
  + w_wait * dynamic_wait_risk
  + w_failure * historical_failure_penalty
```

ReAct 或训练器只允许调 `w_*`、`top_k`、`beam_width`、`destroy_k`、`timeout_budget`。

### 第三层：fallback

任何策略失败都必须 fallback 到 `sa_exact` 或 `robust_first_feasible`。不能让 agent 产生无解状态。

## ReAct 应该怎么接

ReAct 不应该直接写 Go。它应该做 bounded decision。

推荐 ReAct loop：

```text
Observe:
    读取当前 cell 的 problem、density、arrival_scale、SA baseline、失败记忆、上一代结果

Think:
    判断主要瓶颈：timeout / negative_cost / no_improvement / over_conservative / high_runtime

Act:
    输出 JSON 策略动作：
    {
      "family": "beam_insert | lns_repair | sa_exact | hgs_teacher | fast_nearest",
      "top_k": 2,
      "beam_width": 4,
      "destroy_k": 3,
      "pickup_weight": 0.03,
      "runtime_budget_s": 30,
      "fallback": "sa_exact"
    }

Evaluate:
    Go evaluator 编译、运行、guard、记录 cost/runtime

Learn:
    更新 failure_memory 和 strategy_memory
```

关键约束：

- Agent 输出 JSON，不输出 Go 代码。
- JSON 必须经过 schema clamp。
- 每个 action 必须有 fallback。
- evaluator 是唯一真值来源。
- ReAct 的 reasoning 可以写进日志，但不能直接进入可执行代码。

## 从十篇论文迁移什么

### POMO

迁移多起点、多候选思想。不要先训练 POMO 模型。先在 Go 中实现多个候选插入起点和候选车辆顺序。

### SGBS

迁移 beam search。最适合当前 Go。

```text
beam_width = 2/4/8
每层扩展若干插入动作
用轻量估分筛选
最后用真实 evaluator 比较
```

### EAS

迁移推理时调参。把 `pickup_weight`、`capacity_weight`、`top_k` 当成可在线更新参数。

### NLNS

迁移 destroy/repair。不要全局重排；每次只移除受影响的一小部分任务，然后 repair。

### HGS-CVRP

作为强 baseline 和 teacher。优先跑 HGS，不一定嵌入 Go。

### FILO

迁移局部搜索 move 和增量 cost cache。

### Sym-NCO

迁移一致性测试。坐标旋转、反射后，策略不应异常退化。

### COMPASS

迁移策略族/latent search。当前 `strategy_templates.py` 就是手写策略族雏形。

### Omni-VRP

迁移泛化评估思想。不能只在一个 cell 上调。

### Learning to Delegate

迁移子问题选择。对动态调度最关键：每次触发只选择局部子问题交给 solver。

## 训练路线

### 阶段 0：日志与数据

先不要训练。补齐日志。

每个 candidate 记录：

```json
{
  "problem": "rc101.json",
  "density": "d25",
  "arrival_scale": 1.0,
  "strategy_family": "balanced_delta",
  "knobs": {"top_k": 3, "pickup_weight": 0.03},
  "sa_cost": 664.12,
  "candidate_cost": 650.31,
  "runtime_s": 12.4,
  "compiled": true,
  "feasible": true,
  "guard_excluded": false,
  "failure_reason": "",
  "improvement_pct": -2.08
}
```

没有这批数据，训练会变成猜。

### 阶段 1：Bandit / 规则学习

先训练最小选择器：

- 输入：density、arrival_scale、problem stats、failure_memory。
- 输出：template family + knobs。
- 算法：epsilon-greedy、UCB、Thompson sampling 或轻量 XGBoost/RandomForest。
- 目标：在同等 timeout 下打败 SA 或至少不劣于 SA。

这比训练神经 CVRP solver 更实际。

### 阶段 2：LNS 子问题选择

实现 destroy/repair 后，训练选择器判断：

- 移除哪些 ship。
- 移除几个。
- repair 用哪个策略。
- 是否调用 HGS/FILO 外部 teacher。

这对应 Learning to Delegate / NLNS。

### 阶段 3：Teacher Distillation

跑 HGS-CVRP 或 FILO 生成高质量解，把它们作为 teacher：

- 学习客户/任务排序。
- 学习局部 move 接受概率。
- 学习哪些子问题值得重优化。

不要直接蒸馏完整 route；先蒸馏局部动作更稳。

### 阶段 4：神经模型

只有当阶段 0-3 数据足够，再考虑 POMO/SGBS/EAS 类模型：

- 训练小模型做 action scorer。
- Go 仍负责可行性和最终评估。
- 模型只做建议，不直接决定最终解。

## 推荐工程改造顺序

### 第一步：稳定模板策略

文件：

- `eoh_go/operator/strategy_templates.py`
- `eoh_go/operator/agent_controller.py`

目标：

- 默认使用 `mutation_mode=templates` 或 `hybrid`。
- 每个 template 都必须能编译。
- 每个 template 都有固定参数范围。

### 第二步：增加 strategy memory

新增：

```text
eoh_go/operator/strategy_memory.py
```

记录每个策略在每个 cell 上的表现：

- win/loss/tie。
- 平均 improvement。
- timeout rate。
- negative cost rate。
- runtime 分位数。

### 第三步：实现 ReAct JSON planner

替换当前 deterministic `BoundedReactPlanner`，但仍保留 clamp。

输入 observation，输出 `StrategySpec`。LLM 只产生 JSON，不产生 Go。

### 第四步：实现 beam insert

在 Go 侧或模板侧实现：

- top-k vehicle candidates。
- beam width。
- max expansion。
- fallback。

这是 SGBS 的最小迁移。

### 第五步：实现 destroy/repair

对 dispatch 增加局部破坏和修复：

- 按高成本 route 选择。
- 按新到达任务影响范围选择。
- 按历史失败区域选择。

这是 NLNS / Learning to Delegate 的最小迁移。

### 第六步：引入 HGS/FILO teacher

先作为离线外部工具：

- Go 动态实例导出为 `.vrp`。
- HGS/FILO 解导入为 route。
- 对比 SA 与 teacher gap。

## 指标标准

以后每个实验必须同时报告：

- `SA_J`
- `candidate_J`
- `improvement_pct`
- `runtime_s`
- `timeout_rate`
- `compile_success_rate`
- `feasible_rate`
- `guard_excluded_rate`
- `tie_rate`
- `worse_than_sa_rate`

只看 best cost 会误导。一个策略如果偶尔好但大多数超时，不应进入默认 agent。

## 当前最优决策

按投入产出比排序：

1. 保留 SA。
2. 用 bounded templates 替代自由 LLM 代码生成。
3. 加 strategy memory。
4. 实现 beam insert。
5. 实现 destroy/repair。
6. 跑 HGS-CVRP 做 teacher。
7. 训练 bandit/小模型选择策略。
8. 最后才考虑 POMO/EAS/COMPASS 级别的神经训练。

## 不建议做的事

- 不建议继续让 LLM 直接生成完整 `InsertShips`。
- 不建议先训练大模型。
- 不建议只在单 cell 上调策略。
- 不建议用没有 guard 的候选进入结果。
- 不建议把 HGS/FILO 直接嵌进实时路径，先离线 teacher。

## 最小可执行路线

下一步建议做一个 `ReAct v1`：

```text
输入：cell stats + failure memory + strategy memory
输出：bounded StrategySpec JSON
候选：sa_exact / fast_nearest / balanced_delta / robust_first_feasible / beam_insert
评估：当前 Go evaluator
学习：更新 strategy_memory
```

验收标准：

- 75-cell grid 能跑完。
- compile success = 100%。
- feasible rate 接近 100%。
- timeout rate 低于当前 LLM mutation。
- 至少在部分 cell 上稳定优于 SA。
- 不优于 SA 时自动退回 SA，不拖累平均结果。

这个路线比继续堆 LLM prompt 更可控，也更容易把论文方法逐步落到当前 Go 代码。
