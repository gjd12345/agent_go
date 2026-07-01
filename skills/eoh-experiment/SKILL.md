# EOH Experiment Skill

> 实验执行 skill — 帮助 AI 正确地启动、监控、分析 EoH 实验。

## 触发条件

用户要：跑实验、启动 batch、执行 manifest、分析 run 结果

## 前置条件

- 在 `agent_go` 仓库根目录
- `eoh_rag_workspace/shared_pool/` 存在
- 环境变量 `EOH_OFFICIAL_PYTHON` 指向正确 Python
- 网络可访问 JoyAI chatrhino API

## 核心命令

### 启动实验
```bash
python3 -m eoh_rag.experiments.batch_runner \
  --manifest <manifest.json> \
  --shared-pool-dir eoh_rag_workspace/shared_pool \
  --output-dir eoh_rag_workspace/reports/auto_experiment_reports/<suite_name>
```

### 干运行（检查 manifest 是否合法）
```bash
python3 -m eoh_rag.experiments.batch_runner --manifest <manifest.json> --dry-run
```

### 查看 pool 状态
```python
from eoh_rag.experiments.pool_api import PoolAPI
pool = PoolAPI("eoh_rag_workspace/shared_pool")
pool.best_run("bp_online")          # 最佳 run
pool.best_codes("bp_online", 3)     # top-3 精英代码
pool.operator_weights("bp_online")  # 算子权重
pool.failure_hints("bp_online", 5)  # 失败模式提示
```

### 评估单次 run
```python
from eoh_rag.experiments.evaluator import evaluate_run
r = evaluate_run("bp_online", 0.00674)
# r["decision"] = "archive" | "continue" | "adjust" | "escalate"
```

## Manifest 结构

```json
{
  "suite": "island_3",
  "problems": ["bp_online", "tsp_construct", "cvrp_construct"],
  "arms": [
    {"runner_arm": "mixed_rag", "context_strategy": "tocc_v3", "candidate_card_ids": [...]}
  ],
  "generations": [8],
  "repeats": 5,
  "operators": "e1,e2,m1,m2",
  "run_timeout_s": 1800
}
```

## 关键约束

- 必须连接共享池（`--shared-pool-dir`），否则无 island model 效果
- batch_runner 启动后自动管理多进程 pool 读写（fcntl 文件锁）
- 每次 run ≈ 20-30 分钟（取决于 problem 和 gen 数）
- 结果判断走 evaluator：improvement >= 5% 才算 archive

## 相关文档

- `docs/specs/POOL_API_SPEC.md`
- `docs/specs/EVALUATOR_SPEC.md`
- `docs/specs/HOOKS_SPEC.md`
- `docs/project_context/01_TRD_EOH_RAG.md`
