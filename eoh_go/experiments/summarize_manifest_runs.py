"""Auto Summarizer for experiment manifest runs.

Reads run_index.json + individual run summaries, generates
Chinese markdown report with per-problem tables, code snippets,
card decisions, and next actions.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _load_summary(path: Path) -> dict[str, Any] | None:
    summary_path = path / "official_eoh_run_summary.json"
    if not summary_path.exists():
        return None
    return json.loads(summary_path.read_text(encoding="utf-8"))


def _best_code_snippet(code: str | None, max_lines: int = 8) -> str:
    if not code:
        return "（无代码）"
    lines = code.strip().split("\n")
    # Pick the middle 8 lines (skip import statements)
    body = [l for l in lines if not l.strip().startswith(("import ", "from ", "def ", '"""', "#"))]
    if len(body) < 3:
        body = lines[-max_lines:]
    snippet = "\n".join(body[:max_lines])
    return f"```python\n{snippet}\n```"


def summarize(input_dir: str, no_card_memory: bool = False) -> dict[str, Any]:
    root = Path(input_dir).resolve()
    index_path = root / "run_index.json"
    if not index_path.exists():
        return {"error": f"run_index.json not found in {root}"}

    runs = json.loads(index_path.read_text(encoding="utf-8"))
    problems = defaultdict(list)
    for run in runs:
        problems[run["problem"]].append(run)

    # --- Per-problem tables ---
    summary: dict[str, Any] = {"suite": root.name, "problems": {}}

    for problem, problem_runs in sorted(problems.items()):
        rows = []
        for run in problem_runs:
            s = _load_summary(Path(run["output_dir"]))
            if not s:
                rows.append({
                    "arm": run["arm"],
                    "gen": run["generation"],
                    "status": run.get("status", "unknown"),
                    "best": None,
                    "valid": None,
                    "cards": [],
                })
                continue

            run_sum = s.get("run_summary", {})
            rag = s.get("rag_trace") or {}
            cards = [item.get("id", "") for item in rag.get("rag_selected_items", [])]
            rows.append({
                "arm": run["arm"],
                "gen": run["generation"],
                "pop": s.get("pop_size"),
                "status": run.get("status", "ok"),
                "best": run_sum.get("best_objective"),
                "valid": f"{run_sum.get('valid_candidates',0)}/{run_sum.get('population_size',0)}",
                "cards": cards,
                "code_snippet": _best_code_snippet(run_sum.get("best_code")),
                "algorithm": run_sum.get("best_algorithm", ""),
                "runtime_s": s.get("runtime_seconds"),
            })

        # Sort: pure -> api -> default -> targeted, then by gen
        arm_order = {"pure_eoh": 0, "api_only": 1, "default_rag": 2, "targeted_rag": 3}
        rows.sort(key=lambda r: (arm_order.get(r["arm"], 99), r.get("gen", 0)))

        summary["problems"][problem] = rows

    return summary


def _write_markdown(summary: dict[str, Any], output_path: str) -> None:
    lines = [
        f"# 自动化实验报告：{summary['suite']}",
        "",
        "本报告由 Auto Summarizer 自动生成。结论措辞遵循 exploratory 约束：",
        "不写'已证明''稳定优于''sweet spot 已确定'等无统计支持的强结论。",
        "",
        "## 汇总表",
        "",
        "| problem | arm | gen | pop | best | valid | cards | status |",
        "|---|---|---:|---:|---:|---|---|---|",
    ]

    for problem, rows in sorted(summary.get("problems", {}).items()):
        for row in rows:
            cards_str = ", ".join(row.get("cards", [])) or "-"
            status = row.get("status", "")
            if isinstance(status, str) and "exit_" in status:
                status = "FAILED"
            elif isinstance(status, str) and status.startswith("ok"):
                status = "OK"
            lines.append(
                f"| {problem} | {row['arm']} | {row.get('gen','')} | {row.get('pop','')} | "
                f"{row.get('best','') or '-'} | {row.get('valid','')} | {cards_str} | {status} |"
            )

    lines.extend([
        "",
        "## 代码片段",
        "",
    ])
    for problem, rows in sorted(summary.get("problems", {}).items()):
        code_rows = [r for r in rows if r.get("code_snippet") and r["code_snippet"] != "（无代码）"]
        if code_rows:
            lines.append(f"### {problem}")
            lines.append("")
            for row in code_rows[:3]:  # top 3
                lines.append(f"**{row['arm']}** (gen={row.get('gen','')}, best={row.get('best','')}):")
                lines.append(row["code_snippet"])
                lines.append("")

    lines.extend([
        "## 下一步建议",
        "",
        "（由 TOCC controller 或人工审查后填入）",
        "",
        "---",
        "",
        "*本报告自动生成于 summarize_manifest_runs.py*",
    ])

    Path(output_path).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto-summarize experiment manifest runs")
    parser.add_argument("--input", required=True, help="Path to suite output directory")
    parser.add_argument("--output", help="Output markdown path (default: INPUT/summary.md)")
    parser.add_argument("--no-card-memory-write", action="store_true", help="Skip card memory update")
    args = parser.parse_args()

    summary = summarize(args.input, no_card_memory=args.no_card_memory_write)
    if "error" in summary:
        print(f"ERROR: {summary['error']}")
        return

    output_md = args.output or str(Path(args.input) / "summary.md")
    _write_markdown(summary, output_md)

    output_json = str(Path(output_md).with_suffix(".json"))
    json.dump(summary, Path(output_json).open("w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"Summary written to {output_md}")
    print(f"Summary JSON written to {output_json}")


if __name__ == "__main__":
    main()
