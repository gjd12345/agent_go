/goal: TOCC Tool-Using Research Agent

目标：把当前 TOCC 从“trace-conditioned card selector”推进为一个可审计的 tool-using research agent。短期重点不是扩大问题数量，而是提高每一层工具调用和实验闭环的成功率，并把 CVRP 正向信号、TSP 方差诊断、BP 边界案例整理成可支撑 CCF-B 论文雏形的证据链。

报告一律写中文。API key 不读取、不打印、不 echo；如需确认，只输出布尔值。raw run、population、samples、run log 不入 git。允许入 git 的只有 manifest、summary、整理后的报告、card decision、card memory、best-code records、literature notes、goal 文档。

---

## 0. 当前定位

TOCC 的论文定位暂定为：

```text
Trace-conditioned operator-card selection for steering LLM-based heuristic evolution.
```

TOCC 不是替代 EOH，不是普通 RAG，不是 fully autonomous ReAct agent。TOCC 是：

```text
a tool-using, trace-conditioned research controller for heuristic evolution experiments.
```

核心闭环：

```text
run trace
-> diagnosis
-> operator-card selection + query
-> gatekeeper
-> manifest runner
-> official EOH execution
-> summarizer + best-code record
-> next trace
```

---

## 1. 当前证据等级

| Problem | 当前证据 | 允许结论 |
|---|---|---|
| CVRP | `tocc_corrected` repeat 中 3/3 优于 pure，均值约 12.970 vs 13.596；但单轮结果存在 12.738 -> 12.888 -> 13.283 的下降趋势，r3 与 default degenerate 值重合 | 当前最可靠 repeat-level positive signal，但需要扩 repeat 并检查 r3 trace |
| TSP | V2 best=6.217，repeat 中出现 6.189 新低，但均值受 9.656 outlier 影响 | 有 best-score 潜力，但方差未稳 |
| BP/OBP | pure/default/targeted 当前均未突破 0.03984 | 当前没有 RAG 增益证据，可作为边界案例 |

禁止写：

```text
TOCC 已证明有效
RAG 一定有效
TSP/CVRP 统计稳定提升
BP 不适合 RAG
V3 可以直接自动跑大矩阵
```

---

## 2. Tool-Using Agent 定义

### 2.1 工具集

| Tool | 当前模块/资产 | 成功标准 |
|---|---|---|
| Trace Reader | `run_index.json`, `official_eoh_run_summary.json`, `rag_trace` | 正确读取 objective、valid rate、cards、failure reason |
| Card Selector | `operator_card_controller.py`, `tocc_agent.py` | 输出 problem-matched selected_card_ids 和 query |
| Gatekeeper | `tocc_gatekeeper.py` | 拒绝 forbidden fields、预算越权、错误 problem prefix |
| Manifest Runner | `run_experiment_manifest.py`, `official_eoh_run.py` | 按 proposal 执行 bounded run |
| Summarizer | `summarize_manifest_runs.py` | 产出 summary、card decisions、best code、success funnel |

### 2.2 Agent 权限边界

LLM proposer 只能输出：

```text
diagnosis
selected_card_ids
rag_query
rationale
expected_effect
confidence
```

Schema 固定为以上 6 个字段。discussion report、gatekeeper、summarizer 必须使用同一口径；不得在报告中简化成 4 字段。

LLM proposer 不能输出或控制：

```text
budget
shell command
API key
git operation
output path deletion
raw artifact retention
model credential
```

所有可执行动作都必须通过 `tocc_gatekeeper.py` 和 manifest runner。

---

## 3. Agent 成功率漏斗

每次 agent-run 必须记录五层成功率。

```json
{
  "diagnosis_success": true,
  "proposal_accept": true,
  "linkage_success": true,
  "generation_success": true,
  "objective_success": false
}
```

可计算定义：

| 指标 | 成功条件 |
|---|---|
| `diagnosis_success` | diagnosis 至少引用 3 项可复核 trace 证据，例如 best objective、valid candidates、selected cards、failure_reason、context truncation、baseline overlap；引用事实必须与 trace/summary 一致 |
| `proposal_accept` | proposal 通过 gatekeeper，且只包含 6 个允许字段 |
| `linkage_success` | proposal selected_card_ids 与 rag_trace.rag_selected_items 中实际注入的 algorithm_card ids 一致 |
| `generation_success` | valid_candidates >= max(2, ceil(0.5 * population_size))；若 manifest 明确配置 target-specific threshold，则使用 manifest 阈值；seed-only / init-only 不算成功 |
| `objective_success` | best objective 优于 pure、default 或上一轮 reference；必须同时标注 reference 来源，避免把 seed-only 或 degenerate run 当成提升 |

Summary report 必须同时展示 objective 和 success funnel。不能只看 best score。

---

## 4. 文献调研任务（已完成）

详细阅读笔记见 `eoh_go_workspace/reports/paper_notes/` 目录。

### 4.1 必读文献 — 回答

| Paper | 重点问题 | 回答 |
|---|---|---|
| CO-Bench, 2025 | LLM agents 在组合优化 algorithm search 中如何评测 | **评测维度**：Avg Score（与最优解的归一化比值）、Valid Solution（全实例无错的问题比例）、Above Classical（超越经典求解器率）、Survival Rate（得分高于参考 99% 的实例比例）。**框架**：36 个 CO 问题（8 大类）、6482 实例、9 种 agent 框架（含 FunSearch/EoH/ReEvo/MCTS-AHD）、15 个 LLM。**关键发现**：FunSearch 达 0.842 avg score 超越经典求解器 0.797；在 36 个问题中的 25 个上超越经典求解器；但有效解率仍落后（0.555 vs 0.611）；LLM 擅长应用已知技术而非发明新方法。 |
| HeuriGym, 2025 | agentic heuristic generation 如何定义通过率和质量 | **通过率**：SOLVEs@i = 在前 i 次迭代中通过阶段 s（执行/解生成/验证）的实例比例。**质量**：QUALITY = LLM 解代价/专家解代价（capped at 1），仅在通过验证的实例上计算。**综合指标**：QYI = Quality × Yield（Yield = 通过验证的实例比例），专家 QYI=1.0。**关键发现**：最佳模型（Gemini-2.5-Pro）QYI=0.62，仅为专家的 62%；迭代优化至关重要（10 轮 vs 1 轮提升 40%+）；故意排除 TSP/SAT 等经典问题防记忆污染。 |
| HeurAgenix, 2025 | LLM hyper-heuristic selector 与 TOCC 的区别 | **HeurAgenix**：两阶段框架——(1) 启发式进化（种子生成→扰动→LLM 精炼→多轮迭代），(2) 动态选择（问题状态特征→LLM/GRPO 微调的选择器）。选择对象是**可执行代码**，选择依据是**问题状态特征**，核心能力是**生成+进化+选择三位一体**。**与 TOCC 的关键差异**：TOCC 选择的是**预定义的策略卡（非可执行代码）**，选择依据是**执行轨迹（trace）而非静态状态**，TOCC 不生成新策略而是将已有知识注入 LLM prompt。HeurAgenix 需要 RL 微调选择器，TOCC 是检索匹配。 |
| CoEvo-AHD, 2026 | tool-invocation environment library 如何封装 local-search delta | **详见 §4.2**。核心：将计算密集型底层操作（2-opt delta、完整目标评估、贪心重建）封装为环境库中的可信计算内核，LLM 生成的算子通过 `problem_data['env']` 调用，只关注高层邻域设计和分量协调逻辑。消融实验证明去掉工具增强环境导致 TTP50 性能下降 5.5%。 |
| A2DEPT, 2026 | evolutionary program tree 与结构化 AHD 的关系 | **核心贡献**：从模板绑定的 AHD（组件级调优）转向开放式 AAD（系统级完整求解器设计）。**进化程序树**：全局搜索树组织程序空间，每个节点 = (程序, 评分, 算子历史, 局部算子权重)。**分层算子**：微调（局部编辑）/ 宏变异（重写工作流）/ 语义交叉（双父代合成），配合自适应调度。**可执行性保证**：不靠模板约束，靠反馈驱动的依赖修复（调用图分析 + 迭代 LLM 提示）。**结果**：在 CFLP/CVRP/FJSP/MIS 上平均降低 9.8% 归一化优化间隙。**与 EoH 的关键差异**：EoH 是扁平的思维-代码对种群 + GA 风格提示；A2DEPT 是树结构搜索 + 分层算子 + 自适应调度 + 程序维护循环。 |

### 4.2 CoEvo-AHD 对照问题 — 已回答

**Q1: tool-invocation environment library 包含哪些 primitive？**

```text
TTP: {Evaluate, Fast2OptDelta, GreedyPack}
TPP: {Evaluate, GreedyPurchase, CityValueAnalysis, DropCityEval}

通用原语类别：
- objective evaluation（目标评估）
- feasibility checking（可行性检查）
- repair/reconstruction（修复/重建）
- greedy construction（贪心构造）
- structural analysis（结构分析）
- local move evaluation（局部移动评估）
```

**Q2: local-search delta computation 如何被封装？**

```text
封装为 env.fast_2opt_delta(route, pack_plan, i, j) 可调用函数。
LLM 生成的算子直接调用，不需要自己实现 2-opt delta 循环。

论文原文："The environment exposes stable and frequently used primitives...
enabling LLM-generated operators to use standardized interfaces instead of
reimplementing inefficient and error-prone problem-specific loops."

策略：将计算密集型且易出错的底层操作封装为可信计算内核，
LLM 只关注高层邻域设计和分量协调逻辑。
```

**Q3: LLM-generated operators 如何调用这些工具？**

```text
1. 统一接口签名：route_operator(route, pack_plan, problem_data)
2. 通过 problem_data['env'] 访问环境对象
3. Prompt 中明确告知："Use the exposed environment tools when available."
4. 验证流水线：语法→接口→有界执行→可行性，通过后才能进入种群
```

**Q4: 它评估的是 operator implementation success，还是 experiment-control success？**

```text
评估的是 experiment-control success（解质量/优化性能），不是 operator implementation success。

- 主要指标：TTP/TPP 测试实例上的解质量，与传统启发式（MATLS、S5、CoCo 等）对比
- 算子实现成功只是预筛选机制（验证流水线），不是评估目标
- 消融实验证明的是框架组件对解质量的贡献
- 奖励/信用分配基于算子对完整解的改进幅度
```

**Q5: TOCC 如何避免与它的贡献重复？（已确认边界）**

```text
已确认边界（primary-source reading 完成后）：

CoEvo-AHD 的贡献：
  - 双种群协同进化框架（双分量耦合 CO）
  - 工具增强环境库（封装底层计算原语）
  - 共享信息记忆（跨分量信号传递）
  - 评估的是算子实现质量对解质量的影响

TOCC 的贡献：
  - trace-conditioned card selection（基于执行轨迹的策略卡选择）
  - experiment-control primitives（实验控制原语：manifest runner、gatekeeper、summarizer）
  - RAG 注入策略知识到 LLM prompt（不改变算子实现，改变生成分布）
  - 评估的是 card selection 对 init sampling 分布的影响

关键差异：
  - CoEvo-AHD 改变"算子如何实现"（给算子提供工具）
  - TOCC 改变"LLM 如何生成"（给 LLM 提供策略知识）
  - 两者正交，不重复，可组合（TOCC cards + CoEvo-AHD tools）
```

---

## 5. 实验推进原则

### 5.1 白天探索，夜间运行

每日节奏：

```text
Morning:
  read nightly summaries
  update success funnel
  inspect best code and failure code
  write observation notes

Afternoon:
  diagnose trace
  update card/query/proposal rules
  update reports, goal, manifests
  prepare nightly batch

Night:
  run bounded batch
  priority 1: CVRP repeat
  priority 2: TSP outlier
  priority 3: Mixer/Knapsack/SplitOrders smoke
```

### 5.2 夜间 batch 优先级

| Priority | Batch | 目的 |
|---|---|---|
| 1 | CVRP `pure/default/tocc_corrected` repeat 5 或 10 | 稳定主正例 |
| 2 | TSP `tocc_corrected` fixed cards repeat | 诊断 outlier 和方差 |
| 3 | V2/V3 agent-selected vs manual targeted | 衡量 agent 选卡成功率 |
| 4 | Mixer / Knapsack / SplitOrders smoke | 验证迁移，不追求效果 |

### 5.3 实验分级

按 `AGENTS.md`：

| Exp Tier | 用途 | 规则 |
|---|---|---|
| E0 | 报告整理、best code、card decision | 自动 |
| E1 | dry-run、manifest validation、summary regen | 自动 |
| E2 | smoke run, `gen <= 1`, `runs <= 2` | 本地安全检查后可跑，付费 API 最好确认 |
| E3 | repeats 3-20, `gen <= 1` | 需要明确确认 |
| E4 | deep evolution 或 runs > 20 | 需要计划、监控、确认 |
| E5 | paper-level matrix | 分阶段 milestone gate |

### 5.4 实验算子规则（强制）

**背景**：2026-06-09 发现，所有历史 manifest 的 `operators` 字段均为 `"i1"`，导致所有实验本质上是 repeated independent sampling（独立发明），而非真正的进化。EoH 库的默认算子是 `['e1', 'e2', 'm1', 'm2']`（exploratory crossover + exploitation crossover + mutation + parameter mutation），但 manifest runner 的每一层默认值都被硬编码为 `"i1"`，从未触达库默认值。

**规则**：

```text
1. 所有声称 "进化" 或 "evolution" 的实验，operators 必须包含至少一个 crossover 算子（e1 或 e2）和至少一个 mutation 算子（m1 或 m2）。
2. 推荐默认算子组合：--operators "e1,e2,m1,m2"（即 EoH 库原生默认）。
3. 如果实验目的是对比 i1-only vs 进化，必须在同一个 manifest 中同时包含两个 arm，且用相同的 pop_size / generations / repeats。
4. 纯 init-only 实验（generations=[0]）可以用 i1，但不得在报告中称为 "进化"，应称为 "init sampling"。
5. manifest 中 operators 字段不得省略——省略时 runner 默认为 i1，容易误跑。
```

**禁止写**：

```text
"TOCC 提升了进化质量"（如果实验只用了 i1）
"evolution rate"（如果每一代都是独立采样，没有 crossover/mutation）
"进化收敛"（如果 operators 只有 i1）
```

---

## 6. 后续实验规划

详细计划见 `eoh_go_workspace/experiments/EXPERIMENT_PLAN_20260609.md`。

### Phase 1: 真正进化验证（P0，夜间执行）

| 实验 | 问题 | operators | repeats | 目的 |
|------|------|-----------|---------|------|
| Exp 1.1 | TSP | e1,e2,m1,m2 | 3 | TOCC cards 在进化下是否仍优于 pure |
| Exp 1.2 | CVRP | e1,e2,m1,m2 | 5 | 同上（CVRP 是主正例） |
| Exp 1.3 | 对比分析 | — | — | i1-only vs e1,e2,m1,m2 的进化轨迹 |

### Phase 2: TSP Outlier 诊断（P1，白天执行）

| 实验 | 目的 |
|------|------|
| Exp 2.1 | 诊断 9.66 outlier 根因（init 代码、eval 超时、RAG 截断） |
| Exp 2.2 | TSP init 分布分析（8 个 tocc init 的代码差异） |

### Phase 3: 扩展验证（P2，条件执行）

| 实验 | 条件 | 目的 |
|------|------|------|
| Exp 3.1 pop=8 | Phase 1 有效 | 更大 pop 是否缓解方差 |
| Exp 3.2 更多 repeats | Phase 1 promising | 统计显著性 |
| Exp 3.3 新问题 | Phase 1 有效 | 泛化验证（Knapsack/FJSP/MIS） |

### 已创建的 manifest

```text
eoh_go_workspace/experiments/manifests/tocc_day2_tsp_real_evolution_gen4.json  (TSP, e1,e2,m1,m2, n=3)
eoh_go_workspace/experiments/manifests/tocc_day2_cvrp_real_evolution_gen4.json (CVRP, e1,e2,m1,m2, n=5)
```

---

## 7. 两周推进计划

| Day | 白天任务 | 夜间任务 |
|---:|---|---|
| 1 | 历史回填：完成讨论报告和本 goal；建立文献阅读清单 | CVRP repeat 5 batch |
| 2 | 历史回填 + 新增：分析已有 CVRP repeat；加入 success funnel 字段 | TSP outlier repeat |
| 3 | 历史回填：抽取已有 TSP/CVRP best code 和 failure code | CVRP agent-selected vs manual targeted |
| 4 | 写 rule controller vs LLM proposer 对比 | TSP gen=1 small repeat |
| 5 | 完成 CoEvo-AHD 中文阅读笔记 | Mixer/Knapsack smoke |
| 6 | 更新 TOCC architecture diagram 和伪代码 | CVRP 补齐 repeat |
| 7 | 周总结：证据等级、失败模式、下一周计划 | 只跑缺失/失败补丁 |
| 8 | 设计并实现 tool-use success logging | 验证 logging completeness |
| 9 | 设计 V3 bounded correction case | V3 correction smoke |
| 10 | 分析 V3 correction，更新 card memory | CVRP/TSP targeted repeat |
| 11 | 写 related work 草稿 | 可选迁移 smoke |
| 12 | 写 method formalization 草稿 | 低成本补丁 run |
| 13 | 整理导师汇报 PPT/中文报告 | 最后一轮补实验 |
| 14 | 周汇报复盘，决定是否进入 paper-level matrix | 暂停或挂长期 batch |

---

## 8. 交付物

### 8.1 文档

```text
eoh_go_workspace/reports/auto_experiment_reports/tocc_tool_using_research_agent_discussion_20260609.md
.codex/goals/tocc_tool_using_research_agent.md
```

### 8.2 后续建议新增

```text
eoh_go_workspace/reports/paper_notes/coevo_ahd_reading_note_cn.md
eoh_go_workspace/reports/paper_notes/llm_co_agent_related_work_matrix.md
eoh_go_workspace/reports/auto_experiment_reports/tocc_agent_success_funnel_report.md
eoh_go_workspace/reports/figures/tocc_tool_using_agent_architecture_v1.drawio
```

---

## 9. AGENTS.md 审查要求

本 goal 后续所有任务按以下方式执行：

| 任务 | Tier | Agent path |
|---|---|---|
| 文献阅读、报告整理 | S/E0 | scout -> implementer -> verifier |
| success funnel schema / summarizer 改动 | M/E1 | scout -> implementer -> gatekeeper -> verifier |
| RAG/card selection 逻辑改动 | L/E1 | scout -> rag_researcher -> implementer -> gatekeeper -> verifier |
| paid API smoke | L/E2 | scout -> exploration_analyst -> gatekeeper -> verifier |
| repeat batch | L/E3 | scout -> exploration_analyst -> gatekeeper -> verifier |
| paper-level matrix | L/E5 | full milestone review |

P0/P1 阻塞完成。`implementer` 不能自审。`exploration_analyst` 只读，不执行、不写文件、不读取 key。

---

## 10. 验收标准

### 10.1 短期验收

```text
1. 本 goal 和讨论报告存在，并用中文写清楚研究主线。
2. 文献调研至少覆盖 CO-Bench, HeuriGym, HeurAgenix, CoEvo-AHD。
3. Tool set 和 agent success funnel 定义明确。
4. 每日推进计划可执行。
5. AGENTS.md 审查边界明确。
```

### 10.2 研究验收

```text
1. CVRP repeat-level signal 是否稳定。
2. TSP outlier 是否被归因。
3. Agent success funnel 是否能解释失败层级。
4. TOCC 与 CoEvo-AHD / HeuriGym / CO-Bench 的贡献边界是否清楚。
5. 是否可以进入 paper-level matrix。
```

### 10.3 禁止状态

```text
1. 未记录 selected cards 就跑实验。
2. 未记录 best code 就写策略变化。
3. 未记录 success funnel 就声称 agent 有效。
4. 未做 repeat 就写稳定提升。
5. agent 直接控制预算、命令或文件删除。
```
