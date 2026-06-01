/goal: 五小时额度内推进 C+L+V Harness —— 修 C 层 target 绑定并跑 proper 实验

目标：在本次 Codex 五小时额度内持续推进，优先修复 C 层跨 target 绑定，再完成 Knapsack proper smoke；如果 Knapsack 跑通，再启动导师给的搅拌车项目 `SplitOrders` 代码进化迁移。

导师建议评估：先跑通 Knapsack，再迁移搅拌车 `SplitOrders` 是可行路线。原因是 Knapsack 已经具备最小 evaluator 和 prompt，可作为跨问题迁移的第一块验收；搅拌车来自真实项目材料，更适合紧随其后展示“导师问题也能被同一 harness 抽象为 target function + evaluator”。本轮不追求多重复性能结论，只要求每个 target 能完成 build、guarded evaluation、RAG/API context trace 和 smoke 记录。

执行策略：不要继续堆 InsertShips repeats。InsertShips 密度分化结论当前已经足够作为正式证据；本轮重点是让 Knapsack 的 RAG/API context 真正生效，再用最小可控方式把导师提供的搅拌车沙盘问题抽象成新 target。Optimization 保留为同一 VRP solver 内 target 迁移证据，不再作为本轮主线。

成功标准：

1. Knapsack API-only 的 RAG context 生效：`rag_global_items` 包含 `knapsack_api_skeleton`，`rag_context_chars > 0`。
2. Optimization API-only 的 RAG context 继续生效：`rag_global_items` 包含 `optimization_api_skeleton`，`rag_context_chars > 0`。
3. InsertShips 现有 RAG 行为不退化。
4. Knapsack 至少跑一组 baseline vs API-only proper smoke。
5. 完成 `mixer_split` / `SplitOrders` 的最小 evaluator + target spec + smoke，或给出明确 blocker。
6. 更新中文报告，明确区分 formal / exploratory / smoke evidence。

报告一律写中文。实验产物不入 git。API key 不读取、不打印、不 echo。

---

## 当前状态快照

截至 2026-05-31：

| 项目 | 状态 | 判断 |
|---|---|---|
| InsertShips d50 API-only | 3-rep stable，median delta_J 约 -95 | 正式证据，d50 优先 API-only |
| InsertShips d50 History | 3-rep，1 better / 2 worse | 正式证据，弱于 API-only |
| InsertShips d75 History | 3-rep，median delta_J 约 -134 | 正式证据，d75 优先 History-RAG |
| InsertShips d75 API-only | 5-rep，median delta_J = 0 | 正式证据，inconclusive |
| Optimization pipeline | gen=1 / gen=8 均跑通过 | smoke / exploratory，未超过 seed |
| Knapsack pipeline | gen=1 跑通过 | smoke，未超过 seed |
| Mixer / SplitOrders | 论文与沙盘代码已在 `problems/` 下 | 适合作为下一跨问题迁移目标 |
| C 层 corpus | 24 items | 已有 3 个 API skeleton，但 code_examples 仍全是 InsertShips |
| Optimization API context | 当前本地 trace 可生效 | `optimization_api_skeleton` 可进入 global |
| Knapsack API context | 当前存在过滤 bug | `SelectItems` target tag 匹配不到 `knapsack_api_skeleton` |

已知根因：

- 旧报告中“C 层 22 个 item 全部是 InsertShips”的说法已经过时。
- 当前 `build_corpus.py` 已生成 `insertships_api_skeleton`、`optimization_api_skeleton`、`knapsack_api_skeleton`。
- 当前 `runner.py` 用 `config.target_function.lower()` 做 target tag，`SelectItems` 会变成 `selectitems`，但 Knapsack corpus tag 是 `knapsack`，因此 Knapsack API skeleton 被过滤掉。
- history mode 的 code_example 目前仍全是 InsertShips；Optimization / Knapsack 暂时不要声称 history-RAG 已经适配。
- `eoh_go_workspace/problems/项目论文.zip` 和 `blender_project.zip` 来自导师材料。它们适合抽取搅拌车问题，但不能整包直接接入；应先抽 `run_module_1` 的订单切分/车辆需求逻辑，形成干净的 `SplitOrders` evaluator。

---

## 全局执行规则

- 这是一个“直接用完 Codex 五小时额度”的 goal。执行时不要停在计划阶段；按 Phase 顺序持续推进，直到额度耗尽、遇到真实 blocker、或全部完成。
- 遇到 Codex 五小时额度将耗尽时：停止启动新实验，记录当前断点、已完成 run、未完成 run、下一条命令。
- 遇到模型 API rate limit / quota limit：记录断点，等待或退出，不重启已完成 run。
- 只保留一个主要 EOH 实验进程，避免 generated workspace 冲突。
- 长时间实验默认使用：
  ```bash
  caffeinate -i -m -s <command>
  ```
- 后台实验默认使用：
  ```bash
  caffeinate -i -m -s <command> > <log_path> 2>&1 &
  ```
- 加载 API 配置只用：
  ```bash
  set -a
  source ~/.config/agent_go/chatrhino.env
  set +a
  ```
- 禁止输出 API key、key 前缀、Authorization header。
- generated Go code 只通过 guarded evaluator 路径执行。
- 每轮结果记录：`best_EOH_J`、`seed_J`、`valid_candidates`、`best_build_ok`、`best_status`、`rag_trace`、`rag_context_chars`、`rag_global_items`。
- 只用最终 guarded evaluator 的 `best_EOH_J` 做性能结论；不要用 population objective 做最终性能。
- 所有报告写中文。

---

## Phase 0: 开始前检查（P0，10 分钟）

目标：确认不会把旧实验进程和新实验混在一起。

执行：

1. 查看是否有 EOH / python 实验进程：
   ```bash
   pgrep -af "eoh_arrival_grid|knapsack_smoke|EVOL|mainbin" || true
   ```
2. 如果存在非本轮目标进程，先向用户确认是否关闭；不要擅自 kill 不明进程。
3. 读取当前目标文件和报告：
   ```bash
   sed -n '1,220p' .codex/goals/weekly_showcase.md
   sed -n '1,260p' eoh_go_workspace/reports/clv_harness_weekly_showcase.md
   ```
4. 不读取、不打印任何 API key。

验收：

- 明确当前是否有后台实验。
- 若有，记录 PID 和命令。
- 若无，进入 Phase 1。

---

## Phase 1: 修复 C 层 target 绑定（P0，预计 40-60 分钟）

目标：让 target-specific API context 按 target 正确进入 RAG global 区，尤其修复 Knapsack。

### 1.1 设计 target alias

在 `eoh_go/eoh_runner/runner.py` 或更合适的 registry/helper 中增加 target 到 corpus tag 的映射：

```python
TARGET_RAG_TAGS = {
    "InsertShips": {"insertships"},
    "Optimization": {"optimization"},
    "SelectItems": {"knapsack", "selectitems"},
}
```

过滤 global items 时：

- 保留 tag 中包含 `"all"` 的 failure_case。
- 保留 tag 与当前 target aliases 有交集的 api_constraint / failure_case。
- 不再只用 `target_function.lower()`。

### 1.2 检查 corpus 内容

确认以下条目存在：

- `insertships_api_skeleton`
- `optimization_api_skeleton`
- `knapsack_api_skeleton`

如果缺失，只修复 `build_api_constraints()` 和对应 JSONL，不做大规模重构。

### 1.3 测试要求

扩展或新增测试，至少覆盖：

- `InsertShips` API-only：global 包含 `insertships_api_skeleton`。
- `Optimization` API-only：global 包含 `optimization_api_skeleton`。
- `SelectItems` API-only：global 包含 `knapsack_api_skeleton`。
- `SelectItems` 的 global 不应因为 `target_function.lower()=="selectitems"` 而漏掉 knapsack skeleton。
- failure_case 的 `"all"` tags 对所有 target 生效。

建议文件：

- `tests/test_rag_runner_integration.py`
- 如已有 target spec 测试，也可放入 `tests/test_eoh_runner_specs.py`

### 1.4 本地 trace 验收（不调用 LLM）

运行：

```bash
PYTHONPATH=. python3 - <<'PY'
from eoh_go.eoh_runner.config import EOHConfig
from eoh_go.eoh_runner.runner import _build_retrieved_rag_context

cases = [
    ("InsertShips", "vrp_insertships", "insertships_api_skeleton"),
    ("Optimization", "vrp_insertships", "optimization_api_skeleton"),
    ("SelectItems", "knapsack", "knapsack_api_skeleton"),
]

for target, problem, expected in cases:
    cfg = EOHConfig(
        agent_eoh_root="Agent_EOH",
        problem_name=problem,
        target_function=target,
        use_rag_context=True,
        rag_mode="literature",
        rag_top_k=0,
        rag_max_chars=1000,
        dataset_density="d50",
        arrival_scale=1.0,
    )
    ctx, trace = _build_retrieved_rag_context(cfg, ".")
    ids = [item["id"] for item in trace["rag_global_items"]]
    print(target, len(ctx), ids)
    assert expected in ids, (target, expected, ids)
    assert len(ctx) > 0, target

print("TARGET_CONTEXT_TRACE_OK")
PY
```

通过后再进入 Phase 2。

### 1.5 常规验证

运行：

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -q
python3 -m compileall -q eoh_go Agent_EOH/eoh/src/eoh/examples/user_insertships_go Agent_EOH/eoh/src/eoh/examples/user_knapsack_go
go build -o /tmp/eoh_go_mainbin .
```

验收：

- 全部测试通过。
- compileall 通过。
- Go build 通过。
- `TARGET_CONTEXT_TRACE_OK` 通过。

---

## Phase 2: Optimization proper smoke（P1，预计 60-90 分钟）

前提：Phase 1 通过。

目标：在 Optimization target 上跑 baseline vs API-only，确认 context 生效后是否仍然只返回 seed。若时间紧，Optimization 可降级为只做本地 trace，不阻塞 Knapsack 和 Mixer。

实验设置：

| Cell | Mode | 参数 | gen/pop | repeats |
|---|---|---|---:|---:|
| rc101 d50 | baseline | no RAG | 1/8 | 1 |
| rc101 d50 | API-only | `rag_mode=literature top_k=0 max_chars=1000` | 1/8 | 1 |
| rc101 d75 | baseline | no RAG | 1/8 | 1 |
| rc101 d75 | API-only | `rag_mode=literature top_k=0 max_chars=1000` | 1/8 | 1 |

输出目录：

```text
eoh_go_workspace/reports/tables/weekly_optimization_proper/
```

示例命令，执行时按 cell/mode 改 output-dir：

```bash
set -a
source ~/.config/agent_go/chatrhino.env
set +a

caffeinate -i -m -s python3 -m eoh_go.experiments.eoh_arrival_grid \
  --root . \
  --target Optimization \
  --problem-name vrp_insertships \
  --problem rc101.json \
  --density d50 \
  --arrival-scale 1.0 \
  --generations 1 \
  --pop-size 8 \
  --llm-model JoyAI-LLM-Pro \
  --use-density-source-dirs \
  --source-dir solomon_benchmark \
  --output-dir eoh_go_workspace/reports/tables/weekly_optimization_proper/d50_baseline
```

API-only 增加：

```bash
  --use-rag-context \
  --rag-mode literature \
  --rag-top-k 0 \
  --rag-max-chars 1000
```

验收：

- baseline / API-only 均至少 1 个 valid candidate。
- API-only 的 result row 中 `rag_context_chars > 0`。
- API-only 的 `rag_global_items` 包含 `optimization_api_skeleton`。
- 是否超过 seed 只作为结果记录，不作为阻塞条件。

---

## Phase 3: Knapsack proper smoke（P0，预计 45-75 分钟）

前提：Phase 1 通过。

目标：确认 Knapsack 的 API-only context 真正生效，并用一个实例跑 baseline vs API-only。

实验设置：

| Instance | Mode | gen/pop | repeats |
|---|---|---:|---:|
| testdata_01 | baseline | 1/8 | 1 |
| testdata_01 | API-only | 1/8 | 1 |

输出目录：

```text
eoh_go_workspace/reports/tables/weekly_knapsack_proper/
```

命令模板：

```bash
set -a
source ~/.config/agent_go/chatrhino.env
set +a

caffeinate -i -m -s python3 -m eoh_go.experiments.knapsack_smoke \
  --generations 1 \
  --pop-size 8 \
  --llm-model JoyAI-LLM-Pro \
  --output-dir eoh_go_workspace/reports/tables/weekly_knapsack_proper/baseline
```

API-only run 如果 `knapsack_smoke.py` 已支持 RAG 参数，就显式传：

```bash
  --use-rag-context \
  --rag-mode literature \
  --rag-top-k 0 \
  --rag-max-chars 1000
```

如果 `knapsack_smoke.py` 暂不支持这些参数，本阶段先加最小 CLI 支持，复用 `EOHConfig` 中已有字段，不要写独立 RAG 注入逻辑。

验收：

- baseline / API-only 均至少 1 个 valid candidate。
- API-only 的 trace 或 summary 能证明 `knapsack_api_skeleton` 已注入。
- 是否超过 seed 只作为结果记录，不作为阻塞条件。

---

## Phase 4: 搅拌车 SplitOrders 迁移设计与最小实现（P0，预计 90-150 分钟）

前提：Phase 1 通过，且 Knapsack proper smoke 至少完成 baseline 或 API-only 一侧。

目标：把导师给的搅拌车项目抽象成一个新的跨问题 target：`SplitOrders`。先跑通，不追求性能提升。

### 4.1 迁移范围

只迁移 `blender_project/dry_running.py` 中 `run_module_1` 的核心逻辑：

- 输入：单日订单、车辆池、工作时长。
- 输出：子订单列表、需要新增车辆。
- 目标：尽量完成订单切分，减少未覆盖方量和新增车辆。

不迁移：

- `run_module_2` 成本统计。
- `run_module_3` 排队/车辆合并。
- Plotly 图表。
- 月度报告生成。
- 原 zip 内 `.git`、图片、doc、notebook。

### 4.2 建议工程结构

新增：

```text
eoh_go_workspace/problems/mixer_split/
  mixer_split_solver.go
  testdata/testdata_01.json
```

新增 Agent_EOH example：

```text
Agent_EOH/eoh/src/eoh/examples/user_mixer_split_go/
  prompts_mixer_split_go.py
  prob_mixer_split_go.py
  seeds_mixer_split_go.json
```

新增 runner（如复用通用 runner 成本过高）：

```text
eoh_go/experiments/mixer_split_smoke.py
```

### 4.3 目标函数签名

Go target：

```go
func SplitOrders(orders []Order, vehicles []Vehicle, workHours float64) []SubOrder
```

数据结构建议：

```go
type Order struct {
    ID string `json:"id"`
    Volume float64 `json:"volume"`
    GoDistance float64 `json:"go_distance"`
    BackDistance float64 `json:"back_distance"`
    MixTime float64 `json:"mix_time"`
    UnloadTime float64 `json:"unload_time"`
}

type Vehicle struct {
    Capacity float64 `json:"capacity"`
    Count int `json:"count"`
}

type SubOrder struct {
    OrderID string `json:"order_id"`
    Volume float64 `json:"volume"`
    VehicleCapacity float64 `json:"vehicle_capacity"`
}
```

### 4.4 Guard / evaluator

必须检查：

- 每个 `SubOrder.Volume > 0`。
- 每个 `SubOrder.Volume <= SubOrder.VehicleCapacity`。
- 每个 `SubOrder.OrderID` 必须来自输入订单。
- 对每个原订单，子订单总方量与原方量一致，允许 `1e-6` 浮点误差。
- 不允许漏订单。
- 不允许重复创造额外方量。
- 不允许返回空方案，除非输入订单为空。

Objective（越小越好）：

```text
final_cost =
  1000000000 if guard fail
  uncovered_volume * 1000000
  + extra_vehicle_units * 10000
  + suborder_count * 10
  + approximate_workload_imbalance
```

第一版可以不实现复杂车辆时序，只做容量切分和额外车辆估计。报告中明确写 smoke evidence。

### 4.5 C 层 context

新增 API skeleton：

- `mixer_split_api_skeleton`
- tags: `["mixer", "splitorders", "api", "safety"]`

内容用 skill card 格式：

```text
API: mixer_split_skeleton
Rules:
- Return []SubOrder.
- Preserve each original order volume exactly.
- Every suborder volume must be <= chosen vehicle capacity.
- Use fallback splitting by largest available vehicle.
- Never invent unknown order IDs.
```

同时给 `SplitOrders` 增加 target alias：

```python
"SplitOrders": {"mixer", "splitorders"}
```

### 4.6 Smoke 实验

只跑一组：

| Problem | Target | Mode | gen/pop |
|---|---|---|---:|
| mixer_split | SplitOrders | baseline | 1/4 |
| mixer_split | SplitOrders | API-only | 1/4 |

输出：

```text
eoh_go_workspace/reports/tables/weekly_mixer_split_smoke/
```

验收：

- baseline 或 API-only 至少一侧能生成可编译 Go。
- 至少一侧 valid_candidates >= 1。
- API-only trace 包含 `mixer_split_api_skeleton`。
- 报告只声称“搅拌车 SplitOrders 代码进化链路跑通”，不声称性能优越。

---

## Phase 5: 额度仍充足时的加跑优先级（P1）

如果 Phase 1-4 完成后 Codex 五小时额度仍充足，按以下顺序继续：

1. Knapsack API-only 再跑 1 个 repeat。
2. Mixer SplitOrders API-only 再跑 1 个 repeat。
3. Optimization d50 API-only 再跑 1 个 repeat。
4. 若 Mixer SplitOrders smoke 不稳定，优先修 evaluator / prompt，不扩展实验矩阵。
5. 不新增 RoutingTS，不新增 CVRP，不迁移完整 blender_project，除非上述都完成。

停止条件：

- 剩余时间不足以完成一个完整 run。
- 连续 2 个 run 因 API quota/rate limit 阻塞。
- 连续 2 个 run `valid_candidates=0`，先分析失败样本，不继续烧额度。

---

## Phase 6: 更新中文周展示报告（P0，预计 30-45 分钟）

更新：

```text
eoh_go_workspace/reports/clv_harness_weekly_showcase.md
```

必须修正旧说法：

- 不再写“C 层 22 个 corpus item 全部是 InsertShips”。
- 改成：
  - API skeleton 已经扩展到 InsertShips / Optimization / Knapsack。
  - history code_examples 仍主要绑定 InsertShips。
  - 本轮修复了 `SelectItems -> knapsack` 的 target alias 过滤问题。

报告新增：

1. C 层适配前后对比表：

| Target | 修复前 context | 修复后 context | 状态 |
|---|---|---|---|
| InsertShips | insertships API + warnings | same | 不退化 |
| Optimization | optimization API 已可注入 | verified | proper smoke |
| SelectItems | 漏掉 knapsack API | knapsack API 注入 | proper smoke |

2. Optimization proper smoke 结果表。
3. Knapsack proper smoke 结果表。
4. Mixer SplitOrders smoke 结果表。
5. 明确写：是否超过 seed 不是本阶段唯一成功标准；本阶段主要验证 context target binding 和 pipeline portability。
6. 若所有新 target 仍未超过 seed，结论写：

> 当前结果说明 C+L+V harness 已能跨 target / problem 注入目标专属 context，但 Optimization 和 Knapsack 的性能改进仍未稳定出现。下一步需要 target-specific code examples 或更强 seed，而不是继续用 InsertShips history corpus 迁移。

---

## 最终自检

完成前运行：

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -q
python3 -m compileall -q eoh_go Agent_EOH/eoh/src/eoh/examples/user_insertships_go Agent_EOH/eoh/src/eoh/examples/user_knapsack_go
go build -o /tmp/eoh_go_mainbin .
```

检查：

- [ ] `SelectItems` API-only trace 包含 `knapsack_api_skeleton`。
- [ ] `Optimization` API-only trace 包含 `optimization_api_skeleton`。
- [ ] `InsertShips` trace 不退化。
- [ ] proper smoke 输出目录存在。
- [ ] Mixer SplitOrders 若执行，则 evaluator guard 通过且报告标注 smoke evidence。
- [ ] 报告为中文。
- [ ] 报告没有 API key 或 key 前缀。
- [ ] 报告区分 formal / exploratory / smoke。
- [ ] 实验产物不提交 git。

最终回复必须包含：

- files changed
- commands run
- test results
- proper smoke results
- remaining limitations
- next resume point
