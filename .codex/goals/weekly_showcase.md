/goal: OBP raw-to-survivor 审计 + 修正后重启 LLM 实验

目标：解释 Online Bin Packing (OBP) / `ScoreBin` 在 true API-only arm 中 `final population=3` 的真实原因，并在补齐 raw-to-survivor 审计后重启最小 LLM 实验。核心顺序是：先确认 raw candidate 是否足够，再判断 final survivor 是否被 EOH 去重/选择压缩，最后才跑 Residual-RAG 验证策略卡是否有效。

报告一律写中文。实验产物不入 git，汇总报告和关键 best code 入 git。API key 不读取、不打印、不 echo；如需确认，只输出布尔值。

---

## 当前事实

已完成并推送：

```text
当前代码/报告提交 = ad88436 fix(obp): add true API-only warning gate
OBP harness 提交 = 59fe783 feat(obp): add online bin packing showcase harness
origin/main = ad88436
```

已验证：

| 项 | 结果 |
|---|---|
| non-InsertShips Go extraction | 已修复 |
| vanilla OBP | `population=6`, `valid=5`, `best_gap=0.05903` |
| true API-only OBP | `population=3`, `valid=3`, `best_gap=0.05903` |
| true API-only context | `598 chars`, `truncated=false` |
| true API-only injected globals | 仅 `obp_api_skeleton` |
| true API-only selected strategy | `[]` |
| Residual-RAG | 未跑，因 true API-only 未过旧 `population_size >= 5` gate |
| tests | `59 tests OK` |

当前不能说：

```text
Literature-RAG 对 OBP 无效。
```

只能说：

```text
OBP 工程链路 PASS；true API-only prompt 路由已干净；
但 final population 仍偏小，尚未形成可比较的 RAG population。
```

---

## 当前关键怀疑

true API-only 的 `population=3` 不一定代表 LLM 只生成了 3 个合法候选。现有代码和 artifacts 显示：

```text
Agent_EOH/eoh/src/eoh/methods/management/pop_greedy.py 按 objective 去重。
Agent_EOH/eoh/src/eoh/methods/eoh/eoh.py 只保存 survivor population。
当前 true API-only 目录没有 raw offspring / raw response 文件。
日志中多个 offspring objective 为 0.05903，final survivor 只剩 3 个 objective。
```

因此下一步必须补 raw-to-survivor 审计，区分：

1. LLM 是否生成了足够 raw responses。
2. raw response 是否能抽取 `func ScoreBin(...) []float64`。
3. raw code 是否能编译、评估、非 penalty。
4. raw valid candidates 是否因 code/objective 去重被压缩。
5. final survivor population 小是否真的表示生成不稳定。

---

## Phase A: 只读复核现有 true API-only artifact

不跑 LLM，不改代码。读取：

```text
eoh_go_workspace/reports/tables/eoh_obp_true_api_only_20260601/run_20260601_124045/
Agent_EOH/eoh/src/eoh/methods/eoh/eoh.py
Agent_EOH/eoh/src/eoh/methods/eoh/eoh_interface_EC.py
Agent_EOH/eoh/src/eoh/methods/management/pop_greedy.py
```

必须确认：

```text
survivor population size = 3
survivor objectives = 0.05903, 0.08945, 0.11879
raw offsprings 当前没有落盘
pop_greedy objective 去重确实存在
```

报告中禁止把 “final population 小” 直接写成 “候选生成失败”。

---

## Phase B: 增加 raw offspring audit logging

目标：不改变 evaluator 语义、不改变 EOH 选择逻辑，只增加可观察性。

修改范围优先限于：

```text
Agent_EOH/eoh/src/eoh/methods/eoh/eoh.py
eoh_go/experiments/eoh_obp_smoke.py
tests/test_eoh_runner_specs.py 或相邻测试
```

实现要求：

1. 每个 generation/operator 保存 raw offsprings：

```text
results/offsprings/pop_{generation}_{operator}.json
```

每条至少包含：

```text
operator
index
objective
has_code
code_hash
code
algorithm
other_inf
```

2. 每个 generation 保存 audit summary：

```text
results/offsprings/offspring_audit_generation_{generation}.json
```

字段至少包含：

```text
raw_offspring_count
raw_with_code_count
raw_penalty_count
raw_valid_candidate_count
unique_code_count
unique_objective_count
survivor_population_size
survivor_objectives
```

3. `eoh_obp_smoke.py` summary 增加：

```text
raw_offspring_count
raw_with_code_count
raw_valid_candidates
unique_code_count
unique_objective_count
final_population_size
survivor_objectives
survivor_drop_reason
offspring_audit_file
```

4. `survivor_drop_reason` 规则：

```text
raw_valid_candidates >= 5 且 final_population_size < 5 -> "objective_or_code_dedup"
raw_valid_candidates < 5 -> "raw_generation_or_evaluation_shortfall"
无 audit 文件 -> "missing_audit"
```

禁止：

```text
不改 pop_greedy 的选择语义
不改 OBP evaluator 目标
不把 raw 实验目录提交入 git
```

---

## Phase C: 本地验证

必须运行：

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -q
python3 -m compileall -q eoh_go Agent_EOH/eoh/src/eoh/examples/user_bin_packing_go Agent_EOH/eoh/src/eoh/methods/eoh/eoh_evolution.py Agent_EOH/eoh/src/eoh/methods/eoh/eoh.py
go build -o /tmp/eoh_go_mainbin .
go build -o /tmp/eoh_go_obp_solver eoh_go_workspace/problems/bin_packing_online/bin_packing_solver.go
go run eoh_go_workspace/problems/bin_packing_online/bin_packing_solver.go eoh_go_workspace/problems/bin_packing_online/testdata/obp_5x60_c100.json
```

OBP direct seed run 必须保持：

```text
final cost 0.05903030
```

---

## Phase D: 重启 gated LLM 实验

运行前规则：

```bash
set -a
source ~/.config/agent_go/chatrhino.env
set +a
caffeinate -i -m -s python3 -m eoh_go.experiments.eoh_obp_smoke ...
```

禁止打印 API key、key 前缀、Authorization header。

### Arm 1: true API-only rerun

先跑：

```text
--use-rag-context
--rag-mode literature
--rag-top-k 0
--rag-max-chars 700
--no-rag-warnings
--generations 1
--pop-size 8
```

进入 Residual-RAG 的 gate：

```text
raw_valid_candidates >= 5
rag_context_truncated = false
```

如果不满足，停止，不跑 Residual-RAG，并在报告中写明：

```text
true API-only raw valid 不足，不能比较 strategy card 收益。
```

如果满足但 final population 仍小于 5，允许继续跑 Residual-RAG，但报告必须说明：

```text
final population 小来自 survivor 去重，性能比较以 raw valid + best verified objective 辅助判断。
```

### Arm 2: Residual-RAG rerun

仅当 Arm 1 gate 通过才跑：

```text
--use-rag-context
--rag-mode literature
--rag-top-k 1
--rag-max-chars 1800
--no-rag-warnings
--rag-query "online bin packing ScoreBin residual polynomial utilization sqrt exp gap penalty tiny unusable residual gaps"
--generations 1
--pop-size 8
```

验收：

```text
rag_selected_items 包含 obp_funsearch_residual_poly 或 obp_eoh_util_sqrt_exp
rag_context_truncated = false
raw_valid_candidates >= 5
```

### Arm 3: Vanilla repeat

默认不重跑。只有当报告需要同日同模型对照，或代码改动影响非 RAG 路径时才跑。

---

## Phase E: 中文报告更新

更新：

```text
eoh_go_workspace/reports/eoh_obp_research_plan.md
eoh_go_workspace/reports/clv_harness_weekly_showcase.md
```

必须包含：

1. raw-to-survivor audit 字段表。
2. true API-only rerun 的 raw count、raw valid、unique objective、final survivor。
3. 是否触发 Residual-RAG，以及触发/停止原因。
4. 每个已跑 arm 的 best `func ScoreBin(...) []float64`。
5. 明确结论：
   - raw valid 不足：生成/评估稳定性问题。
   - raw valid 足够但 survivor 小：EOH 去重/选择压缩问题。
   - Residual-RAG 改善 best gap：初步正信号，需要 repeats。
   - Residual-RAG 无改善：当前 cards/instance 未显示收益。

---

## Phase F: 子 agent 审核

实现完成后 spawn 一个只读 `explorer` 审核。

审核点：

```text
goal 是否引用最新事实 ad88436 和 true API-only population=3/valid=3
代码是否只增加 audit，不改变 evaluator/selection 语义
summary 是否区分 raw generated、raw valid、unique objective、final survivors
Residual-RAG 是否只在 gate 通过后运行
报告是否包含具体 best code
是否没有把 final population 小误写成 RAG 无效
```

P0/P1 必须修完后再提交。

---

## Phase G: Git 和交付

提交范围：

```text
.codex/goals/weekly_showcase.md
Agent_EOH/eoh/src/eoh/methods/eoh/eoh.py
eoh_go/experiments/eoh_obp_smoke.py
tests
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
subagent review verdict
unresolved risks
merge recommendation
git commit hash
push status
```
