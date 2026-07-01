"""
模块：adaptive_operators —— 已保留为兼容层
功能：Step 1 之后所有算子权重逻辑都收敛到 eoh_rag.experiments.pool_api.PoolAPI。
      本文件仅保留 register_operator_result / get_operator_weights 两个函数作为 shim。
职责：调用 PoolAPI，让外部调用点无感切换。
不负责：任何新的策略/算法实现（请写在 PoolAPI 或独立模块内）。
主要调用方：batch_runner.py（Step 2 迁移完成后已改为直接用 PoolAPI；本 shim 仅供旧脚本）。

接口：
    register_operator_result(pool_dir, problem, operator, improved, delta) -> None
    get_operator_weights(pool_dir, problem) -> dict[str, float]

输入：pool_dir (Path)
输出：JSONL 追加 / 权重字典
示例：
    from eoh_rag.experiments.adaptive_operators import get_operator_weights
    weights = get_operator_weights(Path("shared_pool"), "bp_online")
"""

from __future__ import annotations

from pathlib import Path

from eoh_rag.experiments.pool_api import PoolAPI


def register_operator_result(
    pool_dir: Path,
    problem: str,
    operator: str,
    improved: bool,
    delta: float,
) -> None:
    """[DEPRECATED shim] 请改用 PoolAPI(pool_dir).register_operator_stat(...)。"""
    PoolAPI(pool_dir).register_operator_stat(problem, operator, improved, delta)


def get_operator_weights(pool_dir: Path, problem: str) -> dict[str, float]:
    """[DEPRECATED shim] 请改用 PoolAPI(pool_dir).operator_weights(problem)。"""
    return PoolAPI(pool_dir).operator_weights(problem)
