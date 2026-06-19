# 外部 workspace2 改动与本地 SmartOperator 对比报告

生成日期：2026-05-21  
本地项目：`/Users/guojiadong.9/agent_ad`  
外部目录：`/Users/guojiadong.9/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/wxid_2hro74c3dhj722_fcdc/msg/file/2026-05/eoh_go_workspace2`

## 1. 结论摘要

外部 `eoh_go_workspace2` 的改动有参考价值，但不能直接合并为生产逻辑。

有效部分是：外部实验发现并验证了两类低密度 `d25` 场景下有效的 `InsertShips` 启发式，核心是“扫描所有已有车辆，按插入后成本增量选择最优车辆”，其中一个版本额外加入从车辆当前位置到订单起点的距离惩罚。本地复跑确认这类代码可以通过当前 `SmartOperator` 编译、评估和 guard。

高风险部分是：外部报告明确指出旧 evaluator 存在“丢单不罚分”漏洞，很多 EOH 候选通过少服务订单获得虚假低成本。外部 V2 分析已经按 `objective >= 0.7 * SA_baseline` 过滤疑似 dropper，而本地 `SmartOperator` 当前 guard 仍使用 `0.3 * SA_baseline`，过于宽松。

建议结合方式：不要直接复制外部 `.go` 文件；应把 guard-validated 的启发式沉淀为本地 `strategy_templates.py` 中的受控模板，并同步收紧 suspicious-low guard，最后用本地 grid 重新跑。

## 2. 本地 SmartOperator 当前状态

本地已有组件：

- `eoh_go/operator/agent_controller.py`：SmartOperator 主控，负责候选生成、编译修复、评估、guard、failure memory。
- `eoh_go/operator/strategy_templates.py`：受控模板模式，目前支持 `sa_exact`、`fast_nearest`、`balanced_delta`、`robust_first_feasible`。
- `eoh_go/operator/failure_memory.py`：记录 compile/runtime/negative/suspicious 等失败模式。
- `eoh_go/eoh_runner/candidate_guard.py`：离线候选筛选。
- `eoh_go/experiments/smart_operator_grid.py`：按 problem/density/arrival_scale 跑 grid。

本地设计重点是“把 LLM 可改范围收窄”：LLM 或 ReAct 只选择策略族和参数，真正 Go 代码由模板渲染，避免大段不受控代码造成编译失败、超时或行为漏洞。

当前不足：

- `balanced_delta` 只看 `top_k` 个最近车辆，不会全量扫描所有已有车辆。
- low-density `d25` 默认更偏 `fast_nearest`，没有利用外部验证有效的 all-vehicle best-fit delta。
- `_apply_guard()` 的 suspicious-low 阈值是 `0.3 * baseline`。
- `failure_memory.py` 文档和分类逻辑也使用 `<30% baseline`。
- 当前 runtime guard 只看 final cost，不检查是否所有订单被服务。

## 3. 外部 workspace2 改动内容

外部目录不是完整 git workspace，更像一次 EOH 实验产物，主要包含：

- `analysis_output_v2/ANALYSIS_REPORT_V2.md`
- `analysis_output_v2/tables/summary_comparison_v2.csv`
- `analysis_output_v2/tables/top_valid_algorithms.md`
- `analysis_output_v2/best_code/*_guard_validated.go`
- `analysis_output_v2/best_code/*_best_valid.go`
- `analyze_run_v2.py`
- `find_best_valid.py`
- `extract_guard_validated.py`

外部 V2 报告的关键发现：

| Cell | SA Baseline | Guard-validated J | 外部报告改善 | 状态 |
|---|---:|---:|---:|---|
| `rc101_d25_t0p8` | 660.15 | N/A | N/A | 未完成 guard re-eval |
| `rc101_d25_t0p9` | 645.45 | 511.94 | 20.7% | 可信 |
| `rc101_d25_t1p0` | 664.12 | 514.46 | 22.5% | 可信 |

外部 V2 还明确标出 dropper 污染：

| Cell | 疑似 dropper 占比 |
|---|---:|
| `d25_t0p8` | 88.8% |
| `d25_t0p9` | 23.4% |
| `d25_t1p0` | 35.0% |

这说明旧 EOH 结果中有大量虚假优秀候选，必须先修 guard，再谈集成。

## 4. 本地复跑验证

我用当前本地 `SmartOperator._evaluate_candidate()` 对外部两个 guard-validated Go 版本做了最小复跑：

| 外部代码 | 本地编译 | 本地评估 | 本地 J | Guard | RES |
|---|---|---|---:|---|---:|
| `rc101_d25_t0p9_guard_validated.go` | 通过 | 通过 | 514.463380086386 | valid | 6.805751 |
| `rc101_d25_t1p0_guard_validated.go` | 通过 | 通过 | 514.463380086386 | valid | 6.509003 |

本地 SA baseline：

| 数据 | J | RES |
|---|---:|---:|
| `solomon_benchmark_d25/rc101.json` | 664.1195472849001 | 5.715343 |

按本地复跑结果计算，外部 guard-validated 代码相对 SA baseline 改善约：

`(514.463380086386 - 664.1195472849001) / 664.1195472849001 = -22.53%`

注意：本地 `SmartOperator._run_go_evaluation()` 当前固定取 density 目录下第一个 JSON，即 `rc101.json`。因此这个验证说明“在本地 d25/rc101 的 evaluator 上有效”，但不能证明对全部 problem/density/arrival_scale 泛化有效。

## 5. 核心算法差异

本地模板当前大致是：

| 本地策略 | 行为 | 优点 | 局限 |
|---|---|---|---|
| `sa_exact` | 接近原始随机可行插入 | 安全、可作为 baseline | 不主动优化插入成本 |
| `fast_nearest` | 只看最近 `top_k` 车辆 | 快 | 容易错过远处但插入成本更低的车辆 |
| `balanced_delta` | 最近 `top_k` 内按成本增量 + pickup 距离打分 | 比 nearest 更稳 | 搜索面仍受 `top_k` 限制 |
| `robust_first_feasible` | 保守可行优先 | 适合失败后兜底 | 优化能力弱 |

外部 guard-validated 策略是：

| 外部策略 | 行为 | 本地是否已有 |
|---|---|---|
| best-fit delta | 扫描所有非空车辆，模拟插入，选择 `newCost - oldCost` 最小者 | 没有 |
| distance-weighted delta | 扫描所有非空车辆，选择 `(newCost - oldCost) + 0.5 * dist(current, origin)` 最小者 | 没有 |
| fallback insertion | 若没有可行已有车辆，则尝试新车/顺序兜底 | 部分已有 |

关键差异：外部有效版本不是“最近车辆优先”，而是“全车辆插入成本优先”。这解释了它在 d25/rc101 上能明显优于 SA/random insertion。

## 6. 风险对比

| 风险 | 本地 SmartOperator | 外部 workspace2 |
|---|---|---|
| 编译风险 | 模板化后较低 | 原始 `.go` 文件带报告头、`package main`、截断片段，不能直接复制 |
| 丢单风险 | guard 过宽，只拦截 `<0.3*SA` | V2 已识别问题，并用 `<0.7*SA` 作为疑似 dropper 过滤 |
| 泛化风险 | grid runner 支持多 cell，但当前模板较弱 | 有 d25/rc101 证据，缺少全量 guard-validated 泛化 |
| LLM 失控风险 | 已通过 bounded template 降低 | 原 EOH 候选大量污染，说明自由生成不可靠 |
| 运行时间 | 模板较快 | all-vehicle delta 比 top-k 慢，本地复跑 RES 约 6.5-6.8s，高于 SA 的 5.7s |

## 7. 建议结合方案

### 7.1 必须先改 guard

把 suspicious-low 阈值从 `0.3 * baseline` 收紧到 `0.7 * baseline`，至少覆盖：

- `eoh_go/operator/agent_controller.py::_apply_guard`
- `eoh_go/operator/failure_memory.py`
- `eoh_go/eoh_runner/candidate_guard.py`
- 相关 tests

原因：外部 V2 已证明 `<0.7*SA` 区间存在大量丢单污染。先不改 guard 就集成新策略，会继续把错误信号喂给 SmartOperator。

### 7.2 新增受控模板，而不是复制外部 Go 文件

建议新增一个模板族：

`global_delta`

参数：

- `pickup_weight`: 默认 `0.0` 或 `0.5`
- `fallback`: 保持现有 first-feasible/new-assign 逻辑

行为：

1. 对每个新订单扫描所有已有非空 assign。
2. 临时 `AddShip`。
3. `GenRoute()`。
4. 若成本有效，计算 `delta = newCost - oldCost`。
5. 可选加 `pickup_weight * cal_dis(current, origin)`。
6. 撤销插入并恢复 route。
7. 选择 score 最低车辆真实插入。
8. 若无可行车辆，再尝试新 assign 和保守兜底。

这能保留外部有效机制，同时保持本地 SmartOperator 的模板化边界。

### 7.3 Planner 接入规则

建议 `BoundedReactPlanner` 规则：

| 场景 | 策略 |
|---|---|
| active failure 含 timeout | `fast_nearest` |
| active failure 含 suspicious/negative | `robust_first_feasible` |
| `density == d25` 且 `arrival_scale >= 0.9` | `global_delta(pickup_weight=0.5)` |
| `density == d25` 且 `arrival_scale < 0.9` | `global_delta(pickup_weight=0.0)` 或 `fast_nearest` 做对照 |
| `density >= d45/d50` | 保持 `balanced_delta` 或 `robust_first_feasible` |

先不要把外部 `d25_t0p8` 的 Clarke-Wright/savings 版本接入。它没有 guard re-eval，而且代码更复杂，包含 slice/map/局部 helper，运行时和可控性风险更高。

### 7.4 验证路径

最小验证顺序：

1. 单元测试：模板渲染必须只输出一个 `func InsertShips`，包含 `RenewnTotalCost()`。
2. smoke test：`templates` 模式，`d25/rc101`，`generations=1`，`pop_size=4`。
3. 本地复跑：`rc101` × `d25` × `arrival_scale in [0.9, 1.0]`。
4. 泛化验证：扩到 `rc101-rc105`，再扩到 `d50/d75`。
5. 只保留 guard-valid 且不超时的策略。

## 8. 最终判断

外部改动有效，但有效性边界很窄：目前可靠证据集中在 `d25/rc101/t0.9-t1.0`，并且是在修正 dropper 认知后得到的 guard-validated 结果。

最合理的结合方式是：

1. 先收紧本地 guard。
2. 把外部 guard-validated best-fit delta 改写成本地 `strategy_templates.py` 的 `global_delta` 模板。
3. 让 SmartOperator 在 d25 低密度场景优先尝试该模板。
4. 用本地 grid 重新验证，不直接相信外部 EOH 原始 objective。

不建议直接合并外部 `.go` 文件，也不建议继续使用自由 LLM 变异作为主要候选来源。
