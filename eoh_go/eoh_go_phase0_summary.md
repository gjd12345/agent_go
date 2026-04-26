# 轻量 EoH 外壳与 SA→0422 策略模型总结

## 1. 当前阶段目标

本阶段目标是为当前 Go 路由项目建立一个轻量的 EoH 外壳，吸收 Agent_EOH 的核心思想，但不直接硬耦合其完整工作流。

核心目标包括：

- 建立本地镜像层
- 支持演化循环
- 支持结果分析
- 支持研究记忆
- 支持候选管理
- 将 SA 明确建模为 baseline producer
- 将 0422 建模为 optimizer
- 将 warm 模式建模为 pipeline candidate

---

## 2. 已完成内容

### 2.1 Agent_EOH 仓库修复与落地

已完成外部仓库的 checkout 修复，本地可访问路径：

- [Agent_EOH](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH)

已确认可参考的关键入口包括：

- [eoh.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/eoh.py)
- [user_genroute_go](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/examples/user_genroute_go)
- [user_insertships_go](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/examples/user_insertships_go)

---

### 2.2 轻量 EoH 外壳已建立

当前已在本项目中建立轻量 EoH 外壳：

- [eoh_go](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go)

主要模块如下：

- [__init__.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go/__init__.py)
- [paths.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go/paths.py)
- [store.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go/store.py)
- [memory.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go/memory.py)
- [candidates.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go/candidates.py)
- [benchmark.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go/benchmark.py)
- [evolution.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go/evolution.py)
- [cli.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go/cli.py)

---

### 2.3 工作区已建立

轻量 EoH 工作区路径：

- [eoh_go_workspace](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go_workspace)

已包含：

- [PLAN.md](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go_workspace/memory/PLAN.md)
- [MEMORY.md](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go_workspace/memory/MEMORY.md)
- [research_notes.md](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go_workspace/memory/research_notes.md)
- [run_index.json](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go_workspace/runs/run_index.json)

---

## 3. 当前策略建模方式

本轮重构的核心，不是简单比较三个二进制程序，而是将其转换为“策略语义模型”。

### 3.1 SA 的角色

SA 不再被视为普通候选算法，而是：

- baseline scorer
- seed producer
- round 的基线来源

也就是：

> SA = baseline producer

---

### 3.2 0422 的角色

0422 当前有两种语义：

#### 1）0422_direct

表示直接运行 0422 求解：

> 0422 = direct optimizer

#### 2）sa_then_0422

表示先由 SA 生成 seed，再交给 0422 做 refine：

> SA -> seed -> 0422 refine

这不再被简单视为 `0422_warm`，而是一个正式的 pipeline candidate。

---

## 4. 当前 strategy model

当前 `run_round` 已从旧的 `bin_configs` 语义，升级为 `strategy_configs` 语义。

### 当前支持的策略类型

#### baseline_producer
用于表示 SA：

- strategy_name: `sa_baseline`
- strategy_type: `baseline_producer`
- baseline_solver: `SA`
- optimizer_solver: `None`
- seed_pipeline: `false`

#### direct_optimizer
用于表示直接运行 0422：

- strategy_name: `0422_direct`
- strategy_type: `direct_optimizer`
- baseline_solver: `SA`
- optimizer_solver: `0422`
- seed_pipeline: `false`

#### pipeline_candidate
用于表示 warm/pipeline 策略：

- strategy_name: `sa_then_0422`
- strategy_type: `pipeline_candidate`
- baseline_solver: `SA`
- optimizer_solver: `0422`
- seed_pipeline: `true`
- seed_source: `SA`

---

## 5. run metadata 已升级

当前 run metadata 已经加入新的策略语义信息。

典型字段包括：

- `mode`
- `baseline_solver`
- `strategy_names`

例如成功运行结果中已经出现：

- mode: `sa_to_0422`
- baseline_solver: `SA`
- strategy_names:
  - `sa_baseline`
  - `0422_direct`
  - `sa_then_0422`

这意味着 run 已经不再只是“比较几个程序”，而是在比较几个明确的策略对象。

---

## 6. run_round 当前能力

当前 `run_round` 已经能够：

1. 读取 mode 配置
2. 解析 strategy_configs
3. 执行 baseline_producer
4. 执行 direct_optimizer
5. 执行 pipeline_candidate
6. 输出 full results / improvement / summary
7. 记录 run_index

对应核心实现位于：

- [evolution.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go/evolution.py)

---

## 7. 当前结果文件结构

每次 run 会在如下目录下生成结果：

- [runs](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go_workspace/runs)

成功 run 示例：

- [20260423_131304](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go_workspace/runs/20260423_131304)

典型产物：

- `full_benchmark_results.json`
- `improvement_vs_SA.json`
- `summary.json`

索引文件：

- [run_index.json](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go_workspace/runs/run_index.json)

---

## 8. 已验证的一次成功运行

终端成功输出如下关键信息：

- run_id: `20260423_131304`
- mode: `sa_to_0422`
- baseline_solver: `SA`
- strategy_names:
  - `sa_baseline`
  - `0422_direct`
  - `sa_then_0422`

summary 为：

### 0422_direct

- avg_cost_improvement_pct: `58.9442`
- avg_response_time_improvement_pct: `96.8214`
- count_cost: `2`
- count_time: `2`

### sa_then_0422

- avg_cost_improvement_pct: `94.1707`
- avg_response_time_improvement_pct: `79.703`
- count_cost: `2`
- count_time: `2`

---

## 9. 当前结论

从当前结果可以得到明确结论：

### 9.1 0422_direct
特点：

- 更快
- 成本改进明显
- 适合作为 direct optimizer 基线

### 9.2 sa_then_0422
特点：

- 成本优化更强
- 时间提升不如 0422_direct 极致
- 更适合作为 pipeline candidate

因此，当前已经形成两种不同的优化策略形态：

1. 直接优化型：`0422_direct`
2. 管线优化型：`sa_then_0422`

---

## 10. 这对后续 EoH 的意义

这一步的关键意义是：

后续 EoH 不再只是“进化某个二进制程序”，而是可以进化：

- baseline producer
- direct optimizer
- pipeline candidate

这意味着未来可以继续扩展出：

- `0422_candidate_001`
- `0422_candidate_002`
- `sa_then_0422_candidate_003`
- `sa_then_0422_with_new_seed_filter`
- `sa_then_0422_with_adaptive_score`

也就是从“程序比较”，升级到“策略空间搜索”。

---

## 11. 下一步建议

### 建议 A：强化 analyze_latest_run
补充输出：

- best_strategy
- best_cost_improvement
- best_time_improvement
- latest_run_dir

### 建议 B：接入 candidate optimizer 注册机制
将后续候选体纳入统一策略空间，例如：

- `0422_candidate_001`
- `0422_candidate_002`
- `sa_then_0422_candidate_001`

并统一相对 SA baseline 进行对比。

### 建议 C：把 pipeline candidate 作为 EoH 重点进化对象
优先演化以下部分：

- seed 质量
- seed 过滤规则
- 0422 refine 策略
- `candidateScore`
- `computeLowerBound`
- `getSortedCandidates`

---

## 12. 总结

当前阶段已经完成了从“轻量 benchmark 包装层”到“具备策略语义的轻量 EoH 外壳”的升级。

已经落地的核心能力包括：

- 轻量 EoH 模块化结构
- 本地工作区
- run_round 可执行
- run 结果落盘
- SA baseline producer 建模
- 0422 direct optimizer 建模
- SA->0422 pipeline candidate 建模
- run metadata 升级
- summary 已能反映策略层结果

当前最重要的结构性成果是：

> 已经把“SA 为基础进化、0422 为优化解”的想法，正式落实为可运行的 strategy model。

---
这份文档的前 333 行（即我们在添加最新进展之前的内容）主要总结了 将单纯的 Go 路由评测脚本，升级为“具备策略语义的轻量 EoH 演化外壳”的阶段性核心成果 。

为您提炼和总结其中的核心要点如下：

### 1. 基础设施建设落地
- 轻量级框架隔离 ：没有直接将庞大复杂的 Agent_EOH 硬塞进来，而是独立建了轻量级的 eoh_go 模块（包含状态管理、演化、记忆、评测等子模块）以及 eoh_go_workspace 工作区，实现了运行记录、结果分析的闭环与落盘。
### 2. 核心突破：完成“策略语义建模”
这是这部分报告最重要的思想转变。系统不再仅仅是简单地跑几个 Go 二进制程序看谁快，而是进行了 角色抽象 ：

- SA 算法（ baseline_producer ） ：不再视为普通竞争者，而是专门作为 基准线提供者 和 初始种子产生器 。
- 0422 算法（Optimizer） ：分化为两个具体的策略对象：
  1. 0422_direct （直接优化器）：直接去解题，特点是速度极快，适合作为性能基线。
  2. sa_then_0422 （管线候选体 / pipeline_candidate ）：先用 SA 跑出初始种子，再交由 0422 深度优化。实验证明这种策略在成本（Cost）优化上潜力更强。
### 3. 运行机制与评测体系升级
- 现有的核心入口 run_round 已全面支持“策略模式”。它能够自动执行 SA 基准、运行各种 Optimizer 策略，并自动生成详尽的对比报告（ improvement_vs_SA.json 等），清楚地计算出候选策略相较于基线的提升百分比。
### 4. 对后续大模型进化的重大意义
- 从“改程序”升级为“搜策略” ：由于基座已经按策略建好，后续 Agent_EOH 大模型的任务将变得更加清晰——大模型不仅可以进化 0422 本身，还可以 专门去进化管线策略的某个环节 （比如进化 candidateScore 候选打分逻辑、进化 SA 提供种子的过滤规则等）。
### 💡 简而言之：
这部分报告宣告了**“让 SA 提供基准与种子，让 0422/大模型负责深度优化”的构想已经完全在代码工程上落地**，并成为了一个可随时用来评判大模型生成代码好坏的 坚实基座 。这也是我们为什么在 13 节（刚刚补充的内容）中，能够自信地开始把 Agent_EOH 接入进来跑 V0 闭环的原因。


## 13. V0 纯 EOH 最小闭环构建与架构重构 (最新进展)

### 13.1 当前工作内容总结 (`eoh_go` 与 `eoh_go_workspace`)

在近期开发中，我们成功拉通了从 `eoh_go` 框架到 `Agent_EOH` 的真实调用，实现了端到端的演化测试：

1. **`eoh_go` 核心引擎的增强 (`evolution.py`)**:
   - 实现了对 `Agent_EOH` 原始演化脚本 (`runEoH_insertships_go.py`) 的子进程调用 (`run_agent_eoh_generation`)。
   - 实现了鲁棒的数据集路径挂载/拷贝 (`_ensure_agent_eoh_dataset`)，自动解决子脚本运行时的基准数据集缺失问题。
   - 实现了 AST/正则 级别的代码补丁注入 (`_replace_insertships`)，能将大模型生成的 Go 逻辑(比如 `InsertShips` 函数)动态合并进现有的完整 Go 路由工程的主干 (`main.go`)。
2. **`eoh_go_workspace` 试运行成果**:
   - 成功触发并记录了包含 LLM 调用的演化回合(如 `run_id: 20260423_180525`)。
   - 验证了 EOH 可以产出代码 (`agent_eoh_insertships_001`)。
   - 发现了当前生成的 Go 代码存在上下文缺失的问题（例如提示找不到 `SortManager` 或未导入的包），这是后续 Prompt 或适配器需要解决的问题，但框架层面的流转已然贯通。

### 13.2 讨论敲定的后续路线 (V0 到 V2_Agent)

针对上述进展和遗留痛点，我们明确了未来的架构演进路线图：

#### 阶段一：V0 纯 EOH 最小闭环（当前进行中）
目标是确保端到端（大模型生成 -> Go 代码整合 -> 编译 -> 测评 -> 报告输出）的闭环稳定运行。
- **决定对 `runEoH_insertships_go.py` 进行重构 (已完成)**:
  - **现状痛点**: 之前通过黑盒形式(subprocess 命令行调用)去触发 Agent_EOH 里的 python 脚本，导致难以获取状态和调整参数。
  - **重构方案**: 废弃命令行工具模式，我们新建了 `eoh_go/eoh_runner` 模块，包含 `config.py` 与 `runner.py`，将 Agent_EOH 作为一个原生 Python 库被 `eoh_go/evolution.py` 直接调用 (`run_v0_eoh(config)`)。
  - **优势**: 显著增强主框架与演化生成器的数据交互健壮性，可以在内存中实时获取运行时间、LLM 报错和生成的种群对象。
  - **最新监控运行结果**: 采用重构后的 API 进行了 `eoh_refactor_test` 模式的运行，成功调用了 LLM (Deepseek) 并在当前目录下输出了结果。结果依然复现了代码编译失败问题 (`undefined: SortManager`, `undefined: sort`)，证明端到端链路调用正常，下一步可以直接着手解决 prompt/代码补丁上下文的问题。

#### 阶段二：V2 ReAct 多智能体进化层（规划中）
- 目标：将原有的代码变异/交叉等简单的启发式搜索操作，升级为基于 ReAct (思考-行动-观察) 的高级智能体演化。
- 这意味着 LLM 不仅在“写代码”，而是在自主分析测评失败的报错原因，自主制定修改策略，这才是真正发挥大模型能力的关键，从而实现在成本和时间维度上全面或部分超越 SA baseline 的最终目标。

---

## 14. 本轮关键修改总结（None 目标值定位与修复）

### 14.1 根因定位

针对“进化日志中 Obj 全是 None”的问题，本轮定位到两个核心根因：

1. `eoh_evolution.py` 的 `_get_alg` 解析逻辑原本偏向 Python（`def/import/return`），对 Go 代码块提取不稳，导致候选代码提取失败后进入异常分支，最终出现 `objective=None` 候选。
2. `seed` 文件读取在 Windows 下存在编码兼容问题（GBK/UTF-8 混用），触发解码异常后中断初始化，进一步放大了“无有效目标值”的现象。

### 14.2 代码级修复项

本轮已完成如下修复：

- **Go 代码提取链路修复 (`eoh_evolution.py`)**
  - 在 `_get_alg` 中增加语言分流：当任务是 `InsertShips` 时走 Go 分支。
  - 新增多级正则提取 `func InsertShips(...) Dispatch { ... }`，并保留 Python 分支作为兼容回退。
  - 修复 `code_all` 拼接策略：Go 代码不再追加 Python 风格输出拼接，直接使用提取到的函数体。
  - 增加防御性逻辑：当未提取到有效代码时显式抛错，避免静默退化为无效个体。

- **Seed 初始化与目标函数链路增强 (`eoh_runner` + `prob_insertships_go.py`)**
  - `eoh_go/eoh_runner/runner.py` 新增“从当前 `main.go` 自动提取 SA `InsertShips` 并写入 seed”的机制，确保 V0 从 SA 基线出发。
  - `EOHConfig` 增加复合目标相关配置（`objective_use_composite`、`objective_res_weight`、`run_timeout_s`、`use_sa_seed_as_init`）。
  - `prob_insertships_go.py` 中评估逻辑增加 `RES` 解析，并支持 `cost + w*RES` 复合目标（可通过环境变量开关与调权）。
  - 错误链路统一输出结构化信息，便于上层监控失败阶段。

- **构建兼容修复 (`evolution.py`)**
  - 对 EOH 生成的 `InsertShips` 自动注入缺失依赖：`sort` import 与 `SortManager` 定义，修复 `undefined: SortManager/sort` 编译错误。

### 14.3 当前状态

- V0 已具备“SA 作为初始种群 + Go 代码稳定提取 + 编译兼容补丁 + 可配置 cost/RES 目标”的最小闭环能力。
- 仍需继续观测不同 API/编码环境下的稳定性，以及多代进化时的真实收敛表现。

### 14.4 下一步

- 固定同一数据子集，执行多组 3~5 代实验（不同 `RES` 权重），输出 cost/RES 对比曲线。
- 在 `eoh_evolution.py` 中进一步增强 Go 提取器鲁棒性（如代码块边界/注释干扰场景）。
- 将"失败类型（提取失败/编译失败/评估失败）"纳入统一 run 报告字段，便于后续 ReAct 层自动诊断与修复策略选择。

---

## 15. RES 权重控制实验与结果

### 15.1 实验设计

针对"SA 基线在多代进化后效果退化"的问题，设计了不同 `objective_res_weight` 权重的对比实验，测试在评估目标中引入 RES（响应时间）惩罚项对进化稳定性的影响。

实验配置：
- `ec_n_pop=3`, `ec_pop_size=4`
- `sim_time_multi=10`, `max_instances=1`
- `objective_use_composite=True`
- 三种权重：`w=0.0`, `w=0.05`, `w=0.2`

### 15.2 实验结果对比

| 实验组 | Generation | 有效个体 | Best Fitness | Avg Fitness | None Rate |
|--------|-----------|---------|-------------|-------------|----------|
| **V0 baseline (w=0.2)** | gen=0 | 1 | 47.0190 | 47.0190 | 0% |
| | gen=1 | 3 | 47.0190 | 333333527.71 | 0% |
| | gen=2 | 4 | 47.0190 | 250000266.16 | 0% |
| | gen=3 | 4 | 47.0190 | 250000266.16 | 0% |
| **V0 w=0.0** | gen=0 | 1 | 1e9 | 1e9 | 0% |
| | gen=1 | 1 | 1e9 | 1e9 | 0% |
| | gen=2 | 2 | **38.0789** | 500000019.04 | 0% |
| **V0 w=0.05** | gen=0 | 1 | 1e9 | 1e9 | 0% |
| **V0 w=0.2** | gen=0 | 1 | 1e9 | 1e9 | 0% |
| | gen=1 | 1 | 1e9 | 1e9 | 0% |
| | gen=2 | 2 | 536.1232 | 500000268.06 | 0% |
| | gen=3 | 2 | 536.1232 | 500000268.06 | 0% |

### 15.3 实验结论

1. **稳定性问题仍占主导**：多数实验组都混合了 1e9 惩罚值，说明评估稳定性问题（编译失败、Go 二进制执行异常）的优先级高于权重调优。
2. **w=0.0 组出现最佳单点**：在 gen=2 时产生了 best=38.0789 的有效解，说明纯 cost 目标有潜力但在早期阶段失败率高。
3. **V0 baseline (w=0.2) 保持稳定**：gen=0 即有 47.019 的有效值，后续 gen 保持该最优值，体现了精英保留机制的作用。
4. **权重影响不显著**：由于 1e9 惩罚的方差过大（数量级 1e9），不同权重之间的差异被评估失败的噪声淹没。

---

## 16. V2 Agent 工具层对齐与 max_loops=3 运行结果

### 16.1 V2 工具层参数对齐

为确保 V2 ReAct Agent 的默认行为与 V0 已验证的稳态参数完全一致，对 [react_tools_insertships.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/examples/user_insertships_go/v2_agent/react_tools_insertships.py) 中的所有工具函数进行了参数对齐：

| 参数 | V0 稳态值 | V2 对齐值 |
|------|----------|----------|
| `sim_time_multi` | 10 | 10 |
| `max_instances` | 1 | 1 |
| `run_timeout_s` | 60 | 60 |
| `eva_timeout` | 120 | 120 |
| `objective_use_composite` | True | True |
| `objective_res_weight` | 0.2 | 0.2 |
| `dataset_density` | d100 | d100 |
| `sim_time_interval` | 1 | 1 |

对齐的工具函数包括：
- `run_evolution()` — 执行 EOH 演化
- `run_code_review()` — 编译检查与单点评测
- `run_comprehensive_evaluation()` — 多实例完整评测
- `write_report()` — 生成报告

### 16.2 Fallback 降级机制

在 [react_master_agent_insertships.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/examples/user_insertships_go/v2_agent/react_master_agent_insertships.py) 中新增了 LLM 不可用时的降级机制：

- **环境变量 `EOH_FORCE_FALLBACK=1`** 触发降级模式
- 三级 deterministic fallback plan：
  1. `loop=0` → 执行 `run_evolution`（自动生成 1 代）
  2. `loop=1` → 执行 `analyze_latest_results`（分析最新种群）
  3. `loop=2` → 执行 `finish`（结束）
- API endpoint 归一化函数 `_normalize_endpoint()` 处理用户输入的 `https://.../v1/chat/completions` 格式

### 16.3 max_loops=3 运行结果

在 `EOH_FORCE_FALLBACK=1` 模式下执行 `max_loops=3`，得到以下种群结果：

| Generation | 个体数 | Best Fitness | Avg Fitness | None Rate |
|-----------|-------|-------------|-------------|----------|
| gen=0 | 1 | 49.5452 | 49.5452 | 0% |
| gen=1 | 4 | 49.5452 | 50.5512 | 0% |

**关键指标**：
- `best_fitness=49.54518`（接近 SA 基线 47.019）
- `none_rate=0.0`（全部有效，无 1e9 惩罚）
- 精英保留机制工作：gen=1 的 best_fitness = gen=0 的 best_fitness（精英未丢失）

---

## 17. 新增控制参数：数据集密度 (d) 与模拟时间间隔 (t)

### 17.1 参数设计背景

为了支持用户在 Solomon benchmark 数据集上灵活控制评测难度与规模，新增了两个控制参数：

1. **`dataset_density`**（数据集密度）：对应 Solomon benchmark 中的密度变体（d25 / d50 / d75 / d100），控制每个实例文件中参与评测的客户站点比例。
2. **`sim_time_interval`**（模拟时间间隔）：对应 Solomon benchmark 中的时间窗口紧度变体，控制客户时间窗口的宽窄（值越大，时间窗口越紧，问题越难）。

### 17.2 参数定义

**在 [config.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go/eoh_runner/config.py) 中**：
```python
dataset_density: str = "d25"       # 默认使用 25% 密度
sim_time_interval: int = 1          # 默认 1（原始时间窗口）
```

**在 [prob_insertships_go.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/examples/user_insertships_go/prob_insertships_go.py) Evaluation 类**：
```python
class Evaluation:
    def __init__(
        self,
        ...
        dataset_density: str = "d100",
        sim_time_interval: int = 1,
    ):
```

### 17.3 数据集结构

Solomon benchmark RC101-RC108 数据集存放在：
- [solomon_benchmark](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/solomon_benchmark)

每个 JSON 文件结构如下：
```json
{
  "loadCap": 200,
  "vehicleNum": 25,
  "batch": [
    {
      "timeReady": 0,
      "ori": [ { "x": 40, "y": 50, "timeStart": 0, "timeEnd": 240, "reqCode": 0, "load": 0 }, ... ],
      "des": [ { "x": 25, "y": 85, "timeStart": 145, "timeEnd": 175, "reqCode": 0, "load": 20 }, ... ]
    }
  ]
}
```

每个文件包含 1 个 batch，各有 15 个 `ori`（起点）和 15 个 `des`（终点）Station。

### 17.4 参数功能实现

#### dataset_density：站点密度过滤

根据密度百分比截取 `ori[]` 和 `des[]` 数组的前 N 个站点：

| 密度值 | 含义 | 保留站点数（15个中） |
|-------|------|-------------------|
| `d25` | 25% 密度 | 4 个 |
| `d50` | 50% 密度 | 8 个 |
| `d75` | 75% 密度 | 11 个 |
| `d100` | 100% 密度 | 15 个（全部） |

实现代码在 `_density_pct()` 方法中：
```python
def _density_pct(self) -> float:
    d = self.dataset_density.lower().strip()
    m = re.match(r"d(\d+)", d)
    if m:
        return int(m.group(1)) / 100.0
    return 1.0
```

#### sim_time_interval：时间窗口压缩

当 `sim_time_interval > 1` 时，所有 `timeEnd` 值除以该系数（向下取整，最小为 1），使时间窗口更窄、问题更紧：

| 时间间隔值 | 效果 |
|-----------|------|
| `1` | 原始时间窗口（不变） |
| `2` | 时间窗口缩窄 50% |
| `3` | 时间窗口缩窄 67% |
| `N` | 时间窗口缩窄至 1/N |

### 17.5 参数透传链路

两个参数从配置到评测的全链路透传路径：

```
config.py / react_tools_insertships.py
    → runner.py (run_v0_eoh)
        → prob_insertships_go.py Evaluation.__init__
            → _build_and_run()
                → _prepare_filtered_json()  [生成过滤后的临时 JSON]
                    → mainbin.exe [Go 二进制读取过滤后的数据]
```

涉及的所有文件：
- [config.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go/eoh_runner/config.py) — 配置定义
- [runner.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go/eoh_runner/runner.py) — V0 运行入口
- [prob_insertships_go.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/examples/user_insertships_go/prob_insertships_go.py) — 评测核心，实现过滤逻辑
- [react_tools_insertships.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/examples/user_insertships_go/v2_agent/react_tools_insertships.py) — V2 Agent 工具层

### 17.6 使用示例

通过 V2 Agent 运行密度=d25、时间间隔=2 的实验：
```python
run_evolution(
    generations=3,
    pop_size=4,
    dataset_density="d25",
    sim_time_interval=2,
)
```

通过 V0 runner 运行相同配置：
```python
from eoh_runner.config import EOHConfig
from eoh_runner.runner import run_v0_eoh

config = EOHConfig(
    dataset_density="d50",
    sim_time_interval=2,
    ec_n_pop=3,
    ec_pop_size=4,
)
result = run_v0_eoh(config)
```

---

## 18. 总览：所有代码变更文件清单

| 文件 | 变更类型 | 描述 |
|------|---------|------|
| [config.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go/eoh_runner/config.py) | 修改 | 新增 `dataset_density`、`sim_time_interval` 参数 |
| [runner.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go/eoh_runner/runner.py) | 修改 | 透传 `dataset_density` 到 Evaluation |
| [prob_insertships_go.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/examples/user_insertships_go/prob_insertships_go.py) | 修改 | 1e9 修复、RES 解析、密度/时间间隔过滤 |
| [eoh_interface_EC.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/eoh_interface_EC.py) | 修改 | None objective 显式返回 1e9 惩罚 |
| [react_tools_insertships.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/examples/user_insertships_go/v2_agent/react_tools_insertships.py) | 修改 | 参数对齐 + 密度/时间间隔透传 |
| [react_master_agent_insertships.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/examples/user_insertships_go/v2_agent/react_master_agent_insertships.py) | 修改 | Fallback 降级 + endpoint 归一化 |
| [config.json](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/examples/user_insertships_go/v2_agent/config.json) | 新建 | API key 配置 |
| [eoh_evolution.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/eoh_evolution.py) | 修改 | Go 代码提取分流 + 编译兼容补丁 |

---

## 19. 结论与状态总览

### 已达成的能力

| 能力 | 状态 | 备注 |
|------|------|------|
| V0 最小 EOH 闭环 | ✅ 已稳定 | SA seed → EOH 演化 → 编译 → 评估 → 种群输出 |
| 1e9 问题解决 | ✅ 已修复 | sim_time_multi 调整 + cost/RES 解析增强 |
| RES 复合目标 | ✅ 已实现 | 环境变量控制开关与权重 |
| 编译兼容补丁 | ✅ 已自动注入 | SortManager + sort import |
| V0→V2 参数对齐 | ✅ 已完成 | 所有工具函数使用一致参数 |
| V2 Agent 降级机制 | ✅ 已实现 | EOH_FORCE_FALLBACK 环境变量 |
| V2 max_loops=3 运行 | ✅ 已验证 | best_fitness=49.545, none_rate=0% |
| dataset_density 参数 | ✅ 已实现 | d25/d50/d75/d100 密度过滤 |
| sim_time_interval 参数 | ✅ 已实现 | 时间窗口紧度控制 |

### 待优化项

| 项目 | 优先级 | 说明 |
|------|--------|------|
| V2 Agent LLM 驱动模式验证 | 高 | 当前仅验证了 fallback 模式 |
| 多代进化稳定性提升 | 高 | 1e9 惩罚仍出现在部分评估中 |
| Go 代码 prompt 上下文增强 | 中 | 减少 `undefined: SortManager` 等编译错误 |
| 失败类型报告统一 | 中 | 将提取/编译/评估失败纳入 run 报告 |
| RES 权重对比实验扩展 | 低 | 需先解决评估稳定性问题才能获得有效对比 |

---

## 20. Selected Efficiency Comparison 观察记录（最新）

### 20.1 Res 指标口径修正

当前对论文表格中的 `Res` 采用如下口径：

> `Res = RESPONSE_TIME / RESPONSE_COUNT`

也就是批次插入事件中“首次给出可行/候选调度结果”的平均响应时间，而不是 `.exe` 完整仿真的 wall-clock 总耗时。

负数 final cost 视为不可行结果，在表格中记为 `-`，不参与 best-J 加粗。

### 20.2 当前 EOH 候选的主要胜点

当前最有价值的稳定胜点出现在：

| Inst. | d | t | Runs | SA Res. | SA J | EOH Res. | EOH J | 结论 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| RC101 | d50 | 1 | 5 | **1.204 ± 0.069** | 34.30 | 1.975 ± 0.165 | **32.36** | EOH 将 J 改善约 5.67%，但响应更慢 |

这说明当前 EOH 不是只会生成可编译代码，而是已经能在特定密度/问题条件下发现更低 `J` 的 Go 插入策略。

同时，对已有 generation 的非 seed 候选扫描发现：

- 从 `clean_eoh_3gen_20260424_103613` 中抽到 5 个唯一非 seed 候选；
- 5 个候选均能编译；
- 其中 2 个候选在 `RC101,d50,t=1` 上达到 `J=32.36`；
- 因此该胜点更像是一类策略模式被 EOH 找到，而不是单个文件偶然。

### 20.3 全八题 d50,t=1 对比

在 `d50,t=1` 条件下，当前最佳 EOH 候选与 SA 的全八题对比如下：

| Inst. | d | t | SA Res. | SA J | EOH Res. | EOH J |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| RC101 | d50 | 1 | **1.203** | 34.30 | 1.857 | **32.36** |
| RC102 | d50 | 1 | **0.404** | **54.88** | 1.503 | 81.29 |
| RC103 | d50 | 1 | **0.431** | **54.88** | 1.540 | 81.29 |
| RC104 | d50 | 1 | **0.437** | **54.88** | 1.459 | 81.29 |
| RC105 | d50 | 1 | **0.455** | **54.88** | 1.452 | 81.29 |
| RC106 | d50 | 1 | **0.625** | **46.48** | 1.439 | 81.29 |
| RC107 | d50 | 1 | **0.380** | **54.88** | 1.412 | 81.29 |
| RC108 | d50 | 1 | **0.391** | **57.26** | 1.436 | 81.29 |

观察：

- 当前 EOH 候选只在 `RC101,d50,t=1` 上赢 `J`；
- 在 `RC102-RC108,d50,t=1` 上，SA 同时拥有更低 `Res` 和更低 `J`；
- 当前 EOH 候选应定位为“局部有效候选”，不能作为跨实例通用策略。

### 20.4 d25 与 d75 的密度趋势

低密度 `d25,t=1` 全八题中，SA 全面占优：

- SA 的 `J` 稳定为 `43.81`；
- 当前 EOH 候选的 `J` 稳定为 `74.61`；
- EOH 的 `Res` 也显著慢于 SA。

高密度 `d75,t=1` 全八题中，SA 仍全面占优：

| Inst. | d | t | SA Res. | SA J | EOH Res. | EOH J |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| RC101 | d75 | 1 | **5.686** | **29.53** | 6.779 | 64.05 |
| RC102 | d75 | 1 | **2.089** | **30.53** | 6.405 | 66.05 |
| RC103 | d75 | 1 | **2.138** | **30.53** | 5.814 | 66.05 |
| RC104 | d75 | 1 | **1.178** | **38.53** | - | - |
| RC105 | d75 | 1 | **1.580** | **30.53** | 4.835 | 66.05 |
| RC106 | d75 | 1 | **3.232** | **30.53** | 4.624 | 66.05 |
| RC107 | d75 | 1 | **0.841** | **81.62** | 3.724 | 101.55 |
| RC108 | d75 | 1 | **0.996** | **31.62** | 3.728 | 101.55 |

观察：

- `d75` 下差距很大，不能简单解释为“EOH 略差”；
- 当前 EOH 候选在高密度下泛化失败；
- `RC104,d75,t=1` 上 EOH 未能在预算内产生有效结果；
- 该结果更适合写成“直接迁移失败 / OOD generalization failure”，而不是主算法失败。

### 20.5 d100 初步观察

完整密度 `d100,t=1` 更重，一次性全八题运行会出现长尾超时。

已拆分获得的部分观察：

- `RC101,d100,t=1`：SA 有效且优于 EOH；
- `RC102/RC103/RC104/RC105,d100,t=1`：在 120 秒单 solver 预算下出现双侧无有效输出或 timeout；
- `RC106,d100,t=1`：EOH 出现新的质量胜点，`J=80.48` 优于 SA 的 `J=90.75`，但 `Res` 更慢。

这表明：

- `d100` 不宜一次性整表跑，需要逐实例备份；
- 当前 EOH 候选在高密度下不是完全无效，但稳定性不足；
- 高密度策略需要单独进化，而不能直接复用 `d50` 候选。

### 20.6 当前结论

当前实验支持如下结论：

1. EOH 已经能够产生可编译、可评估、且在局部条件下改善 `J` 的 Go 代码候选。
2. 当前最佳候选主要在中等密度 `d50` 的局部实例上有效。
3. 小密度 `d25` 下 SA 已足够强，EOH 的复杂策略反而变慢且变差。
4. 高密度 `d75/d100` 下，当前候选泛化失败，需要密度感知策略。
5. 后续不应期待一个 EOH 候选覆盖所有场景，而应演化 density-aware 策略族。

---

## 21. 后续工作计划

### 21.1 实验数据管理

后续所有表格与实验结果必须避免覆盖：

- 每次运行写入带时间戳的 `run_YYYYMMDD_HHMMSS` 子目录；
- 长实验按实例拆分运行；
- 每完成一个 row 立即写出 partial JSON；
- 重要中间结果定期复制到 `backup_YYYYMMDD_HHMMSS` 目录；
- 最终表只从明确标注来源的 raw JSON/CSV 中拼接。

当前已对 `eoh_go.efficiency_table` 做出调整：

- 默认输出到 timestamped run 子目录；
- 运行中持续写出 `efficiency_table_partial.json`；
- 如确实需要覆盖，必须显式使用 `--no-run-subdir`。

### 21.2 策略分层：density-aware EOH

后续不再将 EOH 目标设定为“生成一个全场景通用 InsertShips”，而是按密度拆成策略族：

| 策略族 | 目标场景 | 主要目标 | 策略方向 |
|---|---|---|---|
| `EOH-fast` | d25 | 极低 Res，避免复杂搜索 | early exit、top-k 最近车辆、复用 SA |
| `EOH-balanced` | d50 | 改善 J，同时控制 Res | 最小边际成本、slack 二级排序、轻量剪枝 |
| `EOH-robust` | d75/d100 | 可行性、timeout 控制、fallback | top-k 限制、尝试次数上限、SA fallback、硬约束过滤 |

### 21.3 V2 ReAct 的位置调整

本阶段论文不再把 V2 ReAct 写入方法主线。ReAct、多智能体调度、自动诊断失败并生成修复动作等内容都属于后续系统扩展，统一放入“未来展望”。

当前论文主体只保留已经完成并可由实验数据支撑的 Guarded EOH-Go 链路：LLM 变异 `InsertShips`、Go 编译、动态源评价、候选 guard、filtered-best 选择与 cleaned reporting。

### 21.4 近期实验顺序

优先级从高到低：

1. 固定 `RC101,d50,t=1`，继续比较更多 EOH generation/best candidate，建立 `EOH-balanced` 候选池。
2. 固定 `d75,t=1`，单独进化 `EOH-robust`，目标不是立刻赢 SA，而是降低 timeout/无效率。
3. 对 `d100,t=1` 逐实例运行，补齐 timeout/valid 分布，避免一次性整表长跑。
4. 对 `d25,t=1` 设计 `EOH-fast`，目标是接近 SA 的 `Res`，而不是复杂优化。
5. 最终拼接全八题结果表，但区分：
   - direct transfer 结果；
   - density-specific EOH 结果；
   - timeout/invalid 统计。

### 21.5 论文叙事建议

当前更可信的论文叙事是：

> EOH 能在 Go 实时路由代码中发现局部有效策略，但策略具有明显场景敏感性。中等密度下，EOH 能找到改善最终成本的插入策略；低密度下 SA 已足够强；高密度下需要显式引入剪枝、fallback 与密度感知进化。因此，后续框架应从单候选 EOH 升级为 density-aware EOH 策略族。

这比宣称“EOH 全面优于 SA”更准确，也更适合当前实验事实。

---

## 22. d/t 参数修正与后续 EOH 评价口径（2026-04-25）

### 22.1 本轮讨论后的方向校准

本轮讨论中一度将工作推进到 `Router` 规则设计，但该方向已经重新校准：

- 当前工作的核心不是人工设计一个最终路由器；
- 当前工作的核心是让 **EOH 进化 Go 代码**，并观察进化代码在不同密度 `d` 与时间参数 `t` 下的表现；
- Router 只能作为诊断工具或工程化参考，不再作为近期论文主线；
- 后续主表应从 `SA vs Router` 回到 `SA seed / baseline vs EOH evolved candidate`。

更合适的主线表述为：

> 固定一个初始 seed，让 EOH 在不同 `d` 与 `t` 条件下进化 `InsertShips` Go 代码，比较每个 cell 下 generation/best candidate 的 `Res` 与 `J`，从而分析 EOH 代码进化的场景敏感性。

### 22.2 density 参数继续保留四组

后续实验仍然保留四组密度：

| 参数 | 含义 |
|---|---|
| `d25` | 低密度 |
| `d50` | 中密度 |
| `d75` | 高密度 |
| `d100` | 全密度 |

但注意：此前 `solomon_benchmark` 是单 batch 静态数据；`solomon_benchmark_d25/d50/d75` 是多 batch 动态数据。  
因此后续必须在报告中明确标注数据源，避免把“静态截断密度”和“动态多 batch 密度”混为一谈。

### 22.3 t 参数的两种定义与取舍

本轮尝试了两种 `t` 的定义。

#### A. window-scale t：时间窗缩放

定义为：

```text
newTimeEnd = timeStart + t * (oldTimeEnd - timeStart)
```

该定义的优点是不会产生负时间窗；缺点是在 `t=1.0~0.6` 范围内，很多路线结构不变，导致同一个 `d` 下 `J` 几乎不随 `t` 变化。

因此该定义可以保留为“时间窗鲁棒性”实验，但不适合作为当前主线。

#### B. arrival-scale t：请求释放节奏缩放

定义为：

```text
newTimeReady = oldTimeReady * t
```

该定义直接改变动态订单释放节奏，更符合“不同时间间隔对解质量影响”的实验目标。  
在多 batch 数据源 `solomon_benchmark_d25/d50/d75` 上，该定义已经观察到 SA 的 `J` 会随 `t` 变化，说明它能真正改变动态调度过程。

因此后续优先采用 `arrival-scale t` 作为 EOH 评价参数。

### 22.4 已完成的普通 benchmark 观察

普通 benchmark 层已经跑过如下实验：

```text
RC101
d = d25, d50, d75, d100
t = 1.0, 0.9, 0.8, 0.7, 0.6
metric = Res, J
```

其中：

- window-scale t 下，所有 cell 都有结果，但同一密度下 `J` 变化不明显；
- arrival-scale t 下，若使用单 batch `solomon_benchmark`，`J` 仍基本不变；
- arrival-scale t 下，若使用动态多 batch 数据源 `solomon_benchmark_d25/d50/d75`，`J` 会随 `t` 变化；
- d100 目前仍主要来自单 batch 数据，因此 arrival-scale 对 d100 的影响较弱。

这说明：后续要研究 `t` 对进化代码的影响，必须将动态多 batch 数据源接入 EOH evaluation，而不是只在普通 benchmark 层做外部测试。

### 22.5 后续 EOH 实验应采用的表格口径

后续核心表格不再使用 `SA vs Router`，而应使用：

| d | t | gen | seed Res | seed J | best EOH Res | best EOH J | valid candidates | best candidate id |
|---|---:|---:|---:|---:|---:|---:|---:|---|

其中：

- `seed` 建议先固定为 SA 原始 `InsertShips`；
- `best EOH` 指该 cell 下 EOH 进化种群中的最优可编译、可运行候选；
- `valid candidates` 记录非 1e9、非 timeout、非 compile error 的候选数；
- 每个结果目录必须保留 population、candidate source、binary、raw stdout/stderr 与 partial JSON。

第一阶段建议只跑：

```text
problem = RC101
d = d25, d50, d75, d100
t = 1.0, 0.9, 0.8, 0.7, 0.6
generation = 1~3
pop_size = 4
seed = SA InsertShips
```

如果运行成本太高，则先固定：

```text
RC101,d50,t = 1.0, 0.9, 0.8, 0.7, 0.6
```

验证 EOH 是否会在不同 `t` 下产生不同 Go 代码与不同 `J/Res`。

### 22.6 需要接入代码层的修改

后续应把 `arrival_scale` 正式接入 EOH evaluation 链路：

```text
EOHConfig
  -> run_v0_eoh
  -> Agent_EOH Evaluation
  -> _prepare_filtered_json
  -> Go binary benchmark
```

建议新增或明确以下参数：

```python
dataset_density: str
arrival_scale: float
window_scale: float | None
```

近期主线只启用：

```python
arrival_scale = 1.0, 0.9, 0.8, 0.7, 0.6
window_scale = None
```

避免把时间窗紧缩与请求释放节奏混在同一张表中。

### 22.7 论文叙事修正

后续论文叙事应避免写成“人工 Router 优化”。更准确的叙事是：

> EOH is used to evolve executable Go insertion code from a fixed seed under different density and temporal settings. The results show that evolved code can produce locally effective improvements, but the improvements are sensitive to the density and request-release schedule.

中文表述：

> 本文使用 EOH 从固定种子出发进化 Go 插入调度代码，并系统评估不同密度与请求释放节奏下进化代码的 `Res/J` 表现。实验重点不是人工路由，而是验证 EOH 代码进化在动态实时路由问题中的可行性、局部有效性与场景敏感性。

---

## 23. arrival_scale 接入 EOH evaluation 链路实现记录（2026-04-25）

本轮已将 `arrival_scale` 从配置层正式接入 EOH evaluation 链路。

### 23.1 已修改链路

```text
EOHConfig
  -> run_v0_eoh(config)
  -> prob_insertships_go.Evaluation(...)
  -> _prepare_filtered_json(...)
  -> Go binary benchmark
```

### 23.2 新增/对齐参数

在 `EOHConfig` 中新增：

```python
arrival_scale: float = 1.0
use_density_source_dirs: bool = False
```

其中：

- `arrival_scale` 控制请求释放时间缩放：`newTimeReady = oldTimeReady * arrival_scale`；
- `use_density_source_dirs=True` 时，`d25/d50/d75` 会优先读取 `solomon_benchmark_d25/d50/d75` 动态多 batch 数据源；
- 当使用动态密度目录时，不再对同一实例做二次 density 截断。

### 23.3 V0/V2 对齐

已同步修改：

- `eoh_go/eoh_runner/config.py`
- `eoh_go/eoh_runner/runner.py`
- `eoh_go/evolution.py`
- `eoh_go/cli.py`
- `Agent_EOH/eoh/src/eoh/examples/user_insertships_go/prob_insertships_go.py`
- `Agent_EOH/eoh/src/eoh/examples/user_insertships_go/v2_agent/react_tools_insertships.py`

CLI 现在可以通过如下参数传入：

```text
--dataset-density d50
--sim-time-interval 1
--arrival-scale 0.8
--use-density-source-dirs
```

### 23.4 验证结果

已验证：

```text
dataset_density = d50
arrival_scale = 0.8
use_density_source_dirs = True
```

Evaluation 会读取 `solomon_benchmark_d50`，并将 RC101 的 `timeReady` 从：

```text
[0, 5, 11, 28, 29, 34, 61, 65]
```

缩放为：

```text
[0, 4, 9, 22, 23, 27, 49, 52]
```

Python 编译检查已通过。

---

## 24. 动态密度源 SA arrival_scale 探针验证（2026-04-25）

### 24.1 实验目的

验证在 `use_density_source_dirs=True`（使用 `solomon_benchmark_d25/d50/d75` 动态多 batch 数据源）条件下，`arrival_scale t` 是否能真正影响 SA 的 `J` 值，从而确认该参数维度对 EOH 实验有效。

### 24.2 实验配置

- **求解器**: `mainbin_sa.exe`（SA 基线）
- **问题**: RC101
- **数据源**: `solomon_benchmark_d25`, `solomon_benchmark_d50`, `solomon_benchmark_d75`（动态多 batch）
- **密度**: d25, d50, d75
- **时间参数**: arrival_scale t = 1.0, 0.9, 0.8, 0.7, 0.6
- **仿真倍数**: sim_time_multi=10
- **输出**: `reports/tables/_sa_t_probe_tmp/sa_t_sensitivity.json`

### 24.3 实验结果

| Inst. | d | t | SA Res. | SA J |
| --- | --- | --- | --- | --- |
| RC101 | d25 | 1.0 | 0.642 | 664.12 |
| RC101 | d25 | 0.9 | 0.694 | 645.45 |
| RC101 | d25 | 0.8 | 0.707 | 656.44 |
| RC101 | d25 | 0.7 | 0.643 | **607.96** |
| RC101 | d25 | 0.6 | 0.697 | **557.48** |
| RC101 | d50 | 1.0 | 1.003 | **713.52** |
| RC101 | d50 | 0.9 | 0.926 | 697.24 |
| RC101 | d50 | 0.8 | 1.126 | 697.24 |
| RC101 | d50 | 0.7 | 1.050 | 697.24 |
| RC101 | d50 | 0.6 | 1.058 | **647.79** |
| RC101 | d75 | 1.0 | 1.108 | **549.48** |
| RC101 | d75 | 0.9 | 1.207 | **435.48** |

### 24.4 结论

| 密度 | J 范围 | 变化幅度 | t 是否影响 J |
|------|--------|---------|------------|
| **d25** | 557.48 ~ 664.12 | **106.64** | ✅ 明显 |
| **d50** | 647.79 ~ 713.52 | **65.74** | ✅ 明显（两端） |
| **d75** | 435.48 ~ 549.48 | **114.00** | ✅ 明显（仅2点已可见） |

1. **`arrival_scale t` 能有效改变 `J`**，三个密度下均有 >65 的变化范围，证明该参数维度适合用于 EOH 实验。
2. **d25 和 d75 对 t 最敏感**，d50 在 t=0.9~0.7 区间 J 不变（可能是中间 batch 的 timeReady 恰好一致），但 t=0.6 时明显下降。
3. 该探针验证确认了基于动态密度源 + arrival_scale 的实验设计可行，后续 EOH 网格实验可以放心使用此配置。

---

## 25. EOH flash 动态密度网格实验（2026-04-25）

### 25.1 实验配置

- **EOH 模型**: `deepseek-v4-flash`
- **问题**: RC101
- **密度**: d25, d50, d75（动态多 batch 数据源）
- **时间参数**: arrival_scale t = 1.0, 0.9, 0.8, 0.7, 0.6
- **种群**: pop_size=4, generations=2
- **目标**: composite, res_weight=0.2
- **预期 run 目录**: `reports/tables/eoh_arrival_grid_flash_dynamic_full/run_YYYYMMDD_HHMMSS/`

### 25.2 部分已完成结果（3/15 cells）

| Inst. | d | t | Seed Res. | Seed J | Best EOH Res. | Best EOH J | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RC101 | d25 | 1.0 | 0.743 | 664.12 | 0.655 | 664.12 | EOH 候选 J 与 SA 一致（未改善） |
| RC101 | d25 | 0.9 | 0.680 | 645.45 | 0.646 | 645.45 | EOH 候选 J 与 SA 一致（未改善） |
| RC101 | d25 | 0.8 | - | - | - | - | 第3个 cell 运行中被中断 |

### 25.3 问题诊断：为什么 EOH 生成的候选全为 1e9 惩罚？

日志显示 `Pop Objs: 1000000000.0`，说明所有 EOH 变异候选的代码提取或编译评估均失败，只有 SA seed 本身作为有效个体留存。定位到根因如下。

#### 根因：prompt 模板中写死了 "implement it in Python"

在 [eoh_evolution.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/methods/eoh/eoh_evolution.py) 中，所有 6 个 prompt 模板方法都包含：

```python
# lines 62, 80, 97, 112, 127, etc.
"implement it in Python as a function named"
```

但该问题的目标语言是 **Go**。`prompt_other_inf` 虽然要求 "Return ONLY Go code"，但主导指令 `"implement it in Python"` 与 `prompt_task` 中的 Go 签名形成**矛盾**，导致 LLM 行为分裂：

| 冲突源 | 内容 | 位置 |
|--------|------|------|
| `prompt_task` | Go 函数签名 `func InsertShips(...)` | [prompts_insertships_go.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/examples/user_insertships_go/prompts_insertships_go.py#L5-L9) |
| `prompt_other_inf` | "Return ONLY Go code" | [prompts_insertships_go.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/examples/user_insertships_go/prompts_insertships_go.py#L36-L38) |
| `get_prompt_i1/e1/m1/...` | "implement it in **Python**" | [eoh_evolution.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/methods/eoh/eoh_evolution.py#L62) |

#### 修复方法

将 `eoh_evolution.py` 中所有 `"implement it in Python"` 改为 `"implement it in Go"`。涉及 6 个方法：

| 方法 | 行号 |
|------|------|
| `get_prompt_i1` | ~62 |
| `get_prompt_e1` | ~80 |
| `get_prompt_e2` | ~97 |
| `get_prompt_m1` | ~112 |
| `get_prompt_m2` | ~127 |
| `get_prompt_m3` | ~137（不包含 Python 关键词） |

同时，`_get_alg` 中的 Python fallback 正则（`r"import.*return"`, `r"def.*return"`）对 Go-only 任务无意义，也应当删除或绕过。

#### 补充排查：prompt 中 Assign 结构体定义不足

在 [prompts_insertships_go.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/Agent_EOH/eoh/src/eoh/examples/user_insertships_go/prompts_insertships_go.py#L27) 中：

```python
"type Assign struct { ... }\n"
```

这个 `...` 占位符没有给出 Assign 的具体字段（如 `Cost float64`, `StationsLen int`, `Stations []Station` 等）。LLM 无法了解 Assign 的结构，生成的代码容易引用不存在的字段导致编译失败。

#### 临时改善：patch.py 自动注入

当前 [evolution.py](file:///c:/Users/24294/.trae/Archive_2/Archive_0422/eoh_go/evolution.py) 已有 `_replace_insertships` 方法在编译前自动注入 `sort` import 和 `SortManager` 定义。但若生成的代码使用了 Assign 的未知字段或方法名错误，patch 也无法挽救。

### 25.4 初步观察

1. **flash 模型速度**: 单 cell 约 1.5~2 min（含 LLM 调用 + 评估），比 V4 Pro 的 ~5.3 min 快 2~3 倍。
2. **中断原因**: 第三 cell 因 sandbox 环境网络限制被 `KeyboardInterrupt` 中断，非脚本错误。

---

## 26. EOH 评估链路修复与 candidate guard（2026-04-25）

### 26.1 背景问题

在 `deepseek-v4-flash` 跑动态密度源实验时，曾出现两类异常现象：

1. **候选全为 1e9**：早期表现为 seed 或 LLM 变异候选全部被评估成 `1000000000.0`，容易误判为 LLM 无法生成有效 Go 代码。
2. **异常极小 J**：修复 1e9 后，部分候选出现 `Obj=10.57301`、`Obj=9.76656` 一类远低于 SA seed 的极小值。这类值不是正常优化结果，而更可能是候选代码利用了评估器漏洞，例如订单插入失败后提前 `break`，导致漏单仍被计算为低成本。

这说明当前 EOH 闭环已经进入“能生成非 1e9 候选”的阶段，但评价器必须加入合法性过滤，否则演化会自然偏向 reward hacking。

### 26.2 已完成修复

#### 修复 A：EOH evaluation wrapper 的 timeout 参数错误

文件：

- `Agent_EOH/eoh/src/eoh/examples/user_insertships_go/prob_insertships_go.py`

修复内容：

- 将 `_run_command()` 的调用参数从错误的 `timeout=` 改为 `timeout_s=`。
- 修复后，SA seed 在 `Evaluation(..., use_density_source_dirs=True, d25, t=1.0)` 下可正常得到 `664.1195472849001`，不再被错误评为 1e9。

意义：

- 证明“全 1e9”并不是 LLM 本身不可用，而主要是评估 wrapper 的工程错误。
- 修复后 `deepseek-v4-flash` 可以产生多个非 1e9 候选，例如 `657.73438`、`689.9746` 等。

#### 修复 B：新增 candidate guard

新增文件：

- `eoh_go/eoh_runner/candidate_guard.py`
- `tests/test_candidate_guard.py`

核心功能：

| 检查项 | 处理 |
|---|---|
| `objective >= 1e8` | 标记为 `invalid` |
| 缺少 `func InsertShips` | 标记为 `invalid` |
| 缺少 `RenewnTotalCost()` | 标记为 `suspicious` |
| `bestIndex == -1 { break }` 等失败插入后提前退出 | 标记为 `suspicious` |
| objective 或外部 J 低于 `seed_J * 0.3` | 标记为 `suspicious` |
| 多个 `return dispatch` | 标记为 `suspicious` |

选择逻辑：

- `raw_best`：原始最低 objective 候选。
- `filtered_best`：排除 invalid/suspicious 后的最低 objective 候选。
- 后续主表优先采用 `filtered_best`，避免把异常极小 J 当成论文结果。

已有轻量验证：

| cell | raw best | filtered best | 说明 |
|---|---:|---:|---|
| RC101,d25,t=0.9 | 10.57301 | 557.91366 | 极小值被 guard 标为 suspicious |
| RC101,d25,t=1.0 | 657.73438 | 657.73438 | 正常候选保留 |
| RC101,d25,t=1.0 | 1e9 | - | penalty 候选标为 invalid |

#### 修复 C：grid 输出增加 raw/filtered 字段

修改文件：

- `eoh_go/experiments/eoh_arrival_grid.py`

新增输出字段：

| 字段 | 含义 |
|---|---|
| `valid_candidates` | 通过 guard 的候选数 |
| `suspicious_candidates` | 被判定为可疑的候选数 |
| `invalid_candidates` | 编译失败、1e9、无有效代码等候选数 |
| `raw_best_objective` | 未过滤前最低 objective |
| `filtered_best_objective` | 过滤后最低 objective |
| `selected_best_kind` | `filtered` 或 `raw_fallback` |
| `selected_best_status_after_eval` | 外部运行后再次分类的状态 |
| `selected_best_flags_after_eval` | 外部运行后的可疑原因 |

意义：

- 后续表格不再只展示“看起来最小”的结果，而能区分 raw best 与可信 best。
- 异常极小值不删除，而是保留在 raw 记录中，作为 evaluator guard 失效/候选作弊的证据。

#### 修复 D：prompt 约束增强

修改文件：

- `Agent_EOH/eoh/src/eoh/examples/user_insertships_go/prompts_insertships_go.py`

修改内容：

- 修正 `AddShip` 签名为 `func (assign *Assign) AddShip(id int, ori, des Station) bool`。
- 明确要求处理每一个 `oris/dess` 订单。
- 明确禁止因单个订单插入失败而提前退出外层订单循环。
- 要求无改进插入时 fallback 到安全 seed-style insertion。
- 要求返回前调用 `dispatch.RenewnTotalCost()`。
- 禁止 print、mock 或直接篡改 final cost 输出。

### 26.3 本轮修复的定位

这轮修改不是为了让某个 cell 立刻超过 SA，而是把 EOH 从“能跑”推进到“能可信地产生候选并筛掉明显作弊候选”。它对应 mini-LLM4AD pipeline 中的 evaluator guard 层：

```text
LLM mutation
  -> Go compile
  -> simulation evaluation
  -> candidate guard
  -> filtered population selection
  -> table/report output
```

---

## 27. EOH 相关文献调研结论

### 27.1 原版 EOH

原版 EOH（Evolution of Heuristics, ICML 2024）将 LLM 与 evolutionary computation 结合，用自然语言 thought + executable code 共同表示启发式，并通过评估器进行选择和变异。对当前项目的启发是：

- EOH 的核心不是一次性让 LLM 写出完美算法，而是通过 population、mutation、selection 逐步搜索。
- EOH 必须依赖可信 evaluation；如果 evaluator 有漏洞，演化会主动利用漏洞。
- 原版仓库更接近研究原型，不应直接当作稳定实验平台，需要在本项目中补充 sandbox、guard、logging、repair 和表格汇总层。

参考：

- https://github.com/FeiLiu36/EoH
- https://proceedings.mlr.press/v235/liu24bs.html
- https://arxiv.org/abs/2401.02051

### 27.2 LLM4AD

LLM4AD 将 EOH、FunSearch 等 LLM-assisted algorithm design 方法平台化，强调 search method、task、LLM interface、evaluation sandbox 的模块化。对当前项目的启发是：

- 当前工作应继续从“脚本拼接”走向“小型 LLM4AD pipeline”。
- 需要把 candidate generation、compile/run、guard、population selection、report output 分层。
- 不急于上完整复杂 agent，先保证每一层可观测、可复现、可备份。

参考：

- https://arxiv.org/abs/2412.17287
- https://github.com/Optima-CityU/llm4ad
- https://www.llm4ad.com/

### 27.3 FunSearch

FunSearch 的关键经验是 program database + evaluator + iterative improvement。对当前项目尤其重要的是：

- 不能只看单轮 best candidate，应保存完整候选库。
- evaluator 是闭环可信性的核心。
- 如果完整性约束缺失，程序搜索会找到“不服务订单但成本很低”的非法程序。

参考：

- https://www.nature.com/articles/s41586-023-06924-6

### 27.4 ReEvo

ReEvo 的核心是 reflective evolution，即把评估失败原因转化为自然语言反馈，让下一轮变异有方向。对当前项目的启发是：

- 不必现在迁移到复杂 ReAct。
- 可以先采用 ReEvo-style feedback：把 compile error、timeout、1e9、suspicious low J、`bestIndex == -1 break`、J worse than seed 等原因写入下一轮 prompt。
- 这相当于给 EOH 增加 verbal gradient，而不是引入完整 agent loop。

参考：

- https://arxiv.org/abs/2402.01145
- https://openreview.net/forum?id=483IPG0HWL
- https://github.com/ai4co/reevo

### 27.5 Eureka / reward-code evolution

Eureka 虽然主要是 reward code evolution，但它与当前工作结构相似：LLM 生成可执行代码，自动评估，再用反馈迭代。对当前项目的启发是：

- 必须明确防止 reward hacking。
- 对 `InsertShips` 来说，完整服务订单、无提前退出、无伪造输出、无异常低成本应成为硬约束。

参考：

- https://arxiv.org/abs/2310.12931
- https://eureka-research.github.io/

### 27.6 EoH-S / UBER 等变体

EoH-S 强调互补启发式集合，UBER 强调 uncertainty-based exploration/exploitation。对当前项目的启发是：

- 不一定追求一个通用 `InsertShips`。
- 可以演化 density-aware strategy family：
  - `EOH-d25-fast`
  - `EOH-d50-balanced`
  - `EOH-d75-robust`
- 后续可以把“候选是否值得继续变异”也纳入选择逻辑，而不是只看单次 objective。

参考：

- https://arxiv.org/abs/2508.03082
- https://arxiv.org/abs/2412.20694

---

## 28. 当前论文主线：Guarded EOH-Go

### 28.1 判断

当前论文采用的已实现路线是：

> 保留原版 EOH 主线，补 evaluator guard、动态源评价、异常候选过滤和 cleaned reporting，形成一个小型、可复现的 Guarded EOH-Go pipeline。

ReAct、多 agent 调度、自动切换 EOH/ReEVO 框架、后训练、完整订单一致性 guard 等尚未完成内容，不进入当前论文的方法和实验主线，只作为未来展望。

论文当前应强调：

1. EOH 可以生成并变异可编译的 Go 插入启发式。
2. `arrival_scale` 与 `d25/d50/d75` 动态源已经接入 evaluation 链路。
3. 主表只采用 guard 后的 filtered-best，而不是 raw-best。
4. repeat validation 用于区分单次胜点和相对可信的稳定胜点。

### 28.2 具体 pipeline

```text
SA seed
  -> LLM mutation
  -> Go code extraction
  -> Go compile
  -> dynamic source evaluation
  -> candidate guard
  -> filtered-best selection
  -> cleaned SA vs EOH table
```

### 28.3 放入未来展望的扩展方向

后续可以把 guard 结果转成 prompt feedback，例如：

| 失败类型 | 反馈给下一轮 prompt 的信息 |
|---|---|
| compile fail | 具体 Go 编译错误 |
| timeout | 限制候选车辆 top-k、减少搜索循环 |
| 1e9 | 说明编译或运行失败，不进入精英池 |
| suspicious low J | 说明可能漏单，禁止 early break |
| `bestIndex == -1 break` | 要求 fallback 到 seed-style insertion |
| J worse than seed | 要求保留 seed fallback 或减少破坏性改动 |

这属于 ReEvo-style feedback 的未来扩展，不作为当前论文已经完成的方法。完整 ReAct、多 agent 调度和后训练同样放入未来展望，不写入本文实验主线。

---

## 29. 后续实验与论文表格建议

### 29.1 短期实验顺序

优先继续当前 RC101 动态源网格：

```text
d = d25, d50, d75
t = 1.0, 0.9, 0.8, 0.7, 0.6
model = deepseek-v4-flash
generations = 1
pop_size = 4
```

但表格必须采用 filtered best，而不是 raw best。

### 29.2 表格字段建议

每个 cell 输出：

| 字段 | 论文意义 |
|---|---|
| SA Res. | baseline 首次可行响应时间 |
| SA J | baseline 解质量 |
| EOH Raw Obj. | 演化搜索原始最低值，用于展示搜索压力 |
| EOH Filt. Obj. | guard 后可信最低值 |
| EOH Res. | filtered candidate 的首次响应时间 |
| EOH J | filtered candidate 的解质量 |
| Valid/Suspicious/Invalid | 说明候选质量分布 |

### 29.3 异常值处理原则

异常极小值不应直接删除，也不应作为有效结果进入主表。建议：

- 主表使用 `filtered_best`。
- 附录或说明中报告 raw best 与 suspicious 数量。
- 对典型 suspicious code 做定性分析，说明 evaluator guard 的必要性。

这样既能避免虚假结论，也能把“LLM 代码演化会 exploit evaluator”变成论文中的一个有价值观察。

### 29.4 三个策略族的后续方向

| 策略族 | 目标密度 | 主要目标 | 约束 |
|---|---|---|---|
| EOH-fast | d25 | 降低 Res，避免复杂搜索 | 不牺牲完整性 |
| EOH-balanced | d50 | 控制 Res，同时改善 J | 保留 seed fallback |
| EOH-robust | d75/d100 | 避免 timeout 和 invalid | top-k、fallback、硬约束过滤 |

当前不要把 router 当成论文主线。router 可以作为实验组织方式，但核心贡献仍应是：

> LLM-driven EOH 如何在动态密度与时间节奏变化下演化 Go 调度启发式，并通过 guard/filter/feedback 形成可信候选。

---

## 30. 论文报告收尾：参考《第二篇论文中文.pdf》的写作口径（2026-04-26）

本项目当前论文应明确写成对 `第二篇论文中文.pdf` 的延伸，而不是另起一个完全无关的问题。参考论文的核心设定是闭环园区配送中的动态取送货路径规划，实验上同时报告响应时间 `Res.` 与最终目标值 `J`，并比较不同动态请求比例/密度下算法表现。本文沿用该评价口径，但把“人工设计实时路由算法”替换为“用 EOH 自动进化 Go 插入启发式代码”。

### 30.1 与参考论文的对应关系

| 参考论文元素 | 本项目对应实现 |
|---|---|
| 动态取送货/实时路由 | Go 调度程序在动态请求到达时调用 `InsertShips` |
| `Res.` 响应时间 | 首次给出可行 dispatch 的响应时间 |
| `J` 路径/调度质量 | Go benchmark 输出的 final route cost |
| 25%/50%/75% 动态比例实验 | `solomon_benchmark_d25/d50/d75` 动态源 |
| timescale/动态节奏实验 | `arrival_scale t = 1.0,0.9,0.8,0.7,0.6` |
| 算法效率对比表 | SA seed vs guarded EOH filtered-best 对比表 |

因此，论文主线建议表述为：

> 在参考论文的实时动态路由评价框架下，本文研究 LLM-driven EOH 是否能够自动生成可编译、可运行、并在部分密度与到达节奏下改善 `J` 的 Go 插入启发式。

### 30.2 当前可写的实验结论

主表数据来自：

- `eoh_go_workspace/reports/tables/eoh_grid_cleaned_summary_rc101_105/clean_summary.md`
- `eoh_go_workspace/reports/tables/eoh_selected_repeats_summary_20260426/selected_repeat_summary.md`

当前 RC101--RC105 共 75 个 `d,t` cell 中，guard 清洗后得到 43 个有效 SA-vs-EOH 对比：EOH 改善 16 个、持平 11 个、变差 16 个；另有 32 个 cell 因无 SA/EOH 结果、负值或 suspicious-low 结果被排除。这个结果不能支持“EOH 全面优于 SA”，但可以支持“EOH 在动态实时路由中具有局部有效性，且需要 evaluator guard 才能可信评估”。

重复验证显示，早期单次运行中的部分强改善并不稳定；RC102/RC104 的若干胜点在 repeat 中退化为持平或变差。相对更值得保留的证据集中在 RC105 的 `d50,t=0.9` 与 `d75,t=0.6/0.9`，其中 repeat 后仍能观察到至少一次改善，高密度两个 cell 的平均 `Delta J` 仍为负。

### 30.3 论文创新点建议

1. **问题迁移创新**：把 EOH 从常见 Python/数学启发式生成，迁移到 Go 实时调度代码生成，评价对象是可编译的 `InsertShips` 函数，而不是伪代码或离线算法片段。
2. **评估机制创新**：提出 guarded EOH pipeline，将 LLM 生成、Go 编译、动态仿真、异常候选过滤和 cleaned reporting 串成可复现实验链路。
3. **实验视角创新**：参考原论文的 `Res.`/`J` 双指标与动态密度实验，进一步加入 `arrival_scale`，讨论密度和请求到达节奏对自动进化代码质量的影响。
4. **负结果也有价值**：异常极小值、1e9、timeout、漏单候选说明代码进化会主动 exploit evaluator，因此 guard/filter 是 LLM 自动算法设计进入真实系统前的必要层。

### 30.4 已生成的论文草稿与图表

LaTeX 报告目录：

- `eoh_go_workspace/reports/paper_report_20260426/guarded_eoh_report.tex`
- `eoh_go_workspace/reports/paper_report_20260426/build/guarded_eoh_report.pdf`
- `eoh_go_workspace/reports/paper_report_20260426/figures/status_heatmap.svg`
- `eoh_go_workspace/reports/paper_report_20260426/figures/outcome_counts.svg`
- `eoh_go_workspace/reports/paper_report_20260426/tables/top_improvements.tex`
- `eoh_go_workspace/reports/paper_report_20260426/tables/repeat_validation.tex`

报告已按参考论文口径写入：动态路由问题设定、`Res.`/`J` 指标定义、密度与时间节奏实验、guarded EOH 方法、清洗后主结果、repeat validation 和保守结论。

### 30.5 后续若继续扩展数据

优先扩展方向不是盲目跑全量，而是：

1. 继续补 RC106--RC108 的 `d25/d50/d75, t=1.0~0.6`，但主表必须使用 filtered-best。
2. 对 RC105 的稳定胜点增加 3--5 次 repeat，用来支撑论文中的稳定性声明。
3. 对 suspicious-low 候选做 1--2 个代码案例分析，证明 guard 的必要性。
4. 将结论写成“场景相关的自动启发式设计”，避免写成“EOH 普遍击败 SA”。

---

## 31. 论文版最终口径校准（2026-04-26）

为避免前期探索路线影响论文主线，当前论文主体只保留已经完成并可由数据支撑的内容：

```text
SA seed
  -> LLM mutation
  -> Go code extraction
  -> Go compile
  -> dynamic source evaluation
  -> candidate guard
  -> filtered-best selection
  -> cleaned reporting
```

论文正文不再把 ReAct、多 agent 调度、自动切换 EOH/ReEVO 框架、后训练、完整订单一致性校验等尚未完成内容写成当前方法。它们只作为“未来展望”出现，用来说明后续毕业论文或下一阶段系统可以扩展的方向。

### 31.1 当前已经完成、可以进入论文主体的内容

| 模块 | 是否进入正文 | 说明 |
|---|---:|---|
| EOH 变异 `InsertShips` Go 代码 | 是 | 当前实验的核心方法 |
| Go 编译与动态仿真评价 | 是 | 保证候选代码可执行、可复现 |
| `arrival_scale` 动态到达节奏 | 是 | 已正式接入 evaluation 链路 |
| `d25/d50/d75` 动态密度源 | 是 | 对应参考论文动态比例思想 |
| SA vs Guarded EOH 对比 | 是 | 论文主表使用 filtered-best |
| suspicious-low/negative/missing 过滤 | 是 | 当前可信评价的关键机制 |
| repeat validation | 是 | 用于支撑稳定性讨论 |
| ReAct / 多 agent / 后训练 | 否 | 仅放入未来展望 |
| 自动切换 EOH/ReEVO 框架 | 否 | 仅放入未来展望 |
| 更完整的订单/时间窗一致性 guard | 否 | 当前未完整实现，作为未来工作 |

### 31.2 论文结论应采用的保守表述

当前结果支持的结论是：

> 在参考论文的动态取送货实时路由评价框架下，Guarded EOH-Go 能够在部分密度与到达节奏组合上自动发现优于 SA seed 的 Go 插入启发式；但该优势不是全局稳定的，必须通过 guard/filter 与 repeat validation 才能形成可信结论。

不建议在论文中写成：

- EOH 全面优于 SA。
- ReAct agent 已经提升了进化能力。
- 多 agent 或后训练已经接入当前实验。
- 自动框架切换已经完成。

### 31.3 未来展望统一放置内容

以下内容只放入未来展望，不进入方法和实验主线：

1. 扩展 RC106--RC108，并增加 RC105 稳定胜点 repeat。
2. 增加订单完整性、时间窗和车辆状态一致性 guard。
3. 引入 ReEvo-style failure feedback，把 compile fail、timeout、suspicious-low、worse-than-seed 等失败原因反馈到下一轮 prompt。
4. 在毕业论文阶段探索 ReAct、多 agent 调度、自动选择 EOH/ReEVO 框架和后训练机制。

这一口径已经同步到 `eoh_go_workspace/reports/paper_draft_full_20260426/guarded_eoh_go_full_draft_cn.tex` 与重新编译后的 PDF 中。
