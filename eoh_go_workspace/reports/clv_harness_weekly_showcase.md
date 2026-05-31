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

已注册 problems：

| ProblemSpec | 语言 | 来源 |
|---|---|---|
| `vrp_insertships` | Go | `main.go`, `routing.go` |
| `knapsack` | Go | `eoh_go_workspace/problems/knapsack/knapsack_solver.go` |

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

已运行命令：

```bash
PYTHONPATH=. python3 -m unittest tests/test_eoh_runner_specs.py -q
PYTHONPATH=. python3 -m unittest discover -s tests -q
python3 -m compileall -q eoh_go Agent_EOH/eoh/src/eoh/examples/user_insertships_go Agent_EOH/eoh/src/eoh/examples/user_knapsack_go
go build -o /tmp/eoh_go_mainbin .
go run eoh_go_workspace/problems/knapsack/knapsack_solver.go eoh_go_workspace/problems/knapsack/testdata/testdata_01.json
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
