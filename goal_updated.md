/goal: Weekly Showcase — Multi-Operator C+L+V Harness

目标：在现有 registry 基础设施上，完成 3 个算子 + 1 个跨问题的实验，产出导师展示材料。

## Current State (do NOT rebuild)

- `eoh_go/eoh_runner/target_spec.py` + `problem_spec.py` + `registry.py` — 已建成
- 已注册 target: InsertShips (VRP), Optimization (VRP), SelectItems (Knapsack)
- InsertShips: 正式证据 + deep-gen + 代码演化图 已完成
- Optimization: smoke 通过 (gen=1 pop=4), 但 best=seed
- Knapsack: smoke 通过 (gen=1 pop=4), 但 best=seed
- `clv_harness_weekly_showcase.md`: 基础记录存在，需要补充新数据
- `code_evolution_insertships_gen8.md`: 已生成
- 单元测试: 47 pass
- history-RAG bug (runner.py:119): 已修

## Phase 1: InsertShips 数据补强（P0, 1h）

目标：让正式证据的 density branch 结论在统计上稳固。

运行：
1. d50 history-RAG rep_3（当前 2/3 valid pairs，缺 1 个）
   - bash: cd agent_ad/agent_go && export $(grep -v '^#' ~/.config/agent_go/chatrhino.env | xargs) && python3 -m eoh_go.experiments.eoh_arrival_grid --root . --problem rc101.json --density d50 --arrival-scale 1.0 --pop-size 8 --generations 1 --rag-mode history --rag-top-k 1 --rag-max-chars 1500 --llm-model JoyAI-LLM-Pro --output-dir eoh_go_workspace/reports/tables/insertships_data_completion/d50_history_rep3 --ablation-pair --use-density-source-dirs --source-dir solomon_benchmark

2. d75 API-only rep_4 + rep_5（当前 1/1/1，需 5-rep 稳定）
   - 同上，改 --rag-mode literature --rag-top-k 0 --density d75，跑 2 次到不同 output-dir

验收：d50 history 3/3 valid pairs, d75 API-only 5/5 valid pairs

## Phase 2: Optimization 完整实验（P0, 2h）

已有 infrastructure，只需跑实验。Target name = "Optimization"。

1. Optimization gen=1 pop=8 ablation-pair × RC101-d50/d75
   - baseline / API-only / history-RAG（各 1 rep）
   - 使用 --target Optimization --problem-name vrp_insertships
   - 输出: eoh_go_workspace/reports/tables/weekly_optimization/

2. Optimization gen=8 pop=4 deep run × RC101-d50/d75
   - baseline / API-only（各 1 run）
   - 输出: eoh_go_workspace/reports/tables/weekly_optimization_gen8/

3. Optimization 代码演化报告（同 Phase 2 模式，从 gen=8 data 提取）

验收：Optimization 对比表 + 代码演化图 + gen=8 best_J 低于 seed

## Phase 3: Knapsack 完整实验（P1, 2h）

1. Knapsack history-RAG context（如还没有）
   - 为 SelectItems target 注册 history 模式
   - corpus 中加 knapsack-specific code examples

2. Knapsack gen=1 pop=8 × 3-5 instances
   - baseline / API-only / history-RAG（各 1 rep）
   - 输出: eoh_go_workspace/reports/tables/weekly_knapsack/

3. Knapsack gen=8 pop=4 deep run × 2 instances
   - baseline / API-only

验收：Knapsack 对比表 + 至少 1 个 instance 的 gen=8 改进

## Phase 4: RoutingTS 第三个算⼦（P2, 1.5h）

同 VRP solver 内第三类优化：单车辆 TSPTW routing。

1. 注册 RoutingTS target
   - signature: func RoutingTS(task *RoutingTask) RoutingResult
   - 在 routing.go 内，接口独立

2. smoke run: gen=1 pop=4 × RC101-d50
   - 验证 build + eval 通过

3. 如果 smoke 通过: gen=1 pop=8 ablation-pair × RC101-d50/d75

验收：RoutingTS 可运行 + 至少 1 组对比数据

## Phase 5: 汇总报告（P0, 1h）

综合所有产物：

1. 总表：3 算子 × 2 密度 × 3 mode
   ```
   Target        d50_best  d75_best  最佳Mode  跨问题
   InsertShips   274.90    266.06    API/Hist  VRP
   Optimization     TBD       TBD       TBD    VRP
   RoutingTS        TBD       TBD       TBD    VRP
   Knapsack         TBD       —          TBD    0/1 KP
   ```

2. 代码演化可视化：每算子 gen1→4→8 代码对比
3. C+L+V 架构图（含 registry）
4. 明确标注：正式证据 / 探索证据 / smoke evidence
5. 失败案例分析

输出: eoh_go_workspace/reports/clv_harness_weekly_showcase.md (update)

## 约束

- 不重新搭建 registry（已存在）
- 不碰 TSP/CVRP 新问题（本周范围内）
- API key 不可打印
- EOH runs serial, generated code 仅 via guarded evaluator
- V 层过滤: valid/suspicious/invalid, best_build_ok, seed mismatch
- 实验产出不入 git，报告写入 reports/
