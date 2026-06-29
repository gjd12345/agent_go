"""Shared Failure Patterns — cross-process failure memory.

Records code patterns that cause evaluation failures (timeout, invalid output,
runtime errors) and provides failure hints for injection into LLM prompts.
"""

from __future__ import annotations

import fcntl
import json
import re
import time
from collections import Counter
from pathlib import Path


def _failures_path(pool_dir: Path, problem: str) -> Path:
    return pool_dir / f"failures_{problem}.jsonl"


def register_failure(
    pool_dir: Path,
    problem: str,
    code_snippet: str,
    failure_type: str,
    pattern_hint: str = "",
) -> None:
    """Register a code failure pattern in the shared pool."""
    pool_dir.mkdir(parents=True, exist_ok=True)
    path = _failures_path(pool_dir, problem)
    # Extract a short pattern from the code
    if not pattern_hint:
        pattern_hint = _extract_pattern(code_snippet, failure_type)
    entry = json.dumps({
        "failure_type": failure_type,
        "pattern_hint": pattern_hint,
        "code_hash": hash(code_snippet) % 10**8,
        "ts": time.time(),
    }, ensure_ascii=False)
    with open(path, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(entry + "\n")
        fcntl.flock(f, fcntl.LOCK_UN)


def get_failure_hints(pool_dir: Path, problem: str, top_k: int = 5) -> list[str]:
    """Get top-k most common failure patterns as hints for LLM prompt."""
    path = _failures_path(pool_dir, problem)
    if not path.exists():
        return []
    counter: Counter[str] = Counter()
    for line in path.read_text().strip().split("\n"):
        if not line:
            continue
        entry = json.loads(line)
        hint = entry.get("pattern_hint", "")
        if hint:
            counter[hint] += 1
    return [hint for hint, _ in counter.most_common(top_k)]


def _extract_pattern(code: str, failure_type: str) -> str:
    """Extract a short actionable hint from failed code."""
    if failure_type == "eval_timeout":
        if re.search(r"for .+ in .+:\s*\n\s*for", code):
            return "AVOID nested loops over all nodes (causes timeout)"
        if "while" in code and "break" not in code:
            return "AVOID unbounded while loops without break condition"
        return "AVOID O(n^3) or higher complexity operations"
    if failure_type == "invalid_output":
        if "return None" in code or "return []" in code:
            return "MUST return valid output (not None or empty)"
        return "ENSURE return value matches expected type and range"
    if failure_type == "runtime_error":
        if "/ 0" in code or "divide" in code.lower():
            return "AVOID division by zero — add epsilon to denominators"
        return "CHECK array index bounds and division operations"
    if failure_type == "valid_collapse":
        return "AVOID strategies that produce identical outputs for all inputs"
    return f"AVOID pattern causing {failure_type}"
