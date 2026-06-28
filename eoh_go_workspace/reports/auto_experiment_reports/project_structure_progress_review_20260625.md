# agent_go 当前进展与代码结构多 Agent 梳理

日期：2026-06-25  
范围：`agent_go` 全仓库代码、TOCC 当前实验结果、报告/归档结构、Codex agent/skill 配置、复现性风险  
方法：主 agent + 3 个只读 explorer 子 agent 并行梳理

---

## 0. 一句话结论

`agent_go` 已经不再只是早期的 Guarded EOH-Go / RAG 消融脚本，而是演进成了一个围绕 **TOCC（Trace-Conditioned Operator-Card Controller）** 的研究型实验框架。

当前主线是：

```text
上一轮 run trace
-> 诊断搜索偏差和失败模式
-> 选择 operator cards / query / arm config
-> gatekeeper 校验
-> manifest runner 执行 bounded EOH
-> summarizer 汇总 objective、valid rate、best code、success funnel
-> card memory 合成 history cards
-> 下一轮继续选卡
```

当前最可靠实验信号来自 **CVRP**：

```text
CVRP tocc_corrected: n=8, 8/8 优于 pure mean, mean improvement 约 -4.2%
CVRP default_rag: 5/5 degenerate / seed-only collapse
```

这说明当前最强证据不是“RAG 普遍有效”，而是：

```text
operator-card 选择本身是关键控制变量；
TOCC 通过 trace-conditioned card selection 可以避免 default RAG 的错误先验，并把搜索导向有效区域。
```

---

## 1. 多 Agent 审查分工与结论

### 1.1 子 Agent 分工

| Agent | 任务 | 结论 |
|---|---|---|
| 代码结构 explorer | 梳理 `eoh_go/`、`tests/`、Python 模块职责 | Python 侧约 13k 行，测试约 3.5k 行；核心分层清晰，但仍是研究型 pipeline |
| 实验进展 explorer | 梳理 `auto_experiment_reports/`、`paper_notes/`、`.codex/goals/` | CVRP repeat-level positive，TSP exploratory，history-card memory 链路已通但未证明收益 |
| 工程复现 explorer | 梳理 AGENTS、skills、README、requirements、Makefile、git hygiene | agent 分工清楚；最大缺口是干净机器复现、外部 EOH 路径、依赖声明和 env ignore |

### 1.2 验证命令

工程复现 explorer 实际运行：

```bash
PYTHONPATH=. PYTHONPYCACHEPREFIX=/tmp/agent_go_pycache python3 -m pytest tests -q -p no:cacheprovider
# 192 passed, 1 warning

go build -o /tmp/eoh_go_mainbin .
# passed

bash -n scripts/install_codex_skills.sh
# passed
```

未运行 `make test`，因为当前 `Makefile` 的 test target 会写 `final_result.txt`，不符合只读梳理要求。

---

## 2. 当前研究方法定位

### 2.1 TOCC 定义

TOCC 全称：

```text
Trace-Conditioned Operator-Card Controller
```

中文可表述为：

```text
基于运行轨迹的算子卡片控制器
```

TOCC 不是替代 EOH 的搜索算法。EOH 仍然负责：

- population evolution
- LLM mutation / generation
- evaluator scoring
- candidate selection

TOCC 控制的是 EOH 前面的 **生成先验**：

```text
本轮应该给 LLM 注入哪些 operator-card prior？
应该避免哪些错误 card？
是否应该降预算、换 query、换问题、停止或继续？
```

### 2.2 与普通 RAG 的区别

普通 RAG：

```text
query -> top-k retrieval -> prompt
```

TOCC：

```text
trace -> diagnosis -> selected_card_ids / query / arm_config -> gatekeeper -> bounded run
```

关键区别：

| 维度 | 普通 RAG | TOCC |
|---|---|---|
| 输入 | 当前 query | 上一轮 run trace |
| 控制对象 | 检索 top-k | operator-card subset 和实验配置 |
| 风险控制 | 通常较弱 | gatekeeper + success funnel |
| 输出解释 | 检索分数 | trace-backed diagnosis |
| 论文贡献 | 上下文增强 | search steering / context-selection controller |

### 2.3 与 MCTS / BO 的类比

| 框架 | 搜索空间 | 控制器 |
|---|---|---|
| MCTS | game tree nodes | selection policy |
| Bayesian Optimization | continuous parameters | acquisition function |
| TOCC | LLM-generated heuristic programs | trace-conditioned card selection policy |

TOCC 控制的不是采样点，而是 LLM 生成启发式程序时看到的先验。

---

## 3. 仓库总体结构

当前仓库根目录：

```text
agent_go/
├── AGENTS.md                         # 多 agent 治理规则
├── README.md / README_CN.md           # 项目说明
├── main.go / routing.go               # Go 动态调度求解器
├── eoh_go/                            # Python 控制面
├── Agent_EOH/                         # patched EOH core
├── eoh_go_workspace/                  # 实验数据、corpus、reports、problems
├── tests/                             # Python tests
├── .codex/                            # agents/goals/prompts
├── codex_skills/                      # 项目本地 Codex skills
├── docs/                              # skill 安装等文档
├── scripts/                           # 安装/辅助脚本
├── solomon_benchmark_d25/d50/d75/      # VRP 动态 benchmark 数据
└── archived_experiments/              # 历史归档
```

代码规模：

| 区域 | 规模 |
|---|---:|
| `eoh_go/**/*.py` | 约 13,050 行 |
| `tests/test_*.py` | 约 3,495 行 |
| Go solver | `main.go` 约 28k bytes，`routing.go` 约 10k bytes |
| 当前 reports 主目录 | 约 1.8M |
| 历史 reports archive | 约 17M |

---

## 4. Go 层结构

### 4.1 根目录 Go solver

| 文件 | 作用 |
|---|---|
| `main.go` | 动态 dispatch / InsertShips / Optimization / JSON 输入输出 / 主求解流程 |
| `routing.go` | 路径规划、RoutingTS、单车 TSPTW 类逻辑 |
| `go.mod`, `go.sum` | Go module |

Go 层不是主要研究贡献，而是 EOH/TOCC 操作的目标环境。

历史上已经做过两条防御性修复：

1. `AddShip` 边界检查：避免 `StaIndexesLen >= MAXSHIPS` 时越界写。
2. `read_json` 错误检查：避免损坏 JSON 变成零值输入并产生虚假适应度。

### 4.2 Go 层可进化目标

当前 `registry.py` 已把多个目标抽象成 Python spec：

| 目标函数 | 问题类型 | 当前用途 |
|---|---|---|
| `InsertShips` | 动态 VRP 新订单插入 | 早期 Guarded EOH-Go 主线 |
| `Optimization` | 跨车辆调整 / route improvement | 计划迁移目标之一 |
| `RoutingTS` | 单车路径求解 | Go 层已有，但不是当前主要 EOH target |
| `SplitOrders` | 搅拌车 / mixer split | 已纳入 registry/problem smoke |
| `ScoreBin` | Online Bin Packing | official EOH / toy benchmark 迁移 |
| `SelectItems` | Knapsack | smoke / 迁移可行性 |

---

## 5. Python 控制面结构

### 5.1 `eoh_go/eoh_runner/`：EOH 调用与 target 规格

职责：

```text
配置 EOH 参数
注册 target/problem spec
调用 Agent_EOH
注入 RAG context
过滤候选代码
返回 run result + rag_trace
```

关键文件：

| 文件 | 作用 | 成熟度 |
|---|---|---|
| `config.py` | `EOHConfig`，集中管理 LLM、RAG、仿真、目标函数参数 | 较成熟 |
| `target_spec.py` | 单个可进化函数的签名、regex、prompt target | 较成熟 |
| `problem_spec.py` | problem-level spec | 较成熟 |
| `registry.py` | 注册 `InsertShips`、`Optimization`、`ScoreBin`、`SplitOrders` 等 | 较成熟 |
| `runner.py` | `run_v0_eoh()`，封装 Agent_EOH 调用和 RAG env 注入 | 中等成熟 |
| `candidate_guard.py` | 过滤 missing code、penalty objective、异常低值、缺少关键调用等 | 中等成熟 |

主要风险：

- `runner.py` 依赖 `sys.path` 和 `os.environ` 动态注入，不适合并发嵌套运行。
- Go 函数抽取主要靠正则，复杂格式可能失败。
- registry 支持的 target 多于部分 CLI 暴露能力，入口还不完全统一。
- guard 是启发式过滤，不等于完整语义验证。

### 5.2 `eoh_go/rag/`：RAG / card corpus / prompt context

职责：

```text
CorpusItem schema
corpus build/load/filter
keyword retriever
prompt context formatter
best code -> history card synthesis
```

关键文件：

| 文件 | 作用 |
|---|---|
| `schemas.py` | 定义 `CorpusItem` JSONL schema |
| `build_corpus.py` | 加载/构建 `algorithm_cards`、`api_constraints`、`failure_cases`、`code_examples` |
| `retriever.py` | 轻量关键词打分检索 |
| `prompt_context.py` | 两段式 prompt：API/WARNINGS + STRATEGY CARDS |
| `card_synthesis.py` | 从 best_code 抽特征并合成 `history_*` card |

当前 RAG 设计变化：

1. `api_constraint` 固定前置，不参与 top-k。
2. `failure_case` 不占 strategy top-k，只作为 warning。
3. `algorithm_card` 是策略卡，参与检索/注入。
4. `history_*` cards 是自动合成的经验卡，但需要 gate 和 prior audit。

主要风险：

- 检索是 lexical scoring，不是 embedding，query 和 tags 很重要。
- history card 容易把“整段代码总结”变成过强先验，因此必须拆小算子。
- context 仍按字符预算截断，可能切断卡片内容。

### 5.3 `eoh_go/experiments/`：实验入口与 TOCC 主体

这是当前最核心的目录。

| 文件 | 作用 |
|---|---|
| `official_eoh_run.py` | 官方 EOH benchmark runner；支持 pure/api/literature/history/mixed/context arms |
| `run_experiment_manifest.py` | manifest 驱动实验执行，支持 dry-run/resume/force/selected_card_ids |
| `summarize_manifest_runs.py` | 自动汇总 objective、valid rate、success funnel、best code、card memory |
| `operator_card_controller.py` | TOCC V1 规则 controller |
| `tocc_agent.py` | TOCC V2 LLM proposer |
| `tocc_gatekeeper.py` | V2 proposal rule gatekeeper |
| `tocc_v2_pipeline.py` | proposer -> gatekeeper pipeline |
| `tocc_v3_loop.py` | bounded V3 auto-loop pilot |
| `card_prior_decisions.py` | 读取 card audit 决策供 controller/gatekeeper 使用 |
| `eoh_arrival_grid.py` | 早期 VRP arrival/density grid |
| `summarize_rag_ablation.py` | RAG ablation 汇总 |
| `eoh_obp_smoke.py`, `knapsack_smoke.py`, `mixer_split_smoke.py` | 新问题 smoke 迁移 |
| `build_*` 系列 | 早期 paper/table/chart 生成脚本 |

成熟度判断：

- TOCC 主链路：中等偏成熟，已有 tests 和真实 smoke。
- 官方 EOH runner：可用，但对 `/private/tmp/EoH-main` 和 venv 路径有外部依赖。
- 老 paper/chart 脚本：历史价值大于当前主线价值，已部分归档。

### 5.4 `eoh_go/operator/`：Smart Operator 原型

职责：

```text
LLM directed mutation
self-repair
failure memory
strategy templates
smart operator grid
```

关键文件：

| 文件 | 作用 |
|---|---|
| `agent_controller.py` | SmartOperator 主控制器 |
| `directed_mutate.py` | 直接调用 OpenAI-compatible API 生成 Go `InsertShips` |
| `self_repair.py` | 编译失败后让 LLM 修复 |
| `failure_memory.py` | 持久化失败模式 |
| `strategy_templates.py` | 无 API 模板策略生成 |

定位：

这是早期 “operator 智能化” 原型层。它和当前 TOCC 有关系，但不是当前论文最强主线。

主要风险：

- API 调用逻辑与其他 runner 重复。
- 目标函数偏 `InsertShips`，对 TSP/CVRP/BP 迁移少。
- 会写 workspace memory，适合研究，不适合作为纯函数库。

---

## 6. TOCC 当前工程闭环

### 6.1 V1：规则 controller

输入：run summary / trace。

输出：

```json
{
  "diagnosis": "baseline_overlap | wrong_bias | valid_collapse | context_truncated | api_failure | no_issue",
  "selected_card_ids": ["..."],
  "query": "...",
  "next_action": "run | retry | stop",
  "why": ["trace-backed evidence"]
}
```

主要诊断：

| diagnosis | 含义 | 行动 |
|---|---|---|
| `baseline_overlap` | 选卡与 baseline/best family 重叠 | 换差异化 card |
| `wrong_bias` | 错误 history / blocked card 进入 prompt | gate 拦截或换卡 |
| `valid_collapse` | valid candidates 太少 | 降低 top-k / API-only / 换卡 |
| `context_truncated` | context 截断 | 降预算或减少 cards |
| `api_failure` | 模型/API/环境失败 | retry 或修环境 |

### 6.2 V2：LLM proposer + rule gatekeeper

V2 的定位不是 autonomous agent，而是：

```text
LLM as trace-conditioned proposal generator
```

LLM proposer 可以提出 cards/query/arm，但必须经过 gatekeeper。

Gatekeeper 检查：

- 字段完整；
- card id 存在；
- problem prefix 匹配；
- 没有 forbidden fields；
- blocked/split_required cards 不得进入；
- deprioritized card 必须给 trace-backed reason；
- selected_card_ids 与实际注入必须可验证。

### 6.3 V3：bounded loop

V3 把 V2 proposal 接入 runner 和 summarizer：

```text
trace -> proposer -> gatekeeper -> manifest arm -> official run -> summary -> next trace
```

当前 V3 是 bounded pilot，不是无限自动跑。每次必须有：

- manifest；
- run budget；
- stopping condition；
- exploration analyst / gatekeeper review；
- raw artifacts 不入 git。

---

## 7. Operator Card 体系

### 7.1 Card 类型

| 类型 | 来源 | 是否参与 strategy top-k | 作用 |
|---|---|---|---|
| `api_constraint` | 手工接口规则 | 否，固定前置 | API 调用、fallback、安全规则 |
| `literature card` | 文献/经典启发式 | 是 | regret、farthest、savings 等策略先验 |
| `history card` | best code 自动合成 | 是，但受 gate/prior 约束 | 复用项目内已发现模式 |
| `failure warning` | guard/失败经验 | 否或弱注入 | timeout、suspicious-low、invalid 风险提醒 |

### 7.2 Skill card 格式

当前正确形态：

```text
Skill: name
When: trigger condition
Do: concrete operation
Fallback: safe fallback
Safety: validity constraint
```

设计原则：

1. card 是过程指令，不是参考文档；
2. card 应短、小、可组合；
3. API skeleton 不是 algorithm_card；
4. failure_case 不能挤占 strategy top-k；
5. history card 必须拆成小算子，不应直接复制完整最优代码。

### 7.3 Card memory loop

当前已打通：

```text
EOH best_code
-> extract_strategy_features(code)
-> synthesize_card(problem, features)
-> append_card_to_corpus(algorithm_cards.jsonl)
-> history_rag / mixed_rag retrieval
-> selected_card_ids exact injection
-> next official run
```

但当前结论边界是：

```text
history-card memory 已经可控接入；
但未证明 history prior 比 literature-only 更好。
```

---

## 8. 当前实验结果梳理

### 8.1 当前核心证据目录

```text
eoh_go_workspace/reports/auto_experiment_reports/
├── tocc_current_progress_20260619.md
├── tocc_current_progress_20260619.pptx
├── tocc_best_code_records.md
├── tocc_stabilization_report.md
├── tocc_stabilization_repeats/
├── tocc_day1_cvrp_repeat5/
├── tocc_day2_cvrp_real_evolution_gen4/
├── tocc_day2_tsp_pure_gen4/
├── tocc_day2_tsp_tocc_gen4/
├── tocc_day2_tsp_real_evolution_gen4/
├── tocc_history_card_audit_20260619/
├── tocc_history_mixed_cvrp_smoke/
└── tocc_split_history_cvrp_smoke/
```

### 8.2 主要实验结论

| 方向 | 当前结论 | 可写进论文程度 |
|---|---|---|
| CVRP gen=0 | `tocc_corrected` n=8，8/8 优于 pure mean，约 -4.2% | 当前最可靠正面证据 |
| CVRP default_rag | 5/5 seed-only / valid collapse | 强负对照 |
| CVRP gen=4 | `tocc_corrected` n=5，对 pure gen=4 仍正向 | 辅助证据 |
| TSP gen=0 | 方差过大，有好结果也有 outlier | 不作为主证据 |
| TSP gen=4 | `tocc_corrected` mean 比 pure 低约 1.4% | exploratory positive |
| History mixed | 链路已通，但未超过 literature-only | 可写为控制变量/负结果 |

### 8.3 最关键的方法发现

CVRP 中，`default_rag` 和 `tocc_corrected` 的差异不是“有没有 RAG”，而是 **选了哪张 card**。

```text
default_rag:      cvrp_far_first + cvrp_nearest_capacity
tocc_corrected:   cvrp_far_first + cvrp_regret_insertion
```

结果：

```text
default_rag -> valid collapse / seed-only
tocc_corrected -> 8/8 优于 pure mean
```

这支持一个更强、更精准的论点：

```text
RAG context 本身不是充分条件；
operator-card selection 是 LLM heuristic evolution 的关键 steering variable。
```

### 8.4 Success Funnel

当前 success funnel 五层：

| 层级 | 指标 | 成功定义 |
|---|---|---|
| Trace Diagnosis | `diagnosis_success` | 诊断引用 trace 证据且与 trace 一致 |
| Proposal Validity | `proposal_accept_rate` | proposal 通过 gatekeeper |
| Runner Linkage | `linkage_success` | requested cards == actual injected cards |
| Generation Validity | `generation_success` | valid candidates 足够，无 valid collapse |
| Objective Signal | `objective_success` | best objective 优于 pure/default reference |

当前缺口：

```text
diagnosis_success 还不能完全自动统计；
需要人工 reviewer 或独立 LLM judge。
```

---

## 9. 报告、论文与归档结构

### 9.1 当前报告入口

| 路径 | 用途 |
|---|---|
| `eoh_go_workspace/reports/README.md` | reports 总布局 |
| `eoh_go_workspace/reports/auto_experiment_reports/README.md` | 当前 TOCC evidence set 说明 |
| `tocc_current_progress_20260619.md` | 当前进展总报告 |
| `tocc_current_progress_20260619.pptx` | 当前汇报 PPT |
| `tocc_best_code_records.md` | 最优代码和 verified score |
| `tocc_stabilization_report.md` | 稳定性实验总结 |

### 9.2 论文资料

```text
eoh_go_workspace/reports/paper_notes/
```

其中已有：

- `tocc_method_section_draft_20260618.md`
- `tocc_related_work_draft_20260619.md`
- `tocc_related_work_map.md`
- `heurigym_2025_reading_note.md`
- `cobench_2025_reading_note.md`
- `heuragenix_2025_reading_note.md`
- `coevo_ahd_2026_reading_note.md`
- `a2dept_2026_reading_note.md`
- `llm_co_agent_literature_survey_20260609.md`

### 9.3 历史归档

```text
archived_experiments/reports_20260619/
```

主要归档：

- 早期 Guarded EOH-Go 表格；
- RAG ablation；
- 旧 paper figures；
- 20260426 中文/英文草稿；
- 旧 TOCC pilot 和 V2 validation；
- standalone 旧 PPT。

这些可以用于背景和演进叙事，但当前论文主证据应优先引用 `auto_experiment_reports/`。

---

## 10. Agent / Skill / Governance 结构

### 10.1 AGENTS.md 角色体系

核心 agent：

| Agent | 权限 | 用途 |
|---|---|---|
| `scout` | 只读 | 范围映射、文件定位、风险识别 |
| `implementer` | 可写 | 唯一允许改文件 |
| `gatekeeper` | 只读 | 正确性、安全、覆盖率、交付审查 |
| `verifier` | 只读 | 测试、smoke、命令证据 |

TOCC 专用：

| Agent | 权限 | 用途 |
|---|---|---|
| `rag_researcher` | 只读 | RAG、文献、外部 repo |
| `exploration_analyst` | 只读 | 实时监控 EOH/TOCC 实验，建议 continue/stop/change_cards |

### 10.2 Experiment Tier

| Tier | 含义 |
|---|---|
| E0 | 只读分析、报告清理 |
| E1 | dry-run、no-run、summary regen |
| E2 | smoke：`gen <= 1` 且 `runs <= 2` |
| E3 | repeat：`runs 3-20` 且 `gen <= 1` |
| E4 | deep evolution：`gen > 1` 或 `runs > 20` |
| E5 | paper-level matrix |

这套分级对当前科研项目非常重要，因为：

```text
前期探索不应强制大量 repeat；
但论文稳定结论必须经过 repeat / paper-level matrix。
```

### 10.3 项目 skills

当前仓库内新增：

```text
codex_skills/
├── tocc-research-workflow/
├── tocc-presentation/
└── tocc-pseudocode/
```

安装脚本：

```text
scripts/install_codex_skills.sh
```

文档：

```text
docs/codex_skills.md
```

当前风险：

- `docs/codex_skills.md` 中提到外部 skill 名 `algo-reconstruct`，但安装目录名可能是 `gen-pseudocode-skill`，命名需统一。
- `install_codex_skills.sh --force` 采用先删后复制，若中断可能半安装；后续建议改成临时目录 + 原子替换。

---

## 11. 测试结构

当前测试约 3,495 行。

| 测试文件 | 覆盖重点 |
|---|---|
| `test_eoh_runner_specs.py` | target/problem specs、regex、evaluator |
| `test_rag_runner_integration.py` | RAG env 注入、路径防护、corpus mode |
| `test_rag_build_corpus.py` | corpus 构建和过滤 |
| `test_rag_prompt_context.py` | prompt context 两段式输出 |
| `test_rag_retriever.py` | keyword retrieval |
| `test_card_synthesis.py` | best code -> history card |
| `test_operator_card_controller.py` | TOCC V1 诊断 |
| `test_tocc_gatekeeper.py` | V2 proposal gate |
| `test_tocc_v3_loop.py` | V3 bounded loop |
| `test_experiment_manifest_runner.py` | manifest runner |
| `test_summarize_manifest_runs.py` | auto summarizer / funnel |
| `test_official_eoh_run.py` | official runner glue |
| `test_smart_operator.py` | smart operator 原型 |

最新只读审查中通过：

```text
192 passed, 1 warning
go build passed
bash -n scripts/install_codex_skills.sh passed
```

---

## 12. 当前主要风险与缺口

### P1：干净机器复现仍不完整

证据：

- `official_eoh_run.py` 默认依赖 `/private/tmp/EoH-main`。
- `run_experiment_manifest.py` 默认依赖 `/private/tmp/eoh_official_venv/bin/python`。
- README 没完整说明如何准备官方 EOH checkout 和 venv。

影响：

```text
本机能跑，不代表 clone 后能跑。
```

建议：

1. 增加 `scripts/setup_official_eoh.sh` 或 `docs/reproducibility.md`。
2. 把 `/private/tmp/...` 做成 manifest/config 参数。
3. 在 README 里明确 “单测可复现” 与 “真实 LLM/EOH 实验可复现” 的差异。

### P1：requirements 不完整

当前 `requirements.txt` 偏窄，但代码里还有：

- `requests`
- `torch`
- `python-docx`
- `numba`

这些在 Agent_EOH 子路径中被使用。单测可能不触发，但完整路径会触发。

建议：

```text
分成 base requirements 和 optional-official-eoh requirements。
```

### P1：环境密钥文件 ignore 不完整

已有 `.env.example`，但 `.gitignore` 未忽略：

```text
/.env
/.env.*
!.env.example
```

风险：

```text
真实 API key 如果误放 repo root，会进入 git status。
```

### P2：Makefile 输出污染

`make test` 会追加写：

- `final_result.txt`
- `final_result_genetic.txt`

但 `.gitignore` 未忽略。

### P2：skill 命名和安装脚本需统一

`algo-reconstruct` 是 skill frontmatter name，`gen-pseudocode-skill` 是安装目录名。建议文档写清：

```text
folder: gen-pseudocode-skill
trigger/name: algo-reconstruct
```

### P2：TSP 结论边界要严格

TSP gen=4 有正向信号，但仍是 exploratory，不应写稳定提升。

### P2：history-card memory 是链路贡献，不是效果贡献

当前应写：

```text
history-card memory loop 可控接入；
objective 上还没有证明 history prior 带来收益。
```

---

## 13. 当前论文叙事建议

### 13.1 可以写

```text
TOCC 将 operator-card injection 形式化为 trace-conditioned context-selection / search-steering 问题。
```

```text
CVRP 上，TOCC 通过替换错误 card，把 default RAG 的 valid collapse 转为 repeat-level positive signal。
```

```text
当前证据显示：RAG 是否有效不是二元问题；关键在于 trace-conditioned card selection。
```

```text
history-card memory loop 已经打通，但需要 gate 和 prior audit，否则历史最优代码可能变成过强或错误先验。
```

### 13.2 不建议写

```text
TOCC 已稳定提升所有问题。
RAG 一定有效。
history prior 已证明有效。
TSP 已统计显著。
V3 可以无人值守跑大矩阵。
```

### 13.3 当前论文贡献候选

1. **方法贡献**：提出 TOCC，把 operator-card injection 定义为 trace-conditioned context selection。
2. **工程贡献**：实现 manifest -> runner -> trace -> summarizer -> card memory 的闭环。
3. **诊断贡献**：提出 success funnel，区分 proposal、linkage、generation、objective、diagnosis 成功。
4. **实验发现**：CVRP 上 card selection 是关键控制变量；default RAG 可能比 pure 更差。
5. **负结果贡献**：history-card memory 不可默认增强，必须经过 gate/prior audit。

---

## 14. 下一步建议

### 14.1 先修复复现性

优先级最高：

1. 补 `.env` ignore；
2. 补 Makefile 输出 ignore；
3. 拆分 `requirements.txt`；
4. 写 `docs/reproducibility.md`；
5. 外部 EOH path 参数化。

这是“能不能让别人 clone 后跑起来”的基础。

### 14.2 整理论文初稿

建议先写：

```text
Introduction
Method: TOCC
System: C+L+V harness + manifest runner + success funnel
Experiments: CVRP main evidence + TSP exploratory + history-card negative/control
Related Work: EOH, FunSearch, ReEvo, HeuriGym, CO-Bench, HeurAgenix
Limitations
```

### 14.3 新问题迁移

不要继续无限堆 TSP/CVRP repeat。下一阶段更应该验证：

```text
manifest -> selected cards -> trace -> summary -> diagnosis
```

能否迁移到新问题。

候选：

- Online Bin Packing；
- Knapsack；
- Mixer SplitOrders；
- 官方 EOH TSP/CVRP benchmark 的更多 instance；
- HeuriGym/CO-Bench 风格 benchmark 子集。

### 14.4 自动 diagnosis_success

success funnel 目前最弱的是第 5 层 diagnosis_success。建议设计：

```text
trace evidence extractor
-> diagnosis claim
-> rule-based consistency check
-> optional independent LLM judge
```

这会让 TOCC 更像真正 tool-using research agent。

---

## 15. 本次梳理产物与边界

本次执行：

- 读取 `AGENTS.md` 和 `.codex/prompts/task-template.md`；
- 启动 3 个只读 explorer 子 agent；
- 本地主 agent 读取当前报告、goal、目录结构、代码行数；
- 汇总成本文档。

本次没有：

- 修改实验数据；
- 执行真实 LLM 实验；
- 读取或打印 API key；
- 改动代码逻辑。

子 agent verdict：

| Agent | Verdict |
|---|---|
| 代码结构 explorer | PASS with risks |
| 实验进展 explorer | PASS with caveats |
| 工程复现 explorer | WARNING：复现性和 git hygiene 仍有 P1/P2 缺口 |

总体 verdict：

```text
WARNING, but healthy research codebase.
```

解释：

```text
方法主线、实验闭环和代码分层已经成型；
但如果目标是论文/开源复现，下一步必须优先补干净机器复现、依赖、env ignore 和外部 EOH setup。
```

