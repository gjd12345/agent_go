from __future__ import annotations

import json
import re
from pathlib import Path

from .schemas import CorpusItem, load_corpus, save_corpus


CORPUS_FILES = {
    "code_example": "code_examples.jsonl",
    "algorithm_card": "algorithm_cards.jsonl",
    "api_constraint": "api_constraints.jsonl",
    "failure_case": "failure_cases.jsonl",
}

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
    root = Path(project_root).resolve()
    seed_path = root / "Agent_EOH" / "eoh" / "src" / "eoh" / "examples" / "user_insertships_go" / "seeds_insertships_go_sa.json"
    if not seed_path.exists():
        return []
    try:
        payload = json.loads(seed_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []

    items: list[CorpusItem] = []
    for index, entry in enumerate(payload, start=1):
        if not isinstance(entry, dict):
            continue
        algorithm = str(entry.get("algorithm") or f"Seed InsertShips algorithm {index}")
        code = str(entry.get("code") or "")
        items.append(
            CorpusItem(
                id=f"sa_seed_{index}",
                kind="algorithm_card",
                title=algorithm,
                tags=["insertships", "sa", "fallback", "seed"],
                source_path=_source_path(root, seed_path),
                summary="SA baseline or seed heuristic for safe InsertShips generation.",
                constraints=list(_STANDARD_INSERTSHIPS_CONSTRAINTS),
                content=code,
            )
        )
    return items


def build_api_constraints(project_root: str | Path) -> list[CorpusItem]:
    root = Path(project_root).resolve()
    main_path = root / "main.go"
    content = main_path.read_text(encoding="utf-8", errors="replace") if main_path.exists() else ""
    snippet = content[:6000].strip()
    description = (
        "InsertShips must return a Dispatch, preserve all customer assignments, use Dispatch/Assign route APIs "
        "consistently, and refresh total cost before returning."
    )
    return [
        CorpusItem(
            id="insertships_api_contract",
            kind="api_constraint",
            title="InsertShips Dispatch API contract",
            tags=["insertships", "dispatch", "assign", "api", "renewntotalcost"],
            source_path=_source_path(root, main_path) if main_path.exists() else "main.go",
            summary=description,
            constraints=list(_STANDARD_INSERTSHIPS_CONSTRAINTS),
            content=snippet or description,
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
    grouped = {
        "code_example": build_code_examples(project_root),
        "algorithm_card": build_algorithm_cards(project_root),
        "api_constraint": build_api_constraints(project_root),
        "failure_case": build_failure_cases(project_root),
    }
    written: list[Path] = []
    for kind, filename in CORPUS_FILES.items():
        path = target_dir / filename
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
