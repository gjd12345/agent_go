# C+L+V Harness 周展示记录

日期：2026-05-31

本文是 weekly showcase 的本地工作记录，用来说明当前已经实现了什么、smoke 实验证明了什么。它不是论文级最终结果表。

## 范围

本阶段目标是摆脱只演化单一 `InsertShips()` 函数的限制，展示同一套 C+L+V harness 能迁移到：

- 同一个 Go VRP 求解器中的多个目标函数：`InsertShips()` 和 `Optimization()`。
- 多个组合优化问题族：VRP 和 0/1 knapsack。
- 同一个小规模 smoke cell 上的 baseline 与 API-only prompt/context 对比。

## Harness 结构

新增了一个轻量 registry 层：

- `eoh_go/eoh_runner/target_spec.py`
- `eoh_go/eoh_runner/problem_spec.py`
- `eoh_go/eoh_runner/registry.py`

`TargetSpec` 描述可演化函数边界：函数名、签名、prompt 约束、抽取/替换正则、seed 路径、RAG API context 和 guard 检查。

`ProblemSpec` 描述优化问题边界：语言、源文件、二进制/evaluator 形态、benchmark 数据、目标方向和默认指标。

已注册 targets：

| Target | Problem | 状态 | 说明 |
|---|---|---|---|
| `InsertShips` | VRP dynamic insertion | 已有 | 保持向后兼容的默认目标。 |
| `Optimization` | VRP route/order improvement | 已接入 | 复用 `InsertShips` 所在 Go simulator 和 evaluator 路径。 |
| `SelectItems` | 0/1 knapsack | 已接入 | 使用独立的最小 Go evaluator 和 Agent_EOH example。 |
| `SplitOrders` | Mixer/concrete truck split | 已接入 | 导师给的问题，作为跨问题 feasibility smoke。 |
| `ScoreBin` | Online Bin Packing | 已接入 | EoH 原论文主例对齐，作为下一阶段 RAG 有效性主线。 |

已注册 problems：

| ProblemSpec | 语言 | 来源 |
|---|---|---|
| `vrp_insertships` | Go | `main.go`, `routing.go` |
| `knapsack` | Go | `eoh_go_workspace/problems/knapsack/knapsack_solver.go` |
| `mixer_split` | Go | `eoh_go_workspace/problems/mixer_split/mixer_split_solver.go` |
| `bin_packing_online` | Go | `eoh_go_workspace/problems/bin_packing_online/bin_packing_solver.go` |

## InsertShips 代码演化证据

已生成：

- `eoh_go_workspace/reports/code_evolution_insertships_gen8.md`

数据来源：

- `eoh_go_workspace/reports/tables/gen8_explore_20260527/baseline/run_20260527_210925/`

报告不展示 per-generation 内部 `pops_best` objective，因为它只是 EOH 内部选择信号，不等同于最终验证解。性能结论只使用 guarded external evaluator 重新验证后的结果。

| Cell | Seed J | Verified Best EOH J |
|---|---:|---:|
| `rc101 d50 t=1.0` | 713.52 | 274.90 |
| `rc101 d75 t=1.0` | 549.48 | 393.30 |

观察到的策略演化：

- 早期 generations：first feasible insertion + 简单 fallback。
- 中期 generations：遍历所有 Assigns，比较 cost delta，显式 rollback。
- 后期 generations：best-delta insertion + fallback new Assign + `RenewnTotalCost()`。

代表代码片段如下。这里展示的是每代 `pops_best` 中的代表结构；性能结论仍只看最终 guarded evaluator 的 verified J。

Gen 1：first feasible insertion，成功后立即 `break`：

```go
for jj := range oris {
    for _, ii := range rand_range {
        if !dispatch.Assigns[ii].AddShip(total_ship+jj, oris[jj], dess[jj]) {
            dispatch.Assigns[ii].Cost = -1
        } else {
            dispatch.Assigns[ii].GenRoute()
        }
        if dispatch.Assigns[ii].Cost < 0 {
            dispatch.Assigns[ii].RemoveShip(total_ship + jj)
            dispatch.Assigns[ii].GenRoute()
        } else {
            if ii >= dispatch.AssignsLen {
                dispatch.AssignsLen += 1
            }
            break
        }
    }
}
```

Gen 4：trial all Assigns，计算 `deltaCost`，试插后 rollback：

```go
for _, idx := range assignIndices {
    origCost := dispatch.Assigns[idx].Cost
    ok := dispatch.Assigns[idx].AddShip(shipId, ori, des)
    if ok {
        dispatch.Assigns[idx].GenRoute()
        newCost := dispatch.Assigns[idx].Cost
        deltaCost := newCost - origCost
        if deltaCost >= 0 || bestAssignIdx == -1 || deltaCost < bestDeltaCost {
            bestDeltaCost = deltaCost
            bestAssignIdx = idx
        }
        dispatch.Assigns[idx].RemoveShip(shipId)
        dispatch.Assigns[idx].GenRoute()
    }
}
if bestAssignIdx != -1 {
    ok := dispatch.Assigns[bestAssignIdx].AddShip(shipId, ori, des)
    if ok {
        dispatch.Assigns[bestAssignIdx].GenRoute()
        inserted = true
    }
}
```

Gen 8：best-delta commit + new Assign fallback，最后更新总成本：

```go
for aIdx := 0; aIdx < dispatch.AssignsLen; aIdx++ {
    assign := &dispatch.Assigns[aIdx]
    origCost := assign.Cost
    trialOk := assign.AddShip(shipId, ori, des)
    if trialOk {
        assign.GenRoute()
        deltaCost := assign.Cost - origCost
        if deltaCost < bestDeltaCost {
            bestDeltaCost = deltaCost
            bestAssignIdx = aIdx
        }
        assign.RemoveShip(shipId)
        assign.GenRoute()
    }
}
if bestAssignIdx != -1 {
    finalAssign := &dispatch.Assigns[bestAssignIdx]
    if finalAssign.AddShip(shipId, ori, des) {
        finalAssign.GenRoute()
        inserted = true
    }
}
if !inserted && dispatch.AssignsLen < MAXASSIGNS {
    nextIdx := dispatch.AssignsLen
    if dispatch.Assigns[nextIdx].AddShip(shipId, ori, des) {
        dispatch.Assigns[nextIdx].GenRoute()
        dispatch.AssignsLen++
    }
}
dispatch.RenewnTotalCost()
```

## Optimization Target Smoke

证据等级：feasibility-only smoke。当前还没有实现 runtime ship-id multiset guard，所以这些结果只能证明目标管线能跑通，不能证明所有语义保持检查已经完整。

命令形态：

```bash
python3 -m eoh_go.experiments.eoh_arrival_grid \
  --target Optimization \
  --problem-name vrp_insertships \
  --problem rc101.json \
  --density d50 \
  --arrival-scale 1.0 \
  --use-density-source-dirs \
  --generations 1 \
  --pop-size 4 \
  --max-instances 1
```

结果：

| Variant | Run | Valid | Invalid | Seed J | Best EOH J | Verdict |
|---|---|---:|---:|---:|---:|---|
| Baseline | `weekly_optimization_smoke/baseline/run_20260531_135910` | 1 | 1 | 713.52 | 713.52 | PASS: target pipeline runs |
| API-only | `weekly_optimization_smoke/api_only/run_20260531_140257` | 1 | 1 | 713.52 | 713.52 | PASS: manual context path runs |

解读：

- 这是可行性证据，不是性能提升证据。
- `Optimization()` 现在可以被 prompt、从 `main.go` 抽取 seed、替换回 `main.go`、编译、评估和汇总。
- 本次生成的 mutants 没有超过 seed；对于 weekly harness 目标，这是可接受的 smoke 结果。

## Knapsack Problem Smoke

证据等级：smoke。当前 evaluator 只使用一个小 JSON instance，因此它证明的是多问题迁移能力，不是稳定性能。

新增内容：

- `eoh_go_workspace/problems/knapsack/knapsack_solver.go`
- `eoh_go_workspace/problems/knapsack/testdata/testdata_01.json`
- `Agent_EOH/eoh/src/eoh/examples/user_knapsack_go/prompts_knapsack_go.py`
- `Agent_EOH/eoh/src/eoh/examples/user_knapsack_go/prob_knapsack_go.py`
- `Agent_EOH/eoh/src/eoh/examples/user_knapsack_go/seeds_knapsack_go.json`
- `eoh_go/experiments/knapsack_smoke.py`

结果：

| Variant | Run | Population | Valid | Best Objective | Best Value | Verdict |
|---|---|---:|---:|---:|---:|---|
| Baseline | `weekly_knapsack_smoke/run_20260531_135737` | 2 | 1 | -283.00 | 283.00 | PASS: new problem pipeline runs |
| API-only | `weekly_knapsack_smoke/api_only/run_20260531_140651` | 2 | 1 | -283.00 | 283.00 | PASS: manual context path runs |

解读：

- 这证明 harness 可以跑第二类组合优化问题，而且目标函数签名和 evaluator 都不同。
- 本次没有超过 seed；它只作为 smoke evidence 使用。

## 验证

## Online Bin Packing / ScoreBin 更新

证据等级：harness + one-cell smoke。OBP 是 EoH 原论文中最适合对齐的主例之一；当前实现用 Go evaluator 包装 `ScoreBin`，目标是最小化 `gap_to_lb = (used_bins - lower_bound) / lower_bound`。

新增内容：

- `eoh_go_workspace/problems/bin_packing_online/bin_packing_solver.go`
- `eoh_go_workspace/problems/bin_packing_online/testdata/obp_5x60_c100.json`
- `Agent_EOH/eoh/src/eoh/examples/user_bin_packing_go/prompts_bin_packing_go.py`
- `Agent_EOH/eoh/src/eoh/examples/user_bin_packing_go/prob_bin_packing_go.py`
- `Agent_EOH/eoh/src/eoh/examples/user_bin_packing_go/seeds_bin_packing_go.json`
- `eoh_go/experiments/eoh_obp_smoke.py`
- OBP RAG cards: `obp_first_fit`, `obp_best_fit`, `obp_worst_fit`, `obp_harmonic`, `obp_funsearch_residual_poly`, `obp_eoh_util_sqrt_exp`
- OBP API global card: `obp_api_skeleton`

本地 seed code：

```go
func ScoreBin(item int, remaining []int, capacity int) []float64 {
    scores := make([]float64, len(remaining))
    for i, rem := range remaining {
        scores[i] = float64(capacity - (rem - item))
    }
    return scores
}
```

本地 evaluator seed 结果：

| Dataset | Avg used bins | Avg lower bound | Avg gap |
|---|---:|---:|---:|
| `obp_5x60_c100` | 28.8 | 27.4 | 0.0590303 |

最小 EOH 对照：

| Arm | Run | Population | Valid | Seed gap | Best verified gap | RAG selected |
|---|---|---:|---:|---:|---:|---|
| Vanilla | `eoh_obp_showcase_20260601/vanilla/run_20260601_112409` | 2 | 1 | 0.0590303 | 0.05903 | - |
| Literature-RAG | `eoh_obp_showcase_20260601/literature/run_20260601_112555` | 2 | 1 | 0.0590303 | 0.05903 | `obp_best_fit`, `obp_worst_fit`, `obp_first_fit` |

解读：

- OBP harness、target-specific RAG filtering、API/global card 和 literature cards 都已跑通。
- 这一组没有证明 RAG 性能提升；两边都只保住 seed，新候选全部 penalty。
- 当前更像 prompt/变异稳定性问题：`ScoreBin` target 很小，但模型容易生成长度错误、非法 math 或不可编译代码。下一步应先缩短 context 或增加多 seed，而不是扩大实验矩阵。

当前最佳代码就是 seed/best-fit 结构：

```go
func ScoreBin(item int, remaining []int, capacity int) []float64 {
    scores := make([]float64, len(remaining))
    for i, rem := range remaining {
        scores[i] = float64(capacity - (rem - item))
    }
    return scores
}
```

### 2026-06-01 OBP 修正实验

复核发现上一轮 `pop_size=8` 但最终 population 只有 2 条，不是“8 个候选都无提升”。根因是 `Agent_EOH` 的 Go 抽取逻辑只识别 `func InsertShips(`，导致 `ScoreBin` 被误判成 Python target，LLM 返回的 Go 代码无法被抽取，最终变成 `code=None` penalty。

已修复：

- `eoh_evolution.py`：`_extract_go_function(response, function_name)` 支持任意 Go target。
- `prompts_bin_packing_go.py`：强化公式型 `ScoreBin` 约束，要求简单 loop、填满 `scores`、不写复杂结构。
- `tests/test_eoh_runner_specs.py`：新增 `ScoreBin` Go 抽取回归测试。

修正后 smoke：

| Arm | Run | Population | Valid | Seed gap | Best verified gap | RAG context | Verdict |
|---|---|---:|---:|---:|---:|---|---|
| Vanilla | `eoh_obp_repair_20260601/vanilla/run_20260601_114904` | 6 | 5 | 0.0590303 | 0.05903 | none | PASS: 生成稳定性恢复 |
| API+Warning-only | `eoh_obp_repair_20260601/api_warning/run_20260601_114956` | 2 | 2 | 0.0590303 | 0.05903 | 894 chars, not truncated | STOP: 未达 `population>=5/valid>=3` |

API+Warning-only trace：

```text
rag_context_chars = 894
rag_context_truncated = false
rag_global_items = obp_api_skeleton + suspicious_low_objective + negative_or_missing_result + timeout_or_unbounded_search
rag_selected_items = []
```

注意：`rag_global_items` 记录的是可用 global items；当前 `prompt_context.py` 实际只注入第一个 warning。这里仍称为 API+Warning-only，而不是纯 API-only。

两组 best code 均为 best-fit seed：

```go
func ScoreBin(item int, remaining []int, capacity int) []float64 {
    scores := make([]float64, len(remaining))
    for i, rem := range remaining {
        scores[i] = float64(capacity - (rem - item))
    }
    return scores
}
```

解读：

- vanilla arm 已经满足 `population_size >= 5` 和 `valid_candidates >= 3`。
- API+Warning-only arm 未满足停止门槛，因此按 goal 没有继续跑 Residual-RAG。
- 当前能说的是：OBP 的主工程问题已经从“Go 抽取失败”修复为“RAG arm 候选多样性/去重不足”。还不能比较 RAG 性能。

已运行命令：

```bash
PYTHONPATH=. python3 -m unittest tests/test_eoh_runner_specs.py -q
PYTHONPATH=. python3 -m unittest discover -s tests -q
python3 -m compileall -q eoh_go Agent_EOH/eoh/src/eoh/examples/user_insertships_go Agent_EOH/eoh/src/eoh/examples/user_knapsack_go Agent_EOH/eoh/src/eoh/examples/user_bin_packing_go
python3 -m compileall -q Agent_EOH/eoh/src/eoh/methods/eoh/eoh_evolution.py Agent_EOH/eoh/src/eoh/examples/user_bin_packing_go/prompts_bin_packing_go.py
go build -o /tmp/eoh_go_mainbin .
go build -o /tmp/eoh_go_obp_solver eoh_go_workspace/problems/bin_packing_online/bin_packing_solver.go
go run eoh_go_workspace/problems/knapsack/knapsack_solver.go eoh_go_workspace/problems/knapsack/testdata/testdata_01.json
go run eoh_go_workspace/problems/bin_packing_online/bin_packing_solver.go eoh_go_workspace/problems/bin_packing_online/testdata/obp_5x60_c100.json
caffeinate -i -m -s python3 -m eoh_go.experiments.eoh_obp_smoke --root . --output-dir eoh_go_workspace/reports/tables/eoh_obp_repair_20260601/vanilla --llm-model JoyAI-LLM-Pro --generations 1 --pop-size 8 --run-timeout-s 10
caffeinate -i -m -s python3 -m eoh_go.experiments.eoh_obp_smoke --root . --output-dir eoh_go_workspace/reports/tables/eoh_obp_repair_20260601/api_warning --llm-model JoyAI-LLM-Pro --generations 1 --pop-size 8 --run-timeout-s 10 --use-rag-context --rag-mode literature --rag-top-k 0 --rag-max-chars 900
```

观察结果：

- `tests/test_eoh_runner_specs.py`：5 tests OK。
- Full unit suite：50 tests OK。
- Compileall：OK。
- Go build：OK。
- Knapsack seed solver：`value 283`，`weight 50`，feasible。

## 当前限制

- `Optimization()` 目前只有语法/可行性 guard，还没有 runtime ship-id multiset preservation 检查。
- Knapsack 目前只有一个测试实例，足够做 smoke，不足以支撑论文级结论。
- 这些 smoke runs 的实际 population size 是 2，因为当前 EOH operator 配置是 `m1,m2` 加一个 seed；不要把它解读成完整 `pop=4` 统计证据。
- Smoke runs 证明的是 framework portability，不是 performance superiority。

## 2026-05-31 补充实验

### InsertShips 数据补强

目标：补全 density branch 结论的统计稳定性。

| Cell | Rep | Bsl_best_J | RAG_best_J | ΔJ | 裁决 |
|------|:---:|----------:|----------:|-----:|:---:|
| d50 history rep_3 | 3 | 509.82 | 606.97 | +97.15 | worse |
| d75 API rep_4 | 4 | 365.92 | 296.17 | −69.75 | better |
| d75 API rep_5 | 5 | 376.70 | 376.70 | 0.00 | same |

更新后的正式证据：

| 配置 | Cell | valid pairs | median ΔJ | better/worse/same |
|------|------|:---:|------:|:---:|
| d50 API-only | RC101-d50 | 3/3 | −95.44 | 2/0/1 |
| d50 History-RAG | RC101-d50 | 3/3 | +97.15 | 1/2/0 |
| d75 API-only | RC101-d75 | 5/5 | 0.00 | 2/1/2 |
| d75 History-RAG | RC101-d75 | 3/3 | −134.52 | 2/0/1 |

结论不变：API-only(d50) + History-RAG(d75)。d75 API-only 5-rep 中位数 0.00，仍然 inconclusive。

### Optimization gen=1 pop=8 完整实验

| Cell | Arm | Seed J | Best EOH J | Valid | Build |
|------|-----|------:|----------:|:---:|:---:|
| d50 | Baseline | 713.52 | 713.52 | 1 | OK |
| d50 | History-RAG | 713.52 | 713.52 | 1 | OK |
| d75 | Baseline | 549.48 | 549.48 | 1 | OK |
| d75 | History-RAG | 549.48 | 549.48 | 1 | OK |

**所有 arm 均返回 seed**。LLM 能生成编译通过的 Optimization 代码，但无法超过 seed。

### Optimization gen=8 pop=4 深度演化

| Cell | Arm | Seed J | Best EOH J | Valid | 状态 |
|------|-----|------:|----------:|:---:|:---:|
| d50 | Baseline | 713.52 | 713.52 | 1 | 完成 |
| d75 | Baseline | — | — | — | 超时未完成 |

gen=8 也没有改善。LLM 在 Optimization 函数上未能产生有效改进。

### Knapsack gen=1 pop=8

| Arm | Seed Value | Best Value | Valid |
|-----|----------:|----------:|:---:|
| Baseline | 283 | 283 | 1 |
| API-only | 283 | 283 | 1 |

**同样所有 arm 均返回 seed。** Pipeline 跑通，但 LLM 无法改进。

### 跨算子总表（每周展示）

| Target | Problem | d50 best | d75 best | 最佳 Mode | 状态 |
|------|------|------:|------:|------|:--:|
| InsertShips | VRP-dispatch | **274.90** | **266.06** | API(d50)/Hist(d75) | 正式证据 |
| Optimization | VRP-route | 713.52 (seed) | 549.48 (seed) | 未超过 seed | 探索 |
| SelectItems | 0/1 Knapsack | 283 (seed) | — | 未超过 seed | 探索 |

### 关键发现

1. **框架迁移可行（C+L 层通用）**：3 个 target × 2 个 problem 的 pipeline 全部跑通（build + eval + guard）。registry 架构验证了 target-spec 抽象有效。

2. **但 C 层仍然绑定 InsertShips**：所有 22 个 corpus item（13 code_example + 1 API constraint + 3 failure case）的标签、id、内容都是 `insertships` 的。Optimization/Knapsack 的 `ctx_chars=MISSING`——`retrieve()` 返回空集，实际上等效于 baseline。

3. **"LLM 无法改进"的结论不可靠**：Optimization 和 Knapsack 在无任何 context 的情况下返回 seed，不奇怪——InsertShips 在 baseline 下也需要 RAG 才能突破。这是 C 层未适配，不是 LLM 能力不足。

4. **代码演化可视化已生成**：InsertShips gen=8 baseline 的每代代码结构和 strategy shift 已记录在 `code_evolution_insertships_gen8.md`。

## 下一步

1. **P0: 修复 C 层 target 绑定**——为 Optimization 和 Knapsack 各加 target-specific 的 API constraint + 至少 1 个 code_example + 1 个 failure case。方法：在 registry 的 `rag_api_context` 基础上，让 corpus 按 target filter。
2. 修复后重跑 Optimization gen=1 pop=8：检查 RAG 注入是否生效（ctx_chars > 0）。
3. Knapsack: 加 3-5 instances + RAG 后 gen=1 pop=8。
4. 每周展示报告：直接用本文件，加 InsertShips 代码演化可视化（gen1→4→8 图）+ C 层适配状态的对比。

---

## 2026-06-01 补充：C 层绑定修复 + 搅拌车 SplitOrders 迁移启动

本节记录 2026-06-01 的实际推进。上方“C 层仍然绑定 InsertShips / Optimization 和 Knapsack ctx missing”的判断已经过时，本轮已经修复 target-specific API context 绑定。

### 执行流程

- 已读取 `AGENTS.md` 和 `.codex/goals/weekly_showcase.md`。
- 按 L 级流程先启动只读 scout。scout verdict 为 WARNING：Knapsack prompt 未真正注入 `EOH_RAG_CONTEXT`，Knapsack summary 缺少 `rag_trace`，搅拌车属于 greenfield evaluator，需要谨慎分支。
- 后续实现聚焦 infrastructure 和本地 evaluator，不跑真实 LLM 大实验。

### 已完成变更

#### 1. C 层 target-specific global context 修复

`runner.py` 增加 target 到 RAG tag 的 alias：

| Target | RAG tags |
|---|---|
| `InsertShips` | `insertships` |
| `Optimization` | `optimization` |
| `SelectItems` | `knapsack`, `selectitems` |
| `SplitOrders` | `mixer`, `splitorders` |

本地 trace 验收结果：

| Target | Context chars | Global items |
|---|---:|---|
| `InsertShips` | 974 | `insertships_api_skeleton` + failure cases |
| `Optimization` | 911 | `optimization_api_skeleton` + failure cases |
| `SelectItems` | 870 | `knapsack_api_skeleton` + failure cases |
| `SplitOrders` | 949 | `mixer_split_api_skeleton` + failure cases |

结论：API skeleton 已能按 target 进入 global context。Knapsack 之前因为 `SelectItems` 与 `knapsack` tag 不匹配导致 context 为空的问题已修复。

#### 2. Knapsack prompt 注入修复

`Agent_EOH/eoh/src/eoh/examples/user_knapsack_go/prompts_knapsack_go.py` 已补齐 `EOH_RAG_CONTEXT` 注入逻辑，与 `InsertShips` 保持一致：

- 读取 `EOH_RAG_CONTEXT`。
- 非空时追加 `Relevant heuristic examples, pseudo-code, and safety constraints:`。
- 用 `BEGIN RAG CONTEXT` / `END RAG CONTEXT` 包裹。

这一步很关键：之前 Knapsack runner 能生成 trace，但 prompt 侧没有消费环境变量，实际 LLM 看不到 context。

#### 3. 搅拌车 SplitOrders 最小迁移

导师给的搅拌车材料可以作为可迁移组合优化问题，但不能直接把整个项目纳入 harness。当前采用最小可行抽象：

- 问题：混凝土订单拆分到不同容量车辆。
- Evolvable target：
  ```go
  func SplitOrders(orders []Order, vehicles []Vehicle, workHours float64) []SubOrder
  ```
- 目标：在保持订单总量守恒和车辆容量约束下，最小化拆单/容量不匹配/未覆盖惩罚。

新增内容：

| 文件 | 作用 |
|---|---|
| `eoh_go_workspace/problems/mixer_split/mixer_split_solver.go` | Go evaluator + `SplitOrders` seed target |
| `eoh_go_workspace/problems/mixer_split/testdata/testdata_01.json` | 小规模搅拌车测试实例 |
| `Agent_EOH/eoh/src/eoh/examples/user_mixer_split_go/prompts_mixer_split_go.py` | EOH prompt，支持 RAG context 注入 |
| `Agent_EOH/eoh/src/eoh/examples/user_mixer_split_go/prob_mixer_split_go.py` | build/run evaluator |
| `Agent_EOH/eoh/src/eoh/examples/user_mixer_split_go/seeds_mixer_split_go.json` | seed implementation |
| `eoh_go/experiments/mixer_split_smoke.py` | smoke runner |

安全修正：

- Knapsack/Mixer 的 Python evaluator 运行 `go build` 和 generated binary 时只传 allowlist 环境变量，避免 generated code 读取 `DEEPSEEK_API_KEY` 等敏感配置。
- Mixer evaluator 拒绝未知车辆容量，避免 generated `SplitOrders` 返回虚构超大 `VehicleCapacity` 逃过容量约束。

本地 evaluator 验收：

```text
go run eoh_go_workspace/problems/mixer_split/mixer_split_solver.go eoh_go_workspace/problems/mixer_split/testdata/testdata_01.json
final cost 175.014675
suborders 16
feasible true
reason valid
```

Seed 通过 Python evaluator：

```text
Evaluation(seed) = 175.014675
last_error = None
```

结论：搅拌车 `SplitOrders` 已具备“可编译、可替换、可评估”的最小 harness 条件，可以作为 Knapsack 之后的第二个跨问题迁移目标。

### 当前验证

已运行：

```bash
PYTHONPATH=. python3 -m unittest tests.test_eoh_runner_specs tests.test_rag_runner_integration tests.test_rag_build_corpus -q
PYTHONPATH=. python3 -m unittest discover -s tests -q
python3 -m compileall -q eoh_go Agent_EOH/eoh/src/eoh/examples/user_insertships_go Agent_EOH/eoh/src/eoh/examples/user_knapsack_go Agent_EOH/eoh/src/eoh/examples/user_mixer_split_go
go build -o /tmp/eoh_go_mainbin .
go run eoh_go_workspace/problems/mixer_split/mixer_split_solver.go eoh_go_workspace/problems/mixer_split/testdata/testdata_01.json
```

结果：

| 命令 | 结果 |
|---|---|
| focused unit tests | 23 tests OK |
| full unit suite | 54 tests OK |
| compileall | OK |
| top-level Go build | OK |
| mixer direct run | OK |
| mixer seed evaluator | OK |

补充说明：`go test ./...` 不作为本仓库当前验收命令。它会扫到 `eoh_go_workspace/candidate_sources/` 下的历史候选代码片段，这些文件只有 `func InsertShips...`，不是完整 Go package，因此会报 `expected 'package', found 'func'`。顶层 `go build` 和新增 problem 包验证已经覆盖本轮目标。

### LLM smoke 阻塞

尝试启动 Knapsack proper smoke 时，EOH 侧返回：

```text
Error in LLM API, wrong endpoint, key, model or local deployment!
```

只检查了配置是否存在，没有读取或打印 API key：

```text
DEEPSEEK_API_KEY_PRESENT=true
```

随后用公司授权 ChatRhino endpoint 做连通性检查，未输出 key 或前缀。结果为连接超时：

```text
CONNECT_ERROR timeout timed out
```

因此本轮没有继续反复重试 LLM smoke。当前 blocker 是运行环境到 ChatRhino endpoint 的网络/API 连通性，不是 harness 编译或 evaluator 问题。

### 当前结论

| 方向 | 状态 | 结论 |
|---|---|---|
| InsertShips | 已有正式证据 | 继续作为主结果线 |
| Optimization | smoke 已跑通 | 可展示同一 Go solver 内多 target，但未超过 seed |
| Knapsack | prompt/context 绑定已修复 | 等 API 连通后重跑 baseline vs API-only |
| Mixer SplitOrders | evaluator + prompt + seed + smoke runner 已就绪 | 等 API 连通后启动第一组 baseline/API-only smoke |

### 下一步断点

API 连通恢复后，优先执行：

1. Knapsack baseline vs API-only proper smoke，确认 `rag_global_items` 包含 `knapsack_api_skeleton`。
2. Mixer SplitOrders baseline smoke，确认 generated `SplitOrders` 能通过 build/evaluator。
3. Mixer SplitOrders API-only smoke，确认 `rag_global_items` 包含 `mixer_split_api_skeleton`。

建议先只跑一组实例，不追求性能提升；下周展示的重点是“同一 C+L+V harness 能迁移到多个组合优化问题，并且每个 target 都有正确的 evaluator 与 context 注入链路”。

---

## 2026-06-01 续跑：Knapsack 和 Mixer LLM smoke

本节记录 API 连通恢复后的真实 LLM smoke。按用户要求，本节除了写策略/指标，也列出最终 `pops_best` 中被选中的具体代码。注意：这些都是 gen=1 smoke，不是论文级稳定性结果。

### API 连通与运行约束

- 只检查连通性，未读取或打印 API key。
- 连通性结果：`API_CONNECT_OK 200`。
- 所有 EOH smoke 都使用 `caffeinate -i -m -s`，每次只跑一个实验进程。

### Knapsack: baseline vs API-only

| Arm | Run | RAG global | Population | Valid | Best objective | Best value | 结论 |
|---|---|---|---:|---:|---:|---:|---|
| Baseline | `weekly_knapsack_proper_20260601/baseline/run_20260601_100231` | none | 2 | 1 | -283.0 | 283.0 | 跑通，best 为 seed |
| API-only | `weekly_knapsack_proper_20260601/api_only/run_20260601_100907` | `knapsack_api_skeleton` + failure cases | 2 | 1 | -283.0 | 283.0 | RAG context 生效，best 仍为 seed |

API-only trace 证明：

```text
rag_context_chars = 870
rag_global_items = knapsack_api_skeleton, suspicious_low_objective, negative_or_missing_result, timeout_or_unbounded_search
rag_selected_items = []
```

最终 best code（Baseline 与 API-only 相同，来自 `pops_best/population_generation_1.json`）：

```go
func SelectItems(items []Item, capacity int) []bool {
    selected := make([]bool, len(items))
    remaining := capacity
    for i, item := range items {
        if item.Weight <= remaining {
            selected[i] = true
            remaining -= item.Weight
        }
    }
    return selected
}
```

解读：Knapsack 的链路已经跑通，API skeleton 确实进入 prompt；但 gen=1 只生成 2 个候选，其中 mutated candidate 均无效，最终仍选择 seed。这个结果证明 harness portability，不证明 RAG 能提升 Knapsack。

### Mixer SplitOrders: baseline vs API-only

| Arm | Run | RAG global | Population | Valid | Best objective | 结论 |
|---|---|---|---:|---:|---:|---|
| Baseline | `weekly_mixer_split_smoke_20260601/baseline/run_20260601_101704` | none | 2 | 1 | 175.01468 | 跑通，best 为 seed |
| API-only | `weekly_mixer_split_smoke_20260601/api_only/run_20260601_102257` | `mixer_split_api_skeleton` + failure cases | 2 | 1 | 175.01468 | RAG context 生效，best 仍为 seed |

API-only trace 证明：

```text
rag_context_chars = 949
rag_global_items = mixer_split_api_skeleton, suspicious_low_objective, negative_or_missing_result, timeout_or_unbounded_search
rag_selected_items = []
```

最终 best code（Baseline 与 API-only 相同，来自 `pops_best/population_generation_1.json`）：

```go
func SplitOrders(orders []Order, vehicles []Vehicle, workHours float64) []SubOrder {
    caps := make([]float64, 0)
    for _, vehicle := range vehicles {
        if vehicle.Capacity > 0 && vehicle.Count > 0 {
            caps = append(caps, vehicle.Capacity)
        }
    }
    for i := 0; i < len(caps); i++ {
        for j := i + 1; j < len(caps); j++ {
            if caps[j] > caps[i] {
                caps[i], caps[j] = caps[j], caps[i]
            }
        }
    }
    if len(caps) == 0 {
        return []SubOrder{}
    }

    result := make([]SubOrder, 0)
    largest := caps[0]
    for _, order := range orders {
        remaining := order.Volume
        for remaining > 1e-9 {
            chosen := largest
            for _, cap := range caps {
                if remaining <= cap+1e-9 {
                    chosen = cap
                }
            }
            volume := math.Min(remaining, chosen)
            result = append(result, SubOrder{
                OrderID:         order.ID,
                Volume:          volume,
                VehicleCapacity: chosen,
            })
            remaining -= volume
        }
    }
    return result
}
```

解读：搅拌车 `SplitOrders` 已经从导师项目材料抽象成可演化 target，并完成真实 LLM smoke。当前 gen=1 结果仍为 seed，原因和 Knapsack 一样：只有 seed 有效，mutated candidate 未通过 evaluator。下一步如果要追求性能，需要增加实例数、提高 generations，或者提供 SplitOrders 专属 skill cards，而不是只给 API skeleton。

### 续跑后的总判断

| Target | Problem | Evidence | RAG/API context | Performance |
|---|---|---|---|---|
| `InsertShips` | VRP dynamic insertion | 正式多轮实验 + 代码演化 | 已验证 | 有稳定提升分支 |
| `Optimization` | VRP route/order improvement | smoke | 已验证 | 未超过 seed |
| `SelectItems` | Knapsack | LLM smoke | `knapsack_api_skeleton` 已验证 | 未超过 seed |
| `SplitOrders` | Mixer/concrete truck order split | LLM smoke | `mixer_split_api_skeleton` 已验证 | 未超过 seed |
| `ScoreBin` | Online Bin Packing | 修正 smoke | `obp_api_skeleton` 已验证；Residual-RAG 按停止条件未跑 | vanilla 生成稳定性恢复，RAG arm 未达比较门槛 |

结论：本周展示可以诚实表达为“C+L+V harness 已经能跨 target 和跨组合优化问题运行；目前只有 InsertShips 有性能证据，Knapsack/Mixer/OBP 先作为跑通证据。下一阶段要补的是每个新问题的 domain skill cards、prompt 稳定性和多实例 evaluator，而不是再证明框架能不能跑。”

## 2026-06-01 补充：OBP true API-only warning gate

本节记录 `e6590e3` 之后的 OBP RAG arm 修正。目标不是继续扩大实验，而是先把 RAG context 路由做干净：API rules 固定前置，failure warnings 可关闭，strategy cards 只在 Residual-RAG arm 里进入 top-k。

### Infrastructure 改动

新增 true API-only 开关：

- `EOHConfig.rag_include_warnings: bool = True`
- `eoh_obp_smoke.py --no-rag-warnings`
- `runner.py` trace 拆分：
  - `rag_global_items_available`
  - `rag_global_items_injected`
  - `rag_global_items` 保持为 injected alias，兼容旧报告

语义：

| 类型 | true API-only 行为 |
|---|---|
| `api_constraint` | 固定注入 |
| `failure_case` | available trace 中保留，但不注入 |
| `algorithm_card` | `rag_top_k=0` 时不检索 |

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

配置：

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

best code：

```go
func ScoreBin(item int, remaining []int, capacity int) []float64 {
    scores := make([]float64, len(remaining))
    for i, rem := range remaining {
        scores[i] = float64(capacity - (rem - item))
    }
    return scores
}
```

解读：

- true API-only 已经确认：prompt 中只有 `obp_api_skeleton`，没有 warning，也没有 strategy card。
- 但 final population 仍只有 3，未达到本轮 goal 的 `population_size >= 5` gate。
- 因此 Residual-RAG 没有继续跑；这不是实验失败，而是按停损条件避免制造无统计意义的对比。
- 日志显示多个候选 objective 都是 `0.05903`，最终 population 只有 3 个不同 objective。下一步应区分 raw generated candidate count 与 final survivor population，判断是否被 EOH 去重/选择机制压缩。

### 本轮验证

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -q
python3 -m compileall -q eoh_go Agent_EOH/eoh/src/eoh/examples/user_bin_packing_go Agent_EOH/eoh/src/eoh/methods/eoh/eoh_evolution.py
go build -o /tmp/eoh_go_mainbin .
go build -o /tmp/eoh_go_obp_solver eoh_go_workspace/problems/bin_packing_online/bin_packing_solver.go
go run eoh_go_workspace/problems/bin_packing_online/bin_packing_solver.go eoh_go_workspace/problems/bin_packing_online/testdata/obp_5x60_c100.json
```

结果：

| 验证 | 结果 |
|---|---|
| full unit suite | 59 tests OK |
| compileall | OK |
| top-level Go build | OK |
| OBP solver build | OK |
| OBP direct seed run | `final cost 0.05903030` |

当前结论：OBP 工程链路继续保持 PASS；RAG arm 的 prompt 路由已经变干净，但 final population 仍偏小。下一步不应直接声称 RAG 无效，而应先复核 EOH survivor selection / objective 去重是否导致同分合法候选被压缩。
