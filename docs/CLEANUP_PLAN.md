# 仓库清理计划 — 收敛到 Small-Model 数据飞轮主线

## 当前状态

- 24 并行实验进程在跑（15 gen=8 + 9 gen=16），484 runs 积累
- TSP best=6.004, CVRP best=12.423, BP best=0.00714
- 论文主线已确定：Trace-Conditioned Small-Model Controller

## 清理原则

1. 不中断正在跑的实验
2. 先改文档标记，后移代码文件
3. legacy 不删除只归档
4. corpus 拆分等 batch 完成后做（避免影响在跑的 RAG）

---

## Step 1: 文档更新（立即执行，不影响实验）

### README.md 重写主线

```markdown
# EOH-RAG: Trace-Conditioned Small-Model Controllers for Heuristic Evolution

Current research direction:
- Phase 1: RAG reranker small model (strategy card selection)
- Phase 2: Code gen/repair small model (heuristic generation)
- Data source: Island Model batch experiments (batch_runner + shared_pool)

Active pipeline: eoh_go/experiments/ + eoh_go/rag/ + eoh_go/tocc/
Legacy assets: Go InsertShips solver, historical TOCC reports (see legacy/)
```

### AGENTS.md 更新 phase

```markdown
Current phase: data collection for trace-conditioned small-model reranker and code generation/repair models.
```

### docs/ISOLATION.md 标记状态

加 `EXPERIMENTAL: not used by current official EOH pipeline` 注释

---

## Step 2: Legacy 归档（安全操作，不改运行代码）

### 创建 legacy/ 目录

```
legacy/
├── README.md                    # 归档说明
├── insertships_eoh_v0/          # Go EoH v0 相关
│   ├── cli.py                   # from eoh_go/cli.py
│   ├── evolution.py             # from eoh_go/evolution.py
│   ├── benchmark.py             # from eoh_go/benchmark.py
│   ├── candidates.py            # from eoh_go/candidates.py
│   ├── paths.py                 # from eoh_go/paths.py
│   ├── grids/                   # from eoh_go/experiments/grids/
│   ├── reports/                 # arrival_scale_table.py, rag_ablation_report.py
│   └── candidate_sources/       # from eoh_go_workspace/candidate_sources/
├── corpus_insertships/
│   └── code_examples.jsonl      # InsertShips Go code examples
└── reports_20260619/            # from archived_experiments/reports_20260619/
```

### 移动清单

| From | To | 原因 |
|------|-----|------|
| `eoh_go/cli.py` | `legacy/insertships_eoh_v0/` | InsertShips CLI，主线不用 |
| `eoh_go/evolution.py` | `legacy/insertships_eoh_v0/` | 旧进化框架，含 Windows 路径 |
| `eoh_go/benchmark.py` | `legacy/insertships_eoh_v0/` | Go binary 评测 |
| `eoh_go/candidates.py` | `legacy/insertships_eoh_v0/` | Go candidate 管理 |
| `eoh_go/paths.py` | `legacy/insertships_eoh_v0/` | 旧路径管理 |
| `eoh_go/experiments/grids/` | `legacy/insertships_eoh_v0/grids/` | InsertShips grid |
| `eoh_go/experiments/legacy/` | `legacy/insertships_eoh_v0/experiments_legacy/` | 已标 legacy |
| `eoh_go_workspace/candidate_sources/` | `legacy/insertships_eoh_v0/candidate_sources/` | Go heuristic files |
| `eoh_go_workspace/rag/corpus/code_examples.jsonl` | `legacy/corpus_insertships/` | InsertShips 代码 corpus |

---

## Step 3: Manifest 清理

### 删除固定 prev_run_dir（gen16 manifests）

```json
// 删除 "prev_run_dir": "eoh_go_workspace/reports/.../island_X/..."
// 保留 "use_prev_run_dir_chain": true (由 shared pool 自动接入)
```

### 归档旧 manifests

将以下移到 `legacy/manifests/`:
- `tocc_day1_*.json`, `tocc_day2_*.json`
- `tocc_history_*.json`, `tocc_split_*.json`
- `tocc_stabilization_repeats.json`
- `v2_agent_real_run_validation.json`
- `week_tocc_tsp_cvrp.json`
- `phase4_cvrp_targeted_repeat3.json`

保留在主线的：
- `high_gen_*.json` (当前在跑)
- `gen16_*.json` (当前在跑)
- `data_collection_*.json`
- `phase4b_*.json` (有参考价值)
- `rag_ablation_*.json` (有参考价值)

---

## Step 4: Corpus 分层（等 batch 完成后执行）

```
eoh_go_workspace/rag/corpus/
├── algorithm_cards.jsonl          # 保留，是 RAG 核心
├── card_outcomes.jsonl            # 保留，标注 label_quality 字段
├── api_constraints_official.jsonl # 只保留 obp/tsp/cvrp
├── api_constraints_legacy.jsonl   # InsertShips/Knapsack/Mixer
├── failure_cases_short.jsonl      # 压缩为短 warning cards
└── DEPRECATED/
    ├── code_examples.jsonl        # 已移到 legacy
    └── failure_cases_full.jsonl   # 旧完整版
```

---

## Step 5: 报告归档

| 文件 | 动作 |
|------|------|
| `tocc_current_progress_20260619.md` | 移到 legacy/reports_20260619/ |
| `tocc_stabilization_report.md` | 改名加 `_legacy_20260618` 后缀 |
| `tocc_best_code_records.md` | 旧内容归档，新建 `current_best.md` 从 pool 生成 |
| `rag_upgrade_plan_for_review.md` | 移到 legacy/ |

---

## 执行顺序（不中断实验）

1. **立即**：更新 README/AGENTS/ISOLATION 文档
2. **立即**：创建 `legacy/` 目录结构和 README
3. **安全时**：移动 legacy 代码（确认不被 import）
4. **batch 完成后**：拆分 corpus、清理 manifests
5. **最后**：更新 tests 的 import 路径

---

## 验证

- `python3 -m pytest --ignore=tests/test_official_eoh_run.py` 仍通过
- `go build .` 不受影响
- 正在跑的 15+9 进程不中断
- shared_pool 继续正常写入
