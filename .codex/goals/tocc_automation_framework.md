/goal: TOCC V2 Agent 实跑验证与 V3 准入

目标：在 TOCC V1 规则闭环和 V2 LLM proposer + gatekeeper 离线闭环都已验证的基础上，做最小真实实验，验证 V2 agent 推荐的 card set 从 proposal 到 runner 到 trace 到 report 的端到端链路。当前不进入 V3 auto-loop，不扩大大规模实验矩阵。

报告一律写中文。API key 不读取、不打印、不 echo；如需确认，只输出布尔值。raw run、population、samples、run log 不入 git。允许入 git 的只有 manifest、summary、整理后的报告、card decision / card memory 等研究资产。

---

## 0. 当前状态

TOCC V1 的工程闭环已经跑通：

```text
manifest
-> --selected-card-ids
-> official_eoh_run.py
-> card filtering
-> LLM
-> rag_trace / run_summary
-> summarize_manifest_runs.py
-> Chinese report
```

已确认：

| 项 | 状态 |
|---|---|
| Phase 0-3 框架 | PASS |
| P1 修复 | PASS |
| selected_card_ids 生效 | PASS |
| raw run gitignore | PASS |
| TSP targeted smoke | PASS, best=6.47488, valid=4/4 |
| CVRP targeted smoke | PASS, best=13.07835, valid=4/4 |
| phase4_smoke 自动报告 | PASS，summary 同时收录 TSP 和 CVRP |
| V2 LLM proposer 离线诊断 | PASS，3/3 与 V1 规则版一致 |
| V2 gatekeeper | PASS，无越权字段，无违规执行 |
| V2 real-run validation | PASS，3/3 bounded real runs completed, 15/15 proposal/card trace checks pass |
| P0 gatekeeper contract fixes | PASS，`d25a0c3` 修复 forbidden fields 与 `cards` / `selected_card_ids` schema alias |
| P2 goal evidence fixes | PASS，`ead082e` 修复 CVRP cards、TSP evidence tiers、CVRP V2 result、V3 condition 5 |
| tests | PASS，110 tests OK |
| latest V2 delivery commit | `50f37b4` |
| latest goal fix commit | `ead082e` |

V2 离线验证覆盖的 trace：

| trace | V1 / V2 一致诊断 |
|---|---|
| TSP default | nearest / baseline_overlap |
| CVRP old | capacity bias / wrong_bias |
| CVRP default | default far_first/nearest recipe 诊断，V2 推荐 regret + savings 纠偏 |

当前可写结论：

```text
TOCC v1 端到端闭环已验证。
TOCC V2 LLM proposer + rule gatekeeper 离线闭环已验证，并已通过 3 个 bounded real runs 做 proposal-to-run 验证。
TSP targeted card selection 已有 repeat 级正向信号。
CVRP targeted card selection 已有 repeat=2 正向信号，但还不能写统计稳定。
TSP V2 agent real-run best=6.217，刷新当前 TSP 历史最优。
CVRP V2 agent regret+savings real-run best=13.230 / 13.236，略差于 pure，写入 inconclusive / weak negative。
V3 只在 V2 validation report 完成、P0/P1 为 0、治理门禁补齐后进入 bounded pilot。
BP 暂未拉开差距，不作为下一步主线。
```

禁止写：

```text
TOCC 已证明有效
CVRP 稳定优于 pure
RAG 一定有效
BP 不适合 RAG
V2 已经完成自主闭环
V3 可以直接自动跑大矩阵
```

---

## 1. 方法定位保留

方法名仍为 **Trace-Conditioned Operator-Card Controller (TOCC)**。

TOCC 不是替代 EOH 搜索，而是控制 LLM-based heuristic evolution 的生成先验：

```text
previous run trace
-> diagnose search bias / failure mode
-> select operator-card subset + query
-> run EOH under selected context prior
-> observe objective / valid rate / code features
-> update report and card memory
```

方法表述：

> We formulate operator-card injection as a context-selection problem, and propose TOCC: a trace-conditioned controller that diagnoses search bias from run traces and selects the next operator-card subset to steer LLM-based heuristic evolution.

---

## 2. 已完成 P0：phase4_smoke 汇总归档

### 历史问题

`eoh_go_workspace/reports/auto_experiment_reports/phase4_smoke/` 中实际有两条成功 run：

```text
run_tsp_targeted_tsp_g0_r1/
run_cvrp_targeted_cvrp_g0_r1/
```

历史上曾出现：

```text
run_index.json 只包含 TSP
summary.md / summary.json 只包含 TSP
CVRP run_summary 文件存在但未进入自动报告
```

当前状态：

```text
已修复。phase4_smoke summary.md / summary.json / run_index.json 同时收录 TSP 和 CVRP。
```

### 已归档交付

已修复或重生成：

```text
eoh_go_workspace/reports/auto_experiment_reports/phase4_smoke/run_index.json
eoh_go_workspace/reports/auto_experiment_reports/phase4_smoke/summary.md
eoh_go_workspace/reports/auto_experiment_reports/phase4_smoke/summary.json
```

必须包含：

| problem | arm | gen | best | valid | cards |
|---|---|---:|---:|---:|---|
| `tsp_construct` | `targeted_tsp` | 0 | 6.47488 | 4/4 | `tsp_regret_insertion`, `tsp_farthest_insertion` |
| `cvrp_construct` | `targeted_cvrp` | 0 | 13.07835 | 4/4 | `cvrp_regret_insertion`, `cvrp_far_first` |

### 回归验收

```bash
PYTHONPATH=. python3 -m eoh_go.experiments.summarize_manifest_runs \
  --input eoh_go_workspace/reports/auto_experiment_reports/phase4_smoke \
  --no-card-memory-write
```

然后检查：

```text
summary.md 同时包含 tsp_construct 和 cvrp_construct
summary.json 同时包含 tsp_construct 和 cvrp_construct
不生成 raw population / samples 新文件
```

---

## 3. 本阶段 P1 任务：V2 agent proposal real-run 验证

### 目的

验证 V2 LLM proposer 推荐的 card set 能否落到真实 EOH run，并在 trace 中被严格记录。这里验证的是：

```text
trace -> LLM proposer -> proposal JSON -> gatekeeper -> bounded runner -> new trace -> report
```

本阶段不验证统计显著，不扩大到 V3 自动循环。V2 的 `agent` 特指 **LLM as trace-conditioned proposer**，不是全自动 autonomous agent。

V1 / V2 / V3 区分：

```text
V1 rule controller:
trace -> hardcoded rules -> diagnosis -> cards/query

V2 agent-assisted controller:
trace -> LLM proposer -> proposal JSON -> rule gatekeeper -> human/bounded runner

V3 auto-loop controller:
trace -> proposer -> gatekeeper -> runner executes -> observe new trace -> repeat
```

V2 LLM 允许输出：

```text
diagnosis
selected_card_ids
rag_query
why
risk
next_action
confidence
source_trace
```

V2 LLM 禁止输出或决定：

```text
pop_size
generations
repeat budget
model name
output_dir
shell command
file write action
API key / env
git operation
```

如果 proposal JSON 出现禁止字段，gatekeeper 必须 strip 或 reject；不得让 LLM proposer 直接控制实验预算或执行命令。

当前参考基线：

| setting | best |
|---|---:|
| CVRP pure init | 13.20696 |
| CVRP default literature-RAG old cards | 14.49387 |
| CVRP fixed/default cards | 13.28321 |
| CVRP targeted smoke | 13.07835 |
| CVRP targeted historical init | 13.03297 |
| CVRP targeted gen4 pop8 | 12.82084 |
| CVRP targeted gen8 pop8 | 12.91824 |

本阶段只做最小 real-run 验证，不做深度 gen 扩展。

### 输入 proposal 固化

先把 3 个 V2 离线 proposal 固化为可追溯记录：

```text
eoh_go_workspace/reports/auto_experiment_reports/v2_agent_proposals.jsonl
```

每行至少包含：

```json
{
  "source_trace": "tsp_default_nearest",
  "problem": "tsp_construct",
  "diagnosis": "baseline_overlap",
  "selected_card_ids": ["tsp_regret_insertion", "tsp_farthest_insertion"],
  "rag_query": "tsp construct regret farthest lookahead route length",
  "why": ["nearest-style cards overlap pure/baseline family"],
  "risk": "single smoke only validates execution path",
  "next_action": "run_targeted_smoke",
  "gatekeeper_verdict": "accepted"
}
```

需要固化的 proposal：

| source trace | problem | expected cards | purpose |
|---|---|---|---|
| `tsp_default_nearest` | `tsp_construct` | `tsp_regret_insertion`, `tsp_farthest_insertion` | 验证 V2 对 nearest baseline overlap 的纠偏 |
| `cvrp_old_capacity` | `cvrp_construct` | `cvrp_regret_insertion`, `cvrp_savings` | 验证 V2 对 capacity bias 的纠偏 |
| `cvrp_default_far_first` | `cvrp_construct` | `cvrp_regret_insertion`, `cvrp_savings` | 验证 V2 对 default far_first/nearest recipe 的再诊断 |

### 推荐 real-run 口径

不重跑大规模 baseline。baseline 使用已有结果：

| problem | reference |
|---|---|
| TSP | pure/default/targeted historical notes and Phase 4 smoke |
| CVRP | pure/default/targeted repeat=2 and historical gen runs |

本阶段最多跑 3-4 个真实 run：

| problem | runs | reason |
|---|---:|---|
| `tsp_construct` | 1 | TSP 已有较强历史证据，只验证 V2 proposal -> runner 链路 |
| `cvrp_construct` | 2 | CVRP 是当前最能说明 agent 纠偏 capacity/far_first bias 的问题 |
| optional guard run | 1 | 仅当 exploration_analyst 判断前 3 个 run 出现 card mismatch 或 failure 时补 |

推荐 suite：

```text
v2_agent_real_run_validation
```

推荐 manifest：

```text
eoh_go_workspace/experiments/manifests/v2_agent_real_run_validation.json
```

真实运行仍按 E2/E3 管理，付费 API 或长时间 run 需要用户确认。

先 dry-run：

```bash
PYTHONPATH=. python3 -m eoh_go.experiments.run_experiment_manifest \
  --manifest eoh_go_workspace/experiments/manifests/v2_agent_real_run_validation.json \
  --output-dir eoh_go_workspace/reports/auto_experiment_reports \
  --dry-run
```

真实运行必须显式确认，必要时使用防熄屏：

```bash
PYTHONPATH=. caffeinate -i -m -s python3 -m eoh_go.experiments.run_experiment_manifest \
  --manifest eoh_go_workspace/experiments/manifests/v2_agent_real_run_validation.json \
  --output-dir eoh_go_workspace/reports/auto_experiment_reports \
  --force
```

不要打印 API key。不要 echo env 文件内容。

### 验收

每个 real run 必须检查：

```text
failure_reason is null
run_summary.ok is true
valid_candidates >= 1
proposal.selected_card_ids == rag_trace.rag_selected_items
rag_strategy_pool_size == len(proposal.selected_card_ids)
proposal.rag_query == effective rag query
```

生成：

```bash
PYTHONPATH=. python3 -m eoh_go.experiments.summarize_manifest_runs \
  --input eoh_go_workspace/reports/auto_experiment_reports/v2_agent_real_run_validation
```

通过标准：

```text
1. V2 proposal JSON 可追溯到 source trace。
2. gatekeeper verdict 是 accepted / rejected / stripped，并记录理由。
3. accepted proposal 的 selected_card_ids 与真实 rag_trace 完全一致。
4. 没有 failure_reason。
5. best score 不要求刷新历史最优，但应落在已知正向区间附近；如未落入，需要写成 risk / inconclusive，不写失败或稳定。
6. card_decisions 和 best_code_records 都补齐 source summary path。
```

---

## 4. 本阶段 P1 任务：V2 validation report

V2 real-run 验证完成后，写一份中文 validation report：

```text
eoh_go_workspace/reports/auto_experiment_reports/tocc_v2_agent_validation_report.md
eoh_go_workspace/reports/auto_experiment_reports/tocc_v2_agent_validation_report.json
```

同时维护两类标准化记录：

```text
eoh_go_workspace/reports/auto_experiment_reports/v2_agent_real_run_validation/card_decisions.jsonl
eoh_go_workspace/reports/auto_experiment_reports/tocc_best_code_records.md
```

### 每次实验必须补的记录

每条真实实验完成后，不只记录 best score，还必须记录“为什么选这些 cards”和“最优代码是什么”。

#### 1. Card decision 记录

写入对应 suite 的 `card_decisions.jsonl`，每行至少包含：

```json
{
  "suite": "v2_agent_real_run_validation",
  "problem": "cvrp_construct",
  "target": "select_next_customer",
  "arm": "v2_agent_targeted_cvrp",
  "selection_source": "v2_llm_proposer",
  "source_trace": "cvrp_old_capacity",
  "gatekeeper_verdict": "accepted",
  "context_strategy": "tocc_selected_cards",
  "diagnosis": "wrong_bias_or_baseline_overlap",
  "why": [
    "old/default CVRP literature RAG over-weighted nearest/capacity cards",
    "regret insertion adds lookahead",
    "savings adds route-distance structure but may be weaker than far-first seeding"
  ],
  "selected_card_ids": ["cvrp_regret_insertion", "cvrp_savings"],
  "rag_query": "cvrp regret insertion savings distance lookahead route length",
  "expected_effect": "test whether regret+savings can correct capacity/nearest bias under bounded V2 validation",
  "run_summary_path": ".../official_eoh_run_summary.json",
  "outcome": {
    "best_objective": 13.230,
    "valid_candidates": 4,
    "population_size": 4,
    "failure_reason": null
  },
  "confidence": "v2_real_run_smoke_inconclusive"
}
```

#### 2. Best code 记录

更新 `tocc_best_code_records.md`，每条至少包含：

```text
中文记录：
- 问题、arm、generations、pop_size
- 最优分数 best score
- valid candidates
- selected cards
- source summary path
- 中文策略说明

English Record:
- Problem, arm, generations, pop_size
- Best score
- Valid candidates
- Selected cards
- Source summary path
- English strategy note

Full Best Code:
- 完整 run_summary.best_code 代码块
```

规则：

```text
1. 不只写“策略变化”，必须贴完整或可复现定位的 best code。
2. 每个 best score 必须能追溯到 official_eoh_run_summary.json。
3. smoke / repeat / gen-depth 结果必须分开标注，不能混成同一种证据。
4. 历史最优和当前 smoke 最优都要保留，不能覆盖。
```

报告必须分清三类证据：

### 1. 工程闭环证据

```text
proposal JSON -> gatekeeper -> manifest -> selected_card_ids -> official runner -> card filtering -> LLM -> trace -> summarizer
```

说明：

```text
TOCC V2 可以把 LLM proposer 的 bounded card/query proposal 落到真实实验闭环。
```

### 2. TSP 效果证据

写入现有结果——按证据层级分开：

**Smoke / Repeat 级**：

| setting | best | valid | cards | evidence |
|---|---:|---:|---|---|
| pure init pop4 | 6.83907 | 4/4 | - | baseline |
| default RAG init pop4 | 6.83954 | 4/4 | nearest cards | smoke |
| targeted init pop4 | 6.51118 | 4/4 | regret+farthest | smoke |
| targeted repeat 1-3 | 6.305 / 6.500 / 6.733 | 4/4 | regret+farthest | repeat=3 |
| V2 agent targeted | **6.217** | 4/4 | regret+farthest | V2 agent real-run |

**Gen-depth 级**（独立 run，不与 smoke 混用）：

| setting | best | valid | cards |
|---|---:|---:|---|
| targeted gen4 pop8 | 6.28736 | 8/8 | regret+farthest |
| targeted gen8 pop8 | 6.49327 | 8/8 | regret+farthest |
| targeted gen16 pop8 (partial) | 6.46057 | 8/8 | regret+farthest |

允许结论：

```text
TSP 上 targeted card selection 已有 repeat 级正向 best-score 信号。
```

### 3. CVRP 效果证据

写入：

```text
CVRP smoke: best=13.07835, valid=4/4
CVRP targeted repeat=2: best=12.88600 / 12.92217, valid=4/4
V2 real-run validation: done
  - CVRP V2 agent regret+savings r1: best=13.230, valid=4/4
  - CVRP V2 agent regret+savings r2: best=13.236, valid=4/4
  - 结论：regret+savings 两次均略差于 pure (13.207)，写入 inconclusive / weak negative
  - 不否定 V2 agent，但说明 regret+savings 不是 CVRP 最优选卡组合
  - 已知更优组合 regret+far_first (12.821)，作为 V3 correction 方向
```

根据 V2 real-run 结果写：

```text
如果 V2 accepted proposal 的 cards 与 rag_trace 一致，且无 failure_reason：V2 proposal-to-run 链路成立。
如果 V2 CVRP run 落在 13.0 以下或接近既有 targeted repeat 区间：V2 proposal 观察到正向 best-score 信号。
如果 V2 run 未落入既有正向区间：写成 inconclusive / risk，不否定 V2 agent，只说明需要更多 repeat 或重新诊断。
无统计检验前，不写稳定提升。
```

---

## 5. 是否进入 V3 auto-loop 的门槛

V2 不需要证明统计显著，但进入 V3 前必须满足：

```text
1. V2 proposals 已固化，且每条能追溯 source trace。
2. gatekeeper 对 3 个 proposal 均给出 accepted/rejected/stripped verdict。
3. 至少 3 个 bounded real runs 完成，且没有 proposal/card trace mismatch。
4. 每个 accepted proposal 的 selected_card_ids 与 rag_trace.rag_selected_items 一致。
5. V2 validation report 包含以下 section 且均有非空内容：diagnosis_correctness、gatekeeper_safety、runner_linkage、objective_signal、limitations、go_no_go。
6. P0/P1 为 0。
```

满足后才可以启动 V3：

```text
V3 = proposer -> gatekeeper -> bounded runner -> observe -> proposer 的自动循环
```

V3 的第一版仍必须 bounded：

```text
max_iterations <= 2
gen <= 1
runs <= 4
no budget changes by proposer
no direct shell command from proposer
human confirmation before paid API execution
```

V3 不作为本 goal 的当前交付范围；本 goal 只交付 V2 real-run validation 和 V3 go/no-go 建议。

---

## 6. Git 边界

允许入 git：

```text
.codex/goals/tocc_automation_framework.md
eoh_go_workspace/experiments/manifests/v2_agent_real_run_validation.json
eoh_go_workspace/reports/auto_experiment_reports/v2_agent_proposals.jsonl
eoh_go_workspace/reports/auto_experiment_reports/phase4_smoke/summary.md
eoh_go_workspace/reports/auto_experiment_reports/phase4_smoke/summary.json
eoh_go_workspace/reports/auto_experiment_reports/phase4_smoke/run_index.json
eoh_go_workspace/reports/auto_experiment_reports/v2_agent_real_run_validation/summary.md
eoh_go_workspace/reports/auto_experiment_reports/v2_agent_real_run_validation/summary.json
eoh_go_workspace/reports/auto_experiment_reports/v2_agent_real_run_validation/run_index.json
eoh_go_workspace/reports/auto_experiment_reports/v2_agent_real_run_validation/card_decisions.jsonl
eoh_go_workspace/reports/auto_experiment_reports/tocc_v2_agent_validation_report.md
eoh_go_workspace/reports/auto_experiment_reports/tocc_v2_agent_validation_report.json
eoh_go_workspace/reports/auto_experiment_reports/tocc_best_code_records.md
```

禁止入 git：

```text
run_*/results/**
run_*/rag_context.txt
run_*/_run_official_eoh.py
raw population JSON
raw samples JSON
API logs
.DS_Store
```

提交前必须运行：

```bash
git status --short
PYTHONPATH=. python3 -m unittest discover -s tests -q
python3 -m compileall -q eoh_go
git check-ignore -v eoh_go_workspace/reports/auto_experiment_reports/v2_agent_real_run_validation/run_cvrp_construct_v2_agent_targeted_cvrp_g0_r1/results/pops/population_generation_0.json
```

---

## 7. 多 agent 审查门禁

本阶段必须遵守项目 `AGENTS.md`，因为任务涉及 RAG、实验 runner、summary/report、git/artifact 边界，按 `AGENTS.md` 属于 **L 级任务**。

### 执行前必须读取

```text
AGENTS.md
.codex/goals/tocc_automation_framework.md
```

如果涉及 prompt/template 或新 goal 改写，再读取：

```text
.codex/prompts/task-template.md
```

### L 级流程

必须按以下顺序执行：

```text
scout -> exploration_analyst -> rag_researcher? -> implementer -> gatekeeper -> verifier
```

角色约束：

| agent | 权限 | 本阶段职责 |
|---|---|
| `scout` | read-only | 先读 phase4_smoke、existing summaries、manifest、goal，列出影响文件和测试缺口 |
| `exploration_analyst` | read-only | 在 V2 real-run validation 中实时读取 proposal、run_index、trace、valid rate、best score、cards、failure_reason，建议 continue/stop/resume/change_cards/change_query/reduce_budget |
| `rag_researcher` | read-only，可选 | 只在需要新增/修改 operator cards、query 设计或外部文献依据时启用；本阶段默认不需要 |
| `implementer` | workspace-write | 唯一允许编辑文件的 agent；负责补 proposal records、manifest、run_index、summary、card_decisions、best_code_records、V2 validation report |
| `gatekeeper` | read-only | 审查 V2 proposal 是否越权；gatekeeper verdict 是否真实执行；V2 报告是否夸大成 autonomous agent 或稳定提升 |
| `verifier` | read-only | 运行验收命令；确认 proposal cards 与 rag_trace 一致；确认 summary 数字来自 run_summary；确认 raw 产物被 gitignore；确认没有 API key 泄漏 |

写入纪律：

```text
1. 只有 implementer 可以改文件。
2. 不允许多个 write-capable agent 并行编辑。
3. implementer 不能自我批准。
4. gatekeeper 或 verifier 返回 FAIL 时，任务不得完成。
5. P0/P1 阻塞提交和进入 V3。
```

### 本阶段 reviewer checklist

| reviewer | 审查点 |
|---|---|
| `exploration_analyst` | V2 real-run 过程中是否值得继续；是否出现 valid collapse、API failure、context/query/card mismatch；是否应 stop/resume/reduce_budget/change_cards |
| `gatekeeper` | V2 proposal 是否只包含允许字段；禁止字段是否被 strip/reject；是否错误放权给 LLM proposer |
| `gatekeeper` | V2 validation report 是否区分 diagnosis correctness / gatekeeper safety / runner linkage / objective signal |
| `gatekeeper` | 是否夸大成“autonomous agent”“证明有效”“稳定优于”；是否把 historical gen4、repeat=2 与 V2 smoke 混成同一证据 |
| `verifier` | `summary.md/json` 数字是否逐项来自 `official_eoh_run_summary.json` |
| `verifier` | `v2_agent_proposals.jsonl` 和 `card_decisions.jsonl` 每行 JSON 可解析，且 `selected_card_ids` 与 `rag_trace.rag_selected_items` 一致 |
| `verifier` | `tocc_best_code_records.md` 中每个 best score 和完整代码都能追溯到 source summary path |
| `verifier` | `git check-ignore` 覆盖 raw population、samples、run log、`_run_official_eoh.py` |
| `verifier` | 不读取、不打印、不 echo API key；报告里只允许出现 `api_key_present: true/false` |

P0/P1 必须修完才能进入 V3。

### 完成时必须输出

最终回复必须包含：

```text
files changed
commands run
test results
subagent verdicts
unresolved risks
merge recommendation
```

如果改动涉及新模块、pipeline refactor、RAG flow 修改或架构变化，还必须按 `AGENTS.md` 的 Architecture Rule 更新架构图：

```text
eoh_go_workspace/reports/figures/architecture_v{n}.drawio
```

本阶段只补报告/manifest/记录文件时，不需要更新架构图。
