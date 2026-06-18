# TOCC History-card Prior 审计报告

日期：2026-06-19

## 结论

本轮审计把 history prior 从“默认增强”改成了“需要被 TOCC 诊断选择的候选 prior”。

当前证据显示：

1. **旧合成 history cards 不适合直接注入。** 8 张旧 CVRP history cards 中，多数把 capacity、destination、farthest、lookahead、normalize、remaining-aware 等信号压成一个大卡；这些卡会诱导 LLM 在 gen=0 写出复杂 scoring，增加方向错误风险。
2. **gate + split 解决了可控性问题。** 三张拆分卡都能通过 gate，并在真实 LLM smoke 中生成 4/4 valid candidates。
3. **split-history 尚未带来 objective 收益。** 本轮 best 仍来自 literature-only arm：`12.72795`。三个 split-history mixed arms 分别为 `13.00458`、`13.23646`、`12.96129`。
4. **因此不能写“history prior 有效提升”。** 目前只能写：history prior 已可控接入，且能作为候选 prior 被诊断、降权、拆分。

## 输入证据

### 真实 smoke 1：naive mixed history

| arm | cards | best | valid |
|---|---|---:|---:|
| literature_regret_far | `cvrp_regret_insertion`, `cvrp_far_first` | 13.09441 | 4/4 |
| mixed_history_far_regret | `history_cvrp_construct_capacity_destination_farthest_085049`, `cvrp_regret_insertion` | 14.20996 | 4/4 |

判断：链路有效，但旧复合 history card 使 objective 变差。

### 真实 smoke 2：split-history mixed

| arm | cards | best | valid |
|---|---|---:|---:|
| literature_regret_far | `cvrp_regret_insertion`, `cvrp_far_first` | 12.72795 | 4/4 |
| split_far_seed_regret | `history_cvrp_far_destination_seed`, `cvrp_regret_insertion` | 13.00458 | 4/4 |
| split_capacity_filter_regret | `history_cvrp_capacity_feasible_filter`, `cvrp_regret_insertion` | 13.23646 | 4/4 |
| split_remaining_alpha_far | `history_cvrp_remaining_aware_alpha`, `cvrp_far_first` | 12.96129 | 4/4 |

判断：拆分卡解决 valid/generation 问题，但 objective 未超过 literature-only。

## Card Prior 决策

机器可读版本：

```text
eoh_go_workspace/reports/auto_experiment_reports/tocc_history_card_audit_20260619/card_prior_decisions.jsonl
```

### Block / Split

这些卡继续作为历史证据保留，但不应进入默认 `mixed_rag` prompt：

```text
history_cvrp_construct_capacity_destination_savings_8a5bf3
history_cvrp_construct_capacity_clustering_destination_1acd4f
history_cvrp_construct_capacity_destination_lookahead_1a7195
history_cvrp_construct_adaptive_weights_capacity_destination_d7206c
history_cvrp_construct_capacity_destination_farthest_085049
history_cvrp_construct_capacity_clustering_destination_5656e1
history_cvrp_construct_adaptive_weights_capacity_destination_9df661
history_cvrp_construct_capacity_destination_normalize_09fdad
```

原因：

```text
too_many_strategy_signals
too_many_do_steps
observed_negative in naive mixed smoke
```

### Candidate but Deprioritized

```text
history_cvrp_far_destination_seed
history_cvrp_capacity_feasible_filter
```

原因：能生成 valid candidates，但单次 smoke 不如 literature-only。

### Watchlist

```text
history_cvrp_remaining_aware_alpha
```

原因：三个 split-history arms 中最接近 literature-only，但仍未超过。后续可以在新问题或更深 generation 中再试。

## 对 TOCC 的方法含义

这组结果支持论文中一个更稳的论点：

```text
TOCC 的价值不只是“选对一张卡提升 objective”，也包括识别错误 prior、阻断坏上下文、把复合历史代码拆解为可控 operator cards。
```

不应写：

```text
History-RAG 已经带来提升。
Mixed-RAG 一定比 literature-RAG 好。
历史最优代码可以直接作为 prompt prior。
```

可以写：

```text
History-card memory can be integrated into the closed loop, but evolved-code priors require trace-conditioned gating and decomposition before they become useful context.
```

## 下一步

1. 不再扩 CVRP split-history repeat，除非有新的 controller 规则需要验证。
2. 把 `history_cvrp_remaining_aware_alpha` 标为 watchlist，可以在新 benchmark 或 gen>0 小实验中复用。
3. 把这套 audit 逻辑接到 controller：proposal 中若包含 `candidate_deprioritized` card，需要显式说明为什么仍要尝试。
4. 论文中把 history-card 结果写成 negative/control finding，而不是主正例。
