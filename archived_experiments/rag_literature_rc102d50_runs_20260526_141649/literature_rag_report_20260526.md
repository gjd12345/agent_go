# Literature-RAG 检索修正 + rc102 d50 重复实验报告

**日期**: 2026-05-26
**模型**: deepseek-v4-pro
**实例**: rc102.json, d50, arrival_scale=1.0
**EOH 配置**: 1 generation, pop_size=4

---

## 1. 背景

literature-RAG v1（2026-05-25）rc102 d50 实验发现：retrieval top-3 被 failure_case 占据两席（timeout=15分, suspicious-low=11分），regret2/solomon 未进入上下文。根因：

- `failure_case` 和 `algorithm_card` 混在同一 retrieval pool
- auto query 含 "avoid timeout safe rollback"，天然匹配 failure_case
- regret2/solomon 的密度触发词（d50/capacity/lookahead）写在 content 的 When 里，不被 retriever 打分

## 2. 检索修正（2026-05-26）

### 变更清单

| 文件 | 变更 |
|---|---|
| `eoh_go/eoh_runner/runner.py` | strategy_pool = `kind == "algorithm_card"`；global_items = api_constraint + failure_case；query 去 safety 化；trace 加 `rag_all_scores` + selected_items 加 score |
| `eoh_go/rag/retriever.py` | 新增 `score_corpus()` 导出函数，`retrieve()` 通用语义不变 |
| `eoh_go/rag/prompt_context.py` | global 区拆为 `API RULES` + `WARNINGS` 两个子区块；`_warning_block()` 只输出 summary + 前 2 条 constraints |
| `eoh_go/rag/build_corpus.py` | filter 层保持返回 api_constraint + failure_case + literature algorithm_cards |
| `eoh_go_workspace/rag/corpus/algorithm_cards.jsonl` | 5 张卡 tags/summary 补密度触发词 |
| `tests/` | 新增 3 个验收测试 |

### 修正后检索（d50 query）

```
Query: dynamic InsertShips insertion heuristic density=d50 arrival_scale=1.0
       medium density route capacity insertion cost final cost

Scores:
  40  algorithm_card  regret2_insertion
  38  algorithm_card  solomon_i1
  34  algorithm_card  farthest_insertion
  34  algorithm_card  nearest_insertion
   7  algorithm_card  cw_savings

Top-3: regret2_insertion, solomon_i1, farthest_insertion
```

failure_case 全部在 global WARNINGS 区，不参与检索。

### 验收

- 37 个测试全部通过
- top-3 全部 kind == "algorithm_card"
- top-3 包含 regret2 或 solomon
- auto query 不含 avoid/safe/rollback/timeout/skipped
- context chars = 3828（无截断）

## 3. rc102 d50 三轮重复实验

### 结果

| Run | Condition | Pop | Valid | best J | best Res | Eval RC | 备注 |
|---|---|---|---|---|---|---|---|
| v2 | baseline | 4 | 4/4 | **626.44** | 1.94 | 0 | 唯一有改进的 cell |
| v2 | literature | 3 | 2/3 | — | — | 2 | eval binary crash |
| v3 | baseline | 4 | 3/4 | — | — | 2 | eval binary crash |
| v3 | literature | 1 | 1/1 | 551.81 | 1.12 | 0 | = seed，无改进 |
| v4 | baseline | 3 | 1/3 | 551.81 | 1.02 | 0 | = seed，无改进 |
| v4 | literature | 2 | 1/2 | 551.81 | 1.05 | 0 | = seed，无改进 |

seed_J = 551.81（三轮一致，SA baseline seed）

### 检索一致性

三轮 RAG top-3 完全相同：`regret2_insertion, solomon_i1, farthest_insertion`，context_chars = 3828。

### EOH 质量指标

- 6 个 cell 中 4 个 best == seed（无改进）
- eval binary 崩溃率：2/6 = 33%
- 唯一有效改进：v2 baseline（+74.6 J over seed）

## 4. 结论

1. **检索修正成功**：retrieval routing fix 完全达到设计目标，三轮 top-3 稳定、context 紧凑、failure_case 正确路由到 global WARNINGS。
2. **EOH 方差极大**：pop_size=4、1 generation 配置下，绝大多数 cell 找不到优于 seed 的候选。eval binary 崩溃是独立问题（return_code=2），与 RAG 注入无关。
3. **无法做定量 ablation 对比**：n=3 每组的高噪声淹没了任何 RAG 信号。需要 pop_size >= 8、generations >= 2 才能减少方差到可比较的水平。

### 建议

- 如果要继续 ablation：pop_size → 8-16，generations → 2-3，每个 cell 先跑 1 次看信号再决定是否 repeat
- 如果接受当前为 "smoke test" 级别：retrieval fix 到此封板，文献 RAG 的下一步是高方差实验设计问题，不是检索问题

## 5. 文件位置

- 实验原始数据：`eoh_go_workspace/reports/tables/rag_literature_rc102d50_v{2,3,4}/`
- RAG 测试：`tests/test_rag_*.py`（37 个）
- Corpus：`eoh_go_workspace/rag/corpus/*.jsonl`
- 文献参考：`eoh_go_workspace/rag/literature/*.md`
- 存档：`/Users/guojiadong.9/agent_ad/archived_experiments/`
