# 从 InsertShips 到当前 agent_go 代码框架的演化总结

日期：2026-06-04  
范围：`agent_go` 当前本地代码、`InsertShips` 代码演化记录、C+L+V harness、RAG corpus、official EoH TSP Literature-RAG 实验记录。  
说明：仓库中未找到字面文件 `intership.go`；本报告按项目实际目标 `InsertShips()` 及 `*_insertships.go` 候选源码理解。

## 1. 一句话结论

项目已经从“只让 LLM 改一个 Go 函数 `InsertShips()`”演化为一套可迁移的 C+L+V harness：用 `TargetSpec` 定义可进化函数边界，用 `ProblemSpec` 定义问题和 evaluator，用 RAG skill cards 注入文献策略，并已对齐官方 EoH 的 `bp_online`、`tsp_construct`、`cvrp_construct` 入口。当前最强证据来自官方 TSP：targeted Literature-RAG 选中 regret + farthest cards 后，best objective 从 pure EOH 的 6.839 降到 6.287。

## 2. 阶段一：InsertShips 单目标进化

最早的工程目标是动态 VRP 中的：

```go
func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch
```

这个函数决定新增订单应该插入哪辆车、以什么顺序插入，以及失败时是否新开 Assign。它天然适合 LLM 进化，因为有清晰的试插、回滚、提交模式：

```go
AddShip -> GenRoute -> RemoveShip -> GenRoute -> Commit -> RenewnTotalCost
```

已有 `gen=8 baseline` 记录显示，代码形态不是随机变化，而是逐步从简单可行逻辑变成更稳健的插入算子。

| 阶段 | 代表策略 | 代码结构变化 | verified evidence |
|---|---|---|---|
| 早期 | first feasible insertion | 找到第一辆可行车就插入并 break | rc101 d50 seed_J=713.52, best_EOH_J=274.90 |
| 中期 | trial all Assigns + rollback | 遍历所有 Assigns，记录 cost delta，试插后撤销 | d50 Gen 3/4 出现 |
| 后期 | best-delta + fallback | 选择最小增量 Assign，失败时新开 Assign，最后 RenewnTotalCost | d50 Gen 8 稳定 |
| 高密度 | weighted best-delta | 加入 slack / penalty / weighted score | rc101 d75 seed_J=549.48, best_EOH_J=393.30 |

### 2.1 Gen 1：first feasible insertion

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

### 2.2 Gen 4：trial all Assigns + rollback

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
```

### 2.3 Gen 8：best-delta commit + fallback

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

## 3. 阶段二：从单函数到 C+L+V harness

单独演化 `InsertShips()` 的问题是展示面太窄。当前代码通过三层抽象把目标函数、问题 evaluator、上下文注入解耦：

| 层 | 关键文件 | 作用 |
|---|---|---|
| C: Code target | `eoh_go/eoh_runner/target_spec.py` | 定义函数名、签名、抽取/替换正则、guard checks |
| L: Literature / context | `eoh_go/rag/build_corpus.py`, `retriever.py`, `prompt_context.py` | 构建 skill cards，检索策略卡，生成两段式 prompt context |
| V: Verification | `eoh_go/eoh_runner/problem_spec.py`, `candidate_guard.py`, experiments | 编译、运行 evaluator、汇总 objective / valid rate |

当前已注册或接入的目标包括：

| Target | Problem | 当前状态 | 作用 |
|---|---|---|---|
| `InsertShips` | dynamic VRP | 已验证性能提升 | 原始主线 |
| `Optimization` | VRP route/order improvement | smoke 跑通 | 同一 Go 求解器内迁移 |
| `SelectItems` | 0/1 knapsack | smoke 跑通 | 跨问题 Go evaluator |
| `SplitOrders` | mixer/concrete truck | smoke 跑通 | 导师给的新问题 |
| `ScoreBin` | online bin packing | harness 跑通 | 对齐 EoH 原论文示例 |
| `select_next_node` | official TSP construct | targeted RAG 有正向证据 | 当前最强 showcase |

## 4. 阶段三：RAG 从“长参考文档”改成“短 skill cards”

RAG 的关键修正不是简单压缩，而是分类修正：

| kind | 当前语义 | 注入方式 |
|---|---|---|
| `api_constraint` | API 安全调用规则 | 固定前置，不参与 top-k 竞争 |
| `algorithm_card` | 策略选择 skill card | 进入检索池，按 query 选 top-k |
| `failure_case` | guard / timeout / suspicious warning | 只输出短 warning，不输出源码 |
| `code_example` | 历史生成代码 | history/mixed 模式使用 |

典型 skill card 不再写论文背景，而是写可执行指令：

```text
Skill: regret2_select
When: multiple orders compete for limited route capacity.
Do: compute best and second-best insertion cost_delta across Assigns.
Fallback: if only one feasible position exists, insert immediately.
Safety: GenRoute after every trial AddShip/RemoveShip pair.
```

这解决了早期两个问题：第一，`sa_seed_1` 这类 API skeleton 不再和策略卡竞争；第二，`main.go` 或 guard 源码不会被塞进 prompt。

## 5. 阶段四：对齐官方 EoH benchmark

当前新增 `eoh_go/experiments/official_eoh_run.py`，将本项目 RAG harness 接到 `/private/tmp/EoH-main` 官方 EoH runtime：

```text
Corpus JSONL -> retrieve cards -> prompt_context -> official_eoh_run.py
-> official EoH subprocess -> population JSON -> samples_best.json -> local notes/report
```

官方问题配置在 `OFFICIAL_RAG_PROBLEM_CONFIG` 中维护：

| official problem | API card | strategy prefixes | 默认 query |
|---|---|---|---|
| `bp_online` | `obp_api_skeleton` | `obp_` | bin packing / residual capacity / harmonic |
| `tsp_construct` | `tsp_construct_api_skeleton` | `tsp_` | nearest / insertion / regret / route length |
| `cvrp_construct` | `cvrp_construct_api_skeleton` | `cvrp_` | capacity / demand / distance / depot |

## 6. 当前最强实验：official TSP targeted Literature-RAG

TSP 的核心变量不是“是否加 RAG”，而是“检索到什么策略卡”。默认 query 选中 nearest 族，和模型自发策略重合；targeted query 选中 regret + farthest 后才产生增量。

| arm | best objective | vs pure EOH | valid | selected cards |
|---|---:|---:|---:|---|
| pure EOH | 6.83907 | 0.00000 | 4/4 | - |
| API-only | 6.78953 | -0.04954 | 4/4 | - |
| default Literature-RAG | 6.83954 | +0.00047 | 4/4 | nearest_insertion, nearest_neighbor |
| targeted Literature-RAG init | 6.51118 | -0.32789 | 4/4 | regret_insertion, farthest_insertion |
| targeted gen=4 pop=8 | 6.28736 | -0.55171 | 8/8 | regret_insertion, farthest_insertion |

repeat=3 结果也支持稳定性：

| repeat | best | vs pure |
|---|---:|---:|
| 1 | 6.30547 | -0.53360 |
| 2 | 6.50049 | -0.33858 |
| 3 | 6.73293 | -0.10614 |
| median | 6.500 | - |

## 7. TSP 进化出的代表代码

### 7.1 Pure EOH baseline: progress-distance score

```python
progress = distance_matrix[current_node][destination_node] - (
    distance_matrix[current_node][unvisited_nodes]
    + distance_matrix[unvisited_nodes][:, destination_node]
)
combined_score = alpha * norm_dist - (1 - alpha) * norm_prog
return unvisited_nodes[np.argmin(combined_score)]
```

### 7.2 Targeted RAG init: regret + farthest representative

```python
farthest_rep = unvisited_nodes[np.argmax(distance_matrix[current_node][unvisited_nodes])]
conn_costs = [distance_matrix[u][ep] for ep in [current_node, farthest_rep, destination_node]]
regret = second_min(conn_costs) - min(conn_costs)
score = norm_regret + norm_cluster + (1 - norm_current_dist)
return unvisited_nodes[np.argmax(score)]
```

### 7.3 Gen=4 best: isolation + regret score

```python
iso_factor = mean(distance_matrix[cand][others])
two_hop_min = min(distance_matrix[current_node][k] + distance_matrix[k][cand])
regret_val = max(0.0, two_hop_min - distance_matrix[current_node][cand])
score = (0.4 * iso_factor + 0.6 * regret_val) / (d_current + 1e-9)
return unvisited_nodes[np.argmax(score)]
```

这段代码体现了 RAG 对生成方向的影响：从纯 nearest/progress，转为显式考虑“现在不访问会不会后悔”和“该点是否孤立”。

## 8. 当前代码结构总结

| 模块 | 代表文件 | 当前职责 |
|---|---|---|
| 原始 Go 求解器 | `main.go`, `routing.go` | VRP simulator 与可替换函数目标 |
| EOH 控制面 | `eoh_go/eoh_runner/*.py` | config、target/problem registry、guard、RAG env 注入 |
| RAG 子系统 | `eoh_go/rag/*.py` | corpus schema、构建、检索、prompt context |
| 实验入口 | `eoh_go/experiments/*.py` | grid、smoke、official EoH run、summarizer |
| 多问题样例 | `eoh_go_workspace/problems/*` | knapsack、mixer_split、bin_packing_online |
| 证据产物 | `eoh_go_workspace/local_notes`, `local_runs`, `reports` | 本地实验记录、summary JSON、best code |
| 测试 | `tests/*.py` | RAG、官方 runner、smoke、guard 回归测试 |

## 9. 剩余风险

1. OBP、CVRP 目前还不是 RAG 正向证据。OBP 的有效生成率和 card selection 仍需修，CVRP 的 capacity cards 可能过强。
2. 多问题迁移目前有 smoke evidence，但未全部形成稳定性能提升矩阵。
3. `local_runs` 与实验产物体积增长快，需要继续保持“不入仓库”的边界。
4. 如果用于论文，需要补开源模型实验，避免只依赖公司 API。

## 10. 建议下一步

1. 固化 TSP targeted RAG 结果：保留 gen=4,pop=8 作为展示主线，补 1-2 个 repeat 即可。
2. 修 OBP：先保证 population 接近 pop_size，再做 top-k card 指定对比。
3. 修 CVRP card：减少 capacity-only 倾向，引入 savings/regret/farthest 组合。
4. 对外汇报时，将“框架迁移能力”和“RAG 有效性证据”分开讲：迁移能力看多 target smoke，有效性证据先看 TSP targeted RAG。
