"""Experiment Manifest Runner.

Reads a JSON manifest, validates it, expands the experiment matrix,
and executes runs via official_eoh_run.py.

Supports: --dry-run, --no-run, --resume, --force.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Reuse existing EOH runner CLI directly
RUNNER_MODULE = "eoh_go.experiments.eoh_single_runner"

_DEFAULT_PYTHON = os.environ.get("EOH_OFFICIAL_PYTHON", "")
_DEFAULT_ROOT = os.environ.get("EOH_OFFICIAL_ROOT", "")
VALID_ARMS = {"pure_eoh", "api_only", "literature_rag", "history_rag", "mixed_rag", "context_file"}


def _arm_card_ids(arm: dict[str, Any]) -> tuple[list[str], str]:
    if arm.get("candidate_card_ids"):
        return list(arm.get("candidate_card_ids", [])), "candidate_card_ids"
    if arm.get("selected_card_ids"):
        return list(arm.get("selected_card_ids", [])), "selected_card_ids"
    if arm.get("cards"):
        return list(arm.get("cards", [])), "cards"
    return [], "none"


def _effective_rag(manifest: dict[str, Any], arm: dict[str, Any]) -> dict[str, Any]:
    return {**manifest.get("rag", {}), **arm.get("rag", {})}


def _validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = ["suite", "problems", "arms"]
    for key in required:
        if key not in manifest:
            errors.append(f"missing required key: {key}")

    arms = manifest.get("arms", [])
    if not isinstance(arms, list) or len(arms) == 0:
        errors.append("arms must be a non-empty list")
    for i, arm in enumerate(arms):
        runner = arm.get("runner_arm", "")
        if runner not in VALID_ARMS:
            errors.append(f"arm[{i}] invalid runner_arm: {runner!r}, must be one of {sorted(VALID_ARMS)}")
        strategy = arm.get("context_strategy", "")
        card_ids, _ = _arm_card_ids(arm)
        if strategy.startswith("tocc_") and not card_ids:
            errors.append(
                f"arm[{i}] tocc_* strategy requires candidate_card_ids, selected_card_ids, or cards"
            )

    problems = manifest.get("problems", [])
    for p in problems:
        if p not in ("bp_online", "tsp_construct", "cvrp_construct"):
            errors.append(f"unknown problem: {p!r}")

    gens = manifest.get("generations", [])
    if isinstance(gens, list) and any(not isinstance(g, int) or g < 0 for g in gens):
        errors.append("generations must be a list of non-negative ints")

    return errors


def _matrix_count(manifest: dict[str, Any]) -> int:
    return (
        len(manifest.get("problems", []))
        * len(manifest.get("arms", []))
        * len(manifest.get("generations", [1]))
        * manifest.get("repeats", 1)
    )


def _write_run_index(path: Path, records: list[dict[str, Any]]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(path)


def _build_cmd(
    manifest: dict[str, Any],
    problem: str,
    arm: dict[str, Any],
    generation: int,
    repeat: int,
    output_dir: str,
    prev_run_dir: str = "",
) -> list[str]:
    cmd = [
        manifest.get("python_exe") or _DEFAULT_PYTHON or sys.executable,
        "-m",
        RUNNER_MODULE,
        "--problem", problem,
        "--arm", arm["runner_arm"],
        "--pop-size", str(manifest.get("pop_size", 4)),
        "--generations", str(generation),
        "--operators", manifest.get("operators", "i1"),
        "--n-processes", "1",
        "--eval-timeout-s", "40",
        "--llm-timeout-s", "180",
        "--run-timeout-s", str(manifest.get("run_timeout_s", 1800)),
        "--output-dir", output_dir,
        "--official-root", manifest.get("official_root") or _DEFAULT_ROOT,
        "--python", manifest.get("python_exe") or _DEFAULT_PYTHON or sys.executable,
    ]
    rag = _effective_rag(manifest, arm)
    if arm["runner_arm"] in ("literature_rag", "history_rag", "mixed_rag"):
        cmd.extend(["--rag-top-k", str(rag.get("top_k", 2))])
        cmd.extend(["--rag-max-chars", str(rag.get("max_chars", 2500))])
        if arm.get("rag_query"):
            cmd.extend(["--rag-query", arm["rag_query"]])
        card_ids, card_source = _arm_card_ids(arm)
        if card_ids:
            cmd.extend(["--selected-card-ids", ",".join(card_ids)])
            cmd.extend(["--candidate-card-source", card_source])
        effective_prev = prev_run_dir or rag.get("prev_run_dir", "")
        if effective_prev:
            cmd.extend(["--prev-run-dir", effective_prev])
        if rag.get("outcome_file"):
            cmd.extend(["--outcome-file", str(rag["outcome_file"])])
    return cmd


def main() -> None:
    parser = argparse.ArgumentParser(description="Run experiments from a manifest JSON")
    parser.add_argument("--manifest", required=True, help="Path to manifest JSON")
    parser.add_argument("--output-dir", default="eoh_go_workspace/reports/auto_experiment_reports")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--no-run", action="store_true", help="Validate manifest only")
    parser.add_argument("--resume", action="store_true", help="Skip runs with existing summary")
    parser.add_argument("--force", action="store_true", help="Skip run-count safety check")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.exists():
        sys.exit(f"Manifest not found: {args.manifest}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    errors = _validate_manifest(manifest)
    if errors:
        print("Manifest validation FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    total_runs = _matrix_count(manifest)
    max_runs = manifest.get("max_runs", 2)
    suite = manifest["suite"]
    output_root = Path(args.output_dir).resolve() / suite

    gens = manifest.get("generations", [1])
    has_deep_gen = any(g > 1 for g in gens)
    require_confirm = manifest.get("require_confirm_for_real_run", True)

    if not args.force and not args.dry_run and not args.no_run:
        if total_runs > max_runs:
            print(f"ERROR: expanded runs ({total_runs}) exceed max_runs ({max_runs}).")
            print(f"Use --dry-run to preview, --force to override, or reduce the manifest matrix.")
            sys.exit(1)
        if has_deep_gen:
            print(f"ERROR: generations contain > 1 ({gens}). Deep runs require explicit confirmation.")
            print(f"Use --force to override, or reduce max generation to 0 or 1.")
            sys.exit(1)
        if require_confirm:
            print(f"ERROR: manifest requires confirmation for real runs (require_confirm_for_real_run=true).")
            print(f"Use --force to acknowledge.")
            sys.exit(1)

    if not args.no_run:
        output_root.mkdir(parents=True, exist_ok=True)

    print(f"Suite: {suite}")
    print(f"Matrix: {len(manifest['problems'])}×{len(manifest['arms'])}×{len(manifest.get('generations',[1]))}×{manifest.get('repeats',1)} = {total_runs} runs")
    print()

    run_index: list[dict[str, Any]] = []
    index_path = output_root / "run_index.json"
    problems = manifest["problems"]
    arms = manifest["arms"]
    generations = manifest.get("generations", [0])
    repeats = manifest.get("repeats", 1)

    for p_idx, problem in enumerate(problems):
        for a_idx, arm in enumerate(arms):
            arm_problems = arm.get("problems", problems)
            if problem not in arm_problems:
                continue
            use_prev_run_dir_chain = bool(_effective_rag(manifest, arm).get("use_prev_run_dir_chain"))
            for gen in generations:
                prev_run_dir = ""
                previous_repeat_failed = False
                for rep in range(1, repeats + 1):
                    run_tag = f"run_{problem}_{arm['name']}_g{gen}_r{rep}"
                    run_out = str(output_root / run_tag)

                    if args.dry_run:
                        cmd = _build_cmd(manifest, problem, arm, gen, rep, run_out, prev_run_dir=prev_run_dir)
                        print(f"[DRY] {run_tag}")
                        print(f"  {' '.join(cmd)}")
                        print()
                        if use_prev_run_dir_chain:
                            prev_run_dir = run_out
                        continue

                    if args.no_run:
                        continue

                    summary_path = Path(run_out) / "official_eoh_run_summary.json"
                    if args.resume and summary_path.exists():
                        prev = json.loads(summary_path.read_text(encoding="utf-8"))
                        if not prev.get("failure_reason") and prev.get("run_summary", {}).get("ok"):
                            print(f"[SKIP] {run_tag} (already complete)")
                            prev_summary = prev.get("run_summary", {})
                            run_index.append(
                                {
                                    "tag": run_tag,
                                    "problem": problem,
                                    "arm": arm["name"],
                                    "generation": gen,
                                    "repeat": rep,
                                    "status": "ok",
                                    "runtime_s": prev.get("runtime_seconds"),
                                    "output_dir": run_out,
                                    "best_objective": prev_summary.get("best_objective"),
                                    "valid_candidates": prev_summary.get("valid_candidates"),
                                    "resumed_existing": True,
                                }
                            )
                            _write_run_index(index_path, run_index)
                            if use_prev_run_dir_chain:
                                prev_run_dir = run_out
                                previous_repeat_failed = False
                            continue
                        else:
                            print(f"[RETRY] {run_tag} (previous run failed: {prev.get('failure_reason','unknown')})")

                    print(f"[RUN] {run_tag}  start={time.strftime('%H:%M:%S')}")
                    cmd = _build_cmd(manifest, problem, arm, gen, rep, run_out, prev_run_dir=prev_run_dir)
                    started = time.time()
                    try:
                        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=manifest.get("run_timeout_s", 1800) + 60)
                        status = "ok" if proc.returncode == 0 else f"exit_{proc.returncode}"
                    except subprocess.TimeoutExpired:
                        status = "timeout"
                    elapsed = round(time.time() - started, 1)

                    run_record = {
                        "tag": run_tag,
                        "problem": problem,
                        "arm": arm["name"],
                        "generation": gen,
                        "repeat": rep,
                        "status": status,
                        "runtime_s": elapsed,
                        "output_dir": run_out,
                    }
                    if use_prev_run_dir_chain and prev_run_dir:
                        run_record["prev_run_dir"] = prev_run_dir
                    if use_prev_run_dir_chain and previous_repeat_failed:
                        run_record["population_chain_skipped_previous_failed"] = True
                    run_index.append(run_record)

                    run_succeeded = False
                    if summary_path.exists():
                        summary = json.loads(summary_path.read_text(encoding="utf-8"))
                        run_sum = summary.get("run_summary", {})
                        run_index[-1]["best_objective"] = run_sum.get("best_objective")
                        run_index[-1]["valid_candidates"] = run_sum.get("valid_candidates")
                        fail_reason = summary.get("failure_reason")
                        if fail_reason:
                            run_index[-1]["failure_reason"] = fail_reason
                            if status == "ok":
                                run_index[-1]["status"] = "ok_but_summary_failure"
                        run_succeeded = status == "ok" and not fail_reason and bool(run_sum.get("ok"))

                    print(f"[DONE] {run_tag}  status={status}  elapsed={elapsed}s")
                    if use_prev_run_dir_chain:
                        prev_run_dir = run_out if run_succeeded else ""
                        previous_repeat_failed = not run_succeeded
                    _write_run_index(index_path, run_index)

    if not args.dry_run and not args.no_run:
        _write_run_index(index_path, run_index)
        print(f"\nRun index written to {index_path}")


if __name__ == "__main__":
    main()
