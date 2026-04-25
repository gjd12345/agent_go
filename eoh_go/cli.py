from __future__ import annotations

import argparse
import json
from pathlib import Path

from .candidates import add_candidate, list_candidates
from .evolution import analyze_latest_run, initialize_workspace, run_round
from .memory import append_research_note, read_text_file, write_text_file
from .paths import EOHGoPaths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="轻量 EOH 自动代码进化框架")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")

    run_parser = sub.add_parser("run-round")
    run_parser.add_argument("--dataset", action="append", default=[])
    run_parser.add_argument("--problem", action="append", default=[])
    run_parser.add_argument("--fixed-t", type=int, default=1)
    run_parser.add_argument("--mode", default="eoh_auto")
    run_parser.add_argument("--generation-size", type=int, default=5)
    run_parser.add_argument("--generator", choices=["agent_eoh", "seed_only"], default="agent_eoh")
    run_parser.add_argument("--no-seed-fallback", action="store_true")
    run_parser.add_argument("--dataset-density", default="d25")
    run_parser.add_argument("--sim-time-interval", type=int, default=1)
    run_parser.add_argument("--arrival-scale", type=float, default=1.0)
    run_parser.add_argument("--use-density-source-dirs", action="store_true")

    sub.add_parser("analyze-latest")

    add_parser = sub.add_parser("add-candidate")
    add_parser.add_argument("--candidate-id", required=True)
    add_parser.add_argument("--algorithm", required=True)
    add_parser.add_argument("--target-file", required=True)
    add_parser.add_argument("--code-file", required=True)
    add_parser.add_argument("--rationale", default="")

    sub.add_parser("list-candidates")

    read_parser = sub.add_parser("read-note")
    read_parser.add_argument("--kind", choices=["plan", "memory", "research"], required=True)

    write_parser = sub.add_parser("write-note")
    write_parser.add_argument("--kind", choices=["plan", "memory"], required=True)
    write_parser.add_argument("--content-file", required=True)

    research_parser = sub.add_parser("append-research")
    research_parser.add_argument("--title", required=True)
    research_parser.add_argument("--content-file", required=True)

    return parser


def resolve_note_path(paths: EOHGoPaths, kind: str) -> Path:
    if kind == "plan":
        return paths.plan_path
    if kind == "memory":
        return paths.memory_path
    return paths.research_notes_path


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    paths = EOHGoPaths(root=root)

    if args.command == "init":
        initialize_workspace(paths)
        print(json.dumps({"workspace": str(paths.workspace)}, ensure_ascii=False, indent=2))
        return

    if args.command == "run-round":
        datasets = args.dataset or None
        problems = args.problem or None
        result = run_round(
            paths,
            datasets=datasets,
            problems=problems,
            fixed_t=args.fixed_t,
            mode=args.mode,
            generation_size=args.generation_size,
            generator=args.generator,
            include_seed=not args.no_seed_fallback,
            dataset_density=args.dataset_density,
            sim_time_interval=args.sim_time_interval,
            arrival_scale=args.arrival_scale,
            use_density_source_dirs=args.use_density_source_dirs,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "analyze-latest":
        result = analyze_latest_run(paths)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "add-candidate":
        code = Path(args.code_file).read_text(encoding="utf-8")
        path = add_candidate(
            paths,
            candidate_id=args.candidate_id,
            algorithm=args.algorithm,
            target_file=args.target_file,
            code=code,
            rationale=args.rationale,
        )
        print(json.dumps({"candidate_path": str(path)}, ensure_ascii=False, indent=2))
        return

    if args.command == "list-candidates":
        print(json.dumps(list_candidates(paths), ensure_ascii=False, indent=2))
        return

    if args.command == "read-note":
        note_path = resolve_note_path(paths, args.kind)
        print(read_text_file(note_path))
        return

    if args.command == "write-note":
        note_path = resolve_note_path(paths, args.kind)
        content = Path(args.content_file).read_text(encoding="utf-8")
        write_text_file(note_path, content)
        print("OK")
        return

    if args.command == "append-research":
        content = Path(args.content_file).read_text(encoding="utf-8")
        append_research_note(paths.research_notes_path, args.title, content)
        print("OK")
        return


if __name__ == "__main__":
    main()
