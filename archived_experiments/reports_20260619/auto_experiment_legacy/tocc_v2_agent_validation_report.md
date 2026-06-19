# TOCC V2 Agent Validation Report / V2 Agent 验证报告

日期：2026-06-08

---

## 1. diagnosis_correctness / 诊断准确性

V2 LLM proposer 对 3 个 trace 的诊断：

| source trace | V2 agent diagnosis | V1 rule diagnosis | 一致 |
|---|---|---|---|
| TSP default (nearest cards) | baseline_overlap | baseline_overlap | ✅ |
| CVRP old (capacity cards) | baseline_overlap | baseline_overlap | ✅ |
| CVRP default (far_first+nearest) | baseline_overlap | baseline_overlap | ✅ |

**结论**：V2 LLM proposer 诊断与 V1 规则版 100% 一致。

---

## 2. gatekeeper_safety / Gatekeeper 安全性

3 个 proposal 均通过 gatekeeper 校验。验证要点：

| 检查项 | TSP | CVRP #1 | CVRP #2 |
|---|---|---|---|
| accepted | ✅ | ✅ | ✅ |
| violations | 0 | 0 | 0 |
| forbidden fields stripped | N/A | N/A | N/A |
| cards 存在且匹配 problem prefix | ✅ tsp_ | ✅ cvrp_ | ✅ cvrp_ |
| query 非空 | ✅ | ✅ | ✅ |

**结论**：Gatekeeper 在所有 3 个 proposal 上正确执行了 R1-R11 规则，无越权字段进入 safe_arm。

---

## 3. runner_linkage / Runner 执行链路

| 检查项 | TSP | CVRP #1 | CVRP #2 | 标准 |
|---|---|---|---|---|
| failure_reason | null | null | null | must be null |
| run_summary.ok | true | true | true | must be true |
| valid_candidates | 4 | 4 | 4 | >= 1 |
| proposal cards == rag_trace cards | ✅ | ✅ | ✅ | exact match |
| pool_size == len(proposal cards) | 2 | 2 | 2 | exact match |
| return_code | 0 | 0 | 0 | 0 |

**结论**：V2 proposal → runner → trace 链路 15/15 检查全部通过。

---

## 4. objective_signal / Objective 信号

| run | best | reference | delta vs reference | 判断 |
|---|---|---|---|---|
| TSP V2 agent | **6.217** | pure 6.839 | -0.622 | 强正向，刷新历史最优 |
| TSP V2 agent | 6.217 | gen4 6.287 | -0.070 | 优于此前 deep run 最优 |
| CVRP V2 agent #1 | 13.230 | pure 13.207 | +0.023 | inconclusive（接近 pure） |
| CVRP V2 agent #2 | 13.236 | pure 13.207 | +0.029 | inconclusive（略差于 pure） |
| CVRP V2 agent | 13.230 | targeted_far_first 12.821 | +0.409 | weak negative（regret+savings 不如 regret+far_first） |

**TSP**：V2 agent 推荐的 regret+farthest 不仅验证了链路，还产生了当前最优 best=6.217。

**CVRP**：V2 agent 推荐的 regret+savings 两次均略差于 pure。已知 regret+far_first (12.821) 是更优组合。这不否定 V2 agent——agent 正确诊断了 baseline_overlap，但选卡策略（savings 而非 far_first）在 CVRP 上效果不如人工 targeted。这为 V3 提供了明确的 correction 方向。

---

## 5. limitations / 局限性

1. **CVRP agent 选卡不是最优**：LLM proposer 基于词频分数选了 savings（score 20），但 far_first（score 16）实际效果更好。这说明 retrieval scores 和实际 EOH 效果之间不是线性关系。
2. **单次 run**：TSP 1 run + CVRP 2 runs 不能做统计推断。所有结论是 best-score oriented。
3. **未覆盖全部 failure mode**：当前 trace 样本缺乏 valid_collapse、api_failure（真实）、context_truncated 的实例，V2 agent 在这些模式下的表现未知。
4. **Agent 输出 query 质量差异**：V2 agent 生成的 query 偏向自然语言描述（"TSP construction heuristics beyond nearest neighbor..."），不如人工写的 keyword 密集 query（"tsp regret farthest lookahead route length"）精准。

---

## 6. go_no_go / V3 准入建议

对照 V3 准入条件：

| # | 条件 | 状态 |
|---|---|---|
| 1 | V2 proposals 已固化，可追溯 source trace | ✅ |
| 2 | Gatekeeper 对 3 个 proposal 给出 accepted verdict | ✅ |
| 3 | ≥3 bounded real runs 完成，无 mismatch | ✅ |
| 4 | selected_card_ids == rag_trace 一致 | ✅ |
| 5 | 本 report 包含全部 6 个 section | ✅ |
| 6 | P0/P1 = 0 | ✅ |

**建议：GO for V3 bounded pilot。**

V3 pilot 的 research question：
- TSP：验证 TOCC 能否保持 regret+farthest 正向方向
- CVRP：诊断 regret+savings 弱负向，让 controller 在 regret+savings 与 regret+far_first 之间做 bounded correction
- 边界：max_iterations ≤ 2, gen ≤ 1, runs ≤ 4
