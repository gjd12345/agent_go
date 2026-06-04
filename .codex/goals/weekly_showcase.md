/goal: 官方 EoH benchmark 对齐 + RAG/History-RAG 小矩阵验证

目标：先接入/复现 EoH 官方 benchmark，再比较 `pure EOH`、`API-only`、`Literature-RAG`、`History-RAG` 是否优于单纯 EOH。当前不再把自定义 OBP 小例子或 InsertShips 作为主要证明对象；它们只作为本地 harness 工程经验。

报告一律写中文。实验产物不入 git，汇总报告和关键 best code 入 git。API key 不读取、不打印、不 echo；如需确认，只输出布尔值。

---

## 核心判断

EoH 原论文有效的关键不是“任意业务函数都能被 LLM 改好”，而是选择了小而清晰的官方 benchmark target：

| 对齐项 | 目标函数形态 | 为什么适合验证 RAG |
|---|---|---|
| `bp_online` | bin scoring function | 与当前 `ScoreBin` 最接近，能直接比较 best-fit / residual / utilization 类策略 |
| `tsp_construct` | next-node selection heuristic | 经典 TSP 知识丰富，nearest / insertion / regret / 2-opt 等卡片容易映射 |
| `cvrp_construct` | CVRP constructive heuristic | 候选官方/近官方对齐项；待 Phase A 确认官方实现和数据是否稳定可用 |

本地现状：

```text
Agent_EOH/eoh/src/eoh/problems/problems.py 仍引用 tsp_construct 和 bp_online。
但 Agent_EOH/eoh/src/eoh/problems/optimization/ 目录当前不存在。
cvrp_construct 在本地未发现完整注册、代码、数据或 runner；先作为候选项，不强行承诺完成。
当前 Go OBP wrapper 已跑通，但不是官方 bp_online 完整复现。
```

因此下一阶段首要任务是“官方资产对齐”，不是继续调自定义 problem 的 prompt。

---

## Phase A: 官方资产审计

只读优先，不跑 LLM。目标是产出官方 benchmark 映射表。

检查来源：

```text
官方 EoH 仓库：FeiLiu36/EoH
本地 Agent_EOH/eoh/src/eoh/problems/problems.py
本地 Agent_EOH/eoh/src/eoh/examples/
本地 eoh_go/experiments/
本地 eoh_go_workspace/problems/
```

必须确认每个 problem 的状态：

| problem | 必查项 |
|---|---|
| `bp_online` | 官方 prompt、evaluator、数据、seed、objective、是否与本地 Go `ScoreBin` wrapper 兼容 |
| `tsp_construct` | 官方 problem 包、数据、target function、seed、evaluation runner |
| `cvrp_construct` | 是否存在稳定官方/近官方 problem 包、CVRP data、target function、objective、是否能在 1 天内最小跑通 |

Phase A 输出：

```text
eoh_go_workspace/reports/official_eoh_benchmark_alignment.md
```

报告必须写清楚：

```text
本地已有
需要从官方补齐
不采用或延期的原因
每个 problem 的最小 smoke 命令
```

---

## Phase B: 最小官方复现

每个 problem 先只跑 seed/evaluator smoke，不比较 RAG。

验收标准：

```text
seed evaluator 可运行
objective 方向明确
输出可解析
失败原因可记录
不需要真实 LLM
```

优先级：

1. `bp_online`
2. `tsp_construct`
3. `cvrp_construct`

降级规则：

```text
如果 cvrp_construct 在 1 天内无法稳定跑通，不阻塞主线。
交付 bp_online + tsp_construct 完整 smoke，CVRP 作为接入风险报告。
```

---

## Phase C: 统一 benchmark harness

目标：已确认可用的官方/近官方 problem 使用同一种 summary schema，避免每题临时脚本拼结果。

每个 run summary 至少包含：

```text
problem
official_problem_name
arm
model
generations
pop_size
seed_objective
best_objective
delta_vs_seed
raw_offspring_count
raw_valid_candidates
final_population_size
unique_objective_count
best_code
rag_mode
rag_selected_items
rag_context_chars
rag_context_truncated
failure_reason
runtime_seconds
```

明确区分：

```text
raw objective
survivor population objective
外部 verified objective
```

报告只使用 verified objective 做性能结论；raw/survivor 只用于诊断。

---

## Phase D: 四臂小矩阵

每个已跑通 problem 先跑最小矩阵：

| arm | 配置 |
|---|---|
| `pure_eoh` | 使用官方原始 problem prompt，不追加本项目 RAG/API cards |
| `api_only` | 在官方原始 prompt 外，额外固定前置 problem API / signature / output contract |
| `literature_rag` | 注入对应 problem 的短 skill cards |
| `history_rag` | 只使用历史有效候选或官方/项目已有 code example |

默认实验参数：

```text
generations = 1
pop_size = 8
repeats = 1
```

进入 repeat 的 gate：

```text
raw_valid_candidates >= 5
rag_context_truncated = false
best_code 可通过外部 evaluator 复验
```

如果 gate 通过，再对最有信号的 problem/arm 跑：

```text
repeats = 3
generations = 2 或 3
```

### Phase D0: `bp_online` 无提升原因复盘

当前 `bp_online` 最小对比结果：

| arm | 状态 | best objective | 诊断 |
|---|---|---:|---|
| `pure_eoh` | completed gen=1 | 0.03984 | 模型不加 RAG 已自发生成 best-fit / tight-fit 公式 |
| `api_only` | completed gen=1 | 0.03984 | API 约束没有改变策略族，仍是 best-fit 变体 |
| `literature_rag_default` | completed gen=1 | 0.03984 | 检索到 `obp_best_fit`, `obp_first_fit`，与 pure EOH 生成策略重复 |
| `literature_rag_targeted_residual` | init completed, gen=1 timeout | 0.03984 | 成功检索 `obp_eoh_util_sqrt_exp`, `obp_funsearch_residual_poly`，但 context 仍截断且完整进化超时 |

结论：

```text
这不是 RAG 链路没生效，也不能写成 RAG 无效。
它说明 bp_online 在当前小预算/当前 runner 下没有拉开差距。
当前有效最优解都回到 best-fit/tight-fit 强基线策略族，因此 objective 暂时没有拉开。
```

具体原因：

1. **强基线快速占优**：`score(item, bins)` 目标很小，LLM 在 pure prompt 下已经能直接写出 best-fit/tight-fit。当前小预算结果里，RAG 给出的默认知识没有超出这个策略族。
2. **默认检索冗余**：默认 query 选中 `obp_best_fit` 和 `obp_first_fit`，等于把模型已经会写的策略再说一遍，没有引入新搜索方向。
3. **context 截断**：targeted residual run 虽然选中了 `obp_eoh_util_sqrt_exp` 和 `obp_funsearch_residual_poly`，但 1800 chars 仍截断第二张卡，说明 top_k=2 对 BP 仍偏大。
4. **objective 去重压缩 population**：default Literature-RAG 生成 `samples=6`，但当前摘要只证明 survivor/final population 为 `1/1`。这说明 survivor 去重压缩明显；若要断言“6 个样本都有效且 objective 完全重复”，必须补 `raw_valid_candidates` 和 `unique_objective_count`。
5. **预算/延迟限制**：targeted residual、TSP、CVRP 的 Gen 1 都在 20 分钟总预算附近超时。继续做 full generation 矩阵会浪费额度，短期应改成 init-only 或更长 timeout。
6. **验证口径不可混用**：官方 evaluation smoke 和 EoH training objective 的 instance 数、problem size 可能不同。报告中只能比较同一 runner、同一 problem、同一 arm 矩阵内的 objective。

修正后的执行策略：

| problem | 定位 | 下一步 |
|---|---|---|
| `bp_online` | 官方对齐 + RAG 检索诊断，不作为正向收益主证据 | 只再跑 `targeted residual top_k=1, max_chars<=1000, generations=0/init-only`；若仍无提升，停止扩 BP |
| `tsp_construct` | 更适合作为 RAG 正向收益候选 | 先补 TSP skill cards，再跑 `pure_eoh` vs `api_only` vs `literature_rag` 的 init-only 对照 |
| `cvrp_construct` | 更贴近 VRP 知识库，适合作为导师关心的迁移证据 | 先补 CVRP skill cards，再跑 init-only 对照 |

新的 gate：

```text
若 official runner 对 generations=0 的 summary 输出还不稳定，先补 init-only summary，再跑 init-only 对照。
bp_online 不再进入 repeat=3，除非 targeted residual top_k=1 明确优于 0.03984。
TSP/CVRP 在 gen=1 超时前，先统一采用 generations=0（只跑 init population）比较 arm。
所有 arm 必须报告 selected cards、context_chars、context_truncated、valid/raw/survivor。
```

补充诊断（2026-06-04）：

```text
pure_eoh: best 0.03984
api_only: best 0.03984
literature_rag_default: best 0.03984
literature_rag_targeted_residual: init 完成；Gen1 超时；best 0.03984
```

当前不提升的主要原因不是模型完全无法使用 RAG，而是 `bp_online` 在这个小预算设置下已经被强基线压住：

1. **目标函数空间太小**：官方 `bp_online` 只要求 `score(item, bins) -> score array`。模型在 pure EOH prompt 下就能写出 best-fit / tight-fit 族公式，已经达到当前 runner 观察到的 best objective `0.03984`。
2. **RAG 默认知识与 pure EOH 重复**：默认 Literature-RAG 主要选中 `obp_best_fit`、`obp_first_fit`，没有给模型带来新的策略族。
3. **targeted residual 已生效但仍未越过强基线**：定向检索能选中 `obp_eoh_util_sqrt_exp` / `obp_funsearch_residual_poly`，说明检索链路有效；但 init-only 最好代码仍退回 tight-fit / best-fit 变体，objective 仍是 `0.03984`。
4. **完整 Gen1 的预算不稳定**：targeted residual 在 Gen1 阶段超时，TSP/CVRP 的 Gen1 smoke 也接近 20 分钟预算上限。继续扩 `bp_online` repeat 会消耗额度但信息增量低。
5. **不能把“无提升”写成 RAG 失败**：当前证据只能说明 `bp_online` 在当前 problem size、operator、pop_size、timeout 下没有拉开差距。它仍然证明了 official benchmark 接入、RAG trace、problem-specific filtering 能工作。

因此执行策略调整为：

```text
停止扩大 bp_online。
保留 bp_online 作为 official EOH 对齐和 RAG 检索诊断样例。
把正向收益验证重心转向 tsp_construct / cvrp_construct。
TSP/CVRP 先跑 generations=0 init-only 四臂对照，避免 Gen1 超时掩盖 signal。
```

### Phase D1: TSP/CVRP init-only 对照前置条件

已补齐 problem-specific RAG 条目后，才能跑 TSP/CVRP 的 Literature-RAG，否则会出现 OBP cards 混入其他 problem 的错误结论。

当前要求：

```text
tsp_construct:
  global api = tsp_construct_api_skeleton
  strategy_pool = 5 张 tsp_* algorithm_card
  selected items 只能是 tsp_*，不得出现 obp_ / cvrp_

cvrp_construct:
  global api = cvrp_construct_api_skeleton
  strategy_pool = 5 张 cvrp_* algorithm_card
  selected items 只能是 cvrp_*，不得出现 obp_ / tsp_
```

通过后再跑：

```text
tsp_construct: pure_eoh / api_only / literature_rag, generations=0, pop_size=4
cvrp_construct: pure_eoh / api_only / literature_rag, generations=0, pop_size=4
```

只有在 init-only 出现 `best_objective`、`valid_candidates` 或 best code 明显差异后，才进入 Gen1 或 repeats。

2026-06-04 pop1/init-only 诊断结果：

| problem | pure EOH | API-only | Literature-RAG | selected cards | 判断 |
|---|---:|---:|---:|---|---|
| `tsp_construct` | 6.83907 | 6.86186 | 6.83907 | `tsp_nearest_insertion`, `tsp_nearest_neighbor` | RAG 与 pure 打平；可作为下一步放大对象 |
| `cvrp_construct` | 13.20696 | 13.41247 | 14.49387 | `cvrp_nearest_capacity`, `cvrp_capacity_slack` | RAG 变差；先复核 CVRP cards，不直接扩大 |

该结果的使用边界：

```text
pop_size=1, generations=0，每臂只有 2 个 init samples，survivor population=1。
只能作为链路诊断和下一步筛选，不作为最终性能结论。
```

修正后的下一步：

```text
优先：tsp_construct pop_size=4, generations=0 三臂对照。
暂缓：cvrp_construct 扩大实验；先审查 cvrp_capacity_slack / nearest_capacity 是否过度保守。
停止：bp_online repeat=3，除非更换 problem size 或 target。
```

TSP pop4 进展（2026-06-04）：

| problem | arm | pop_size | generations | best objective | valid/pop | 状态 |
|---|---|---:|---:|---:|---:|---|
| `tsp_construct` | `pure_eoh` | 4 | 0 | 6.83907 | 4/4 | done |
| `tsp_construct` | `api_only` | 4 | 0 | 6.78953 | 4/4 | done |
| `tsp_construct` | `literature_rag` | 4 | 0 | 6.83954 | 4/4 | done |

解释：

```text
api_only 相对 pure_eoh 改善 -0.04954，说明 API/signature/contract 约束在 TSP 上有轻微信号。
默认 literature_rag 没有超过 pure_eoh；selected cards = tsp_nearest_insertion, tsp_nearest_neighbor。
当前默认 RAG 问题不是链路失败，而是 top-2 过于保守，未把 tsp_regret_insertion / 更强 global scoring 纳入上下文。
```

下一步：

```text
不要直接扩大默认 literature_rag。
先跑 targeted Literature-RAG：query 明确包含 regret / lookahead / second-best / global scoring，使 tsp_regret_insertion 进入 top-k。
targeted TSP RAG 若低于 6.78953，才进入 Gen1 或 repeats。
```

targeted TSP RAG 结果（2026-06-04）：

| problem | arm | pop_size | generations | best objective | delta vs pure | delta vs API-only | valid/pop | selected cards |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `tsp_construct` | `literature_rag_targeted_regret_farthest` | 4 | 0 | 6.51118 | -0.32789 | -0.27835 | 4/4 | `tsp_regret_insertion`, `tsp_farthest_insertion` |

结论：

```text
这是当前 official benchmark 上最清晰的正向 signal。
默认 literature_rag 未提升，是因为 top-2 选卡过于保守；
targeted query 让 regret/farthest 进入上下文后，明显超过 pure_eoh 和 api_only。
```

后续策略更新：

```text
TSP 不再讨论“是否加 RAG”这个粗粒度问题。
改为比较 default nearest-RAG vs targeted regret/farthest-RAG。
targeted TSP RAG 可进入 repeats=3 或 generations=1，但必须记录 selected cards 和具体 best code。
```

五天内优先交付：

```text
bp_online + tsp_construct 的 A/B/C/D 完整闭环。
cvrp_construct 只在 Phase A/B 确认可稳定接入后进入四臂矩阵。
Phase E/G/H 只做支撑上述闭环的最小必要范围。
```

---

## Phase E: RAG corpus 对齐

每个官方 problem 都必须有自己的 target-specific RAG 条目。

Skill card 规则保持不变：

```text
content 使用 Skill / When / Do / Fallback / Safety 短指令格式
长版文献或代码说明放 source_path，不直接塞 prompt
api_constraint 固定前置，不进 retrieval pool
failure_case 只输出 warning 摘要，不输出源码
```

初始 corpus 范围：

| problem | literature cards | history cards |
|---|---|---|
| `bp_online` | best-fit, worst-fit, harmonic, residual penalty, utilization scoring | 官方/本地合法 ScoreBin 候选 |
| `tsp_construct` | nearest neighbor, nearest insertion, farthest insertion, regret insertion, 2-opt awareness | 官方 seed / 有效候选 |
| `cvrp_construct` | savings, sweep, nearest insertion, regret insertion, capacity-aware insertion | 待 Phase A 确认的官方/近官方 seed / 有效候选 |

禁止把一个 problem 的 skill card 混入另一个 problem 的 top-k。

---

## Phase F: 多 agent 审查关口

必须引入多 agent 审查，不允许单 agent 自说自话完成整条链路。

| 关口 | agent | 审查内容 |
|---|---|---|
| A 后 | `scout` / `explorer` | 官方资产是否真实存在，是否把本地 wrapper 误写成官方 benchmark |
| B 后 | `gatekeeper` | evaluator 目标方向、数据、seed、sandbox 是否正确 |
| D 前 | `verifier` | 四臂命令、API key 安全、RAG trace 字段、context 长度 |
| 结果后 | `gatekeeper + verifier` | 汇总表是否可比，是否混淆 raw/survivor/verified objective |

P0/P1 必须修完再提交。

---

## Phase G: 中文报告与交付

更新或新增：

```text
eoh_go_workspace/reports/official_eoh_benchmark_alignment.md
eoh_go_workspace/reports/clv_harness_weekly_showcase.md
eoh_go_workspace/reports/official_eoh_rag_ablation_summary.md
```

报告必须包含：

```text
每个 problem 的官方对齐状态
每个 arm 的 objective 表
每个 arm 的 valid/raw/survivor 诊断
RAG selected items 和 context chars
每个 problem 的 best code
失败或降级原因
```

具体进化出来的代码必须列进去，不能只写“策略变化”。

---

## Phase H: Git 和运行约束

允许提交：

```text
.codex/goals/weekly_showcase.md
必要的 runner / harness / tests
RAG corpus 小文本
中文汇总报告
```

禁止提交：

```text
API key / env
raw 大型实验目录
.DS_Store
PPT/HTML 临时产物
```

运行 LLM 实验时：

```text
使用已确认授权的公司 API
不打印 key
使用 caffeinate，熄屏后继续运行
同一时间只保留必要实验进程
到额度上限后暂停，额度恢复后继续
```

最终响应必须包含：

```text
files changed
commands run
test results
experiment results
subagent verdicts
unresolved risks
merge recommendation
git commit hash
push status
```
