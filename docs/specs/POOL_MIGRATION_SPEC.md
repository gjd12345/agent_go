# Pool Migration SPEC

> 位置：`scripts/migrate_pool.py`
> 状态：Step 7 交付（2026-07）
> 目的：将旧 shared_pool JSONL 规范化到统一 schema（copy，不 move），保障数据完整性。

## 1. 设计原则

- **Copy-first, move-later**：迁移只创建新目录 normalized_pool/，不删除/修改旧文件。
- **计数校验**：source_count == normalized_count + skipped_count，否则报错退出。
- **幂等**：重复执行覆盖 target，不重复追加。
- **损坏容错**：跳过无法 JSON.parse 的行，打印 warning。

## 2. 规范化规则

| 文件 | 必需字段 | 类型转换 |
| --- | --- | --- |
| pool_index.jsonl | problem, run_dir, objective, ts | objective→float, ts→float |
| best_codes_*.jsonl | code, objective, ts | objective→float |
| operator_stats_*.jsonl | operator, improved, delta, ts | improved→bool, delta→float |
| failures_*.jsonl | failure_type, pattern_hint, code_hash, ts | ts→float |

缺少必需字段的记录被丢弃（计入 skipped）。

## 3. 使用方式

```bash
# Dry run（只看统计）
python3 scripts/migrate_pool.py --source eoh_rag_workspace/shared_pool --target eoh_rag_workspace/normalized_pool --dry-run

# 执行迁移
python3 scripts/migrate_pool.py --source eoh_rag_workspace/shared_pool --target eoh_rag_workspace/normalized_pool
```

## 4. PoolAPI 支持

迁移完成后，PoolAPI 可直接指向 normalized_pool：
```python
pool = PoolAPI("eoh_rag_workspace/normalized_pool")
```

旧 pool 保持只读直到确认迁移无误。

## 5. 验收标准

- `tests/test_migrate_pool.py` 全绿
- dry-run 在实际 shared_pool 上执行无报错
- source_count == normalized_count（实际数据 1815 条全部迁移）
