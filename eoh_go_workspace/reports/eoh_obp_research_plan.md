# EoH-OBP 对齐实现记录

日期：2026-06-01

本文记录 Online Bin Packing (OBP) 迁移工作的当前状态。它是 agent 工作记录，不是论文最终结论。

## 为什么转向 OBP

Knapsack 和 Mixer 已经证明了 C+L+V harness 可以迁移到新问题，但它们目前不适合作为 RAG 有效性的主证据：

- Knapsack 单实例已被 seed 接近或达到 DP 最优，提升空间太小。
- Mixer 的 `SplitOrders` 当前 objective 也接近 largest-capacity fallback 的下界，RAG 很难显示差异。
- OBP 是 EoH 原论文主例之一，官方仓库明确把 `bp_online` 描述为“为在线装箱设计 bin-scoring function，最小化 used bins”。EoH 论文也强调低查询预算下在 OBP 上优于常用手工 heuristic 和 FunSearch。

因此当前主线改为：在一个最小但可复现的 OBP harness 上验证 vanilla EoH 和 Literature-RAG EoH 是否在同一 evaluator、同一 query budget 下产生差异。

参考来源：

- EoH 官方仓库：https://github.com/FeiLiu36/EoH
- EoH OpenReview 页面：https://openreview.net/forum?id=BwAkaxqiLB
- EoH arXiv 页面：https://arxiv.org/abs/2401.02051

## Target 设计

新增 problem：

```text
ProblemSpec: bin_packing_online
Target: ScoreBin
Language: Go
Source: eoh_go_workspace/problems/bin_packing_online/bin_packing_solver.go
Dataset: eoh_go_workspace/problems/bin_packing_online/testdata/obp_5x60_c100.json
```

可进化函数：

```go
func ScoreBin(item int, remaining []int, capacity int) []float64
```

语义：

- evaluator 按在线顺序处理 item。
- `remaining` 只包含当前 item 可放入的 feasible bins。
- `ScoreBin` 必须返回 `len(remaining)` 个有限分数。
- evaluator 选择最高分 bin；若没有 feasible bin，则自动开新 bin。
- 目标最小化 `gap_to_lb = (used_bins - lower_bound) / lower_bound`。

本地 seed 是 best-fit scoring：

```go
func ScoreBin(item int, remaining []int, capacity int) []float64 {
    scores := make([]float64, len(remaining))
    for i, rem := range remaining {
        scores[i] = float64(capacity - (rem - item))
    }
    return scores
}
```

## Evaluator 边界

已实现的 guard：

- Score 长度必须等于 feasible bins 数。
- Score 不能是 NaN/Inf。
- item 必须在 `(0, capacity]`。
- generated code 只替换 `ScoreBin`。
- evaluator 子进程只传 allowlist env，不传 API key。

本地 seed evaluator 结果：

```text
objective / avg_gap_to_lb: 0.05903030
avg_used_bins: 28.8
avg_lower_bound: 27.4
instances: 5
```

## OBP Literature-RAG cards

新增 OBP strategy cards：

| id | 作用 |
|---|---|
| `obp_first_fit` | 早期 feasible bin 优先 |
| `obp_best_fit` | 最小 residual capacity，当前 seed 同类 |
| `obp_worst_fit` | 最大 residual capacity，保留中等空隙 |
| `obp_harmonic` | 按 item/capacity size class 切换策略 |
| `obp_funsearch_residual_poly` | residual polynomial / unusable gap penalty |
| `obp_eoh_util_sqrt_exp` | utilization + sqrt/exp smooth scoring |

新增 API global item：

```text
obp_api_skeleton
```

RAG target filtering 已生效：`ScoreBin` 的 literature mode 只从 OBP cards 中检索，不混入 VRP/InsertShips cards。

一次 trace：

```text
query: online bin packing ScoreBin feasible bins residual capacity best fit worst fit harmonic used bins lower bound gap
global: obp_api_skeleton + 3 failure_case warnings
selected: obp_best_fit, obp_worst_fit, obp_first_fit
context chars: 2500
```

## 最小对照实验

配置：

```text
model: JoyAI-LLM-Pro
generations: 1
pop_size: 8
dataset: obp_5x60_c100
```

结果：

| Arm | RAG | Population | Valid | Seed gap | Best gap | RAG selected |
|---|---|---:|---:|---:|---:|---|
| Vanilla | off | 2 | 1 | 0.0590303 | 0.05903 | - |
| Literature-RAG | literature top_k=3 | 2 | 1 | 0.0590303 | 0.05903 | best-fit, worst-fit, first-fit |

当前判断：

- OBP harness 跑通。
- Literature-RAG trace 生效，且 target-specific filtering 正确。
- 这一组没有性能提升；两边都只保住 seed，新增 8 个候选全部 penalty。
- 这说明当前 prompt/EOH 变异预算对 `ScoreBin` 还不够稳，不能把“无提升”解释为 RAG 无效。

## 下一步

优先修生成稳定性，而不是扩大矩阵：

1. 缩短 context：`rag_top_k=1` 或 `rag_max_chars=1200`，先避免 2500 chars 截断。
2. 调整 seed：加入 First Fit / Worst Fit 多 seed，让 EOH 有可变异的合法结构。
3. 调整 prompt：明确 `remaining` 已经是 feasible bins，不需要检查容量；只做 score formula。
4. 若继续无有效候选，再改为 Python target，对齐 EoH 官方 `score(item, bins)` 形态。

当前结论格式应写作：

```text
跑通：OBP harness + target-specific Literature-RAG trace 生效。
未验证：gen=1 pop=8 下 Literature-RAG 未超过 vanilla/seed，原因是候选有效率不足。
```

## 2026-06-01 修正实验

### Phase A: population 过小根因

上一轮 vanilla 和 Literature-RAG 的 `population_generation_1.json` 都只有 2 条：

```text
idx 0: seed, objective=0.05903, code exists
idx 1: failed candidate, objective=1000000000.0, code=None
```

直接原因不是 `ScoreBin` evaluator 太严格，而是 `Agent_EOH/eoh/src/eoh/methods/eoh/eoh_evolution.py` 的代码抽取逻辑只把 `func InsertShips(` 识别为 Go。`ScoreBin` prompt 被误判成 Python target，LLM 即使返回合法 Go 函数，也会因为 Python regex 抽取失败变成 `code=None`。

修复：

- 将 `_extract_go_insertships()` 改成通用 `_extract_go_function(response, function_name)`。
- 对 `ScoreBin` 增加回归测试，确认非 `InsertShips` Go target 也能被抽取。
- 在 `prompts_bin_packing_go.py` 中补充公式型 `ScoreBin` 约束，要求分配 `scores := make([]float64, len(remaining))`、填满每个 `scores[i]` 并返回。

### Phase B/C: 修正后 smoke

固定配置：

```text
model: JoyAI-LLM-Pro
generations: 1
pop_size: 8
dataset: obp_5x60_c100
```

结果：

| Arm | RAG | Population | Valid | Seed gap | Best gap | Context | 裁决 |
|---|---|---:|---:|---:|---:|---|---|
| Vanilla | off | 6 | 5 | 0.0590303 | 0.05903 | - | 达到生成稳定性门槛 |
| API+Warning-only | `rag_top_k=0` | 2 | 2 | 0.0590303 | 0.05903 | 894 chars, not truncated | 未达门槛，停止 |

Residual-RAG 没有继续跑，因为 goal 的停止条件是：

```text
population_size < 5 或 valid_candidates < 3 时停止，不扩大实验。
```

API+Warning-only 已触发该停止条件。继续跑 Residual-RAG 会让对比建立在不稳定的候选生成基础上。

当前 best code 仍是 best-fit seed：

```go
func ScoreBin(item int, remaining []int, capacity int) []float64 {
    scores := make([]float64, len(remaining))
    for i, rem := range remaining {
        scores[i] = float64(capacity - (rem - item))
    }
    return scores
}
```

### 当前判断

- 修复通用 Go 抽取后，vanilla 从 `population=2/valid=1` 提升到 `population=6/valid=5`，说明上一轮主要瓶颈确实是代码抽取，而不是 OBP evaluator。
- API+Warning-only 仍退化到 `population=2/valid=2`，说明即使 context 不截断，API skeleton + warning 也可能让模型生成更同质的候选，被 `pop_greedy` 按 objective 去重后只剩少量个体。
- 当前仍不能比较 RAG 性能；下一步应先让 RAG arm 的 `population_size >= 5` 且 `valid_candidates >= 3`，再跑 Residual-RAG。

建议下一步：

1. API+Warning-only 改成真正 API-only：允许禁用 failure_case warning，避免 global warning 干扰。
2. 或缩短 global block，只保留 `obp_api_skeleton` 的 Rules，不重复 Summary/Constraints。
3. Residual-RAG 用 `rag_top_k=1, rag_max_chars=1800`，因为本地 trace 显示 top-1 可做到 `rag_context_truncated=false`，top-2 在 1800 字符下仍截断。

## 2026-06-01 true API-only 修正实验

### 改动目的

上一轮 API+Warning-only 仍然把 3 条 `failure_case` 放进 global context。对 `ScoreBin` 这种很小的公式函数来说，这些 warning 可能让模型过度关注 guard，而不是生成简单 scoring formula。本轮实现了真正的 API-only 路径：

- 新增 `EOHConfig.rag_include_warnings`，默认 `True`，保持旧行为。
- `eoh_obp_smoke.py` 新增 `--no-rag-warnings`。
- trace 拆分为 `rag_global_items_available` 和 `rag_global_items_injected`。
- 当 `--no-rag-warnings` 生效时，`failure_case` 只在 available trace 中出现，不进入 prompt。

本地 context 验收：

```text
rag_selected_items = []
rag_global_items_available = obp_api_skeleton + 3 failure_case
rag_global_items_injected = obp_api_skeleton
rag_context_chars = 598
rag_context_truncated = false
WARNINGS in context = false
failure_case id in context = false
```

### true API-only smoke

命令参数：

```text
model = JoyAI-LLM-Pro
generations = 1
pop_size = 8
rag_mode = literature
rag_top_k = 0
rag_max_chars = 700
no_rag_warnings = true
```

结果：

| Arm | Run | Population | Valid | Seed gap | Best gap | Context | Verdict |
|---|---|---:|---:|---:|---:|---|---|
| True API-only | `eoh_obp_true_api_only_20260601/run_20260601_124045` | 3 | 3 | 0.0590303 | 0.05903 | 598 chars, not truncated | STOP: `population_size < 5` |

best code 仍是 best-fit 等价公式：

```go
func ScoreBin(item int, remaining []int, capacity int) []float64 {
    scores := make([]float64, len(remaining))
    for i, rem := range remaining {
        scores[i] = float64(capacity - (rem - item))
    }
    return scores
}
```

### 当前判断

- true API-only 比 API+Warning-only 的 trace 更干净：只注入 `obp_api_skeleton`，没有 warning，也没有 strategy card。
- 但是最终 population 仍只有 3，低于 goal 设定的 `population_size >= 5` gate。
- 因此本轮按停损规则没有继续跑 Residual-RAG。现在仍不能比较 OBP Literature-RAG 的性能收益。
- 现象更像 EOH 的 final population 去重/选择压力问题：日志中多个候选 objective 都是 `0.05903`，最终只保留 3 个不同 objective 个体，而不是 8 个候选全部失败。

下一步建议：

1. 复核 `pop_greedy` 或 EOH survivor selection 是否按 objective 去重，导致同分候选被压缩。
2. OBP 报告里同时记录 raw generated count 和 final population size，避免把“候选生成成功但被去重”误判为“候选生成失败”。
3. 如果目标是比较 RAG 策略收益，可以把 gate 改成 `raw_valid_candidates >= 5`，或暂时接受 final population 较小但要求 raw responses 完整。
