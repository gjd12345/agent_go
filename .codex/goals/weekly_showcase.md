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
