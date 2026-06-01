/goal: OBP RAG arm 稳定性修复 - 先做真 API-only，再跑 Residual-RAG

目标：在已经修好的 Online Bin Packing (OBP) / `ScoreBin` harness 上，继续推进 RAG 对照实验。当前重点不是扩大矩阵，而是先把 RAG arm 的候选生成稳定性修好：API 规则可以帮助模型写合法代码，但 failure warnings 和 strategy cards 不能继续挤占 `ScoreBin` 的生成预算。

报告一律写中文。实验产物不入 git，汇总报告和关键 best code 入 git。API key 不读取、不打印、不 echo；如需确认，只输出 `DEEPSEEK_API_KEY_PRESENT=true/false` 或同类布尔值。

---

## 当前状态

已完成并推送：

```text
当前代码/报告提交 = e6590e3 fix(obp): support ScoreBin Go extraction and record repair smoke
OBP harness 提交 = 59fe783 feat(obp): add online bin packing showcase harness
origin/main = e6590e3
```

工程状态：

| 项 | 状态 |
|---|---|
| OBP Go evaluator | 已接入 |
| `ScoreBin` target | 已注册 |
| Agent_EOH example | 已接入 |
| OBP literature cards | 已接入 |
| `obp_api_skeleton` | 已接入 |
| target-specific RAG filtering | 已生效 |
| non-InsertShips Go extraction | 已修复 |
| tests | `58 tests OK` |

本地未跟踪目录里有 raw 实验产物、`.DS_Store`、PPT/HTML 临时文件，默认不提交。

---

## 已验证事实

### 1. Go extraction 根因已修复

上一轮 OBP population 只有 seed + failed candidate 的根因不是 OBP evaluator，而是 `Agent_EOH` 的 Go 函数提取逻辑只识别 `func InsertShips(`。`ScoreBin` 被误当成 Python 输出解析，导致候选变成 `code=None`。

已修复：

```text
Agent_EOH/eoh/src/eoh/methods/eoh/eoh_evolution.py
Agent_EOH/eoh/src/eoh/examples/user_bin_packing_go/prompts_bin_packing_go.py
tests/test_eoh_runner_specs.py
```

验证结果：

```text
PYTHONPATH=. python3 -m unittest discover -s tests -q        -> 58 tests OK
python3 -m compileall -q eoh_go Agent_EOH/...                -> OK
go build -o /tmp/eoh_go_mainbin .                            -> OK
go build -o /tmp/eoh_go_obp_solver .../bin_packing_solver.go -> OK
go run .../bin_packing_solver.go .../obp_5x60_c100.json      -> final cost 0.05903030
```

### 2. Vanilla 已恢复稳定

修复后 vanilla OBP smoke：

```text
summary = eoh_go_workspace/reports/tables/eoh_obp_repair_20260601/vanilla/run_20260601_114904/eoh_obp_smoke_summary.json
population_size = 6
valid_candidates = 5
best_gap_to_lb = 0.05903
seed_objective = 0.0590303
best code = best-fit seed 等价实现
```

结论：EOH 对 `ScoreBin` 已能稳定生成/解析合法 Go 候选。

### 3. API+Warning-only 仍不稳定

修复后 API+Warning-only smoke：

```text
summary = eoh_go_workspace/reports/tables/eoh_obp_repair_20260601/api_warning/run_20260601_114956/eoh_obp_smoke_summary.json
population_size = 2
valid_candidates = 2
best_gap_to_lb = 0.05903
seed_objective = 0.0590303
rag_context_chars = 894
rag_context_truncated = false
rag_selected_items = []
best code = best-fit seed 等价实现
```

结论：RAG 链路没有截断，但当前所谓 API-only 不是“真 API-only”。它仍注入 failure warnings，可能对小函数目标造成额外约束噪声。Residual-RAG 被跳过是正确的，因为停损条件已经触发。

---

## 当前判断

工程质量：PASS。

实验结论：未验证 RAG 是否有效。

允许说：

```text
OBP 最小闭环和 ScoreBin Go extraction 已修复；vanilla 生成稳定性恢复。
RAG arm 仍不稳定，当前瓶颈从解析错误转移到 context 路由/注入策略。
```

不能说：

```text
Literature-RAG 对 OBP 无效。
```

原因：RAG arm 尚未形成可比较的 population。

---

## Phase A: 实现 true API-only / warning gate

目标：让 OBP 可以跑真正的 API-only arm，只注入 `api_constraint`，不注入 `failure_case`，也不检索 strategy card。

建议改动：

```text
eoh_go/eoh_runner/config.py
eoh_go/eoh_runner/runner.py
eoh_go/experiments/eoh_obp_smoke.py
tests/test_rag_runner_integration.py
tests/test_eoh_obp_smoke.py 或相邻测试文件
```

实现要求：

1. 在 `EOHConfig` 增加：

```python
rag_include_warnings: bool = True
```

2. 在 OBP smoke CLI 增加：

```text
--no-rag-warnings
```

传入：

```python
rag_include_warnings=False
```

3. 在 `_build_retrieved_rag_context()` 中拆分 global items：

```text
api_constraint: always injected
failure_case: injected only when config.rag_include_warnings is True
algorithm_card: strategy retrieval pool only
```

4. trace 语义要精确：

```text
rag_global_items_available
rag_global_items_injected
rag_selected_items
rag_context_chars
rag_context_truncated
```

如果为了兼容旧报告保留 `rag_global_items`，它必须表示实际注入项，不表示 available 项。

5. 测试必须覆盖：

```text
rag_include_warnings=True  -> failure_case 出现在 injected globals
rag_include_warnings=False -> failure_case 不出现在 injected globals
rag_top_k=0                -> rag_selected_items=[]
api_constraint             -> 仍然出现在 context 前部
```

禁止改动：

```text
Go solver 正常路径
OBP evaluator 语义
raw experiment output 入仓库
```

---

## Phase B: 本地验证 true API-only context

不跑真实 LLM 前，先用本地 trace 验证 context。

验收点：

```text
rag_selected_items = []
rag_global_items_injected 只含 obp_api_skeleton / api_constraint
context 不含 WARNINGS
context 不含 failure_case summary/content
context 不含 package main / func ScoreBin 外的 Go 源码
context chars <= 700
rag_context_truncated = false
```

必须运行：

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -q
python3 -m compileall -q eoh_go Agent_EOH/eoh/src/eoh/examples/user_bin_packing_go Agent_EOH/eoh/src/eoh/methods/eoh/eoh_evolution.py
go build -o /tmp/eoh_go_mainbin .
go build -o /tmp/eoh_go_obp_solver eoh_go_workspace/problems/bin_packing_online/bin_packing_solver.go
go run eoh_go_workspace/problems/bin_packing_online/bin_packing_solver.go eoh_go_workspace/problems/bin_packing_online/testdata/obp_5x60_c100.json
```

---

## Phase C: 修正后小实验

目标：只跑足够判断 RAG arm 是否恢复稳定的小实验，不扩大矩阵。

固定设置：

```text
problem = bin_packing_online
target = ScoreBin
model = JoyAI-LLM-Pro 或当前已授权公司 API 模型
generations = 1
pop_size = 8
dataset = obp_5x60_c100
```

运行规则：

```bash
set -a
source ~/.config/agent_go/chatrhino.env
set +a
caffeinate -i -m -s python3 -m eoh_go.experiments.eoh_obp_smoke ...
```

熄屏运行默认使用 `caffeinate -i -m -s`。后台运行时保留日志文件，避免频繁轮询。到模型/API 额度上限时允许暂停，额度恢复后从未完成 arm 继续，不重跑已完成且 summary 完整的 arm。

### Arm 1: true API-only

只跑这一组作为下一步 gate。

```text
--use-rag-context
--rag-mode literature
--rag-top-k 0
--rag-max-chars 700
--no-rag-warnings
```

停损条件：

```text
population_size < 5 或 valid_candidates < 3 -> 停止，不跑 Residual-RAG
```

通过条件：

```text
population_size >= 5
valid_candidates >= 3
rag_context_truncated = false
rag_selected_items = []
```

### Arm 2: Residual-RAG

仅当 Arm 1 通过才跑。

```text
--use-rag-context
--rag-mode literature
--rag-top-k 1
--rag-max-chars 1800
--no-rag-warnings
--rag-query "online bin packing ScoreBin residual polynomial utilization sqrt exp gap penalty tiny unusable residual gaps"
```

验收：

```text
rag_selected_items 包含 obp_funsearch_residual_poly 或 obp_eoh_util_sqrt_exp
rag_context_truncated = false
population_size >= 5
valid_candidates >= 3
```

### Arm 3: Vanilla repeat

默认不重跑。只有在 Phase A/B 改动影响非 RAG 路径或报告需要同一天同模型对照时才跑。

如果跑，参数：

```text
RAG off
generations=1
pop_size=8
同 dataset / model
```

---

## Phase D: 报告更新

更新中文报告：

```text
eoh_go_workspace/reports/eoh_obp_research_plan.md
eoh_go_workspace/reports/clv_harness_weekly_showcase.md
```

报告必须包含：

1. `e6590e3` 后的事实：Go extraction 已修复，vanilla stable。
2. API+Warning-only 为何仍不能比较：population 只有 2。
3. true API-only 的 trace：实际注入了什么，没注入什么。
4. Residual-RAG 的 selected card、context chars、是否截断。
5. 每组 metric：`population_size`、`valid_candidates`、`best_gap_to_lb`、`seed_objective`。
6. 每组 best code。不能只写策略变化，必须贴出具体 `func ScoreBin(...) []float64`。
7. 如果触发停损，明确写停损原因，不伪造对比结论。

结论用词：

| 情况 | 允许说法 |
|---|---|
| true API-only 仍不稳定 | “RAG arm 的 global context 注入仍影响候选生成，不能比较策略收益” |
| true API-only 稳定、Residual-RAG 不稳定 | “策略卡对 OBP 小函数仍有干扰，需要进一步压缩或指定更简单公式卡” |
| Residual-RAG 稳定但无提升 | “当前实例/卡片未显示收益，可换更难 instance 或官方 Python target” |
| Residual-RAG 稳定且 gap 更低 | “Literature-RAG 出现初步正信号，需要 repeats 验证稳定性” |

---

## Phase E: Git 和交付

完成实质进展后提交并推送。

提交范围：

```text
.codex/goals/weekly_showcase.md
相关 Python 源码
相关 tests
中文汇总报告
```

不提交：

```text
API key / env
raw 大型实验目录
.DS_Store
PPT/HTML 临时产物
```

最终响应必须包含：

```text
files changed
commands run
test results
experiment results
unresolved risks
merge recommendation
git commit hash
push status
```
