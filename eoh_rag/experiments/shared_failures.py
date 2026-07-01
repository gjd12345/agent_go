"""
模块：shared_failures —— 已保留为兼容层
功能：Step 1 之后失败模式记录/查询统一由 PoolAPI 承担。本文件仅保留 shim。
职责：调用 PoolAPI.register_failure / failure_hints。
不负责：定义新的失败类型或提示逻辑（请修改 PoolAPI._extract_pattern）。
主要调用方：batch_runner.py（旧调用），未来会全部改直连 PoolAPI。

接口：
    register_failure(pool_dir, problem, code_snippet, failure_type, pattern_hint="") -> None
    get_failure_hints(pool_dir, problem, top_k=5) -> list[str]

输入：pool_dir (Path)
输出：JSONL 追加 / 提示字符串列表
示例：
    from eoh_rag.experiments.shared_failures import get_failure_hints
    hints = get_failure_hints(Path("shared_pool"), "bp_online", top_k=3)
"""

from __future__ import annotations

from pathlib import Path

from eoh_rag.experiments.pool_api import PoolAPI


def register_failure(
    pool_dir: Path,
    problem: str,
    code_snippet: str,
    failure_type: str,
    pattern_hint: str = "",
) -> None:
    """[DEPRECATED shim] 请改用 PoolAPI(pool_dir).register_failure(...)。"""
    PoolAPI(pool_dir).register_failure(problem, code_snippet, failure_type, pattern_hint)


def get_failure_hints(pool_dir: Path, problem: str, top_k: int = 5) -> list[str]:
    """[DEPRECATED shim] 请改用 PoolAPI(pool_dir).failure_hints(problem, top_k)。"""
    return PoolAPI(pool_dir).failure_hints(problem, top_k=top_k)
