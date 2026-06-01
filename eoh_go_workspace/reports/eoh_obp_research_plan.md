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
