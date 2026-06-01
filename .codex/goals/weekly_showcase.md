/goal: OBP 修正实验 —— 先提高生成有效率，再验证 Literature-RAG 是否优于 vanilla EoH

目标：在已经跑通的 Online Bin Packing (OBP) / `ScoreBin` harness 上，修正上一轮最小对照暴露的问题，再做一组更干净的 vanilla vs Literature-RAG 对照。核心不是扩大矩阵，而是先证明 EOH 能稳定产生接近 `pop_size` 的合法候选，并且 RAG context 完整、选卡有差异性。

当前结论必须保持克制：

```text
OBP 最小闭环已跑通；Literature-RAG trace 生效。
本轮未观察到提升，主要受候选生成失败和 context 截断影响。
当前结果不能证明 RAG 无效。
```

报告一律写中文。实验产物不入 git，汇总和关键 best code 入报告。API key 不读取、不打印、不 echo。

---

## 当前状态

已完成并推送：

```text
HEAD = 59fe783 feat(obp): add online bin packing showcase harness
origin/main = 59fe783
```

工程状态：

| 项 | 状态 |
|---|---|
| OBP Go evaluator | 已接入 |
| `ScoreBin` target | 已注册 |
| Agent_EOH example | 已接入 |
| OBP literature cards | 已接入 |
| `obp_api_skeleton` | 已接入 |
| target-specific RAG filtering | 已生效 |
| tests | `57 tests OK` |

本地未跟踪目录里有实验产物和 `.DS_Store`，默认不提交。

---

## 复核发现

### P1: 实际 population 太小

上一轮命令设置 `pop_size=8`，但最终 population 只有 2 条：

```text
1 条 seed
1 条 None / failed candidate
```

这说明上一轮不是“8 个候选都没有提升”，而是 EOH 实际只留下了 seed + 一个失败候选。vanilla 和 RAG 都没有统计意义。

优先排查：

- LLM 输出是否为空、非 Go code、markdown 包裹、函数签名不匹配。
- EOH parser 是否只保留了少量解析成功候选。
- generated candidate build/run 失败原因。
- `ScoreBin` prompt 是否让模型写出复杂但不合法的函数。

验收目标：

```text
population_size >= 5
valid_candidates >= 3
```

如果做不到，不扩大实验。

### P1: Literature-RAG context 被截断

上一轮 trace：

```text
rag_context_chars = 2500
rag_context_truncated = true
selected = obp_best_fit, obp_worst_fit, obp_first_fit
```

实际 prompt 中 `obp_first_fit` 只剩开头，`Do/Fallback/Safety` 没完整进入。这会削弱 RAG 的可执行性。

下一轮参数：

```text
rag_top_k = 1 或 2
rag_max_chars = 1200 到 1800
```

验收目标：

```text
rag_context_truncated = false
selected card 的 Skill/When/Do/Fallback/Safety 完整出现在 context
```

### P1: top-3 选卡太保守

当前 top-3：

```text
obp_best_fit
obp_worst_fit
obp_first_fit
```

其中 `obp_best_fit` 基本就是 seed，同类知识不太可能带来提升。更可能产生差异的是：

```text
obp_harmonic
obp_funsearch_residual_poly
obp_eoh_util_sqrt_exp
```

下一步不要只依赖默认 query。至少跑一个指定 query，让 residual/poly/utilization 进入 top-k。

建议 query：

```text
online bin packing ScoreBin residual polynomial utilization sqrt exp gap penalty avoid tiny unusable residual gaps
```

验收目标：

```text
rag_selected_items 包含 obp_funsearch_residual_poly 或 obp_eoh_util_sqrt_exp
```

### P2: trace global items 语义不精确

trace 中 `rag_global_items` 显示 3 个 failure_case，但 `prompt_context.py` 实际只注入第一个 warning。后续分析容易误判“模型看到了 3 个 warning”。

后续可改：

```text
rag_global_items_available
rag_global_items_injected
```

这不是当前阻塞项。若改，必须补测试。

---

## 当前最佳判断

工程质量：PASS。

实验结论：未验证。

不能说：

```text
Literature-RAG 对 OBP 无效
```

只能说：

```text
当前 gen=1 pop=8 smoke 中，vanilla 和 Literature-RAG 都只保住 seed；
主要瓶颈是候选生成/解析失败和 RAG context 截断；
需要先修实验设置，再比较性能。
```

---

## Phase A: 只读排查上一轮失败候选

目标：解释为什么 `pop_size=8` 最后只有 2 条 population。

只读检查：

```text
eoh_go_workspace/reports/tables/eoh_obp_showcase_20260601/vanilla/run_*/agent_eoh_results/
eoh_go_workspace/reports/tables/eoh_obp_showcase_20260601/literature/run_*/agent_eoh_results/
```

检查内容：

- `results/pops/population_generation_1.json`
- 是否有 `pops_best/`
- 是否有 raw response / generated code 临时文件
- failed candidate 的 code/error/traceback
- EOH 是否实际请求 8 个 LLM candidates，还是 operator/population 逻辑只产生 1 个 mutation

输出到中文报告：

```text
eoh_go_workspace/reports/eoh_obp_research_plan.md
```

记录：

- population 为什么只有 2 条。
- invalid candidate 的具体失败原因。
- 是否需要改 prompt、EOH operator、还是 evaluator。

---

## Phase B: prompt 稳定性修正

目标：让模型更容易生成合法 `ScoreBin`。

修改范围优先限于：

```text
Agent_EOH/eoh/src/eoh/examples/user_bin_packing_go/prompts_bin_packing_go.py
Agent_EOH/eoh/src/eoh/examples/user_bin_packing_go/seeds_bin_packing_go.json
tests/test_eoh_runner_specs.py
```

建议 prompt 增补：

```text
Use a simple formula-only scoring function.
Do not create structs, helper functions, goroutines, maps, file/env/network calls, or random logic.
Do not check infeasible bins; remaining already contains only feasible bins.
Always allocate scores := make([]float64, len(remaining)).
Fill every scores[i].
Return scores.
```

可选：增加 2 个 seed，但不要改变 evaluator：

1. best-fit seed
2. worst-fit seed
3. residual penalty seed

验收：

```text
PYTHONPATH=. python3 -m unittest tests.test_eoh_runner_specs -q
go run eoh_go_workspace/problems/bin_packing_online/bin_packing_solver.go eoh_go_workspace/problems/bin_packing_online/testdata/obp_5x60_c100.json
```

---

## Phase C: RAG context 修正实验

目标：跑小而干净的三组，不扩大矩阵。

固定：

```text
problem = bin_packing_online
target = ScoreBin
model = JoyAI-LLM-Pro
generations = 1
pop_size = 8
dataset = obp_5x60_c100
```

三组：

| Arm | RAG | 参数 | 目的 |
|---|---|---|---|
| Vanilla | off | - | 基线 |
| API-only | literature | `rag_top_k=0`, `rag_max_chars=900` | 只看 API skeleton 是否提升有效率 |
| Residual-RAG | literature | `rag_top_k=2`, `rag_max_chars=1800`, custom query | 强制非 seed 策略进入 context |

Residual-RAG query：

```text
online bin packing ScoreBin residual polynomial utilization sqrt exp gap penalty avoid tiny unusable residual gaps
```

运行命令必须使用：

```bash
set -a
source ~/.config/agent_go/chatrhino.env
set +a
caffeinate -i -m -s python3 -m eoh_go.experiments.eoh_obp_smoke ...
```

禁止打印 API key、key 前缀、Authorization header。

验收：

- 每组 summary 写出 `population_size`、`valid_candidates`、`best_gap_to_lb`。
- RAG 组写出 `rag_context_truncated`、`rag_context_chars`、`rag_selected_items`。
- Residual-RAG 必须选中 `obp_funsearch_residual_poly` 或 `obp_eoh_util_sqrt_exp`。
- 如果 population 仍然只有 2 条，停止，不再扩大实验。

---

## Phase D: 报告更新

更新：

```text
eoh_go_workspace/reports/eoh_obp_research_plan.md
eoh_go_workspace/reports/clv_harness_weekly_showcase.md
```

报告必须包含：

1. 上一轮复核结论：工程 PASS，实验未验证。
2. population 过小的实际证据。
3. context 截断证据。
4. top-k 选卡偏保守证据。
5. 修正后三组实验结果。
6. 每组 best code。不要只写策略描述。
7. 下一步判断：继续 OBP、改 Python target 对齐官方 `score(item,bins)`，还是转 TSP/GLS。

结论用词：

| 情况 | 允许说法 |
|---|---|
| population 仍很小 | “OBP EOH 生成稳定性未解决，不能比较 RAG 性能” |
| API-only 有效候选更多 | “API skeleton 可能提升合法性，但还不是策略提升” |
| Residual-RAG gap 更低 | “Literature-RAG 出现初步正信号，需要 repeats” |
| Residual-RAG 无提升但有效率足够 | “本实例/当前 cards 未显示收益，可考虑更难 instance 或换官方 Python target” |

---

## Phase E: Git 和交付

完成实质进展后提交并推送。

提交范围：

- goal 文档。
- prompt/seed/test 代码改动。
- 中文汇总报告。

不提交：

- API key / env。
- raw 大型实验产物。
- `.DS_Store`。
- ppt/html 临时产物。

最终响应必须包含：

- files changed
- commands run
- test results
- experiment results
- unresolved risks
- merge recommendation
