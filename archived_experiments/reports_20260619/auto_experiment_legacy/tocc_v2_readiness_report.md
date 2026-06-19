# TOCC V2 Readiness Report / V2 就绪报告

日期：2026-06-08

---

## 1. V1 工程闭环验收 / V1 Engineering Closed-Loop

| 检查项 | 状态 | 证据 |
|---|---|---|
| manifest → card filter → LLM ✅ | PASS | phase4_smoke TSP + CVRP |
| selected_card_ids 生效 (pool=2) | PASS | rag_strategy_pool_size=2 for both |
| trace 记录完整 (cards/query/context/best/valid) | PASS | all summaries have rag_trace + run_summary |
| summarizer 出中文报告 | PASS | auto_experiment_reports/phase4_smoke/summary.md |
| raw run 不入 git | PASS | git check-ignore confirmed |
| --no-run 只读 | PASS | test_no_run_is_read_only |
| gen>1 + require_confirm 门禁 | PASS | test_real_run_requires_force |
| --resume 只跳过成功 run | PASS | checks failure_reason |

## 2. 双问题 Smoke 信号 / Two-Problem Smoke Signals

| Problem | Arm | Best | vs Pure | Valid | Selected Cards | Source |
|---|---|---|---|---|---|---|
| TSP | pure_eoh | 6.839 | baseline | 4/4 | — | init-only historical |
| TSP | default_rag | 6.840 | +0.001 | 4/4 | nearest_insertion, nearest_neighbor | init-only historical |
| TSP | targeted_tocc | **6.475** | **-0.364** | 4/4 | regret_insertion, farthest_insertion | Phase 4 smoke |
| CVRP | pure_eoh | 13.565 | baseline | 4/4 | — | Phase 4 repeat r1 |
| CVRP | default_rag | 13.283 | -0.282 | 1/1 | far_first, nearest_capacity | Phase 4 repeat r1 |
| CVRP | targeted_tocc | **12.886** | **-0.679** | 4/4 | regret_insertion, far_first | Phase 4 repeat r1 |

**关键观察**:
- TSP: targeted_tocc 两个 smoke 都低于 pure，best=6.475 < pure=6.839
- CVRP: targeted_tocc repeat=2 均低于 pure (12.886, 12.922 < 13.565-13.611)，valid=4/4
- CVRP default_rag 虽 objective 更低但 valid=1 (degenerate to recipe)

## 3. 失败模式诊断覆盖 / Failure Mode Coverage

| 诊断类型 | 真实 trace 数 | 来源 |
|---|---|---|
| baseline_overlap | 2 | TSP default (nearest), CVRP default (far_first+nearest) |
| wrong_bias | 1 | CVRP old capacity cards (14.494 vs pure 13.207) |
| low_diversity | 1 | CVRP default gen=4 (48 samples all 13.283) |
| valid_collapse | 0 | 需要构造或等待自然出现 |
| api_failure | 1 | TSP gen=16 partial run |
| context_truncated | 0 | current max_chars=2500, actual ~1917, safe |
| no_issue | 2 | TSP targeted, CVRP targeted (smoke passing) |

## 4. V2 Agent 实现状态 / V2 Agent Implementation

| 模块 | 文件 | 测试 | 状态 |
|---|---|---|---|
| Gatekeeper (R1-R11) | `tocc_gatekeeper.py` | 16 tests OK | ✅ |
| Agent (LLM proposer) | `tocc_agent.py` | (needs API for smoke) | ✅ 代码就绪 |
| Pipeline orchestrator | `tocc_v2_pipeline.py` | — | ✅ 代码就绪 |
| CVRP repeat=2 | `phase4_cvrp_targeted_repeat3/` | 6/6 runs done | ✅ |

## 5. V2 就绪判断 / V2 Readiness Verdict

| V2 门槛 | 满足? |
|---|---|
| V1 闭环稳定 | ✅ |
| 两个问题 smoke 通过 | ✅ TSP + CVRP |
| 最小 repeat 证据 | ✅ CVRP repeat=2 |
| trace 样本覆盖 ≥4 种 failure mode | ✅ 4/8 covered |
| 规则 gatekeeper 就绪 | ✅ 16 tests, 11 rules |
| Agent 代码就绪 | ✅ tocc_agent + pipeline |

**结论**: **READY_FOR_V2** ✅

V2 agent 代码已就绪。下一步用现有 TSP/CVRP traces 调用 LLM agent 出 proposal → gatekeeper 校验 → 对比 V1 规则版诊断准确率，即可完成 V2 最小闭环验证。
