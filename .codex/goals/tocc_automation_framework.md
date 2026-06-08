/goal: Trace-Conditioned Operator-Card Controller 自动化实验闭环

目标：把 `agent_go` 从“人工选卡 + 人工跑命令 + 人工汇总”的实验方式，升级为一个可长期执行的自动化 Literature-RAG / EoH 实验框架。核心方法名采用 **Trace-Conditioned Operator-Card Controller (TOCC)**，不要在论文主叙事里泛称 ReAct Agent；只在实现描述中说它是 ReAct-style closed-loop experimental controller。

报告一律写中文。实验产物不入 git；关键报告、manifest、controller 决策记录、best code 摘要可以入 git。API key 不读取、不打印、不 echo；如需确认，只输出布尔值。

---

## 0. 方法定位

当前阶段的核心判断：

```text
RAG 是否有效，不取决于“有没有注入上下文”这一粗粒度变量，
而取决于“选中了哪些 operator cards”。
```

因此本长期 goal 的主线不是继续手动找 best objective，而是把 operator-card selection 做成自动化控制层：

```text
previous run trace
-> diagnose search bias / failure mode
-> select operator-card subset + query
-> run EOH
-> observe objective / valid rate / code features
-> update card memory and write report
```

论文口径：

> We formulate operator-card injection as a context-selection problem, and propose TOCC: a trace-conditioned controller that diagnoses search bias from run traces and selects the next operator-card subset to steer LLM-based heuristic evolution.

关键区分：

```text
EOH 负责执行搜索：LLM 通过 genetic operators 生成 heuristic programs。
TOCC 不替代 EOH 搜索；TOCC 控制搜索方向：
它选择注入哪种 operator-card prior，改变 LLM 生成启发式程序时的生成偏置。
```

因此，TOCC 的贡献不是“多跑一个 agent”，而是把 heuristic evolution 中的知识注入变成可反馈、可诊断、可复现的 context-selection / search-steering 问题。控制对象不同是重点：

| 框架 | 搜索空间 | 控制器 |
|---|---|---|
| MCTS | game tree nodes | selection policy, such as UCT |
| Bayesian optimization | continuous parameters | acquisition function, such as EI |
| TOCC | LLM-generated heuristic programs | trace-conditioned operator-card policy |

TOCC 控制的不是采样位置，也不是直接修改 EOH 的遗传算子，而是系统性地选择哪类启发式知识作为 LLM 的生成先验。

---

## 1. 已复用的现有能力

必须优先复用，不重复造轮子：

| 能力 | 现有文件 / 模块 | 复用方式 |
|---|---|---|
| 官方 EoH 对齐 runner | `eoh_go/experiments/official_eoh_run.py` | 作为统一 run action，不新写官方 EoH 调用逻辑 |
| problem/API 配置 | `OFFICIAL_RAG_PROBLEM_CONFIG` | 复用 problem-specific API cards 和 strategy prefixes |
| RAG corpus | `eoh_go_workspace/rag/corpus/*.jsonl` | 继续使用 `CorpusItem` schema |
| 检索与打分 | `eoh_go/rag/retriever.py` | 复用 `score_corpus()` 和 `retrieve()` |
| prompt context | `eoh_go/rag/prompt_context.py` | 复用 API RULES + RETRIEVED STRATEGY CARDS 两段式格式 |
| 目标/问题 registry | `eoh_go/eoh_runner/target_spec.py`, `problem_spec.py` | 作为后续自定义 problem 的边界定义 |
| 现有实验记录 | `eoh_go_workspace/local_runs`, `local_notes`, `reports` | 作为 TOCC v1 的离线输入 |
| 测试门禁 | `tests/test_official_eoh_run.py`, `tests/test_rag_*` | 每次改 infrastructure 后必须跑 |

不复用的原因必须写清楚；默认不得新增重复的 retriever、prompt formatter 或 official runner。

---

## 2. 最小新增内容

本 goal 允许新增的最小内容：

```text
eoh_go/experiments/operator_card_controller.py
eoh_go/experiments/run_experiment_manifest.py
eoh_go/experiments/summarize_manifest_runs.py
eoh_go_workspace/experiments/manifests/*.yaml 或 *.json
eoh_go_workspace/reports/auto_experiment_reports/*.md / *.json
tests/test_operator_card_controller.py
tests/test_experiment_manifest_runner.py
```

如果可以先用 JSON，优先 JSON，避免引入 PyYAML 新依赖。若必须用 YAML，需要同步更新 `requirements.txt` 并解释原因。

---

## 3. 总体闭环

目标闭环：

```text
Experiment Manifest
  -> TOCC chooses or validates card policy
  -> official_eoh_run executes arms
  -> trace / population / samples_best collected
  -> summarizer writes tables + diagnosis + best code snippets
  -> card memory updated
  -> next recommended experiment generated
```

统一输入：

```json
{
  "suite": "week_tocc_tsp_cvrp",
  "model": "JoyAI-LLM-Pro",
  "problems": ["tsp_construct", "cvrp_construct"],
  "arms": [
    {
      "name": "pure_eoh",
      "runner_arm": "pure_eoh",
      "context_strategy": "none"
    },
    {
      "name": "api_only",
      "runner_arm": "api_only",
      "context_strategy": "api_rules_only"
    },
    {
      "name": "default_rag",
      "runner_arm": "literature_rag",
      "context_strategy": "default_retrieval",
      "rag_query": null,
      "selected_card_ids": []
    },
    {
      "name": "targeted_rag",
      "runner_arm": "literature_rag",
      "context_strategy": "tocc_selected_cards",
      "rag_query": "tsp construct regret farthest lookahead route length",
      "selected_card_ids": ["tsp_regret_insertion", "tsp_farthest_insertion"]
    }
  ],
  "generations": [0, 4],
  "pop_size": 8,
  "repeats": 3,
  "max_runs": 2,
  "max_llm_calls_estimate": 64,
  "require_confirm_for_real_run": true,
  "rag": {
    "top_k": 2,
    "max_chars": 2500
  }
}
```

`name` 是报告展示名；`runner_arm` 必须映射到现有 `official_eoh_run.py` 支持的 arm：`pure_eoh`、`api_only`、`literature_rag`、`history_rag`、`context_file`。不得因为报告名不同而新造 runner arm。

`max_runs` 约束的是展开后的总 run 数：`len(problems) * len(arms) * len(generations) * repeats`。如果 manifest 示例中的完整矩阵超过 `max_runs`，runner 默认只允许 `--dry-run` / `--no-run`；真实运行必须显式缩小矩阵或加 `--force` 并记录用户确认。

统一输出：

```text
run_manifest.json
per_run_trace.json
card_decisions.jsonl
summary.json
summary.md
best_code_snippets.md
next_actions.md
```

---

## 4. TOCC v1: 规则版 Controller

TOCC v1 不做复杂学习，先做规则版。输入上一轮 trace 和 corpus，输出 diagnosis、card set、query、risk、recommended next action。

### 输入字段

```text
problem
arm
rag_query
rag_selected_items
rag_all_scores
rag_context_chars
rag_context_truncated
valid_candidates
population_size
best_objective
best_code
baseline_family
```

`baseline_family` 来源优先级：

```text
1. per-problem 配置中声明的 baseline family；
2. pure_eoh / api_only 的 best_code 静态特征分析；
3. 人工审查写入的 run metadata。
```

缺失时填 `unknown`，不得为了触发 `baseline_overlap` 伪造。

### Trace adapter

必须先写一个轻量 trace adapter，统一 `official_eoh_run.py` 与 `eoh_runner/runner.py` 的字段口径。现状中部分字段只存在于一条链路，例如 `rag_context_truncated` 在 `eoh_runner/runner.py` 中存在，但 official runner 可能只给 `rag_context_chars`。

要求：

```text
缺失字段填 null，不得伪造。
summary 中列出 schema_gap 字段。
TOCC 诊断只能使用真实存在或可从文件验证的字段。
如果缺少 rag_context_truncated，则不能直接触发 context_truncated，只能标记 needs_context_length_check。
```

### 输出字段

```json
{
  "problem": "tsp_construct",
  "diagnosis": "baseline_overlap",
  "recommended_cards": ["tsp_regret_insertion", "tsp_farthest_insertion"],
  "recommended_query": "tsp construct regret farthest lookahead second best route length",
  "why": [
    "default nearest cards overlap with baseline family",
    "regret card adds lookahead",
    "farthest card adds spatial diversity"
  ],
  "risk": "may over-prioritize distant nodes; run init-only smoke first",
  "next_action": "run_init_only"
}
```

### 诊断规则

| failure mode | 检测条件 | 推荐动作 |
|---|---|---|
| `baseline_overlap` | selected cards 与 pure/baseline 代码族同质，如 nearest / best-fit | 换 regret / farthest / residual / savings 等改变搜索偏好的卡 |
| `wrong_bias` | selected cards 带来明显错误方向，如 CVRP capacity-first 变差 | 降权或排除该 card family，换 target-specific diversity cards |
| `low_diversity` | 多个样本代码几乎同一 recipe，unique objective 很少 | 引入互补 card，或降低 recipe 强约束 |
| `context_truncated` | `rag_context_truncated=true` 或 selected card body 不完整 | 降低 top_k、压缩 card、只保留 API + 1 张策略卡 |
| `valid_collapse` | valid rate 低或 generation failed 多 | 使用 API-only / simpler cards / shorter context |
| `api_failure` | run log 出现连续 API failed | 标记 run incomplete，不纳入 deep comparison |
| `budget_mismatch` | arms 的 gen/pop/repeats 不一致 | 禁止写确认性结论，只能写 exploratory observation |

### Problem-specific 初始策略

| problem | baseline-overlap cards | targeted candidate cards |
|---|---|---|
| `tsp_construct` | nearest_neighbor, nearest_insertion | regret_insertion, farthest_insertion, two_opt_awareness |
| `cvrp_construct` | nearest_capacity, capacity_slack | regret_insertion, far_first, savings, sweep |
| `bp_online` | first_fit, best_fit, worst_fit | residual_poly, util_sqrt_exp, harmonic |
| `vrp_insertships` | first_feasible, least_cost | regret2, farthest, savings, solomon_i1 |

注意：`vrp_insertships` 不走 `official_eoh_run.py` 当前 problem choices，属于非 official runner 路径。P0/P1 manifest runner 只覆盖 `bp_online`、`tsp_construct`、`cvrp_construct`；若要纳入 `vrp_insertships`，必须先实现单独的 runner adapter。

---

## 5. Experiment Manifest Runner

新增 manifest runner 的职责：

```text
读取 manifest
展开 problem x arm x repeat x generation
为每个 run 生成独立 output_dir
调用 official_eoh_run.py 或已有 problem smoke runner
失败不中断整个 suite
写 run_index.json
写每个 run 的 status, trace, summary path
```

关键要求：

- 不读取或打印 API key。
- 支持 `--dry-run`，只打印将要执行的命令和输出路径。
- 支持 `--resume`，跳过已完成 run。
- 支持 `--no-run`，只做 manifest 验证。
- 长时间真实实验默认使用 `caffeinate`，但不能把 raw env 写入报告。
- 若 API 连续失败，标记 `incomplete_api_failure`，不继续无限重试。

最小命令形态：

```bash
PYTHONPATH=. python3 -m eoh_go.experiments.run_experiment_manifest \
  --manifest eoh_go_workspace/experiments/manifests/week_tocc_tsp_cvrp.json \
  --output-dir eoh_go_workspace/reports/auto_experiment_reports/week_tocc_tsp_cvrp \
  --dry-run
```

---

## 6. Auto Summarizer

自动汇总器必须生成中文报告，不能只给 JSON。

### 报告必须包含

1. suite 总览
2. 每个 problem 的 per-arm 表
3. selected cards / query / context chars 表
4. valid rate / population size / unique objective 诊断
5. best objective 表，但明确 best-score oriented，不默认统计显著
6. 代码演化片段：每个 problem 至少 2 段
7. failure / incomplete run 列表
8. TOCC diagnosis 和 next recommended actions

### 结论措辞约束

允许：

```text
观察到正向 best-score 信号
当前单次 run 给出最低 best
default retrieval 可能存在 baseline overlap
targeted card selection 改变了生成代码结构
```

禁止，除非有 repeat/statistics 支撑：

```text
明确有效
稳定优于
sweet spot 已确定
BP 不适合 RAG
已证明
```

---

## 7. Card Memory

长期需要维护 card memory，用来支撑后续从规则版 TOCC 走向 bandit / memory-based selection。

建议格式：

```text
eoh_go_workspace/experiments/card_memory/operator_card_outcomes.jsonl
```

这是长期可提交的研究资产，不是 raw run 状态。如果后续只是记录运行缓存，则放到已 ignore 的 `eoh_go_workspace/memory/tocc/`。

每行：

```json
{
  "timestamp": "2026-06-08T00:00:00+08:00",
  "problem": "tsp_construct",
  "target": "select_next_node",
  "card_set": ["tsp_regret_insertion", "tsp_farthest_insertion"],
  "query": "tsp construct regret farthest lookahead second best route length",
  "arm": "targeted_rag",
  "gen": 4,
  "pop": 8,
  "repeat": 1,
  "best_objective": 6.28736,
  "valid_rate": 1.0,
  "context_chars": 1917,
  "status": "positive",
  "confidence": "single_run",
  "diagnosis": "baseline_overlap_fixed",
  "run_dir": "..."
}
```

`status` 使用短 enum，如 `positive`、`neutral`、`negative`、`incomplete`；`confidence` 单独记录证据强度，如 `single_run`、`repeated`、`statistical_tested`。无 repeat/statistics 时不得解释为稳定有效。

后续可以将 card set 视为 bandit arm：

```text
reward = -objective_improvement - lambda * invalid_rate - mu * context_cost
```

---

## 8. 阶段计划

### Phase 0: 工程边界与 schema 对齐

不跑 LLM，先修执行边界。

交付：

```text
.gitignore raw-run 规则确认或更新
trace adapter schema 说明
manifest arm mapping schema
```

验收：

- `.gitignore` 必须覆盖 raw run 目录：`eoh_go_workspace/local_runs/**`、`eoh_go_workspace/reports/official_eoh_runs/**`、`eoh_go_workspace/reports/auto_experiment_reports/**/run_*`。
- 对关键 raw 路径运行 `git check-ignore` 断言，确认 raw samples、population、run log、临时 `_run_official_eoh.py` 会被 ignore；`git status --short --ignored` 只作为辅助检查。
- manifest arm 必须通过 `runner_arm` 映射到现有 official runner arm，不得新造不支持的 arm。
- trace adapter 对缺失字段输出 `null` 和 `schema_gap`。
- 非 `--dry-run` / `--no-run` 时，如果展开后的总 run 数超过 `max_runs`，或任一 run 的 `generations > 1`，runner 必须报错并要求 `--force` 或显式用户确认，避免误跑大矩阵。

### Phase 1: 离线 TOCC Controller

不跑 LLM，只读已有 TSP/CVRP/BP run。

交付：

```text
operator_card_controller.py
tests/test_operator_card_controller.py
eoh_go_workspace/reports/auto_experiment_reports/tocc_offline_diagnosis.md
```

验收：

- 能对 TSP default nearest 输出 `baseline_overlap`
- 能对 CVRP old capacity 输出 `wrong_bias`
- 能对 BP default best_fit/first_fit 输出 `baseline_overlap`
- 能推荐 TSP regret+farthest、CVRP regret+far_first、BP residual/util
- 所有输出包含 why/risk/next_action

### Phase 2: Manifest + dry-run

不跑真实 LLM，先验证自动实验规划。

交付：

```text
run_experiment_manifest.py
week_tocc_tsp_cvrp.json
run_index.dry_run.json
```

验收：

- manifest schema 校验通过
- dry-run 输出所有命令
- output_dir 唯一且可 resume
- invalid manifest 报错清楚

### Phase 3: Existing Runs Summarizer

先用已有实验产物验证汇总器。

交付：

```text
summarize_manifest_runs.py
summary.md
summary.json
best_code_snippets.md
```

验收：

- 能复现 TSP/CVRP/BP 阶段性报告中的关键数字
- 自动标记 TSP gen16 为 partial/incomplete
- 自动标记 gen4/gen8 为 independent runs
- 结论措辞符合 exploratory 约束

### Phase 4: 小规模真实闭环

只跑最小闭环，不扩大矩阵。

推荐：

```text
TSP: 读已有 default run summary -> TOCC 诊断 baseline_overlap -> 触发 regret+farthest init-only 或 gen=1 smoke
CVRP: 读已有 old/fixed run summary -> TOCC 诊断 wrong_bias/baseline_overlap -> 触发 regret+far_first init-only 或 gen=1 smoke
BP: 读已有 default run summary -> TOCC 诊断 baseline_overlap/context issue -> 触发 residual/util init-only only
```

验收：

- 每个 problem 至少产生一条 TOCC decision record
- run summary 与 TOCC recommendation 对齐
- 报告能解释 why this next action

### Phase 5: 论文级消融准备

只有 Phase 1-4 稳定后再做。

需要：

- 多 seed repeat
- budget-aligned arms
- random cards
- oracle/manual targeted cards
- TOCC selected cards
- mean/std/median/best
- paired or non-parametric test（如 Wilcoxon）

---

## 9. 多 agent 审查门禁

每个阶段必须有只读审查，不直接落地改动。按仓库既有 L 级流程命名，不另造 reviewer 角色：

```text
scout -> implementer -> gatekeeper -> verifier
```

其中 `gatekeeper` 负责方法口径、数据口径、实验安全和报告措辞审查；`verifier` 负责命令验收和 git/artifact 边界检查。

| 阶段 | reviewer | 审查点 |
|---|---|---|
| Phase 0 后 | gatekeeper | gitignore、arm mapping、trace schema 是否可执行 |
| Phase 1 后 | gatekeeper | TOCC diagnosis 是否只是硬编码结果；是否能泛化到新 trace |
| Phase 1 后 | gatekeeper | 推荐 cards 是否与 trace 证据一致 |
| Phase 2 后 | verifier | manifest schema、resume、output path、安全边界 |
| Phase 3 后 | gatekeeper | 数字、路径、best/latest/best-so-far 口径 |
| Phase 4 后 | gatekeeper | API failure、timeout、valid collapse、context truncation |
| 入 git 前 | gatekeeper | P0/P1 是否修完；实验产物是否误入仓库 |

P0/P1 必须修完才能提交。

---

## 10. Git 与产物边界

允许入 git：

```text
.codex/goals/tocc_automation_framework.md
.gitignore
eoh_go/experiments/operator_card_controller.py
eoh_go/experiments/run_experiment_manifest.py
eoh_go/experiments/summarize_manifest_runs.py
tests/test_operator_card_controller.py
tests/test_experiment_manifest_runner.py
eoh_go_workspace/experiments/manifests/*.json
eoh_go_workspace/experiments/card_memory/operator_card_outcomes.jsonl
eoh_go_workspace/reports/auto_experiment_reports/<suite>/summary.md
eoh_go_workspace/reports/auto_experiment_reports/<suite>/summary.json
eoh_go_workspace/reports/auto_experiment_reports/<suite>/best_code_snippets.md
eoh_go_workspace/reports/auto_experiment_reports/<suite>/next_actions.md
eoh_go_workspace/reports/auto_experiment_reports/<suite>/card_decisions.jsonl
```

其他 `local_notes` / `reports` 文件必须逐文件说明理由后才能入 git。

默认不入 git：

```text
eoh_go_workspace/local_runs/**
eoh_go_workspace/reports/official_eoh_runs/**
eoh_go_workspace/reports/auto_experiment_reports/**/run_*
raw population JSON
raw samples JSON
generated binaries
.DS_Store
```

提交前必须检查：

```bash
git status --short
git status --short --ignored
PYTHONPATH=. python3 -m unittest discover -s tests -q
python3 -m compileall -q eoh_go
```

阶段级验收命令：

```bash
PYTHONPATH=. python3 -m eoh_go.experiments.run_experiment_manifest \
  --manifest eoh_go_workspace/experiments/manifests/week_tocc_tsp_cvrp.json \
  --no-run

PYTHONPATH=. python3 -m eoh_go.experiments.run_experiment_manifest \
  --manifest eoh_go_workspace/experiments/manifests/week_tocc_tsp_cvrp.json \
  --output-dir eoh_go_workspace/reports/auto_experiment_reports/week_tocc_tsp_cvrp \
  --dry-run

PYTHONPATH=. python3 -m eoh_go.experiments.summarize_manifest_runs \
  --input eoh_go_workspace/reports/auto_experiment_reports/week_tocc_tsp_cvrp \
  --no-card-memory-write
```

如果修改 Go 层，再跑：

```bash
go build -o /tmp/eoh_go_mainbin .
```

---

## 11. 本周建议交付

本周不追求新增大规模 best objective。主交付是自动化框架。

优先级与 Phase 对齐：

```text
P0 = Phase 0-3：只读 / dry-run / existing-run summarizer，不跑真实 LLM。
P1 = card memory 初始记录 + 自动阶段报告 + 多 agent 审查。
P2 = 1-2 个 gen<=1 的最小真实 smoke。
Phase 5 不属于本 goal 当前验收范围，只作为论文级后续准备。
```

P0：

```text
工程边界与 schema 对齐
TOCC v1 offline controller
existing-run summarizer
manifest dry-run
```

P1：

```text
用已有 TSP/CVRP/BP 结果生成一份自动化阶段报告
补 card_memory 初始记录
用多 agent 审查报告口径
```

P2：

```text
跑 1-2 个最小真实 smoke，验证 controller -> runner -> summarizer 可以端到端运行
```

导师汇报口径：

> 上周已经观察到 targeted cards 在 TSP/CVRP 上有正向信号。这周重点不是继续手动跑 best，而是把人工 targeted 选卡升级为 TOCC 自动控制层：读取上一轮 trace，诊断 default retrieval 为什么失败，自动推荐 operator cards，并通过 manifest runner 和 summarizer 形成可复用实验闭环。
