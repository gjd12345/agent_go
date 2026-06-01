/goal: EoH 原始问题对齐实验 —— Online Bin Packing 上验证 RAG / History-RAG 是否优于 vanilla EoH

目标：在 EoH 原始论文的 Online Bin Packing (OBP) 问题上，构建一个最小但可复现的 C+L+V 对照实验，比较 vanilla EoH、Literature-RAG EoH、History-RAG EoH 在相同 target、相同 evaluator、相同 query budget 下的表现。核心问题不是再证明 harness 能跑，而是验证“在 EoH 已经证明可进化的同一问题上，加入文献/历史经验是否比原始 EoH 更快或更稳地产生好 heuristic”。

研究判断：Knapsack 当前单实例已经 DP 最优，Mixer 当前 objective 近似被 largest-capacity seed 打到下界，因此它们适合展示跨问题可行性，不适合作为 RAG 有效性主证据。Online Bin Packing 是 EoH 原论文最强主例，target 小、指标清晰、文献结果明确，适合作为下一阶段主线。

报告一律写中文。实验产物不入 git，汇总和关键 best code 入报告。API key 不读取、不打印、不 echo。

---

## 依据：EoH 原始论文和官方实现

EoH 原论文测试了三个问题：

| 问题 | EoH 中的可进化对象 | 对本项目价值 |
|---|---|---|
| Online Bin Packing | `score(item, bins)`，给 feasible bins 打分 | 最优先，target 小且提升明显 |
| Traveling Salesman Problem | 构造式 next-node / GLS objective update | 第二优先，适合后续做 route heuristic |
| Flow Shop Scheduling | GLS / perturbation heuristic | 可做但工程成本较高 |

EoH 官方 `bp_online` example 的核心 target：

```python
def score(item: int, bins: np.ndarray) -> np.ndarray:
    """Score each bin for assigning the current item. Higher score = preferred bin."""
    return bins
```

论文中 OBP 关键证据：

- EoH 在 Online Bin Packing 上显著优于 First Fit / Best Fit，并优于 FunSearch 的若干设置。
- Table 1 中，Best Fit 在 `1k C100` gap 为 4.87%，EoH 为 2.24%；Best Fit 在 `1k C500` gap 为 4.50%，EoH 为 2.13%。
- Table 5 显示 prompt/evolution 变体中 EoH 最稳：`1k C500` EoH=2.13%，EoH-e2=5.86%，EoC=150.89%。
- Table 6 显示 thought+code 共同进化明显优于只用 code 或只用 thought：C2C avg 2.57，T2T2C avg 2.13，EoH avg 0.66。
- Table 8 显示加入 expert heuristic 更强：FunSearch avg 0.97，EoH avg 0.66，EoH expert avg 0.55。

这直接支持我们的 RAG 假设：把已有专家 heuristic / 文献 heuristic 作为 context 或初始经验输入，有机会在同 budget 下改善 EoH。

---

## 当前状态快照

已完成并可作为背景：

| Target | Problem | Evidence | 结论 |
|---|---|---|---|
| `InsertShips` | VRP dynamic insertion | 多轮正式实验 + 代码演化 | 已有 RAG/API/history 提升证据 |
| `Optimization` | VRP route/order improvement | smoke | 同一 Go solver 内多 target 可行，未超过 seed |
| `SelectItems` | Knapsack | smoke | 跨问题可行，当前实例已 DP 最优，不适合验证 RAG 提升 |
| `SplitOrders` | Mixer/concrete truck split | smoke | 导师问题可迁移，当前 objective 提升空间太小 |

下一步主线：新增或对齐 `bp_online` / `ScoreBin`，用 EoH 原始问题验证 RAG 是否比 vanilla EoH 更有帮助。

---

## 全局执行规则

- 这是一个 research-first goal。先读 EoH 原论文和官方 `bp_online` example，再动代码。
- 不再优先改 Knapsack/Mixer evaluator，除非只是记录状态或修 blocking bug。
- 只保留一个主要 EOH 实验进程，避免 generated workspace 冲突。
- 长时间实验默认使用：
  ```bash
  caffeinate -i -m -s <command>
  ```
- 加载 API 配置只用：
  ```bash
  set -a
  source ~/.config/agent_go/chatrhino.env
  set +a
  ```
- 禁止输出 API key、key 前缀、Authorization header。
- generated code 只通过 guarded evaluator 路径执行。
- 每轮结果记录：`gap_to_lb`、`used_bins`、`lower_bound`、`valid_candidates`、`rag_trace`、`rag_context_chars`、`rag_global_items`、`best code`。
- 只用 evaluator 汇总指标做性能结论；population objective 可记录但不能作为最终结论。
- 报告写中文；具体进化出来的 best code 必须列入报告。
- 实验原始产物默认不入 git，除非用户明确要求；报告、目标文档、必要代码入 git。

---

## Phase 0: 论文和代码调研（P0）

目标：形成 EoH-OBP 对齐实现规格，避免改造后发现 target 不适合进化。

必读来源：

1. EoH 原论文 ICML 2024 / OpenReview PDF。
2. EoH official GitHub `examples/bp_online`。
3. FunSearch OBP heuristic（作为 expert/literature source）。
4. 经典 OBP heuristics：First Fit、Best Fit、Worst Fit、Harmonic、residual-capacity penalty。

输出到本地中文记录：

```text
eoh_go_workspace/reports/eoh_obp_research_plan.md
```

记录内容：

- EoH 原始 OBP target、evaluator、数据分布、指标。
- 官方 `score(item, bins)` 的签名和行为。
- EoH 论文中可对齐的 baseline 数字。
- 哪些 heuristic 可以转成 skill cards。
- 我们的最小复现实验设置和差异说明。

验收：

- 报告说明为什么 OBP 比 Knapsack/Mixer 更适合验证 RAG 有效性。
- 报告给出可执行的 target/function/evaluator 设计。
- 不要求这一步跑 LLM。

---

## Phase 1: 新增 OBP / ScoreBin 最小 harness（P0）

目标：新增一个能本地跑通的 Online Bin Packing target，不先追求性能。

建议设计：

| 项 | 值 |
|---|---|
| ProblemSpec | `bin_packing_online` |
| Target | `ScoreBin` 或 `ChooseBin`，优先 `ScoreBin` |
| 语言 | Go 或 Python 均可；为贴近现有 guarded evaluator，优先 Go wrapper + generated Go function |
| 可进化函数 | `func ScoreBin(item int, remaining []int, capacity int) []float64` |
| evaluator | sequential online packing，选择 score 最大的 feasible bin |
| 指标 | used_bins / lower_bound，gap_to_lb = `(used_bins-lb)/lb` |
| lower bound | `ceil(sum(items)/capacity)` |
| baseline | First Fit / Best Fit / seed score |

最小数据：

- capacity=100。
- 先用 5 个小中型 instances（例如 200 items），确保 Best Fit 不是总能打到下界。
- 数据生成可固定 seed，保存在 `eoh_go_workspace/problems/bin_packing_online/testdata/`。

安全要求：

- generated code 只替换 `ScoreBin`。
- evaluator 子进程 scrub env，不传 API key。
- `ScoreBin` 输出长度必须等于 feasible bins 数量；NaN/Inf/长度错误直接 penalty。
- 不允许 generated code 读取文件、网络或环境变量；如 Go skeleton 需要 `os` 只在 main 中使用，子进程环境仍需 allowlist。

验收：

- seed evaluator 本地跑通。
- First Fit / Best Fit baseline 可计算。
- 单元测试覆盖：valid score、invalid length、NaN/Inf、env scrub、lower bound/gap。

---

## Phase 2: Literature-RAG skill cards for OBP（P1）

目标：让 Literature-RAG 给 OBP 提供真正有信息量的 expert heuristic，不再使用 VRP cards。

新增 corpus 条目：

| id | 类型 | 内容 |
|---|---|---|
| `obp_first_fit` | algorithm_card | 按 bin 顺序选择第一个 feasible bin |
| `obp_best_fit` | algorithm_card | 选择放入后剩余容量最小的 feasible bin |
| `obp_worst_fit` | algorithm_card | 选择剩余容量最大的 feasible bin，保留中等空隙 |
| `obp_harmonic` | algorithm_card | 按 item size class 使用分桶策略 |
| `obp_funsearch_residual_poly` | algorithm_card | residual capacity polynomial / penalty idea |
| `obp_eoh_util_sqrt_exp` | algorithm_card | utilization + sqrt(diff) + exp decay hybrid |
| `obp_api_skeleton` | api_constraint | `ScoreBin` 输入输出、安全约束 |

Skill card 格式保持：

```text
Skill: ...
When: ...
Do: ...
Fallback: ...
Safety: ...
```

要求：

- 每张 `content <= 450 chars`。
- `obp_api_skeleton <= 400 chars`。
- `filter_corpus_by_mode("literature")` + target alias 应能让 `ScoreBin` 只拿 OBP-relevant cards。
- 不让 InsertShips/VRP cards 干扰 OBP。

验收：

- 本地 trace：`rag_global_items` 包含 `obp_api_skeleton`。
- `rag_selected_items` 至少包含 1 个 OBP algorithm_card。
- context <= 2500 chars。

---

## Phase 3: 最小对照实验（P1）

目标：同一 OBP evaluator 上比较 vanilla vs literature-RAG；若时间允许再加 history-RAG。

实验矩阵（最小版）：

| Arm | RAG | 参数 | repeats |
|---|---|---|---:|
| Vanilla EoH | off | gen=3, pop=8 | 1 |
| Literature-RAG | `rag_mode=literature`, top_k=3 | gen=3, pop=8 | 1 |
| History-RAG | `rag_mode=history` | gen=3, pop=8 | optional |

如果 API 额度/时间紧，降级为：gen=1 pop=8 smoke + 本地 evaluator / trace 证明，不声称性能。

记录指标：

- best used_bins
- lower_bound
- gap_to_lb
- valid_candidates
- first_valid_generation
- best code
- RAG selected cards
- 是否出现 EoH/FunSearch 类似结构：`diff`、`sqrt`、`exp`、`utilization`、`penalty`

验收：

- 至少 vanilla 和 Literature-RAG 各完成一组。
- 如果 Literature-RAG 没提升，也要报告原因：seed 是否过强、实例是否太小、cards 是否未被选中、valid rate 是否崩。
- 所有 best code 片段写进中文报告。

---

## Phase 4: 报告和决策（P1）

输出/更新：

```text
eoh_go_workspace/reports/eoh_obp_research_plan.md
eoh_go_workspace/reports/clv_harness_weekly_showcase.md
```

报告必须包含：

1. 为什么从 Knapsack/Mixer 转向 OBP。
2. EoH 原论文 OBP 的 target 和结果摘要。
3. 我们的 C+L+V 对齐设计。
4. vanilla vs literature/history-RAG 的结果表。
5. best generated code，不只写策略描述。
6. 下一步建议：扩大 instance / repeats，还是转 TSP/GLS。

最终判断格式：

| 结论类型 | 允许说法 |
|---|---|
| 跑通 | OBP harness + RAG trace 生效 |
| 初步有效 | Literature-RAG 在同 budget 下 gap 更低或更早出现有效 heuristic |
| 未验证 | 只完成 smoke、无提升或实例太小 |
| 不成立 | 多轮重复后 RAG 不如 vanilla，且 trace/card 选择无明显问题 |

---

## Phase 5: Git 和交付

完成任意实质进展都要记录并推送。

提交范围：

- goal 文档。
- OBP harness 源码和测试。
- OBP corpus skill cards。
- 中文研究/实验报告。

不提交：

- API key / env。
- raw 大型实验产物，除非用户明确要求。
- `.DS_Store`。
- 导师 zip 原始包。

最终响应必须包含：

- files changed
- commands run
- test results
- subagent verdicts（如启用）
- unresolved risks
- merge recommendation
