from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


DEFAULT_CELLS = [
    ("rc102.json", "d50", 0.7),
    ("rc102.json", "d75", 1.0),
    ("rc104.json", "d50", 0.8),
    ("rc104.json", "d50", 0.6),
    ("rc104.json", "d75", 0.8),
    ("rc105.json", "d50", 0.9),
    ("rc105.json", "d75", 0.9),
    ("rc105.json", "d75", 0.6),
]


def _parse_cell(value: str) -> tuple[str, str, float]:
    problem, density, scale = value.split(":", 2)
    return problem, density, float(scale)


def _latest_result_file(out_root: Path, before: set[Path]) -> Path | None:
    candidates = set(out_root.glob("run_*/eoh_arrival_grid_results.json")) - before
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run selected EOH grid cells as repeat validation.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--cell", action="append", help="Format: rc102.json:d50:0.7")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--llm-model", default="deepseek-v4-flash")
    parser.add_argument("--output-dir", default="eoh_go_workspace/reports/tables/eoh_selected_repeats")
    parser.add_argument("--generations", type=int, default=1)
    parser.add_argument("--pop-size", type=int, default=4)
    parser.add_argument("--eva-timeout", type=int, default=120)
    parser.add_argument("--run-timeout-s", type=int, default=60)
    parser.add_argument("--objective-res-weight", type=float, default=0.2)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_root = (root / args.output_dir).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    cells = [_parse_cell(item) for item in args.cell] if args.cell else DEFAULT_CELLS
    run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    manifest_path = out_root / f"selected_repeats_{run_tag}.json"
    records = []

    for repeat in range(1, args.repeats + 1):
        for problem, density, scale in cells:
            existing = set(out_root.glob("run_*/eoh_arrival_grid_results.json"))
            start = time.time()
            cmd = [
                sys.executable,
                "-m",
                "eoh_go.experiments.eoh_arrival_grid",
                "--root",
                str(root),
                "--problem",
                problem,
                "--density",
                density,
                "--arrival-scale",
                f"{scale:.1f}",
                "--use-density-source-dirs",
                "--llm-model",
                args.llm_model,
                "--output-dir",
                args.output_dir,
                "--generations",
                str(args.generations),
                "--pop-size",
                str(args.pop_size),
                "--eva-timeout",
                str(args.eva_timeout),
                "--run-timeout-s",
                str(args.run_timeout_s),
                "--objective-res-weight",
                str(args.objective_res_weight),
                "--suspicious-low-ratio",
                "0.3",
            ]
            print(f"[repeat {repeat}] {problem} {density} t={scale:.1f}", flush=True)
            completed = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
            result_file = _latest_result_file(out_root, existing)
            record = {
                "repeat": repeat,
                "problem": problem,
                "density": density,
                "arrival_scale": scale,
                "return_code": completed.returncode,
                "duration_s": time.time() - start,
                "result_file": str(result_file) if result_file else None,
                "stdout_tail": completed.stdout[-4000:],
                "stderr_tail": completed.stderr[-4000:],
            }
            if result_file:
                try:
                    payload = json.loads(result_file.read_text(encoding="utf-8"))
                    rows = payload.get("rows", [])
                    record["row"] = rows[0] if rows else None
                except Exception as exc:
                    record["read_error"] = repr(exc)
            records.append(record)
            manifest_path.write_text(json.dumps({"records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({k: record.get(k) for k in ["return_code", "duration_s", "result_file"]}, ensure_ascii=False), flush=True)

    manifest_path.write_text(json.dumps({"records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote selected repeat manifest to {manifest_path}")


if __name__ == "__main__":
    main()
