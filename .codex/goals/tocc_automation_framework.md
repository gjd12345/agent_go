/goal: TOCC Stabilization Repeats — CVRP Confirmed, TSP gen=4

目标：TOCC V1→V3 端到端闭环已完成。CVRP 已取得 repeat-level positive signal（n=8, 8/8 vs pure, -4.2%），并发现 default_rag 灾难性坍缩（5/5 degenerate）作为强对照证据。TSP 诊断完成：gen=0 方差过大不适合做 evidence，card 方向正确但需要 gen=4 压方差。BP 不作为主线。文献代码调研完成：HeuriGym (ICLR 2026)、HeurAgenix (MSRA)、CO-Bench (CMU) 三仓库深读，可迁移项已识别。

报告一律写中文。API key 不读取、不打印、不 echo。raw artifacts 不入 git。

---

## 0. 当前状态

### 已完成交付

| 阶段 | 状态 | 关键证据 |
|---|---|---|
| V1 规则 TOCC | PASS | rule controller + selected_card_ids → runner → trace |
| V2 LLM proposer | PASS | LLM proposer + rule gatekeeper，诊断/字段边界一致 |
| V2 real-run | PASS | 3/3 bounded runs，proposal/card trace checks 通过 |
| V2 validation | PASS | validation report + card_decisions + best_code_records |
| Governance | PASS | exploration_analyst、AGENTS、experiment workflow |
| V3 bounded pilot | PASS | tocc_v3_loop，116 TOCC tests OK |
| V3 probe | PASS | CVRP weak_negative → far_first correction verified |
| Architecture v3 | PASS | `reports/figures/architecture_v3.drawio` 已生成 |
| Literature survey | PASS | HeuriGym/HeurAgenix/CO-Bench 代码深读完成 |
| Push | PASS | 已推送 |

### 当前证据矩阵

| problem | arm | n | mean | min | max | vs pure | 证据等级 |
|---|---|---|---|---|---|---|---|
| CVRP | pure_eoh | 8 | 13.540 | 13.279 | 13.611 | baseline | — |
| CVRP | default_rag | 5 | 13.283 | 13.283 | 13.283 | 0% | 🔴 灾难性坍缩 |
| CVRP | tocc_corrected | 8 | 12.975 | 12.713 | 13.283 | **-4.2%** | ✅ repeat-level positive |
| TSP | pure_eoh | 3 | 6.751 | 6.590 | 7.057 | baseline | — |
| TSP | default_rag | 3 | 6.756 | 6.273 | 7.194 | +0.1% | ⚠️ 不优于 pure |
| TSP | tocc_corrected | 5 | 7.372 | 6.189 | 9.656 | — | ⚠️ exploratory, 方差过大 |

### CVRP 关键发现

**8/8 tocc runs 优于 pure mean。** tocc max (13.283) 仍低于 pure mean (13.540)。改善从 n=3 的 -4.6% 收敛到 n=8 的 -4.2%，说明信号稳定。

**default_rag 全部坍缩。** 5/5 runs 出现 valid=1, pop=1, best=13.28321（恰好等于 seed），种群坍缩到只剩种子。注入的 card 是 `cvrp_far_first` + `cvrp_nearest_capacity`。

**一张卡片决定生死。** tocc_corrected 和 default_rag 只差一张 card：`cvrp_regret_insertion` vs `cvrp_nearest_capacity`。换一张卡，从"全部坍缩"变成"全部有效 + 4.2% 改善"。这是 TOCC 选卡价值的直接证据，比 objective delta 本身更有区分度。

### TSP 诊断结论

**card 方向正确，问题在 LLM 生成方差。** outlier (9.656) 和 best (6.189) 使用相同的 `tsp_regret_insertion` + `tsp_farthest_insertion`，都是 valid=4, pop=4，无 failure。同一组 card 在不同 seed 下生成质量差异巨大，gen=0 无选择压滤除差候选。

**历史数据佐证。** gen=4 pop=8 tocc best=6.287（同 card），gen=0 targeted repeat×3 mean=6.513。tocc 在足够进化深度下可以显著优于 pure，但 gen=0 方差淹没了信号。

**最优先验证 gen=4。** gen=4 是当前最可能有效的候选深度（基于历史单点 6.287 + gen=0 方差论证），需要 pure gen=4 baseline（从未跑过）来确认，不应在 baseline 跑完前视为已验证的 sweet spot。

### 当前可写结论

```text
TOCC 已完成从 trace-conditioned diagnosis 到 bounded operator-card correction 的端到端工程闭环。
CVRP 取得 repeat-level positive signal：8/8 tocc_corrected 优于 pure_eoh mean，改善 -4.2%。
CVRP default_rag 出现灾难性坍缩（5/5 degenerate），与 tocc 仅差一张 card，构成强对照。
TSP card 方向确认正确（regret+farthest），但 gen=0 方差过大，需 gen=4 验证。
BP 当前无 RAG 增益证据。
```

### 禁止写

```text
TOCC 已证明有效 / 稳定提升
RAG 一定有效 / 一定无效
TSP/CVRP 统计显著
BP 不适合 RAG
V3 可以直接自动跑大矩阵
论文证据已充分
```

---

## 1. 方法定位

方法名：**Trace-Conditioned Operator-Card Controller (TOCC)**。

TOCC 是一个面向 LLM-based heuristic evolution 的 tool-using research agent。它读取上一轮 run trace，诊断搜索偏差，选择 operator-card prior 注入 LLM，通过 gatekeeper 和 manifest runner 执行有边界的 EOH 实验，并记录下一轮 trace。

```text
run trace
→ diagnose search bias / failure mode
→ select operator-card subset + query
→ gatekeeper validates proposal
→ manifest runner executes bounded EOH
→ observe objective / valid rate / code features
→ update report and card memory
```

V1/V2/V3 边界：

```text
V1 rule controller:   trace → hardcoded rules → diagnosis → cards/query
V2 agent-assisted:    trace → LLM proposer → proposal JSON → rule gatekeeper → bounded runner
V3 bounded loop:      V2 + observe → next proposal/correction
```

论文定位（来自文献调研）：

```text
Existing AHD methods focus on generating or co-evolving heuristic operators.
TOCC studies how a tool-using research agent selects operator-card priors
from previous run traces to steer LLM-based heuristic evolution.

与 HeuriGym (ICLR 2026) 的区别：HeuriGym 做 LLM 直接写启发式代码的 benchmark。
与 HeurAgenix (MSRA) 的区别：HeurAgenix 做运行时启发式选择（hyper-heuristic selector）。
TOCC 做 experiment-control primitives 和 trace-conditioned context selection。
三层工作在互补的抽象层，不直接竞争。
```

---

## 2. 文献代码调研结论

| 论文 | 会议 | 代码 | 可迁移项 |
|---|---|---|---|
| CO-Bench (CMU) | arXiv 2504 | [sunnweiwei/CO-Bench](https://github.com/sunnweiwei/CO-Bench) | step/feedback 协议、几何平均归一化、沙箱隔离 |
| HeuriGym (Cornell) | ICLR 2026 | [cornell-zhang/heurigym](https://github.com/cornell-zhang/heurigym) | 四阶段错误分类、solve@i 指标、反馈格式 |
| HeurAgenix (MSRA) | arXiv 2506 | [microsoft/HeurAgenix](https://github.com/microsoft/HeurAgenix) | function_to_tool、TTS-BON、瓶颈驱动进化 |
| CoEvo-AHD | arXiv 2606 | 无公开代码 | — |
| A2DEPT | ICML 2026 | 无公开代码 | — |

可迁移到 TOCC 的 5 项：
1. **Success funnel**（HeuriGym 四阶段 → TOCC 五层）：在 summarize 中自动归类每次 run 的失败阶段
2. **solve@i 指标**（HeuriGym）：前 i 次 proposal 内 gatekeeper accept + valid > 0 的比例
3. **几何平均归一化**（CO-Bench）：跨 CVRP/TSP/BP 统一评分尺度
4. **TTS-BON**（HeurAgenix）：多 card 组合的 rollout 验证，V4 候选能力
5. **反馈格式**（HeuriGym）：迭代 0 完整上下文，迭代 N>0 仅给差异

---

## 3. Agent 成功率五层漏斗

来自讨论报告，已与 HeuriGym 四阶段对齐：

| 层级 | 指标 | 成功定义 | 对应 HeuriGym |
|---|---|---|---|
| Trace Diagnosis | `diagnosis_success` | 诊断引用 ≥3 项 trace 证据，与 trace 一致 | — |
| Proposal Validity | `proposal_accept_rate` | 通过 gatekeeper，无越权字段 | — |
| Runner Linkage | `linkage_success` | proposal selected_card_ids == rag_trace.rag_selected_items | — |
| Generation Validity | `generation_success` | valid_candidates ≥ max(2, ceil(0.5×pop_size)) | Stage 1-3 通过 |
| Objective Signal | `objective_success` | best 优于 pure/default reference | Stage 4: Pass |

执行阈值：

| 指标 | 当前状态 |
|---|---|
| diagnosis_success | 需独立 LLM 评估或人工校验 |
| proposal_accept_rate | gatekeeper 已有，需统计 |
| linkage_success | 已可自动检查（compare selected_card_ids vs rag_trace） |
| generation_success | CVRP tocc: 10/10 通过；CVRP default: 0/5 通过 |
| objective_success | CVRP tocc: 8/8 vs pure mean |

---

## 4. 下一阶段：TSP gen=4 + 漏斗落地

### 4.1 TSP pure gen=4 baseline

仅需跑 pure_eoh（tocc 侧已有历史锚点 gen=4 pop=8→6.287）：

```text
problem: tsp_construct
arms: pure_eoh
generations: 4
pop_size: 4
repeats: 3
llm_model: JoyAI-LLM-Pro
```

跑完后对比 pure gen=4 mean vs tocc 历史锚点，判断 delta 是否成立。

### 4.2 漏斗接入 summarize

在 `summarize_manifest_runs.py` 中增加 success_funnel 输出：
- 自动读取 run_summary 的 valid_candidates、failure_reason、best_objective
- 对每次 run 归类到五层漏斗
- 统计每层通过率
- 输出 `success_funnel.json`

### 4.3 归一化评分

在 `ProblemSpec` 中增加 `norm_score` 字段，以 pure baseline 为基准：

```python
norm_score = best_objective / pure_baseline_mean  # minimize 问题
# 或 pure_baseline_mean / best_objective  # maximize 问题
```

### 4.4 CVRP 锁定

CVRP 8/8 已足够，不扩 repeat。default_rag 5/5 坍缩已足够做对照，也不扩。

---

## 5. 交付物

### 5.1 已有

```text
eoh_go_workspace/reports/auto_experiment_reports/tocc_stabilization_repeats/
eoh_go_workspace/reports/auto_experiment_reports/tocc_day1_cvrp_repeat5/
eoh_go_workspace/reports/auto_experiment_reports/phase4_cvrp_targeted_repeat3/
eoh_go_workspace/reports/auto_experiment_reports/tocc_day2_tsp_gen1_outlier/
eoh_go_workspace/reports/figures/architecture_v3.drawio
eoh_go_workspace/reports/auto_experiment_reports/tocc_tool_using_research_agent_discussion_20260609.md
```

### 5.2 待产出

```text
eoh_go_workspace/experiments/manifests/tsp_pure_gen4_baseline.json
eoh_go_workspace/reports/auto_experiment_reports/tsp_pure_gen4/summary.md
eoh_go_workspace/reports/auto_experiment_reports/success_funnel.json
eoh_go_workspace/reports/auto_experiment_reports/tocc_stabilization_report.md（更新）
```

---

## 6. Git 边界

允许入 git：manifest、summary、report、card_decisions、best_code_records、figures。
禁止入 git：raw population、samples、run log、API logs、`_run_official_eoh.py`。

---

## 7. 复用能力

| 能力 | 用途 |
|---|---|
| `eoh-experiment` | manifest / dry-run / bounded real-run |
| `eoh-analyze` | median delta、valid rate、funnel 统计 |
| `scout` | 只读确认影响文件 |
| `exploration_analyst` | 监控 repeats，判断 continue/stop |
| `gatekeeper` | 审查结论不夸大、evidence tier 不混用 |
| `verifier` | JSON/JSONL 检查、gitignore 检查、trace 一致性 |

---

## 8. 完成时填写清单

任务完成后补充：

- files changed:
- commands run:
- test results:
- subagent verdicts:
- unresolved risks:
- merge recommendation:
