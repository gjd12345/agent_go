"""
脚本：migrate_pool.py
功能：将旧 shared_pool JSONL 文件规范化到统一 schema 的新目录（copy，不 move）
输入：旧 pool_dir 路径
输出：normalized_pool/ 目录（结构与旧一致，但每条记录有完整字段）
用法：python3 scripts/migrate_pool.py --source eoh_rag_workspace/shared_pool --target eoh_rag_workspace/normalized_pool [--dry-run]

规范化规则：
  - pool_index.jsonl: 确保 {problem, run_dir, objective, ts} 四字段完整
  - best_codes_*.jsonl: 确保 {code, objective, ts} 三字段完整
  - operator_stats_*.jsonl: 确保 {operator, improved, delta, ts} 四字段完整
  - failures_*.jsonl: 确保 {failure_type, pattern_hint, code_hash, ts} 四字段完整
  - 跳过损坏行，打印 warning
  - 输出后校验：legacy count == normalized count（不计损坏行）
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def _read_jsonl(path: Path) -> tuple[list[dict], int]:
    """读取 JSONL，返回 (有效记录, 跳过行数)。"""
    if not path.exists():
        return [], 0
    entries = []
    skipped = 0
    for line in path.read_text(encoding="utf-8").strip().split("\n"):
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            skipped += 1
    return entries, skipped


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _normalize_pool_index(entry: dict) -> dict | None:
    """规范化 pool_index 记录。"""
    problem = entry.get("problem")
    run_dir = entry.get("run_dir")
    objective = entry.get("objective")
    if problem is None or run_dir is None or objective is None:
        return None
    return {
        "problem": str(problem),
        "run_dir": str(run_dir),
        "objective": float(objective),
        "ts": float(entry.get("ts", 0)),
    }


def _normalize_best_code(entry: dict) -> dict | None:
    code = entry.get("code")
    objective = entry.get("objective")
    if code is None or objective is None:
        return None
    return {
        "code": str(code),
        "objective": float(objective),
        "ts": float(entry.get("ts", 0)),
    }


def _normalize_operator_stat(entry: dict) -> dict | None:
    operator = entry.get("operator")
    if operator is None:
        return None
    return {
        "operator": str(operator),
        "improved": bool(entry.get("improved", False)),
        "delta": float(entry.get("delta", 0)),
        "ts": float(entry.get("ts", 0)),
    }


def _normalize_failure(entry: dict) -> dict | None:
    failure_type = entry.get("failure_type")
    if not failure_type:
        return None
    return {
        "failure_type": str(failure_type),
        "pattern_hint": str(entry.get("pattern_hint", "")),
        "code_hash": str(entry.get("code_hash", "")),
        "ts": float(entry.get("ts", 0)),
    }


def migrate(source: Path, target: Path, dry_run: bool = False) -> dict:
    """执行迁移。返回统计摘要。"""
    stats: dict[str, dict] = {}

    # pool_index.jsonl
    src_file = source / "pool_index.jsonl"
    entries, skipped = _read_jsonl(src_file)
    normalized = [r for r in (_normalize_pool_index(e) for e in entries) if r is not None]
    stats["pool_index"] = {"source": len(entries), "normalized": len(normalized), "skipped": skipped}
    if not dry_run and normalized:
        _write_jsonl(target / "pool_index.jsonl", normalized)

    # best_codes_*.jsonl
    for src_file in sorted(source.glob("best_codes_*.jsonl")):
        entries, skipped = _read_jsonl(src_file)
        normalized = [r for r in (_normalize_best_code(e) for e in entries) if r is not None]
        stats[src_file.name] = {"source": len(entries), "normalized": len(normalized), "skipped": skipped}
        if not dry_run and normalized:
            _write_jsonl(target / src_file.name, normalized)

    # operator_stats_*.jsonl
    for src_file in sorted(source.glob("operator_stats_*.jsonl")):
        entries, skipped = _read_jsonl(src_file)
        normalized = [r for r in (_normalize_operator_stat(e) for e in entries) if r is not None]
        stats[src_file.name] = {"source": len(entries), "normalized": len(normalized), "skipped": skipped}
        if not dry_run and normalized:
            _write_jsonl(target / src_file.name, normalized)

    # failures_*.jsonl
    for src_file in sorted(source.glob("failures_*.jsonl")):
        entries, skipped = _read_jsonl(src_file)
        normalized = [r for r in (_normalize_failure(e) for e in entries) if r is not None]
        stats[src_file.name] = {"source": len(entries), "normalized": len(normalized), "skipped": skipped}
        if not dry_run and normalized:
            _write_jsonl(target / src_file.name, normalized)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Normalize shared_pool JSONL to unified schema")
    parser.add_argument("--source", required=True, help="旧 pool 目录")
    parser.add_argument("--target", required=True, help="新 normalized pool 目录")
    parser.add_argument("--dry-run", action="store_true", help="只打印统计，不写文件")
    args = parser.parse_args()

    source = Path(args.source)
    target = Path(args.target)

    if not source.exists():
        print(f"ERROR: source {source} does not exist")
        sys.exit(1)
    if target.exists() and any(target.iterdir()):
        print(f"WARNING: target {target} is non-empty; files may be overwritten")

    stats = migrate(source, target, dry_run=args.dry_run)

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Migration summary:")
    print(f"{'File':<35} {'Source':>8} {'Normalized':>12} {'Skipped':>8}")
    print("-" * 65)
    total_src = total_norm = total_skip = 0
    for name, s in sorted(stats.items()):
        print(f"{name:<35} {s['source']:>8} {s['normalized']:>12} {s['skipped']:>8}")
        total_src += s["source"]
        total_norm += s["normalized"]
        total_skip += s["skipped"]
    print("-" * 65)
    print(f"{'TOTAL':<35} {total_src:>8} {total_norm:>12} {total_skip:>8}")

    if total_src != total_norm + total_skip:
        print("\nERROR: count mismatch! Some records lost in normalization.")
        sys.exit(1)
    elif total_skip > 0:
        print(f"\nWARNING: {total_skip} corrupted lines skipped (see above)")
    else:
        print("\nOK: all records migrated successfully (source count == normalized count)")


if __name__ == "__main__":
    main()
