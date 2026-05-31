/goal: C+L+V Harness 每周展示 —— InsertShips 稳定性 + C 层跨 target 适配

目标：InsertShips 密度分化结论已稳固。下一步修复 C 层 target 绑定问题，让 Optimization/Knapsack 的 RAG 能真正工作。

当前最重要发现：Optimization 和 Knapsack 的 "no improvement" 不是因为 LLM 能力不足，而是因为 **C 层 22 个 corpus item 全部是 InsertShips 的**——`retrieve()` 对 Optimization/Knapsack 返回空集，`ctx_chars=MISSING`。

下一阶段不继续堆 InsertShips repeats，也不继续无 context 跑 Optimization/Knapsack。而是先修 C 层，再跑实验。

报告一律写中文。实验产物不入 git。API key 不读取、不打印、不 echo。

---

## 当前状态

截至 2026-05-31 16:00：

| 项目 | 状态 | 备注 |
|------|:--:|------|
| InsertShips d50 API-only | 3-rep stable (median ΔJ=-95) | 正式证据 |
| InsertShips d50 History | 3-rep (1/2 worse) | 正式证据，API 胜 |
| InsertShips d75 History | 3-rep (median ΔJ=-134) | 正式证据 |
| InsertShips d75 API-only | 5-rep (median ΔJ=0) | 正式证据，inconclusive |
| Optimization pipeline | gen=1+8 跑通 | 但 ctx_chars=MISSING——C 层无 context |
| Knapsack pipeline | gen=1 跑通 | 但 ctx_chars=MISSING——C 层无 context |
| C 层 corpus | 22 items, 全部 InsertShips | **root cause** |
| Target registry | 3 targets 已注册 | 有 rag_api_context 但未接入 corpus |

---

## 全局规则

- 长时间实验默认使用 `caffeinate -i -m -s <command>`
- 加载 API 配置：`set -a; source ~/.config/agent_go/chatrhino.env; set +a`
- 禁止输出 API key
- generated Go code 只通过 guarded evaluator 路径执行
- 每轮结果记录：`best_EOH_J`、`seed_J`、`valid_candidates`、`best_build_ok`、`rag_trace`、`ctx_chars`
- 只用 `best_EOH_J` 做性能结论
- 所有报告写中文

---

## Phase 1: 修复 C 层 target 绑定（P0）

目标：让 Optimization/Knapsack 的 RAG 检索到属于它们的 context。

**1.1 为每个 target 创建专属 API constraint**

利用 registry 中已有的 `rag_api_context`，生成独立的 API constraint corpus item：
- `optimization_api_skeleton`：`"Use dispatch.Assigns[].RemoveShip/AddShip/GenRoute and dispatch.RenewnTotalCost. ..."`
- `knapsack_api_skeleton`：`"func SelectItems(items []Item, capacity int) []bool. Return len(items) booleans. ..."`

**1.2 为每个 target 创建专属 failure case**

- Optimization：`optimization_ship_duplicate`、`optimization_cost_negative`
- Knapsack：`knapsack_capacity_exceeded`

**1.3 按 target 过滤 corpus**

修改 `filter_corpus_by_mode` 或新增 `filter_corpus_by_target`，让 `history` mode 只返回对应 target 的 code_example。当前 13 个 code_example 全是 InsertShips，Optimization/Knapsack 需要自己的 code_example——当前没有，先标记为 "target has no code_examples yet"。

**验收**：
- Optimization API-only 的 `ctx_chars > 0` 且 `rag_trace.global_items` 包含 optimization 专属项
- Knapsack API-only 的 `ctx_chars > 0` 且 `rag_trace.global_items` 包含 knapsack 专属项
- InsertShips 现有行为不退化

---

## Phase 2: 补跑 Optimization/Knapsack 正式实验（P0）

**前提**：Phase 1 通过后执行。

### 2.1 Optimization

| Cell | Mode | 参数 | gen/pop | repeats |
|------|------|------|:---:|:---:|
| d50 | Baseline | no RAG | 1/8 | 1 |
| d50 | API-only | rag_mode=literature top_k=0 max_chars=1000 | 1/8 | 1 |
| d75 | Baseline | no RAG | 1/8 | 1 |
| d75 | API-only | rag_mode=literature top_k=0 max_chars=1000 | 1/8 | 1 |

输出：`eoh_go_workspace/reports/tables/weekly_optimization_proper/`

### 2.2 Knapsack

| Instance | Mode | gen/pop | repeats |
|------|------|:---:|:---:|
| testdata_01 | Baseline | 1/8 | 1 |
| testdata_01 | API-only | 1/8 | 1 |

输出：`eoh_go_workspace/reports/tables/weekly_knapsack_proper/`

**验收**：每组至少 1 rep 在 RAG context 生效下有非 seed 的 best_EOH_J

---

## Phase 3: 更新每周展示报告（P0）

更新 `eoh_go_workspace/reports/clv_harness_weekly_showcase.md`：

1. 总表：3 算子 × 2 密度 × 3 mode
2. 标注：正式证据 vs 探索证据（有 RAG context vs 无 RAG context）
3. InsertShips 代码演化可视化（gen1→4→8）
4. C 层适配前后的对比表
5. 失败案例分析
