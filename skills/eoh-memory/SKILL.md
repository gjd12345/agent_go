# EOH Memory Skill

> Pool 记忆管理 skill — 帮助 AI 查询、诊断、维护实验记忆池。

## 触发条件

用户要：查 pool 状态、诊断 operator 效果、分析失败模式、迁移数据

## 核心操作

### 查询记忆池
```python
from eoh_rag.experiments.pool_api import PoolAPI

pool = PoolAPI("eoh_rag_workspace/shared_pool")

# 总 run 数
print(f"Total runs: {len(pool.list_runs())}")

# 每个 problem 的最佳
for p in ["bp_online", "tsp_construct", "cvrp_construct"]:
    best = pool.best_run(p)
    codes = pool.best_codes(p, top_k=3)
    weights = pool.operator_weights(p)
    hints = pool.failure_hints(p)
    print(f"\n{p}:")
    print(f"  best_run: {best}")
    print(f"  top codes: {[c['objective'] for c in codes]}")
    print(f"  operator weights: {weights}")
    print(f"  failure hints: {hints[:2]}")
```

### 诊断 operator 偏差
```python
# 如果某个 operator weight 持续 < 0.7，说明它在该 problem 上表现差
weights = pool.operator_weights("bp_online")
weak = {op: w for op, w in weights.items() if w < 0.7}
if weak:
    print(f"建议禁用或降权: {weak}")
```

### 数据迁移
```bash
# 规范化旧数据
python3 scripts/migrate_pool.py --source eoh_rag_workspace/shared_pool --target eoh_rag_workspace/normalized_pool --dry-run

# 确认无误后执行
python3 scripts/migrate_pool.py --source eoh_rag_workspace/shared_pool --target eoh_rag_workspace/normalized_pool
```

### 手工注册（修复遗漏）
```python
pool = PoolAPI("eoh_rag_workspace/shared_pool")
pool.register_run("bp_online", "/path/to/missed/run", 0.00674)
pool.register_code("bp_online", "def heuristic(...):\n    ...", 0.00674)
```

## 数据目录

```
eoh_rag_workspace/shared_pool/
├── pool_index.jsonl                  # run 索引
├── best_codes_<problem>.jsonl        # 精英代码
├── operator_stats_<problem>.jsonl    # 算子统计
└── failures_<problem>.jsonl          # 失败模式
```

## 关键约束

- 所有文件 append-only，永远不 truncate
- 多进程安全（fcntl.LOCK_EX）
- objective 越小越好（minimize 语义）
- operator_weights 在样本 < 3 时返回默认 1.0

## 相关文档

- `docs/specs/POOL_API_SPEC.md`
- `docs/specs/POOL_MIGRATION_SPEC.md`
