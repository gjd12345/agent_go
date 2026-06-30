# History-card 质量诊断：CVRP history/mixed smoke

## 结论

本次真实 LLM smoke 证明了 history card 可以被 `selected_card_ids` 精确注入，并能生成 4/4 valid 候选；但 `mixed_history_far_regret` 的 objective 明显差于 `literature_regret_far`。

| arm | cards | best | valid | 判断 |
|---|---|---:|---:|---|
| literature_regret_far | `cvrp_regret_insertion`, `cvrp_far_first` | 13.09441 | 4/4 | 更好 |
| mixed_history_far_regret | `history_cvrp_construct_capacity_destination_farthest_085049`, `cvrp_regret_insertion` | 14.20996 | 4/4 | 更差 |

这不是 RAG 链路失败，也不是 generation collapse；两组都通过 proposal/linkage/generation 三层漏斗。问题在于 history card 的策略语义过强，诱导 LLM 生成了过复杂的组合评分函数。

## 证据

### Literature-only best code

该候选采用清晰的两段策略：

```python
if current_node == depot:
    depot_distances = distance_matrix[depot][feasible_nodes]
    return feasible_nodes[np.argmax(depot_distances)]

dist_from_current = distance_matrix[current_node][feasible_nodes]
sorted_indices = np.argsort(dist_from_current)
best_node = feasible_nodes[sorted_indices[0]]
```

行为解释：
- 起点处用 far-first seed 远簇。
- 路线中用简单距离/regret 逻辑，不把容量和回仓距离混进主分数。
- 代码结构短，主要风险低。

### Mixed history best code

history card 引导生成了更复杂的加权分数：

```python
alpha = min(2.0, 0.5 + 1.5 * (n_remaining / max(len(demands) - 1, 1)))
base_scores = distance_matrix[current_node, feasible] + alpha * distance_matrix[feasible, depot]

regrets[i] = regret * cap_factor
look_penalty = (1.0 - avg_norm) * (1.0 - beta)
combined = base_scores - 0.3 * regrets + 0.4 * look_penalty * np.max(base_scores)
```

行为解释：
- 同时使用 farthest、destination/depot、capacity-normalized regret、2-step lookahead、remaining-aware alpha。
- 这些信号并非都与 CVRP constructive 的当前局部选择一致。
- `base_scores` 被注释为“lower is better”，但 history card 描述里是“score each candidate by d(current,u)+alpha*d(u,dest); prefer far”，方向容易混淆。
- gen=0 没有后续 evolution 纠错，复杂 scoring 的参数和符号错误会直接反映到 objective。

## 根因

`history_cvrp_construct_capacity_destination_farthest_085049` 的 content 同时包含太多启发式动作：

```text
capacity + destination + farthest + lookahead + normalize + remaining_aware
```

这类 card 更像“某次最优代码的压缩描述”，不是一个干净的可组合 operator card。和 `cvrp_regret_insertion` 混合后，LLM 倾向于把所有概念塞进一个公式，导致搜索方向过拟合、符号方向不稳。

## 修正进展

已落地 history-card gate v1：

1. `official_eoh_run.py` 在 `history_rag` / `mixed_rag` 构造 strategy pool 时检查 history cards。
2. 硬拦截条件：
   - 策略信号标签超过 4 个。
   - `Do` 段组合步骤超过 5 个。
3. trace 记录：
   - `rag_history_pool_size_before_gate`
   - `rag_history_pool_size_after_gate`
   - `rag_blocked_history_items`
   - `rag_history_gate_warnings`
4. 如果 `selected_card_ids` 显式指定被拦截的 history card，runner 直接报错，避免 silent bad-context。
5. `card_synthesis.py` 已改为未来新合成卡最多保留 3 个核心策略特征，并显式写出 `minimize` / `maximize` score 方向。

仍需后续处理：

1. 对现有 history cards 做拆分：
   - `history_cvrp_far_destination_seed`
   - `history_cvrp_capacity_feasible_filter`
   - `history_cvrp_remaining_aware_alpha`
2. 下一轮 mixed 实验不要继续用当前复合卡，先改成“拆分后的单一 operator card + regret literature card”。

## 拆分结果

已从复合卡 `history_cvrp_construct_capacity_destination_farthest_085049` 拆出 3 张小 operator cards：

| card | 作用 | gate |
|---|---|---|
| `history_cvrp_far_destination_seed` | 起点/新路线时用 depot distance seed 远簇 | PASS |
| `history_cvrp_capacity_feasible_filter` | 把 capacity 只作为 feasibility filter，不进入 score | PASS |
| `history_cvrp_remaining_aware_alpha` | 用 remaining_ratio 生成 bounded alpha，调节探索权重 | PASS |

验证：

```text
history_cvrp_far_destination_seed -> gate []
history_cvrp_capacity_feasible_filter -> gate []
history_cvrp_remaining_aware_alpha -> gate []

CVRP history_rag:
  before_gate=11
  after_gate=3
  selected=[
    history_cvrp_remaining_aware_alpha,
    history_cvrp_capacity_feasible_filter,
    history_cvrp_far_destination_seed
  ]

CVRP mixed_rag:
  selected=[
    history_cvrp_remaining_aware_alpha,
    history_cvrp_capacity_feasible_filter,
    history_cvrp_far_destination_seed,
    cvrp_nearest_capacity,
    cvrp_far_first
  ]
```

含义：旧复合卡仍保留为历史证据，但默认不会进入 prompt；拆分后的单一卡可以进入 `history_rag` / `mixed_rag`。下一次真实 smoke 应使用显式 `selected_card_ids`，例如：

```text
history_cvrp_far_destination_seed + cvrp_regret_insertion
history_cvrp_capacity_feasible_filter + cvrp_regret_insertion
history_cvrp_remaining_aware_alpha + cvrp_far_first
```

已准备 manifest：

```text
eoh_go_workspace/experiments/manifests/tocc_split_history_cvrp_smoke.json
```

Dry-run 与 linkage 验证：

```text
literature_regret_far:
  cards=[cvrp_regret_insertion, cvrp_far_first]
  ctx=2122

split_far_seed_regret:
  cards=[history_cvrp_far_destination_seed, cvrp_regret_insertion]
  ctx=2177

split_capacity_filter_regret:
  cards=[history_cvrp_capacity_feasible_filter, cvrp_regret_insertion]
  ctx=2136

split_remaining_alpha_far:
  cards=[history_cvrp_remaining_aware_alpha, cvrp_far_first]
  ctx=2165

all contexts <= 2500 chars
selected_card_ids == rag_trace.rag_selected_items
```

## Split-history 真实 smoke 结果

Manifest：

```text
eoh_go_workspace/experiments/manifests/tocc_split_history_cvrp_smoke.json
```

真实 LLM run：

| arm | cards | best | valid | 判断 |
|---|---|---:|---:|---|
| literature_regret_far | `cvrp_regret_insertion`, `cvrp_far_first` | 12.72795 | 4/4 | 本轮最好 |
| split_far_seed_regret | `history_cvrp_far_destination_seed`, `cvrp_regret_insertion` | 13.00458 | 4/4 | 可运行，但不如 literature-only |
| split_capacity_filter_regret | `history_cvrp_capacity_feasible_filter`, `cvrp_regret_insertion` | 13.23646 | 4/4 | 可运行，但不如 literature-only |
| split_remaining_alpha_far | `history_cvrp_remaining_aware_alpha`, `cvrp_far_first` | 12.96129 | 4/4 | 最接近 literature-only |

Success funnel：

```text
proposal_accept: 4/4
linkage_success: 4/4
generation_success: 4/4
objective_success: insufficient data (no pure baseline in manifest)
```

结论：

```text
拆分卡 + gate 解决了 mixed history 的可控性问题：不再出现旧复合卡那种复杂 scoring 诱导，4 条 run 均 4/4 valid。
但本轮 objective 仍由 literature-only 最优，split-history mixed 没有超过文献卡组合。
当前证据支持“history prior 可控接入”，不支持“history prior 带来收益”。
```

## 可写边界

可以写：

```text
History/mixed RAG 链路已通过真实 LLM smoke；history card 能被精确注入并生成 valid candidates。
但 naive mixed history+literature 在本次 CVRP smoke 中差于 literature-only，说明历史最优代码不能直接作为默认增强，必须经过 operator-card 质量门控。
```

不能写：

```text
History RAG 无效。
Mixed RAG 一定差。
Best-code memory 已带来 objective 提升。
```
