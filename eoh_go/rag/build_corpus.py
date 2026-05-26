from __future__ import annotations

import re
from pathlib import Path

from .schemas import CorpusItem, load_corpus, save_corpus


CORPUS_FILES = {
    "code_example": "code_examples.jsonl",
    "algorithm_card": "algorithm_cards.jsonl",
    "api_constraint": "api_constraints.jsonl",
    "failure_case": "failure_cases.jsonl",
}

LITERATURE_IDS = {"nearest_insertion", "farthest_insertion", "solomon_i1", "regret2_insertion", "cw_savings"}

_STANDARD_INSERTSHIPS_CONSTRAINTS = [
    "Never skip orders unless no feasible assignment exists.",
    "Rollback tentative insertions when a candidate route fails.",
    "Call RenewnTotalCost before returning Dispatch.",
    "Avoid negative, suspiciously low, timeout, and missing-result candidates.",
]


def default_corpus_dir(project_root: str | Path) -> Path:
    return (Path(project_root) / "eoh_go_workspace" / "rag" / "corpus").resolve()


def resolve_corpus_dir(project_root: str | Path, corpus_dir: str | Path | None) -> Path:
    root = Path(project_root).resolve()
    allowed_dir = default_corpus_dir(root)
    if not corpus_dir:
        candidate = allowed_dir
    else:
        raw = Path(corpus_dir)
        if raw.is_absolute():
            candidate = raw.resolve()
        else:
            root_relative = (root / raw).resolve()
            try:
                root_relative.relative_to(allowed_dir)
                candidate = root_relative
            except ValueError:
                candidate = (allowed_dir / raw).resolve()

    try:
        candidate.relative_to(allowed_dir)
    except ValueError:
        raise ValueError("RAG corpus directory must stay under eoh_go_workspace/rag/corpus")
    return candidate


def _source_path(project_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path.resolve())


def _title_from_id(item_id: str) -> str:
    return item_id.replace("_", " ").replace("-", " ").title()


def _tags_from_name(name: str) -> list[str]:
    tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9]+", name)]
    tags = ["insertships"]
    for token in tokens:
        if token not in tags:
            tags.append(token)
    return tags


def build_code_examples(project_root: str | Path) -> list[CorpusItem]:
    root = Path(project_root).resolve()
    source_dir = root / "eoh_go_workspace" / "candidate_sources"
    items: list[CorpusItem] = []
    for path in sorted(source_dir.glob("*.go")):
        content = path.read_text(encoding="utf-8", errors="replace").strip()
        if not content:
            continue
        item_id = path.stem
        items.append(
            CorpusItem(
                id=item_id,
                kind="code_example",
                title=_title_from_id(item_id),
                tags=_tags_from_name(item_id),
                source_path=_source_path(root, path),
                summary=f"Candidate InsertShips heuristic from {path.name}.",
                constraints=list(_STANDARD_INSERTSHIPS_CONSTRAINTS),
                content=content,
            )
        )
    return items


def build_algorithm_cards(project_root: str | Path) -> list[CorpusItem]:
    """Algorithm cards are curated manually; SA seed content moved to api_constraint."""
    return []


def filter_corpus_by_mode(corpus: list[CorpusItem], mode: str) -> list[CorpusItem]:
    normalized = mode.strip().lower() if mode else "mixed"
    if normalized == "mixed":
        return list(corpus)
    if normalized == "history":
        return [item for item in corpus if item.id not in LITERATURE_IDS]
    if normalized == "literature":
        return [item for item in corpus if item.id in LITERATURE_IDS or item.kind in {"api_constraint", "failure_case"}]
    raise ValueError("RAG mode must be one of: history, literature, mixed")


def build_api_constraints(project_root: str | Path) -> list[CorpusItem]:
    root = Path(project_root).resolve()
    content = (
        "API: insertships_skeleton\n"
        "Rules:\n"
        "- Save Assign state before trial AddShip.\n"
        "- If AddShip succeeds: GenRoute, record cost_delta, then RemoveShip+GenRoute to undo.\n"
        "- Commit: re-apply best (Assign, position) once. GenRoute after final insert.\n"
        "- Every order needs a fallback insertion path.\n"
        "- Call RenewnTotalCost exactly once before return."
    )
    return [
        CorpusItem(
            id="insertships_api_skeleton",
            kind="api_constraint",
            title="InsertShips Go API skeleton",
            tags=["insertships", "api", "safety"],
            source_path="curated",
            summary="Safe Go API call sequence: save state, trial insert, record delta, rollback, commit best, RenewnTotalCost.",
            constraints=[
                "Every order MUST be inserted; fallback to new Assign if no existing Assign works.",
                "RenewnTotalCost() exactly once before return.",
            ],
            content=content,
        )
    ]


def build_failure_cases(project_root: str | Path) -> list[CorpusItem]:
    root = Path(project_root).resolve()
    guard_path = root / "eoh_go" / "eoh_runner" / "candidate_guard.py"
    guard_text = guard_path.read_text(encoding="utf-8", errors="replace") if guard_path.exists() else ""
    source = _source_path(root, guard_path) if guard_path.exists() else "eoh_go/eoh_runner/candidate_guard.py"
    return [
        CorpusItem(
            id="suspicious_low_objective",
            kind="failure_case",
            title="Suspiciously low objective",
            tags=["insertships", "suspicious-low", "guard", "objective"],
            source_path=source,
            summary="Very low objective values can indicate skipped orders, broken costs, or incomplete evaluation.",
            constraints=[
                "Do not treat suspicious-low objective values as valid unless guard checks pass.",
                "Preserve all orders and recompute total cost.",
            ],
            content=guard_text,
        ),
        CorpusItem(
            id="negative_or_missing_result",
            kind="failure_case",
            title="Negative cost or missing result",
            tags=["insertships", "negative", "missing-result", "guard"],
            source_path=source,
            summary="Negative costs and missing results are invalid candidate outcomes.",
            constraints=["Return a complete Dispatch object.", "Do not allow negative cost artifacts."],
            content=guard_text,
        ),
        CorpusItem(
            id="timeout_or_unbounded_search",
            kind="failure_case",
            title="Timeout or unbounded search",
            tags=["insertships", "timeout", "guard", "fallback"],
            source_path=source,
            summary="Expensive exhaustive insertion can timeout on dense or large instances.",
            constraints=["Limit candidate route scans.", "Use bounded top-k attempts and safe fallback logic."],
            content=guard_text,
        ),
    ]


def build_all_corpora(project_root: str | Path, corpus_dir: str | Path | None = None) -> list[Path]:
    target_dir = resolve_corpus_dir(project_root, corpus_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    algorithm_path = target_dir / CORPUS_FILES["algorithm_card"]
    curated_algorithm_cards: list[CorpusItem] = []
    if algorithm_path.exists():
        existing_algorithm_cards = [item for item in load_corpus(algorithm_path) if item.id in LITERATURE_IDS]
        curated_algorithm_cards = existing_algorithm_cards
        lit_count = len({item.id for item in curated_algorithm_cards})
        if lit_count < 5:
            print("Warning: algorithm_cards.jsonl has fewer than 5 curated literature cards.")
    else:
        print("Warning: algorithm_cards.jsonl missing; writing empty curated algorithm card corpus.")

    grouped = {
        "code_example": build_code_examples(project_root),
        "algorithm_card": curated_algorithm_cards,
        "api_constraint": build_api_constraints(project_root),
        "failure_case": build_failure_cases(project_root),
    }

    written: list[Path] = []
    for kind, filename in CORPUS_FILES.items():
        path = target_dir / filename
        if kind != "algorithm_card" or not algorithm_path.exists():
            save_corpus(grouped[kind], path)
        written.append(path)
    return written


def load_all_corpora(project_root: str | Path, corpus_dir: str | Path | None = None) -> list[CorpusItem]:
    target_dir = resolve_corpus_dir(project_root, corpus_dir)
    expected = [target_dir / filename for filename in CORPUS_FILES.values()]
    if any(not path.exists() for path in expected):
        build_all_corpora(project_root, target_dir)

    items: list[CorpusItem] = []
    for path in expected:
        items.extend(load_corpus(path))
    return items
