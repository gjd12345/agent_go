# TOCC 历史记录与现有成果压缩版

日期：2026-06-08  
项目：`agent_go` / Official EOH + Literature-RAG + TOCC  
报告性质：阶段性压缩记录，用于导师沟通、后续 goal 继承和论文前材料整理。本文只写可追溯事实和谨慎结论，不写统计稳定或最终证明。

---

## 1. 一句话结论

当前项目已经从“人工给 EOH 加 RAG 上下文”推进到 **TOCC: Trace-Conditioned Operator-Card Controller**：

```text
run trace -> 诊断检索/生成偏差 -> 选择 operator cards + query -> EOH 实跑 -> 记录 trace / best code / outcome
```

核心发现是：**Literature-RAG 的关键变量不是是否注入 RAG，而是选中了哪些 operator cards**。默认检索可能无效甚至有害；targeted card selection 在 TSP 和 CVRP 上都观察到正向 best-score 信号。V2 已把规则诊断升级为 LLM proposer + rule gatekeeper 的 agent-assisted controller，但还需要最小 real-run 验证后才进入 V3 自动循环。

---

## 2. 历史演化压缩

| 阶段 | 产出 | 关键判断 |
|---|---|---|
| InsertShips / 自定义 harness | 从单个 `InsertShips()` 进化函数扩展到 C+L+V harness | 证明项目不只是单函数 prompt，而是可迁移实验框架 |
| Official EOH 对齐 | 对齐 `bp_online`、`tsp_construct`、`cvrp_construct` | 用官方 benchmark 避免只在自定义任务上自证 |
| Literature-RAG v0 | 构建 API cards + strategy cards + retriever + prompt context | RAG 链路能生效，但默认检索不一定带来收益 |
| TSP targeted RAG | 从 nearest cards 改为 regret + farthest | TSP 出现最强正向信号，历史 best=6.28736 |
| CVRP card 修复 | 从 capacity-first 修为 distance/far-first/regret | CVRP old cards 明显有害，targeted 后转正 |
| BP 诊断 | pure EOH 已自发生成 tight-fit / best-fit 族 | 当前没有 RAG 增益证据，但不能写 BP 不适合 RAG |
| TOCC V1 | 规则版 controller + manifest runner + summarizer + 记录规范 | 工程闭环跑通，selected_card_ids 能真实进入 RAG trace |
| TOCC V2 | LLM proposer + gatekeeper，commit `321790f` | 离线 3/3 诊断与 V1 一致，106 tests OK |

---

## 3. 工程成果

### 3.1 已提交主线

| commit | 内容 |
|---|---|
| `f455ccc` | TOCC automation framework goal |
| `e607991` | Phase 0: raw run gitignore + schemas |
| `e7a1e53` | Phase 1: TOCC V1 rule controller |
| `e968e7b` | Phase 2: manifest runner |
| `7eaf20b` | Phase 3: auto summarizer |
| `3939e6d`, `edaf4ba` | P1 修复：selected_card_ids、failure_reason、--no-run、gitignore、summarizer/tests |
| `0d3ff32` | Phase 4 TSP targeted smoke |
| `56b5613` | TOCC V2 framework + CVRP repeat=2 + readiness report |
| `321790f` | V2 agent endpoint handling + Python 3.9 compatibility |

### 3.2 当前核心模块

| 模块 | 作用 |
|---|---|
| `official_eoh_run.py` | official EOH runner，负责真实 LLM/EoH 实验 |
| `operator_card_controller.py` | TOCC V1 规则诊断与 card/query 推荐 |
| `run_experiment_manifest.py` | manifest 展开、dry-run、no-run、resume、force 门禁 |
| `summarize_manifest_runs.py` | 自动汇总 run_summary / rag_trace，生成中文报告 |
| `tocc_gatekeeper.py` | V2 proposal 安全与字段边界审查 |
| `tocc_agent.py` | V2 LLM proposer |
| `tocc_v2_pipeline.py` | V2 trace -> proposal -> gatekeeper pipeline |

---

## 4. 实验结果压缩

指标方向：越低越好。以下结论都是 exploratory best-score signal，不是统计稳定结论。

### 4.1 TSP Construct

| setting | best | valid | cards | 结论 |
|---|---:|---:|---|---|
| pure init pop4 | 6.83907 | 4/4 | - | baseline |
| default RAG init pop4 | 6.83954 | 4/4 | nearest_insertion, nearest_neighbor | 与 pure 策略重合，基本无增益 |
| targeted init pop4 | 6.51118 | 4/4 | regret, farthest | targeted 转正 |
| targeted repeats | 6.30547 / 6.50049 / 6.73293 | 4/4 | regret, farthest | repeat 级正向信号 |
| targeted gen4 pop8 | **6.28736** | 8/8 | regret, farthest | 当前 TSP 历史最优 |
| Phase 4 smoke | 6.47488 | 4/4 | regret, farthest | TOCC pipeline 端到端验证 |

TSP 的机制解释：默认 RAG 选中 nearest 族，和模型自发策略重合；targeted cards 引入 regret lookahead 和 farthest/isolation 信号，改变了生成代码结构。

### 4.2 CVRP Construct

| setting | best | valid | cards | 结论 |
|---|---:|---:|---|---|
| pure historical init | 13.20696 | - | - | historical baseline |
| old default RAG | 14.49387 | - | nearest_capacity, capacity_slack | capacity-first 方向有害 |
| fixed/default RAG | 13.28321 | 1/1 或 2/2 | far_first, nearest_capacity | 接近 pure，但容易退化成 recipe |
| targeted init historical | 13.03297 | 4/4 | regret, far_first | targeted 转正 |
| targeted gen4 pop8 | **12.82084** | 8/8 | regret, far_first | 当前 CVRP 历史最优 |
| Phase 4 smoke | 13.07835 | 4/4 | regret, far_first | TOCC pipeline 端到端验证 |
| Phase 4 repeat=2 targeted | 12.88600 / 12.92217 | 4/4 | regret, far_first | repeat=2 正向信号 |

CVRP 的机制解释：旧 cards 强调 capacity/slack，牺牲总路线距离；targeted cards 把 far-first seeding 与 regret-aware selection 结合起来，能改变模型偏差。

### 4.3 BP Online

| setting | best | cards | 结论 |
|---|---:|---|---|
| pure_eoh | 0.03984 | - | baseline 已较强 |
| api_only | 0.03984 | - | 无差异 |
| default RAG | 0.03984 | best_fit, first_fit | 与 pure 策略重合 |
| targeted residual | 0.03984 | util_sqrt_exp, residual_poly | 当前 budget 下未突破 |

BP 只能写“当前没有 RAG 增益证据”。不能写“BP 不适合 RAG”。

---

## 5. TOCC V1 / V2 / V3 边界

```text
V1 rule controller:
trace -> hardcoded rules -> diagnosis -> cards/query

V2 agent-assisted controller:
trace -> LLM proposer -> proposal JSON -> rule gatekeeper -> human/bounded runner

V3 auto-loop controller:
trace -> proposer -> gatekeeper -> runner executes -> observe new trace -> repeat
```

V2 的 agent 不是全自动 autonomous agent。准确说法是：

> TOCC V2 uses an LLM as a trace-conditioned proposer, constrained by a rule-based gatekeeper. It is an agent-assisted controller rather than a fully autonomous experimental agent.

当前 V2 状态：

| 项 | 状态 |
|---|---|
| V1 闭环稳定 | PASS |
| V2 LLM proposer | PASS，离线 3/3 与 V1 一致 |
| V2 gatekeeper | PASS，无越权字段，无违规执行 |
| tests | PASS，106 tests OK |
| latest commit | `321790f` |
| 下一步 | V2 agent proposal real-run validation |

---

## 6. 当前最重要的研究资产

| 文件 | 用途 |
|---|---|
| `.codex/goals/tocc_automation_framework.md` | 当前目标与 V2/V3 准入规则 |
| `AGENTS.md` | L 级多 agent 工作流、实验分级 E0-E5、exploration_analyst 规则 |
| `eoh_go_workspace/local_notes/official_eoh_literature_rag_final_report_20260606.md` | TSP/CVRP/BP 阶段性实验总报告 |
| `eoh_go_workspace/reports/auto_experiment_reports/phase4_smoke/summary.md` | Phase 4 TSP/CVRP smoke 自动汇总 |
| `eoh_go_workspace/reports/auto_experiment_reports/tocc_v2_readiness_report.md` | V2 就绪判断 |
| `eoh_go_workspace/reports/auto_experiment_reports/tocc_best_code_records.md` | 历史最优和 Phase 4 best code 记录 |
| `eoh_go_workspace/reports/auto_experiment_reports/phase4_smoke/card_decisions.jsonl` | Phase 4 选卡理由与 outcome |

---

## 7. 当前不能夸大的地方

禁止或需要避免的表述：

```text
TOCC 已证明有效
RAG 一定有效
CVRP 稳定优于 pure
gen4 是 sweet spot
BP 不适合 RAG
V2 已完成自主 agent 闭环
V3 可以直接自动跑大矩阵
```

允许的谨慎表述：

```text
TOCC V1 端到端工程闭环已验证。
TOCC V2 LLM proposer + gatekeeper 离线闭环已验证。
TSP targeted card selection 已有 repeat 级正向 best-score 信号。
CVRP targeted card selection 已有 repeat=2 正向 best-score 信号。
当前证据支持把 RAG 研究重点从“是否注入上下文”转为“如何选择 operator cards”。
```

---

## 8. 下一步建议

最值得做的是 **V2 agent 推荐 card set 的最小实跑验证**，而不是直接做 V3 或扩大论文矩阵。

建议范围：

| problem | runs | 目的 |
|---|---:|---|
| TSP | 1 | 验证 V2 proposal -> runner -> trace 链路 |
| CVRP | 2 | 验证 V2 对 capacity / far_first bias 的纠偏是否能落到实跑 |
| optional guard | 1 | 只在 card mismatch、failure_reason 或 valid collapse 时补 |

验收标准：

```text
proposal.selected_card_ids == rag_trace.rag_selected_items
failure_reason is null
run_summary.ok is true
valid_candidates >= 1
best score 落在已知正向区间附近；若没有，写 inconclusive，不写失败或稳定
```

V3 auto-loop 的准入条件：

```text
V2 proposals 已固化并可追溯 source trace
gatekeeper 对所有 proposal 给出 accepted/rejected/stripped
至少 3 个 bounded real runs 无 card mismatch
V2 validation report 区分 diagnosis correctness / gatekeeper safety / runner linkage / objective signal
P0/P1 为 0
```

---

## 9. 面向导师汇报的压缩话术

我们现在不把 RAG 当作一个“加不加上下文”的开关，而是把它抽象成 operator-card selection 问题。实验显示，默认检索会选到和模型自发策略重合甚至方向错误的 cards；TSP 中 nearest cards 无增益，CVRP 中 capacity-first cards 反而变差。把 cards 定向切换到 regret + farthest / far_first 后，TSP 和 CVRP 都观察到正向 best-score 信号。

工程上，V1 已经实现 trace -> rule diagnosis -> selected cards -> manifest runner -> EOH -> trace -> summarizer 的闭环。V2 进一步把规则诊断替换为 LLM proposer，并用 rule gatekeeper 限制其只能提出 diagnosis/cards/query，不能控制预算、执行命令或写文件。当前 V2 离线诊断与 V1 规则版 3/3 一致，106 tests OK。下一步只需要做 3 个左右 bounded real runs，验证 agent proposal 能真实落到 runner 和 trace，再决定是否进入 V3 自动循环。

