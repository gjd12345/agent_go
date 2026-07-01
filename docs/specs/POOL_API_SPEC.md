# PoolAPI SPEC

> 位置：`eoh_rag/experiments/pool_api.py`
> 状态：Step 1 交付（2026-07）
> 目的：把散落在 `batch_runner.py` / `adaptive_operators.py` / `shared_failures.py` 中
> 的 shared-pool 读写函数统一到 `PoolAPI` 类，供 batch_runner、hooks、retriever 调用。

## 1. 责任边界

| 做 | 不做 |
| --- | --- |
| pool_dir 下 4 类 JSONL 的 append/read | 决定谁应该 register（属 batch_runner / hooks） |
| fcntl 文件锁保证多进程安全 | card synthesis / 语料库写入（属 `rag.card_synthesis`） |
| 目标值最小化（minimize）语义的排序去重 | baseline 阈值（属 `experiments.baselines`） |
| 失败模式短提示的静态推断 | 语义化理解失败原因（未来可交给小模型） |

## 2. 磁盘布局

```
<pool_dir>/
├── pool_index.jsonl                  # 每次完成 run 的索引
├── best_codes_<problem>.jsonl        # 每个 problem 的精英代码池
├── operator_stats_<problem>.jsonl    # e1/e2/m1/m2 的成功率统计
└── failures_<problem>.jsonl          # 失败代码短提示
```

所有文件是 **JSONL**（一行一条 dict），且 append-only。**永远不 truncate**——
即使 Step 7 做数据迁移，也是新 pool_dir，不 rewrite 旧文件。

## 3. 接口

```python
class PoolAPI:
    def __init__(self, pool_dir: str | Path)

    # run 索引
    def register_run(problem, run_dir, objective, **meta) -> None
    def best_run(problem) -> str
    def list_runs(problem=None) -> list[dict]

    # 精英代码
    def register_code(problem, code, objective, **meta) -> None
    def best_codes(problem, top_k=3) -> list[dict]

    # 算子成功率
    def register_operator_stat(problem, operator, improved, delta) -> None
    def operator_weights(problem) -> dict[str, float]

    # 失败模式
    def register_failure(problem, code, failure_type, pattern_hint="") -> None
    def failure_hints(problem, top_k=5) -> list[str]
```

### 3.1 语义要点

- **objective 越小越好**（minimize）。`best_run` / `best_codes` 均按升序取。
- `best_codes` 会按 `objective` 去重，避免多次注入同一份 code。
- `operator_weights` 在 `total < 3` 时返回默认 `1.0`，避免早期偶然导致过拟合。
- `register_failure` 允许调用方传 `pattern_hint` 覆盖静态推断（后续 Step 5 hooks
  可以让小模型来生成 hint）。
- `list_runs(problem=None)` 用于诊断脚本/迁移脚本；生产代码请传具体 problem。

### 3.2 线程/进程安全

- 所有 append 走 `_append_jsonl`，用 `fcntl.LOCK_EX` 独占写。
- 读取无锁（append-only + JSONL 行独立 → 最坏情况读到少一行，不会读到损坏行）。

## 4. 兼容层策略（Step 2 落地）

Step 1 **只新增，不删除**。旧函数 `shared_pool_register` / `shared_pool_best` /
`shared_pool_register_code` / `shared_pool_best_codes` /
`register_operator_result` / `get_operator_weights` /
`register_failure` / `get_failure_hints` 保留，但改成 **一行 shim**：

```python
# 例：batch_runner.py
def shared_pool_register(pool_dir, problem, run_dir, objective):
    PoolAPI(pool_dir).register_run(problem, run_dir, objective)
```

外部脚本无需感知；Step 5 hooks 完成后再彻底删除 shim。

## 5. 验收标准

- 单元测试 `tests/test_pool_api.py` 覆盖：
  - `register_run` + `best_run` 单/多 problem
  - `best_codes` 去重与 top_k
  - `operator_weights` 阈值行为（<3 → 1.0；≥3 → 0.5+rate）
  - `failure_hints` 按频次排序
  - 空 pool_dir 时读接口返回空
- 手工验证：拿现有 evidence 中 pool 目录（如果存在）跑 `PoolAPI.best_run`，
  结果与旧函数一致。
- 中文模块头：新人/AI 读前 30 行即可回答"这个模块解决什么"。

## 6. 后续演进（Step 3-8 提前登记）

| Step | 会不会改 PoolAPI | 改动方向 |
| --- | --- | --- |
| Step 2 | ✗ | 只把 batch_runner 内联函数替换成 PoolAPI 调用 |
| Step 3 | ✗ | baselines/evaluator 是独立模块，不入池 |
| Step 4 | ✓ 可能新增 `register_run_manifest` | RunTracker 会想追加 run 目录里的 manifest 摘要 |
| Step 5 | ✓ 可能新增 `register_hook_event` | hooks 需要一个通用事件流 |
| Step 6 | ✗ | 只影响 card_synthesis 阈值/词表 |
| Step 7 | 迁移脚本调用 PoolAPI 读写 | 不改接口 |
| Step 8 | ✗ | 抽象 SKILL.md，不动运行时 |

任何新增方法都要先更新本 SPEC，再改代码。
