# TOCC 自动化实验闭环当前进展

日期：2026-06-19

## 1. 当前一句话结论

TOCC（Trace-Conditioned Operator-Card Controller）已经从“手工选择 RAG 卡片”推进到“trace 诊断 -> 选卡/门禁 -> manifest 执行 -> trace 汇总 -> history card 记忆”的自动化实验闭环。当前最可靠的正面证据来自 CVRP：`tocc_corrected` 在 8 次重复中全部优于 pure EOH 均值，平均改善约 4.2%；TSP 在 gen=4 下有小幅 exploratory 正向信号；history-card memory 已经打通，但目前不能写成“history prior 带来收益”。

## 2. 已完成的工程闭环

| 模块 | 状态 | 说明 |
|---|---|---|
| V1 规则 TOCC | PASS | 根据 trace 规则诊断 baseline overlap、valid collapse、wrong bias，并给出 card/query |
| V2 LLM proposer | PASS | LLM 产生 proposal，rule gatekeeper 检查字段、card、风险边界 |
| V3 bounded loop | PASS | proposal -> runner -> summary -> 下一轮诊断的小闭环已跑通 |
| Manifest runner | PASS | 支持 pure/default/tocc/history/mixed 等 arm，支持 selected_card_ids 精确注入 |
| Auto summarizer | PASS | 自动输出 summary、success_funnel、best code snippet、card-memory 选卡记录 |
| Card memory loop | PASS | best_code -> feature extraction -> history card -> algorithm_cards.jsonl -> 下轮检索 |
| History-card gate | PASS | 复合 history card 会被 gate 拦截；拆分卡、watchlist、deprioritize 决策已接入 |
| Prior-aware controller | PASS | `card_prior_decisions.jsonl` 已进入 controller/gatekeeper，错误 prior 可被阻断或降权 |

## 3. TOCC 原理：控制搜索方向，而不是替代 EOH

TOCC 不替代 EOH 的启发式代码进化。EOH 仍然负责 population、mutation、LLM 生成代码和 evaluator 选择；TOCC 控制的是“下一轮给 LLM 注入什么 operator-card prior”。

闭环可以概括为：

```text
run trace
-> diagnose search bias / failure mode
-> select operator-card subset + query
-> gatekeeper validates proposal
-> manifest runner executes bounded EOH
-> summarize objective / valid rate / linkage / code features
-> update report and card memory
```

论文中更准确的表述是：

```text
Trace-conditioned operator-card selection for steering LLM-based heuristic evolution.
```

它不是泛泛的 ReAct agent，而是一个面向启发式程序进化的 search-steering controller。

### 3.1 与 EOH / RAG 的关系

| 层级 | 负责什么 | 当前实现 |
|---|---|---|
| EOH | 生成和变异启发式代码，执行 population search | `Agent_EOH` + `official_eoh_run.py` |
| RAG | 把 operator cards 格式化进 prompt | `rag/retriever.py`, `rag/prompt_context.py` |
| TOCC | 根据 trace 诊断搜索偏差，选择下一轮 cards 和实验配置 | `operator_card_controller.py`, `tocc_gatekeeper.py`, `run_experiment_manifest.py` |

关键区别：

```text
普通 RAG:  query -> top-k cards -> prompt
TOCC:      trace -> diagnosis -> selected_card_ids/query/arm_config -> gate -> bounded run
```

TOCC 的方法贡献不是“再加一个 RAG prompt”，而是把 operator-card injection 形式化为 context-selection / search-steering 问题。

### 3.2 与 MCTS / BO 的类比

| 框架 | 搜索空间 | 控制器 |
|---|---|---|
| MCTS | game tree nodes | selection policy |
| Bayesian optimization | continuous parameters | acquisition function |
| TOCC | LLM-generated heuristic programs | trace-conditioned card selection policy |

TOCC 控制的不是采样点本身，而是 LLM 生成启发式程序时看到的先验。

## 4. Operator cards：TOCC 的控制动作

TOCC 的 action 不是直接改代码，而是选择 operator cards。当前 cards 分为四类：

| 类型 | 来源 | 是否参与 strategy top-k | 作用 |
|---|---|---|---|
| `api_constraint` | 手工接口规则 | 否，固定前置 | 保证函数签名、fallback、返回值、API 调用顺序 |
| `literature card` | 文献/经典启发式 | 是 | 提供 regret、farthest、savings 等策略先验 |
| `history card` | best_code 自动合成 | 是，但受 gate/prior decisions 约束 | 复用本项目已发现的代码模式 |
| `failure warning` | guard/失败经验 | 否或弱注入 | 提醒 timeout、suspicious-low、invalid 等风险 |

每张 strategy card 采用短指令格式：

```text
Skill: name
When: trigger condition
Do: concrete rule
Fallback: safe fallback
Safety: validity constraint
```

设计原则：

1. card 是过程指令，不是参考文档；
2. `api_constraint` 不参与检索竞争；
3. `failure_case` 不占用 strategy top-k；
4. `history card` 必须小算子化，不能把整段最优代码压成一个复合大卡。

## 5. TOCC 代码结构

### 5.1 核心 Python 模块

| 模块 | 文件 | 作用 |
|---|---|---|
| 目标注册 | `eoh_go/eoh_runner/target_spec.py`, `registry.py` | 定义 TSP/CVRP/BP 等可进化目标 |
| 官方 runner | `eoh_go/experiments/official_eoh_run.py` | 调用官方 EOH，构造 RAG context，输出 run summary |
| V1 controller | `eoh_go/experiments/operator_card_controller.py` | 读取 trace，规则诊断，输出 card/query/action |
| V2 agent | `eoh_go/experiments/tocc_agent.py`, `tocc_v2_pipeline.py` | LLM proposal + gatekeeper 的 agent-assisted 控制 |
| Gatekeeper | `eoh_go/experiments/tocc_gatekeeper.py` | 校验 proposal 字段、cards、风险、prior decisions |
| Manifest runner | `eoh_go/experiments/run_experiment_manifest.py` | 把 manifest 展开成 bounded runs，支持 `selected_card_ids` |
| Auto summarizer | `eoh_go/experiments/summarize_manifest_runs.py` | 汇总 objective、valid rate、funnel、best code、card-memory |
| History synthesis | `eoh_go/rag/card_synthesis.py` | 从 best_code 抽特征，合成 `history_*` cards |
| Prior decisions | `eoh_go/experiments/card_prior_decisions.py` | 读取 card audit 决策，供 controller/gatekeeper 共享 |

### 5.2 RAG 子系统

| 模块 | 文件 | 作用 |
|---|---|---|
| Corpus schema | `eoh_go/rag/schemas.py` | 定义 `CorpusItem` |
| Corpus build/filter | `eoh_go/rag/build_corpus.py` | 加载 literature/history/api/failure cards，按 mode 过滤 |
| Retriever | `eoh_go/rag/retriever.py` | 关键词打分，输出 top-k |
| Prompt context | `eoh_go/rag/prompt_context.py` | 两段式注入：GLOBAL API/WARNINGS + STRATEGY CARDS |
| Card synthesis | `eoh_go/rag/card_synthesis.py` | 自动合成 history cards |

### 5.3 实验与报告产物

| 产物 | 路径 |
|---|---|
| TOCC goal | `.codex/goals/tocc_automation_framework.md` |
| 主要 manifest | `eoh_go_workspace/experiments/manifests/tocc_*.json` |
| 自动实验报告 | `eoh_go_workspace/reports/auto_experiment_reports/` |
| 架构图 | `eoh_go_workspace/reports/figures/architecture_v3/v4/v5.drawio(.png)` |
| 方法草稿 | `eoh_go_workspace/reports/paper_notes/tocc_method_section_draft_20260618.md` |
| 相关工作图谱 | `eoh_go_workspace/reports/paper_notes/tocc_related_work_map.md` |
| best code 记录 | `eoh_go_workspace/reports/auto_experiment_reports/tocc_best_code_records.md` |

## 6. TOCC 执行流

### 6.1 V1：规则 controller

输入：`official_eoh_run_summary.json`。

输出：

```json
{
  "diagnosis": "baseline_overlap | wrong_bias | low_diversity | context_truncated | valid_collapse | api_failure | no_issue",
  "selected_card_ids": ["..."],
  "query": "...",
  "next_action": "run | retry | stop",
  "why": ["trace-backed evidence"],
  "risk": "..."
}
```

典型诊断：

| diagnosis | 触发 | 行动 |
|---|---|---|
| `baseline_overlap` | selected cards 与当前 best code family 重叠 | 换成更有差异的 cards |
| `wrong_bias` | 被审计 block 的 history card 或错误策略进入 prompt | 拒绝/替换 |
| `valid_collapse` | valid candidates 不足，种群坍缩 | 减少 cards、换 API-only 或降低复杂度 |
| `context_truncated` | prompt context 截断 | 降低 top-k / max chars |
| `api_failure` | 环境或 API 调用失败 | retry 或修 env |

### 6.2 V2：LLM proposer + gatekeeper

LLM 可以提出 proposal，但不能直接执行。Gatekeeper 负责：

1. 检查必需字段；
2. 限制最多 cards 数；
3. 校验 card id 是否属于当前 problem/family；
4. 阻断被 prior audit 标记为 `split_required` / `split_or_deprioritize` 的 cards；
5. 对 `candidate_deprioritized` 要求显式 trace-backed why；
6. 输出可执行 manifest arm。

### 6.3 V3：bounded loop

V3 把 V2 proposal 接到 runner 和 summarizer：

```text
trace -> proposer -> gatekeeper -> manifest arm -> official run -> summary -> next trace
```

当前 V3 仍是 bounded pilot，不是无限自动跑大矩阵。每轮实验必须有预算、manifest、run count 和停止条件。

## 7. History-card memory loop

History memory 的真实闭环已经实现：

```text
EOH best_code
-> extract_strategy_features(code)
-> synthesize_card(problem, features)
-> append_card_to_corpus(algorithm_cards.jsonl)
-> history_rag / mixed_rag retrieval
-> selected_card_ids exact injection
-> next official run
```

### 7.1 修复过的问题

| 问题 | 修复 |
|---|---|
| `history_rag` 曾走旧 `code_example` 分支 | `official_eoh_run.py` 改为检索 `history_{problem}_*` |
| `_is_history_card()` 误判外部文献卡 | 改为 `kind == algorithm_card` 且 `id.startswith("history_")` |
| 复合 history card 过大 | `card_synthesis.py` 限制最多 3 个核心特征 |
| history prior 默认混入导致变差 | 增加 gate + prior decisions |

### 7.2 Prior audit 结果

| 类别 | 处理 |
|---|---|
| 旧 `history_cvrp_construct_*` 复合卡 | block / split required |
| `history_cvrp_far_destination_seed` | candidate_deprioritized |
| `history_cvrp_capacity_feasible_filter` | candidate_deprioritized |
| `history_cvrp_remaining_aware_alpha` | candidate_watchlist |

方法含义：

```text
history prior 可控接入，但不能默认增强。
历史最优代码需要先拆成小 operator，再由 TOCC 根据 trace 选择。
```

## 8. Success funnel：为什么不只看 objective

TOCC 不只看 objective，而是分五层看 agent 是否真正成功：

| 层级 | 指标 | 成功定义 |
|---|---|---|
| Proposal Accept | `proposal_accept` | gatekeeper 通过，无 infra failure |
| Linkage | `linkage_success` | `selected_card_ids` 与实际 `rag_trace.rag_selected_items` 一致 |
| Generation | `generation_success` | valid candidates 达到阈值，无 valid collapse |
| Objective | `objective_success` | best objective 优于 pure baseline mean |
| Diagnosis | `diagnosis_success` | 诊断引用 trace 证据且与 trace 一致 |

这个漏斗解释了为什么 `default_rag` 不能算有效：它在 CVRP 上 objective 看似不差，但 generation 层 5/5 坍缩到 seed，本质上不是成功搜索。

## 9. 选卡追溯：每次实验必须记录什么

TOCC 的核心不是“有 RAG”，而是“为什么选这几张卡、实际有没有注入、注入后生成是否健康”。因此每次真实实验至少要保留以下记录：

| 字段 | 来源 | 用途 |
|---|---|---|
| `selected_card_ids` | manifest arm / gatekeeper output | 记录控制器请求注入的 cards |
| `rag_trace.rag_selected_items` | official runner | 记录实际进入 prompt 的 cards |
| `rag_trace.rag_global_items` | official runner | 记录固定前置 API rules / warnings |
| `rag_context_chars` | official runner | 判断 context 是否过长或被截断 |
| `valid_candidates / population_size` | run summary | 判断 generation 层是否坍缩 |
| `best_objective` | run summary | 判断 objective 层是否有收益 |
| `best_code_record_id` | summarizer | 绑定 best score 与真实代码 |
| `history_card_ids` | summarizer | 区分 literature-only、history-only、mixed |

当前 auto summarizer 已经把这些字段写入 summary 表格中的 “Card-memory / 选卡记录”。这一步非常关键：后续论文不能只说 “RAG 有效/无效”，而要说明是哪些 cards、在哪个问题、以什么 trace 证据被选中。

## 10. 当前核心实验结果

### 10.1 CVRP：当前最强正面证据

| arm | n | mean | min | max | valid rate | 结论 |
|---|---:|---:|---:|---:|---:|---|
| pure_eoh | 8 | 13.540 | 13.279 | 13.611 | 8/8 | baseline |
| default_rag | 5 | 13.283 | 13.283 | 13.283 | 0/5 generation success | 5/5 退化到 seed |
| tocc_corrected | 8 | 12.975 | 12.713 | 13.283 | 8/8 | 比 pure mean 改善约 4.2% |

关键发现：

1. `tocc_corrected` 的 8 次运行全部优于 pure mean，改善从早期 n=3 的 4.6% 收敛到 n=8 的 4.2%。
2. `default_rag` 5/5 出现 valid collapse，种群退化到 seed。
3. `default_rag` 与 `tocc_corrected` 的关键差异是一张卡：`cvrp_nearest_capacity` 换成 `cvrp_regret_insertion`。这说明“选卡”本身是有效控制变量。

### 10.2 TSP：方向正确，但仍是 exploratory

| arm | n | mean | min | max | 结论 |
|---|---:|---:|---:|---:|---|
| pure_eoh gen=0 | 3 | 6.751 | 6.590 | 7.057 | 方差较大 |
| tocc_corrected gen=0 | 5 | 7.372 | 6.189 | 9.656 | 同卡组合下 outlier 明显 |
| pure_eoh gen=4 | 3 | 6.548 | 6.430 | 6.608 | 进化深度降低方差 |
| tocc_corrected gen=4 | 3 | 6.456 | 6.292 | 6.615 | 小幅正向，约 1.4% |

TSP 不能写成稳定证明。当前只能写：在 gen=4 下，TOCC 从 gen=0 的高方差状态转为小幅 exploratory 正向信号。

### 10.3 History-card memory：链路打通，但收益未证明

已完成两轮真实 smoke：

| 实验 | arm | cards | best | valid |
|---|---|---|---:|---:|
| naive mixed history | literature_regret_far | `cvrp_regret_insertion`, `cvrp_far_first` | 13.09441 | 4/4 |
| naive mixed history | mixed_history_far_regret | `history_cvrp_construct_capacity_destination_farthest_085049`, `cvrp_regret_insertion` | 14.20996 | 4/4 |
| split history | literature_regret_far | `cvrp_regret_insertion`, `cvrp_far_first` | 12.72795 | 4/4 |
| split history | split_far_seed_regret | `history_cvrp_far_destination_seed`, `cvrp_regret_insertion` | 13.00458 | 4/4 |
| split history | split_capacity_filter_regret | `history_cvrp_capacity_feasible_filter`, `cvrp_regret_insertion` | 13.23646 | 4/4 |
| split history | split_remaining_alpha_far | `history_cvrp_remaining_aware_alpha`, `cvrp_far_first` | 12.96129 | 4/4 |

结论边界：

- 可以写：history card 已经可被检索、可被 selected_card_ids 精确注入、可被 TOCC 诊断和门禁。
- 不能写：history prior 已经带来 objective 收益。
- 当前更有价值的发现是：历史最优代码不能直接压成复杂大卡；必须拆成小 operator，并经过 gate/audit/prior decisions。

目前 CVRP 的正例来自两个层面：

1. `default_rag` 在 Generation 层失败，说明“有 RAG”不等于有效。
2. `tocc_corrected` 在 Generation 和 Objective 层都通过，说明 trace-conditioned 选卡确实改变了搜索方向。

## 11. 真实 best code 示例

报告和 PPT 后续必须展示“代码真的怎么变了”，不能只写策略变化。下面列出当前最有代表性的 best code 片段。

### 11.1 TSP gen=4 TOCC best：regret + farthest

来源：`tocc_day2_tsp_real_evolution_gen4/summary.md`

设置：

```text
problem: tsp_construct
arm: tocc_corrected
gen=4, pop=4
selected cards: tsp_regret_insertion, tsp_farthest_insertion
best score: 6.29166
valid: 4/4
```

代码片段：

```python
def select_next_node(current_node: int, destination_node: int,
                     unvisited_nodes: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    n_unvisited = len(unvisited_nodes)
    if n_unvisited <= 2:
        return unvisited_nodes[np.argmin(distance_matrix[current_node][unvisited_nodes])]
    dist_from_current = distance_matrix[current_node][unvisited_nodes]
    dist_to_dest = distance_matrix[destination_node][unvisited_nodes]
    regrets = []
    for i, u in enumerate(unvisited_nodes):
        d_curr = dist_from_current[i]
        d_dest = dist_to_dest[i]
        others = np.concatenate([unvisited_nodes[:i], unvisited_nodes[i+1:]])
        avg_dist_to_others = np.mean(distance_matrix[u][others])
```

解读：这不是单纯 nearest neighbor，而是在当前距离、终点距离和未访问节点间隔上构造 regret/farthest 混合信号。它支持“TOCC 注入的 regret + farthest cards 确实改变了代码结构”这一点，但不单独证明 TSP 稳定提升。

### 11.2 CVRP split-history literature-only best：regret + far-first

来源：`tocc_split_history_cvrp_smoke/summary.md`

设置：

```text
problem: cvrp_construct
arm: literature_regret_far
gen=0, pop=4
selected cards: cvrp_regret_insertion, cvrp_far_first
best score: 12.72795
valid: 4/4
```

代码片段：

```python
def select_next_node(current_node: int, depot: int, unvisited_nodes: np.ndarray,
                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    if len(unvisited_nodes) == 0:
        return depot
    dist_from_current = distance_matrix[current_node, unvisited_nodes]
    dist_from_depot = distance_matrix[depot, unvisited_nodes]
    max_curr_dist = np.max(dist_from_current) if len(dist_from_current) > 0 else 1.0
    min_curr_dist = np.min(dist_from_current) if len(dist_from_current) > 0 else 0.0
    range_curr = max_curr_dist - min_curr_dist
    if range_curr == 0:
        range_curr = 1.0
```

解读：该代码在距离归一化和远端客户优先之间构造 scoring，属于文献卡引导下的可执行策略。它也是 split-history smoke 中 objective 最好的 arm。

### 11.3 CVRP split-history watchlist：remaining-aware alpha

来源：`tocc_split_history_cvrp_smoke/summary.md`

设置：

```text
problem: cvrp_construct
arm: split_remaining_alpha_far
gen=0, pop=4
selected cards: history_cvrp_remaining_aware_alpha, cvrp_far_first
best score: 12.96129
valid: 4/4
```

代码片段：

```python
def select_next_node(current_node: int, depot: int, unvisited_nodes: np.ndarray,
                     rest_capacity: float, demands: np.ndarray,
                     distance_matrix: np.ndarray) -> int:
    if len(unvisited_nodes) == 0:
        return depot
    total_customers = len(demands) - 1
    remaining_ratio = len(unvisited_nodes) / total_customers if total_customers > 0 else 0.5
    alpha = min(1.0, max(0.0, remaining_ratio))
    if current_node == depot:
        dist_from_depot = distance_matrix[depot][unvisited_nodes]
        median_dist = np.median(dist_from_depot)
        far_candidates = unvisited_nodes[dist_from_depot >= median_dist]
```

解读：这段代码说明 history card 确实能引导 LLM 生成 “remaining-aware alpha” 结构；但 score 没有超过 literature-only，因此只能放入 watchlist，不能写成 history prior 的正例。

## 12. 当前代码与产物状态

### 12.1 已提交核心能力

| 能力 | 代表文件 |
|---|---|
| TOCC controller | `eoh_go/experiments/operator_card_controller.py` |
| Gatekeeper | `eoh_go/experiments/tocc_gatekeeper.py` |
| Manifest runner | `eoh_go/experiments/run_experiment_manifest.py` |
| Auto summarizer | `eoh_go/experiments/summarize_manifest_runs.py` |
| History card synthesis | `eoh_go/rag/card_synthesis.py` |
| Prior decisions | `eoh_go/experiments/card_prior_decisions.py` |
| Operator cards | `eoh_go_workspace/rag/corpus/algorithm_cards.jsonl` |
| 自动化实验报告 | `eoh_go_workspace/reports/auto_experiment_reports/` |

### 12.2 当前本地边界

当前仍有一个未归档实验产物修改：

```text
eoh_go_workspace/reports/auto_experiment_reports/tocc_split_history_cvrp_smoke/run_index.json
```

它可能来自后台或外部重新运行。只有在同步重生成 `summary.md`、`success_funnel.json` 和审查报告后，才允许提交；不能只提交 `run_index.json`，否则报告与原始索引会不一致。

`eoh_go_workspace/local_notes/` 是本地笔记，默认不提交。

## 13. 论文写作边界

```text
TOCC 已证明统计显著提升。
RAG 一定有效或一定无效。
TSP/CVRP 已足够支撑完整论文实验。
History-RAG 已经带来收益。
V3 可以直接自动跑大矩阵。
```

可以写：

```text
TOCC 是一个 trace-conditioned operator-card controller。
TOCC 已完成工程闭环，并在 CVRP 上取得 repeat-level positive signal。
TOCC 的价值包括：选对 card、阻断坏 prior、把失败分解到 success funnel。
history-card memory 已能接入闭环，但当前不是默认增强。
```

## 14. AGENTS.md 审稿结果

依据项目 `AGENTS.md`，本稿属于 E0 文档整理，不执行真实 LLM，不读取 API key，不修改实验流程。审稿结论：

| 审稿项 | 结论 | 证据 |
|---|---|---|
| 是否区分 smoke / repeat / paper evidence | PASS | CVRP 写为 repeat-level signal，TSP 写为 exploratory，history prior 写为 control finding |
| 是否区分 selected_card_ids 与实际 rag_trace | PASS | 第 9 节列出 linkage 字段和记录来源 |
| 是否避免稳定性夸大 | PASS | 第 13 节列出禁止写法 |
| 是否保留真实代码证据 | PASS | 第 11 节列出 TSP/CVRP best code snippets |
| 是否避免 raw artifacts 入仓 | PASS | 第 12.2 节明确未归档 run_index 不提交 |
| 是否符合中文报告要求 | PASS | 全文中文为主，英文术语仅作为方法名/字段名保留 |

剩余风险：

```text
1. diagnosis_success 仍需人工或 LLM reviewer 独立判断，目前不能自动统计。
2. 新 benchmark 迁移尚未完成，因此论文主张仍不能写成跨问题稳定提升。
3. split-history 的本地 run_index 有未归档改动，后续若要使用必须同步重生成 summary/funnel。
```

## 15. 下一步建议

### P1：论文初稿整合

把 `tocc_method_section_draft_20260618.md` 整理进论文初稿，但写成“TOCC 扩展层”和“实验控制框架”，不要覆盖原 Guarded EOH-Go 主线。重点写：

- operator-card injection 是 context-selection / search-steering 问题；
- TOCC 的五层 success funnel；
- CVRP 是当前 repeat-level positive signal；
- TSP 是 exploratory positive；
- history prior 是 negative/control finding。

### P1：新问题或新官方 benchmark

不再继续堆 TSP/CVRP repeat。下一步应选一个新问题或官方 benchmark，目标不是一次性追求大幅提升，而是验证：

```text
manifest -> runner -> selected_card_ids -> rag_trace -> best verified score -> best code snippet -> summary
```

整个链路能否无人工补洞地跑通。

### P2：实时探索 agent

把 `exploration_analyst` 固化成实验过程中的实时审查角色：

- 监控 valid rate、population size、selected cards、context truncation；
- 给出 continue / stop / change cards / reduce context / increase generation 的建议；
- 后续论文可以把“agent 成功率”作为方法指标之一，而不仅是 objective。

## 16. 本报告对应 PPT 结构

建议 PPT 采用 12 页：

1. 标题：TOCC 自动化实验闭环当前进展
2. 为什么需要 TOCC：EOH 生成代码，但缺少搜索方向控制
3. TOCC 原理：trace-conditioned card selection
4. Operator cards：literature / history / api / warning
5. 代码结构：controller / gatekeeper / manifest / summarizer / card memory
6. 执行流：V1 / V2 / V3
7. Success funnel：五层成功率
8. CVRP 证据：选卡决定 valid collapse vs improvement
9. TSP 证据：gen=4 exploratory positive
10. History-card memory：链路打通，但收益未证明
11. 当前边界：不能写的强结论
12. 下一步：论文初稿 + 新 benchmark 迁移 + exploration analyst
