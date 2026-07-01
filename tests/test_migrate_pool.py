"""
脚本：test_migrate_pool.py
功能：验证 migrate_pool 的规范化逻辑（normalize 函数 + 损坏行处理 + 计数校验）
输入：无（tmp_path 隔离）
输出：pytest 断言
用法：python3 -m pytest tests/test_migrate_pool.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# 直接测试内部函数
import sys
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from migrate_pool import (
    _normalize_best_code,
    _normalize_failure,
    _normalize_operator_stat,
    _normalize_pool_index,
    _read_jsonl,
    migrate,
)


class TestNormalize:
    def test_pool_index_valid(self):
        r = _normalize_pool_index({"problem": "bp_online", "run_dir": "/x", "objective": 0.01, "ts": 1.0})
        assert r == {"problem": "bp_online", "run_dir": "/x", "objective": 0.01, "ts": 1.0}

    def test_pool_index_missing_field(self):
        assert _normalize_pool_index({"problem": "bp"}) is None

    def test_best_code_valid(self):
        r = _normalize_best_code({"code": "def f(): pass", "objective": 0.01, "ts": 2.0})
        assert r["code"] == "def f(): pass"

    def test_operator_stat_valid(self):
        r = _normalize_operator_stat({"operator": "e1", "improved": True, "delta": 0.01, "ts": 3.0})
        assert r["improved"] is True

    def test_failure_valid(self):
        r = _normalize_failure({"failure_type": "timeout", "pattern_hint": "hint", "code_hash": "abc", "ts": 4.0})
        assert r["failure_type"] == "timeout"

    def test_failure_empty_type(self):
        assert _normalize_failure({"failure_type": "", "pattern_hint": "x"}) is None


class TestReadJsonl:
    def test_reads_valid(self, tmp_path: Path):
        f = tmp_path / "test.jsonl"
        f.write_text('{"a":1}\n{"a":2}\n')
        entries, skipped = _read_jsonl(f)
        assert len(entries) == 2
        assert skipped == 0

    def test_skips_corrupted(self, tmp_path: Path):
        f = tmp_path / "test.jsonl"
        f.write_text('{"a":1}\nNOT JSON\n{"a":3}\n')
        entries, skipped = _read_jsonl(f)
        assert len(entries) == 2
        assert skipped == 1

    def test_missing_file(self, tmp_path: Path):
        entries, skipped = _read_jsonl(tmp_path / "nope.jsonl")
        assert entries == []
        assert skipped == 0


class TestMigrate:
    def test_full_migrate(self, tmp_path: Path):
        source = tmp_path / "source"
        source.mkdir()
        target = tmp_path / "target"

        # pool_index
        (source / "pool_index.jsonl").write_text(
            json.dumps({"problem": "bp", "run_dir": "/r", "objective": 0.01, "ts": 1.0}) + "\n"
        )
        # best_codes
        (source / "best_codes_bp.jsonl").write_text(
            json.dumps({"code": "x", "objective": 0.02, "ts": 2.0}) + "\n"
        )
        # operator_stats
        (source / "operator_stats_bp.jsonl").write_text(
            json.dumps({"operator": "e1", "improved": True, "delta": 0.01, "ts": 3.0}) + "\n"
        )
        # failures
        (source / "failures_bp.jsonl").write_text(
            json.dumps({"failure_type": "timeout", "pattern_hint": "h", "code_hash": "abc", "ts": 4.0}) + "\n"
        )

        stats = migrate(source, target, dry_run=False)
        assert (target / "pool_index.jsonl").exists()
        assert (target / "best_codes_bp.jsonl").exists()
        assert stats["pool_index"]["source"] == 1
        assert stats["pool_index"]["normalized"] == 1

    def test_dry_run_no_write(self, tmp_path: Path):
        source = tmp_path / "source"
        source.mkdir()
        target = tmp_path / "target"
        (source / "pool_index.jsonl").write_text(
            json.dumps({"problem": "bp", "run_dir": "/r", "objective": 0.01, "ts": 1.0}) + "\n"
        )
        migrate(source, target, dry_run=True)
        assert not target.exists()
