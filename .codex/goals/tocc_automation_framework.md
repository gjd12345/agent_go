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
| Card memory loop | PASS | best_code → history card synthesis → `history_rag/mixed_rag` retrieval 已打通 |
| History/mixed real LLM smoke | PASS | 2/2 真实 LLM runs OK，4/4 valid；literature-only 13.094，mixed history+literature 14.210 |
| History-card gate v1 | PASS | 复合 history card 默认/显式注入前会被拦截；未来合成卡限制为小 operator |
| Split history cards | PASS | 已拆出 3 张 CVRP 小 operator cards，可通过 gate 并进入 history/mixed pool |
| Split-history real LLM smoke | PASS | 4/4 runs OK，均 4/4 valid；literature-only 12.728 最好，split-history mixed 未超过 |
| History-card prior audit | PASS | 已输出 accept/deprioritize/split 决策表；history prior 暂作为候选而非默认增强 |
| Architecture v3 | PASS | `reports/figures/architecture_v3.drawio` 已生成 |
| Literature survey | PASS | HeuriGym/HeurAgenix/CO-Bench 代码深读完成 |
| Push | PASS | 已推送 |

### 2026-06-14 修复记录：history/mixed RAG 闭环

本轮修复目标：确认 “EOH 进化 → best_code → history card → 下一轮 RAG 检索可用” 不只是写入 corpus，而是真正被官方实验 runner 消费。

修复前问题：
- `card_synthesis.py` 能把 TSP/CVRP 最优代码合成为 `history_*` algorithm cards，并写入 `algorithm_cards.jsonl`。
- 通用 `eoh_runner` 的 `mixed/history` 模式能看到这些卡。
- 但 `official_eoh_run.py` 的 `history_rag` 仍走旧的 `code_example` 分支，TSP/CVRP 官方实验不会检索 `history_tsp_construct_*` / `history_cvrp_construct_*`。
- `_is_history_card()` 用 `source_path != "curated"` 判定，可能误把外部文献卡当作 history card。

已修复：
- `_is_history_card()` 严格改为 `algorithm_card` 且 `id.startswith("history_")`。
- `official_eoh_run.py` 增加三类 strategy pool：
  - `literature_rag`: 只检索 problem-specific literature cards，不混入 history。
  - `history_rag`: 只检索 `history_{problem}_*` synthesized cards。
  - `mixed_rag`: literature + history 去重后共同检索。
- `run_experiment_manifest.py` 支持 `mixed_rag`。
- `operator_card_controller.py` 将 `history_rag` / `mixed_rag` 视为 RAG card arms，继续执行卡级诊断。

验证：

```text
PYTHONPATH=. python3 -m pytest -q
181 passed, 1 warning

PYTHONPATH=. python3 -m unittest discover -s tests -q
120 tests OK

python3 -m compileall -q eoh_go
OK
```

Trace smoke（不调用 LLM）：

```text
literature_rag -> tsp_* literature cards only
history_rag    -> history_tsp_construct_* cards
mixed_rag      -> history_tsp_construct_* + tsp_* literature cards
```

当前结论：

```text
Card memory loop 已从“可写入”升级为“可检索、可注入、可被 TOCC 诊断”。
后续涉及 historical best-code prior 的实验应使用 history_rag 或 mixed_rag；
literature_rag 保持为纯文献先验对照。
```

### 当前证据矩阵

| problem | arm | n | mean | min | max | vs pure | 证据等级 |
|---|---|---|---|---|---|---|---|
| CVRP | pure_eoh | 8 | 13.540 | 13.279 | 13.611 | baseline | — |
| CVRP | default_rag | 5 | 13.283 | 13.283 | 13.283 | 0% | 🔴 灾难性坍缩 |
| CVRP | tocc_corrected | 8 | 12.975 | 12.713 | 13.283 | **-4.2%** | ✅ repeat-level positive |
| TSP | pure_eoh gen=0 | 3 | 6.751 | 6.590 | 7.057 | baseline | — |
| TSP | default_rag | 3 | 6.756 | 6.273 | 7.194 | +0.1% | ⚠️ 不优于 pure |
| TSP | tocc_corrected gen=0 | 5 | 7.372 | 6.189 | 9.656 | — | ⚠️ exploratory, 方差过大 |
| TSP | pure_eoh gen=4 | 3 | 6.548 | 6.430 | 6.608 | baseline | — |
| TSP | tocc_corrected gen=4 | 3 | 6.456 | 6.292 | 6.615 | -1.4% | ⚠️ exploratory positive |

### CVRP 关键发现

**8/8 tocc runs 优于 pure mean。** tocc max (13.283) 仍低于 pure mean (13.540)。改善从 n=3 的 -4.6% 收敛到 n=8 的 -4.2%，说明信号稳定。

**default_rag 全部坍缩。** 5/5 runs 出现 valid=1, pop=1, best=13.28321（恰好等于 seed），种群坍缩到只剩种子。注入的 card 是 `cvrp_far_first` + `cvrp_nearest_capacity`。

**一张卡片决定生死。** tocc_corrected 和 default_rag 只差一张 card：`cvrp_regret_insertion` vs `cvrp_nearest_capacity`。换一张卡，从"全部坍缩"变成"全部有效 + 4.2% 改善"。这是 TOCC 选卡价值的直接证据，比 objective delta 本身更有区分度。

### TSP 诊断结论

**card 方向正确，问题在 LLM 生成方差。** outlier (9.656) 和 best (6.189) 使用相同的 `tsp_regret_insertion` + `tsp_farthest_insertion`，都是 valid=4, pop=4，无 failure。同一组 card 在不同 seed 下生成质量差异巨大，gen=0 无选择压滤除差候选。

**历史数据佐证。** gen=4 pop=8 tocc best=6.287（同 card），gen=0 targeted repeat×3 mean=6.513。tocc 在足够进化深度下可以显著优于 pure，但 gen=0 方差淹没了信号。

**gen=4 已完成同口径验证。** pure_eoh gen=4 repeat=3 mean=6.548；tocc_corrected gen=4 repeat=3 mean=6.456，改善约 -1.4%，3 次中 2 次优于 pure mean。该结果是 exploratory 正向信号，不可写成稳定证明。

### 当前可写结论

```text
TOCC 已完成从 trace-conditioned diagnosis 到 bounded operator-card correction 的端到端工程闭环。
CVRP 取得 repeat-level positive signal：8/8 tocc_corrected 优于 pure_eoh mean，改善 -4.2%。
CVRP default_rag 出现灾难性坍缩（5/5 degenerate），与 tocc 仅差一张 card，构成强对照。
TSP card 方向确认正确（regret+farthest），但 gen=0 方差过大，需 gen=4 验证。
TSP gen=4 同口径验证显示 exploratory 正向信号：tocc mean 比 pure mean 低约 1.4%，但 1/3 run 仍劣于 pure mean。
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

## 4. 下一阶段：结果固化 + 漏斗落地

### 4.0 Card-memory routing 前置条件

TSP gen=4 和后续 mixed/history 实验必须满足：

```text
literature_rag: trace.rag_selected_items 不包含 history_*
history_rag: trace.rag_selected_items 全部为 history_{problem}_*
mixed_rag: trace.rag_selected_items 可同时包含 literature cards 与 history cards
selected_card_ids: 必须精确反映最终注入 cards
```

推荐 smoke：

```text
PYTHONPATH=. python3 - <<'PY'
from pathlib import Path
from eoh_go.experiments.official_eoh_run import build_official_rag_context
root = Path('.').resolve()
for mode in ['literature_rag', 'history_rag', 'mixed_rag']:
    ctx, trace = build_official_rag_context(
        root,
        'tsp_construct',
        mode,
        top_k=5,
        max_chars=2500,
        query='tsp construct regret evolved adaptive destination',
    )
    print(mode, [x['id'] for x in trace['rag_selected_items']])
PY
```

### 4.1 TSP gen=4 baseline + TOCC 对照

状态：已完成。

```text
problem: tsp_construct
arms: pure_eoh, tocc_corrected
generations: 4
pop_size: 4
repeats: 3
llm_model: JoyAI-LLM-Pro
```

结果：

```text
pure_eoh:       mean=6.548, min=6.430, max=6.608
tocc_corrected: mean=6.456, min=6.292, max=6.615
delta:          -1.4% mean improvement
objective_success: 2/3 tocc runs better than pure mean
generation_success: 6/6
linkage_success: 3/3 RAG runs
```

结论边界：

```text
可写：TSP gen=4 下 TOCC 从 gen=0 的高方差转为小幅 exploratory 正向信号。
不可写：TOCC 在 TSP 上稳定优于 pure EOH。
```

### 4.2 漏斗接入 summarize

状态：已完成基础版本，并补充 card-memory 字段。

`summarize_manifest_runs.py` 已支持：
- 自动读取 run_summary 的 valid_candidates、failure_reason、best_objective
- 对每次 run 归类到五层漏斗
- 统计每层通过率
- 输出 `success_funnel.json`
- 额外记录 card-memory 维度：
  - `card_source`: `literature` / `history` / `mixed`
  - `selected_card_ids`
  - `history_card_ids`
  - `best_code_record_id`
  - `synthesized_card_id`
- summary markdown 中展示每个 arm 的最优代码片段，不再截取 docstring/Args。

### 4.3 归一化评分

状态：已完成基础版本。

在 `ProblemSpec` 中增加 `norm_score` 字段，以 pure baseline 为基准：

```python
norm_score = best_objective / pure_baseline_mean  # minimize 问题
# 或 pure_baseline_mean / best_objective  # maximize 问题
```

### 4.4 CVRP 锁定

CVRP 8/8 已足够，不扩 repeat。default_rag 5/5 坍缩已足够做对照，也不扩。

### 4.5 History/mixed RAG 真实 smoke

目标：验证 card-memory 不只是 routing smoke，而是在官方 CVRP runner 中能实际驱动 LLM 生成候选。

Manifest：

```text
eoh_go_workspace/experiments/manifests/tocc_history_mixed_cvrp_smoke.json
```

实验设计：

```text
problem: cvrp_construct
generation: 0
pop_size: 4
repeats: 1
arms:
  literature_regret_far:
    runner_arm=literature_rag
    selected_card_ids=[cvrp_regret_insertion, cvrp_far_first]
  mixed_history_far_regret:
    runner_arm=mixed_rag
    selected_card_ids=[history_cvrp_construct_capacity_destination_farthest_085049, cvrp_regret_insertion]
```

2026-06-18 首次尝试结果：

```text
status: ok_but_summary_failure
runtime: 0.1s each
failure_reason: missing_env_DEEPSEEK_API_KEY
LLM actually called: no
```

判断：这不是 RAG/TOCC 失败，也不是模型失败，而是运行环境没有把 API key export 给 Python 子进程。`chatrhino.env` 中若使用普通 `VAR=value` 写法，`source` 后 shell 可见但未必 export；manifest runner 的 Python 进程只能读取 exported env。

修复方式：

```bash
set -a
source ~/.config/agent_go/chatrhino.env
set +a
caffeinate -i -m -s python3 -m eoh_go.experiments.run_experiment_manifest \
  --manifest eoh_go_workspace/experiments/manifests/tocc_history_mixed_cvrp_smoke.json \
  --output-dir eoh_go_workspace/reports/auto_experiment_reports \
  --force
```

真实重跑结果（2026-06-18）：

```text
literature_regret_far:
  status=ok
  runtime=1046.8s
  selected_cards=[cvrp_regret_insertion, cvrp_far_first]
  valid=4/4
  best=13.09441

mixed_history_far_regret:
  status=ok
  runtime=493.7s
  selected_cards=[history_cvrp_construct_capacity_destination_farthest_085049, cvrp_regret_insertion]
  valid=4/4
  best=14.20996
```

已执行 summary：

```text
PYTHONPATH=. python3 -m eoh_go.experiments.summarize_manifest_runs \
  --input eoh_go_workspace/reports/auto_experiment_reports/tocc_history_mixed_cvrp_smoke \
  --no-card-memory-write
```

验收结论：

```text
proposal_accept: 2/2
linkage_success: 2/2
generation_success: 2/2
objective_success: insufficient data (manifest 未包含 pure baseline)
```

方法结论：

```text
Card-memory routing 已通过真实 LLM smoke：history card 可以被 selected_card_ids 精确注入，并产生 4/4 valid 候选。
但 naive mixed history+literature 本次 objective 明显差于 literature-only（14.210 vs 13.094）。
这说明 history card 不能简单“有就混入”，下一步应做 history-card 质量诊断和组合策略，而不是把 mixed_rag 当作默认增强。
```

---

## 5. 交付物

### 5.1 已有

```text
eoh_go_workspace/reports/auto_experiment_reports/tocc_stabilization_repeats/
eoh_go_workspace/reports/auto_experiment_reports/tocc_day1_cvrp_repeat5/
eoh_go_workspace/reports/auto_experiment_reports/phase4_cvrp_targeted_repeat3/
eoh_go_workspace/reports/auto_experiment_reports/tocc_day2_tsp_gen1_outlier/
eoh_go_workspace/reports/auto_experiment_reports/tocc_day2_tsp_real_evolution_gen4/
eoh_go_workspace/reports/figures/architecture_v3.drawio
eoh_go_workspace/reports/auto_experiment_reports/tocc_tool_using_research_agent_discussion_20260609.md
eoh_go_workspace/reports/auto_experiment_reports/tocc_stabilization_report.md
eoh_go_workspace/reports/paper_notes/tocc_method_section_draft_20260618.md
eoh_go_workspace/reports/auto_experiment_reports/tocc_history_mixed_rag_smoke_20260618.md
eoh_go_workspace/experiments/manifests/tocc_history_mixed_cvrp_smoke.json
```

### 5.2 待产出

```text
下一步不是继续扩 TSP/CVRP repeat，而是：
1. 已完成 history-card 质量诊断：`history_cvrp_construct_capacity_destination_farthest_085049` 是复合卡，混合 capacity/destination/farthest/lookahead/normalize/remaining-aware，诱导 gen=0 生成过复杂 scoring，导致 14.210，显著差于 literature-only 的 13.094。
2. 已落地 history-card gate v1：
   - `official_eoh_run.py` 在 `history_rag` / `mixed_rag` 构造 strategy pool 时拦截过度复合 history cards。
   - trace 增加 `rag_history_pool_size_before_gate`、`rag_history_pool_size_after_gate`、`rag_blocked_history_items`、`rag_history_gate_warnings`。
   - 显式 `selected_card_ids` 指向被拦截 history card 时直接报错，不 silent fallback。
   - `card_synthesis.py` 限制未来合成卡最多 3 个核心特征，并写清 `minimize` / `maximize` 方向。
3. 下一步拆分现有复合 history cards，形成单一 operator cards 后再做 mixed smoke。
   - 已拆出 `history_cvrp_far_destination_seed`
   - 已拆出 `history_cvrp_capacity_feasible_filter`
   - 已拆出 `history_cvrp_remaining_aware_alpha`
   - routing smoke: CVRP history pool before_gate=11, after_gate=3；mixed_rag 可检索这 3 张拆分卡。
4. 下一步真实 smoke 应只使用拆分卡 + literature card 的显式组合，不再使用旧复合卡：
   - `history_cvrp_far_destination_seed + cvrp_regret_insertion`
   - `history_cvrp_capacity_feasible_filter + cvrp_regret_insertion`
   - `history_cvrp_remaining_aware_alpha + cvrp_far_first`
   - 已新增 manifest: `eoh_go_workspace/experiments/manifests/tocc_split_history_cvrp_smoke.json`
   - dry-run 已通过，4 条命令可执行。
   - linkage 已验证：`selected_card_ids == rag_trace.rag_selected_items`，所有 context <= 2500 chars。
5. 已完成 split-history 真实 LLM smoke：
   - `literature_regret_far`: best=12.72795, valid=4/4
   - `split_far_seed_regret`: best=13.00458, valid=4/4
   - `split_capacity_filter_regret`: best=13.23646, valid=4/4
   - `split_remaining_alpha_far`: best=12.96129, valid=4/4
   - funnel: proposal/linkage/generation 全部 4/4。
   - 结论边界：拆分卡解决了可控接入和 valid 问题，但本轮 objective 仍由 literature-only 最优；当前不支持“history prior 带来收益”。
6. 已完成 history-card prior audit：
   - `history_cvrp_construct_*` 旧复合卡：`split_required` 或 `split_or_deprioritize`。
   - `history_cvrp_far_destination_seed`: `candidate_deprioritized`。
   - `history_cvrp_capacity_feasible_filter`: `candidate_deprioritized`。
   - `history_cvrp_remaining_aware_alpha`: `candidate_watchlist`。
   - 结论边界：history prior 已可控接入，但当前不支持“history prior 带来 objective 收益”。
7. 下一步应把 `card_prior_decisions.jsonl` 接入 controller：proposal 若选择 `candidate_deprioritized` card，必须给出 trace 证据和显式理由；默认不自动增强。
8. 若要扩实验，优先选一个新问题或新官方 benchmark，而不是继续堆同一 TSP/CVRP repeat。
9. 将 `tocc_method_section_draft_20260618.md` 整理进论文初稿。
```

### 5.3 已完成但未提交的新增记录

```text
eoh_go_workspace/reports/paper_notes/tocc_method_section_draft_20260618.md
  - TOCC 方法定义、operator-card 表示、闭环、success funnel、实验边界。

eoh_go_workspace/reports/auto_experiment_reports/tocc_history_mixed_rag_smoke_20260618.md
  - 不调用 LLM 的 routing smoke。
  - TSP: literature/history/mixed 三种路径均符合预期。
  - CVRP: mixed top-5 被 history cards 占满，后续真实 smoke 应用 selected_card_ids 控制组合比例。

eoh_go_workspace/experiments/manifests/tocc_history_mixed_cvrp_smoke.json
  - 2-run 真实 LLM smoke manifest。
  - dry-run 已通过。
  - selected-card linkage 已验证：literature arm = 2 literature cards；mixed arm = 1 history + 1 literature。
  - 首次 real-run 未真正调用 LLM：`missing_env_DEEPSEEK_API_KEY`。
  - 修复 env export 后真实重跑通过：literature-only best=13.09441，mixed history+literature best=14.20996，二者均 4/4 valid。

eoh_go_workspace/reports/auto_experiment_reports/tocc_history_mixed_cvrp_smoke/
  - `run_index.json`: 2/2 status=ok。
  - `summary.md`: 中文自动报告，含 best code snippet 与 card-memory 选卡记录。
  - `success_funnel.json`: proposal/linkage/generation 均 2/2。
  - `history_card_diagnosis.md`: 解释 mixed history+literature 差于 literature-only 的原因，并记录 history-card gate v1 与拆分卡落地情况。

eoh_go_workspace/experiments/manifests/tocc_split_history_cvrp_smoke.json
  - 1 条 literature-only 对照 + 3 条 split-history mixed arms。
  - dry-run 通过。
  - selected-card linkage 通过。

eoh_go_workspace/reports/auto_experiment_reports/tocc_split_history_cvrp_smoke/
  - `run_index.json`: 4/4 status=ok。
  - `summary.md`: 中文自动报告，含 best code snippet 与 card-memory 选卡记录。
  - `success_funnel.json`: proposal/linkage/generation 均 4/4。

eoh_go_workspace/reports/auto_experiment_reports/tocc_history_card_audit_20260619/
  - `history_card_audit.md`: 中文审计报告，说明旧复合 history cards 继续 block/split，拆分卡可控但未带来收益。
  - `card_prior_decisions.jsonl`: 机器可读 card prior 决策表，可供后续 controller 读取。
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

新增执行规则：
- 做 literature 对照时，用 `literature_rag`。
- 做历史最优代码反馈时，用 `history_rag`。
- 做文献先验 + 历史反馈混合时，用 `mixed_rag`。
- 每次报告必须写清楚 cards 来源，不能把 `history_*` 结果表述为纯 literature-RAG。

---

## 8. 完成时填写清单

任务完成后补充：

- files changed:
- commands run:
- test results:
- subagent verdicts:
- unresolved risks:
- merge recommendation:
