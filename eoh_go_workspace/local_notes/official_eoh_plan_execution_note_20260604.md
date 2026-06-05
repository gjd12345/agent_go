# 官方 EoH 计划执行记录（本地）

本文档是本地 agent 工作记录，不作为正式报告提交。目标是记录当前计划执行状态、`bp_online` 无提升原因，以及下一步应如何推进。

## 当前目标

执行 `.codex/goals/weekly_showcase.md` 中的官方 EoH benchmark 对齐计划。当前阶段不写正式报告，只沉淀本地记录。

## 已完成的关键事实

### 1. `bp_online` 四组最小对照

已有正式摘要：

- `eoh_go_workspace/reports/official_eoh_runs/official_eoh_bp_online_comparison.md`
- `eoh_go_workspace/reports/official_eoh_runs/official_eoh_multi_problem_status.md`

结果：

| arm | status | best objective | 诊断 |
|---|---|---:|---|
| `pure_eoh` | completed gen=1 | 0.03984 | 不加 RAG 已生成 best-fit/tight-fit |
| `api_only` | completed gen=1 | 0.03984 | API 约束没有改变策略族 |
| `literature_rag_default` | completed gen=1 | 0.03984 | 检索到 `obp_best_fit`, `obp_first_fit`，与 pure EOH 重复 |
| `literature_rag_targeted_residual` | init completed, gen=1 timeout | 0.03984 | 检索到 residual/EoH 卡，但 context 截断且 Gen1 超时 |

结论：这不是 RAG 链路失败，而是当前 `bp_online` 小预算下没有拉开差距。`score(item, bins)` 目标很小，模型在 pure prompt 下已经能写出强 best-fit 类策略。

### 2. `generations=0` init-only 行为已验证

执行命令（API key 未打印，使用 `caffeinate`）：

```bash
set -a
source <company_api_env_file>
set +a
caffeinate -i -m -s python3 -m eoh_go.experiments.official_eoh_run \
  --problem bp_online \
  --arm literature_rag \
  --rag-top-k 1 \
  --rag-max-chars 1000 \
  --rag-query "online bin packing eoh utilization sqrt exp smooth scoring awkward gaps minimize used bins" \
  --pop-size 2 \
  --generations 0 \
  --operators i1 \
  --n-processes 1 \
  --eval-timeout-s 40 \
  --llm-timeout-s 180 \
  --run-timeout-s 1200 \
  --output-dir eoh_go_workspace/local_runs/official_eoh_init_only
```

结果：

```text
run_dir = /Users/guojiadong.9/agent_ad/agent_go/eoh_go_workspace/local_runs/official_eoh_init_only/bp_online/literature_rag/run_20260604_124502
return_code = 0
runtime_seconds = 423.218
latest_generation = 0
samples = 4
valid_candidates = 2/2
best_objective = 0.03984
rag_selected_items = obp_eoh_util_sqrt_exp
rag_context_chars = 1000
```

关键判断：

- `generations=0` 可用：官方 EoH 仍会跑 init population，并在 `population_generation_0.json` 写出 survivor population。
- targeted top-k=1 生效：只注入了 `obp_eoh_util_sqrt_exp`。
- context 仍等于 `max_chars=1000`，说明仍可能存在截断或接近截断边界。
- best objective 仍是 `0.03984`，没有超过 pure EOH。

### 3. 本轮 `bp_online` 的实际结论

`bp_online` 可以作为“官方 EoH 对齐 + RAG 检索诊断”案例，但暂时不适合作为 RAG 正向收益主证据。

原因：

1. strong best-fit baseline 已经由 pure EOH 自发生成。
2. 默认 RAG 检索选中的卡片与 pure EOH 策略重复。
3. targeted RAG 虽能选中非默认卡，但没有改善 objective。
4. BP 的 `score(item, bins)` 函数空间较小，容易快速回到 tight-fit/best-fit。
5. 后续继续扩大 BP repeat 的边际价值低。

## 当前 best code（targeted init-only）

```python
import numpy as np

def score(item: int, bins: np.ndarray) -> np.ndarray:
    """Score each bin for assigning the current item. Higher score = preferred bin.

    Args:
        item: size of the current item to assign
        bins: remaining capacities of feasible bins (all >= item size)
    Returns:
        scores: priority scores for each bin
    """
    remaining_after = bins - item
    exact_fit_bonus = (remaining_after == 0).astype(float) * 1e6
    eps = 1e-9
    tightness = np.exp(-remaining_after / max(bins.max(), item))
    fill_ratio = item / (bins + eps)
    raw_scores = tightness * 0.7 + fill_ratio * 0.3 + exact_fit_bonus
    scores = np.where(np.isfinite(raw_scores), raw_scores, 0.0)
    return scores
```

该代码仍是 best-fit/tight-fit 族，只是加入了 exp smooth 和 fill ratio；评价没有超过 `0.03984`。

## 下一步执行建议

### A. 停止扩大 BP 矩阵

除非改数据或目标函数，否则不再对 `bp_online` 做 repeat=3。保留 BP 作为：

- 官方 benchmark 接入证明；
- RAG 检索 trace 示例；
- “RAG 未提升不是链路失败，而是强基线/目标饱和”的反例诊断。

### B. 转向 TSP/CVRP init-only 对照

优先做：

```text
tsp_construct:
  pure_eoh init-only
  api_only init-only
  literature_rag init-only

cvrp_construct:
  pure_eoh init-only
  api_only init-only
  literature_rag init-only
```

理由：

- TSP/CVRP 的启发式知识空间更大，RAG 可能提供真正增量。
- 已经证明二者 init 阶段可生成和评估。
- Gen1 full evolution 在 20 分钟内易超时，因此先比较 init population。

### C. 先补 problem-specific skill cards

当前 OBP cards 已存在；TSP/CVRP cards 需要补齐，且必须避免跨问题混入。

建议最小 cards：

```text
tsp_construct:
  tsp_nearest_neighbor
  tsp_nearest_insertion
  tsp_farthest_insertion
  tsp_regret_insertion
  tsp_two_opt_awareness

cvrp_construct:
  cvrp_nearest_capacity
  cvrp_savings
  cvrp_sweep
  cvrp_regret_insertion
  cvrp_capacity_slack
```

每张 card 仍按 Skill/When/Do/Fallback/Safety，控制在 450 chars 内。

## 不提交内容

本轮新增/使用的 raw run 目录不提交：

```text
eoh_go_workspace/local_runs/
eoh_go_workspace/reports/official_eoh_runs/bp_online/
eoh_go_workspace/reports/official_eoh_runs/tsp_construct/
eoh_go_workspace/reports/official_eoh_runs/cvrp_construct/
```

只在需要形成正式交付时，再把汇总报告或关键表格整理入仓。

## 2026-06-04 追加：无提升原因与下一步修正

### BP online 为什么没有提升

当前结果：

```text
pure_eoh: best 0.03984
api_only: best 0.03984
literature_rag_default: best 0.03984
literature_rag_targeted_residual: init 完成，Gen1 超时，best 0.03984
```

判断：

1. 不是 RAG 链路未生效。默认 RAG 和 targeted residual 都能产生 trace，selected cards 可解释。
2. 核心问题是 `bp_online` 的 `score(item, bins)` 目标太小，pure EOH 已经能直接生成 best-fit / tight-fit 族强基线。
3. 默认 Literature-RAG 选中的 `obp_best_fit` / `obp_first_fit` 与 pure EOH 策略重复，没有提供新搜索方向。
4. targeted residual 能选中 `obp_eoh_util_sqrt_exp` / `obp_funsearch_residual_poly`，但 init-only 仍未越过 `0.03984`；Gen1 又超时，继续扩 BP repeat 的信息增量低。
5. 因此当前不能写成“RAG 无效”，只能写成“BP 在当前小预算和当前 problem size 下被强基线压住，没有拉开差距”。

后续决策：

```text
停止扩大 bp_online。
保留 bp_online 作为官方 benchmark 接入和 RAG trace 诊断样例。
转向 tsp_construct / cvrp_construct 的 init-only 对照，寻找更适合 RAG 的知识空间。
```

### TSP/CVRP skill cards 已补齐（本地）

新增 strategy cards：

```text
tsp_construct:
  tsp_nearest_neighbor
  tsp_nearest_insertion
  tsp_farthest_insertion
  tsp_regret_insertion
  tsp_two_opt_awareness

cvrp_construct:
  cvrp_nearest_capacity
  cvrp_savings
  cvrp_sweep
  cvrp_regret_insertion
  cvrp_capacity_slack
```

新增 API skeleton：

```text
tsp_construct_api_skeleton
cvrp_construct_api_skeleton
```

本地检索 smoke：

```text
tsp_construct:
  global = tsp_construct_api_skeleton
  selected = tsp_nearest_insertion, tsp_nearest_neighbor
  strategy_pool = 5
  context_chars = 1800
  obp cards mixed in = false

cvrp_construct:
  global = cvrp_construct_api_skeleton
  selected = cvrp_nearest_capacity, cvrp_capacity_slack
  strategy_pool = 5
  context_chars = 1800
  obp cards mixed in = false
```

下一步命令级方向：

```text
先跑 generations=0 init-only：
  tsp_construct: pure_eoh / api_only / literature_rag
  cvrp_construct: pure_eoh / api_only / literature_rag

只有 init-only 出现 best_objective、valid_candidates 或 best code 差异后，再进入 Gen1 或 repeats。
```

### 审查状态

已尝试启动只读 subagent 审查 BP no-improvement 归因和 goal 改写，但当前 Codex subagent 额度耗尽，审查未完成。后续额度恢复后需要补一次 reviewer gate，重点检查：

```text
BP 无提升归因是否过度解释；
TSP/CVRP cards 是否真正匹配官方 target function；
init-only 对照是否足以作为下一阶段 gate；
是否仍存在 raw/survivor/verified objective 口径混用。
```

## 2026-06-04 追加：TSP/CVRP pop1 init-only 诊断

本轮没有生成正式报告，只沉淀本地记录：

```text
eoh_go_workspace/local_notes/official_eoh_init_matrix_pop1_20260604.md
```

实验设置：

```text
problem = tsp_construct, cvrp_construct
arm = pure_eoh, api_only, literature_rag
generations = 0
pop_size = 1
operators = i1
n_processes = 1
```

结果摘要：

| problem | pure EOH | API-only | Literature-RAG | 初步判断 |
|---|---:|---:|---:|---|
| `tsp_construct` | 6.83907 | 6.86186 | 6.83907 | Literature-RAG 与 pure 打平，没有负面破坏，但未证明提升 |
| `cvrp_construct` | 13.20696 | 13.41247 | 14.49387 | Literature-RAG 更差，可能是 capacity/slack cards 引导过强 |

注意：

```text
这是 pop1/init-only 诊断，每臂只有 2 个 init samples，survivor population 只有 1 个。
不能作为最终性能结论，只能用于判断下一步实验方向。
```

新的判断：

1. `bp_online` 没提升不是孤例；在非常小的 init budget 下，RAG 未必自动带来收益。
2. `tsp_construct` 是下一步更值得放大的对象，因为 Literature-RAG 没有变差，且 problem heuristic 空间比 BP 更大。
3. `cvrp_construct` 需要先复核 skill cards，尤其 `cvrp_capacity_slack` / capacity-first 逻辑可能牺牲路线距离。
4. 下一步建议只对 `tsp_construct` 跑 `pop_size=4, generations=0` 三臂对照；CVRP 先改 cards 再重跑。

## 2026-06-04 追加：TSP pop4 init-only 部分结果

本地记录：

```text
eoh_go_workspace/local_notes/official_eoh_tsp_pop4_partial_20260604.md
```

已完成：

| problem | arm | pop_size | generations | best objective | valid/pop | 运行时间 |
|---|---|---:|---:|---:|---:|---:|
| `tsp_construct` | `pure_eoh` | 4 | 0 | 6.83907 | 4/4 | 1622.299s |

关键事实：

```text
Init 8/8 evaluated
survivor pop=4
best=6.83907
```

解释：

1. `pure_eoh pop4` 与 `pure_eoh pop1` 的 best 相同，说明 TSP strong baseline 在 init 阶段稳定出现。
2. 后续 `api_only` / `literature_rag` 必须低于 `6.83907` 才算有正向 signal。
3. 当前还不能比较三臂，因为 `api_only` 和 `literature_rag` 未完成。

阻塞：

```text
尝试启动 tsp_construct/api_only/pop4/generations=0 时，Codex 审批/额度系统拒绝执行，
提示 5:59 PM 后再试。未绕过审批，待额度恢复后继续。
```

## 2026-06-04 追加：TSP pop4 init-only 三臂已补齐

完整本地记录：

```text
eoh_go_workspace/local_notes/official_eoh_tsp_pop4_init_20260604.md
```

设置：

```text
problem = tsp_construct
pop_size = 4
generations = 0
operators = i1
```

结果：

| arm | best objective | delta vs pure | valid/pop | selected cards |
|---|---:|---:|---:|---|
| `pure_eoh` | 6.83907 | +0.00000 | 4/4 | - |
| `api_only` | 6.78953 | -0.04954 | 4/4 | - |
| `literature_rag` | 6.83954 | +0.00047 | 4/4 | `tsp_nearest_insertion`, `tsp_nearest_neighbor` |

判断：

1. `api_only` 出现轻微信号，说明 API/signature/contract 约束在 TSP 上有帮助。
2. 默认 `literature_rag` 没有超过 pure，原因不是 RAG 链路无效，而是检索选中了偏保守的 nearest/insertion cards。
3. `tsp_regret_insertion` 分数排第 3，未进入 top-2；下一步应做 targeted Literature-RAG，让 regret/global scoring 进入上下文。
4. 该结果仍是 init-only，不是最终论文结论，但足以指导下一轮实验配置。

## 2026-06-04 追加：TSP targeted Literature-RAG 出现正向信号

已更新完整四臂本地记录：

```text
eoh_go_workspace/local_notes/official_eoh_tsp_pop4_init_20260604.md
```

targeted query：

```text
tsp construct select next node regret farthest insertion lookahead second best global route length
```

结果：

| arm | best objective | delta vs pure | delta vs API-only | valid/pop | selected cards |
|---|---:|---:|---:|---:|---|
| `pure_eoh` | 6.83907 | +0.00000 | +0.04954 | 4/4 | - |
| `api_only` | 6.78953 | -0.04954 | +0.00000 | 4/4 | - |
| `literature_rag_default` | 6.83954 | +0.00047 | +0.05001 | 4/4 | `tsp_nearest_insertion`, `tsp_nearest_neighbor` |
| `literature_rag_targeted_regret_farthest` | 6.51118 | -0.32789 | -0.27835 | 4/4 | `tsp_regret_insertion`, `tsp_farthest_insertion` |

关键判断：

1. targeted Literature-RAG 是当前 official benchmark 上最清晰的正向 signal。
2. 默认 Literature-RAG 失败不是“RAG 无效”，而是检索选卡太保守。
3. RAG 的核心变量应从“是否加 RAG”改成“检索/选择了哪类 skill cards”。
4. 下一步可以围绕 TSP 做 repeat 或 Gen1，但需要保留 query、selected cards、best code，避免只汇报 objective。

## 2026-06-04 追加：TSP targeted Literature-RAG repeat=3 + 深度进化完成

已执行 prompt_loop 中 Step 1-2c：

### repeat=3 (init-only, gen=0, pop=4)

| repeat | best | vs pure |
|---|---|---|
| 1 | 6.30547 | -0.53360 |
| 2 | 6.50049 | -0.33858 |
| 3 | 6.73293 | -0.10614 |
| median | 6.50049 | |
| min | 6.30547 | |

3/3 全部低于 pure 和 api_only。信号稳定。

### 深度进化

| config | best | vs pure | 进化轨迹 |
|---|---|---|---|
| gen=1,pop=4 | 7.3266 | +0.48753 | init 弱 (7.33)，gen1 无改善 |
| gen=4,pop=8 | **6.28736** | **-0.55171** | init=6.51 → gen2=6.32 → gen3=6.29 |
| gen=8,pop=8 | 6.49327 | -0.34580 | init=6.49，plateau 到 gen8 |

关键判断：

1. targeted Literature-RAG 的 signal 已验证稳定——repeat 3/3 有效。
2. gen=4,pop=8 取得当前最佳 **6.28736**，且进化有可解释轨迹（gen0→gen2→gen3 逐步改善）。
3. gen=8 未超过 gen=4——deep evolution 进入 plateau，边际收益递减。
4. gen=16 留待后续（预计 6h，不阻塞其他任务）。

## 2026-06-05 追加：CVRP card 修复完成

### 问题诊断

old lit_rag 选中的 `cvrp_nearest_capacity` + `cvrp_capacity_slack` 全部容量优先：
- pure EOH: distance-first, switch near depot (13.207)
- old lit_rag: capacity-first 加权 (14.494, **+1.287** worse)

### 修复

| 变更 | 内容 |
|---|---|
| `cvrp_capacity_slack` → `cvrp_far_first` | 从 depot 出发优先选远方 customer |
| `cvrp_nearest_capacity` | 去掉 demand/capacity 评分项 |
| `cvrp_savings` / `cvrp_regret` | 去掉 capacity slack penalty |
| 默认 query | "cvrp construct select next customer distance farthest cluster regret route depot" |

### 结果

| arm | best | vs pure |
|---|---|---|
| pure_eoh | 13.207 | baseline |
| old lit_rag | 14.494 | +1.287 |
| fixed lit_rag | 13.283 | +0.076 |

改善 **-1.21**，已逼近 pure baseline (+0.08)。策略生成正确：far-first from depot → nearest from current。
