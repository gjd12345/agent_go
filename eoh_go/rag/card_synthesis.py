"""Best-code → Card feedback loop.

Extracts strategy features from evolutionary best code, synthesizes
Skill Cards, and appends them to the RAG corpus so future runs can
retrieve evolved strategies.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .schemas import CorpusItem, load_corpus, save_corpus

# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

# Each feature maps to a list of lowercase substrings that signal its presence.
# Checked via simple `token in code_lower` — no regex needed.
FEATURE_PATTERNS: dict[str, list[str]] = {
    # --- Scoring strategies ---
    "nearest": ["nearest", "argmin", "closest"],
    "farthest": ["farthest", "far_first", "distant"],
    "regret": ["regret", "second_best", "second-best"],
    "savings": ["saving", "clarke", "wright"],
    "centrality": ["centrality", "closeness", "mst", "spanning"],
    # --- Distance handling ---
    "destination": ["dest", "destination", "return", "bwd", "backward"],
    "normalize": ["normalize", "range_fwd", "/ range", "[0, 1]", "[0,1]"],
    "forward_score": ["fwd_score", "forward", "dist_from_current"],
    "penalty": ["penalty", "penalize"],
    # --- Adaptive / lookahead ---
    "adaptive_weights": ["alpha", "beta", "gamma", "remaining_ratio"],
    "lookahead": ["lookahead", "look_ahead", "future"],
    "remaining_aware": ["remaining", "n_rem", "n_unvisited"],
    # --- Structural ---
    "clustering": ["cluster", "centroid", "k-means", "kmeans"],
    "capacity": ["capacity", "demand", "feasible"],
    "diffusion": ["diffusion", "discount"],
    "threshold": ["threshold"],
}

# Subset used by _get_code_family for backward compatibility.
_CODE_FAMILY_FEATURES: set[str] = {
    "nearest", "farthest", "regret", "capacity", "residual",
    "best_fit", "first_fit", "utilization", "savings", "sweep",
    "cluster", "lookahead", "two_hop", "progress", "tightness",
    "isolation", "detour", "destination", "depot", "distance",
}


def extract_strategy_features(code: str | None) -> set[str]:
    """Return the set of strategy feature names detected in *code*.

    >>> sorted(extract_strategy_features("regret = second_best - best; dest = ..."))
    ['destination', 'regret']
    """
    if not code:
        return set()
    code_lower = code.lower()
    return {name for name, tokens in FEATURE_PATTERNS.items()
            if any(tok in code_lower for tok in tokens)}


def get_code_family(code: str | None) -> set[str]:
    """Backward-compatible feature extraction (matches operator_card_controller)."""
    if not code:
        return set()
    code_lower = code.lower()
    return {f for f in _CODE_FAMILY_FEATURES if f in code_lower}


# ---------------------------------------------------------------------------
# Card synthesis
# ---------------------------------------------------------------------------

# Human-readable descriptions per feature, used to build Skill Card content.
_FEATURE_DO: dict[str, str] = {
    "destination": "minimize d(current,u) + alpha*d(u,dest), increasing alpha as fewer nodes remain",
    "normalize": "normalize forward and backward distances to [0,1] before combining",
    "adaptive_weights": "use remaining_ratio to dynamically adjust forward vs backward weights",
    "regret": "maximize regret = second_best - best and prefer high regret candidates",
    "farthest": "maximize depot/current distance early to seed distant clusters",
    "clustering": "identify unvisited node clusters; visit distant clusters before nearby ones",
    "centrality": "prefer nodes with high closeness centrality or high MST edge weight",
    "penalty": "penalize candidates very close to destination unless few nodes remain",
    "lookahead": "consider 2-step lookahead; penalize choices that strand distant nodes",
    "savings": "compute savings S(i,j) = d(ref,i)+d(ref,j)-d(i,j); merge by highest savings",
    "nearest": "select the unvisited node with minimum distance from current node",
    "capacity": "filter to feasible candidates that fit remaining vehicle capacity",
    "forward_score": "weight the direct distance from current node to candidate",
    "remaining_aware": "adapt strategy based on how many nodes remain",
    "diffusion": "propagate influence scores through nearby nodes for diversified selection",
    "threshold": "filter candidates whose score exceeds a dynamic threshold",
}

_FEATURE_WHEN: dict[str, str] = {
    "destination": "the tour must return to a destination/depot and the last edge is costly",
    "normalize": "forward and backward distances are on different scales",
    "adaptive_weights": "early tour steps should favor exploration, late steps should favor return",
    "regret": "several candidates compete and one may become costly later",
    "farthest": "distant clusters may be left until too late",
    "clustering": "unvisited nodes form spatial clusters",
    "centrality": "some nodes are more central and should be visited strategically",
    "penalty": "premature return to destination wastes tour length",
    "lookahead": "greedy choices can strand distant nodes",
    "savings": "merging separate trips can reduce total distance",
    "nearest": "a simple greedy baseline is needed",
    "capacity": "vehicle capacity constrains which customers can be served",
    "forward_score": "direct connection cost is the primary selection signal",
    "remaining_aware": "strategy should adapt as the tour progresses",
    "diffusion": "pure greedy gets stuck in local patterns",
    "threshold": "too many candidates need filtering before scoring",
}

# Problem-specific API constraints (reused from build_corpus patterns).
_PROBLEM_CONSTRAINTS: dict[str, list[str]] = {
    "tsp_construct": [
        "Return exactly one int from unvisited_nodes.",
        "Never return a visited node or destination_node.",
        "Do not mutate unvisited_nodes or distance_matrix.",
        "Keep computation bounded and deterministic.",
    ],
    "cvrp_construct": [
        "Return one int from unvisited_nodes, or depot only when intentionally ending the route.",
        "Never return an infeasible node (demand > rest_capacity).",
        "Do not mutate unvisited_nodes, demands, or distance_matrix.",
    ],
}


def _feature_hash(features: set[str], max_features: int = 3) -> str:
    """Short hash from top feature names for unique card IDs."""
    sorted_features = sorted(features)
    key = "_".join(sorted_features[:max_features])
    # Add short hash to avoid collisions when feature sets overlap
    short = hashlib.md5("_".join(sorted_features).encode()).hexdigest()[:6]
    return f"{key}_{short}"


_CARD_FEATURE_PRIORITY: list[str] = [
    "regret",
    "farthest",
    "savings",
    "clustering",
    "centrality",
    "destination",
    "capacity",
    "normalize",
    "adaptive_weights",
    "lookahead",
    "remaining_aware",
    "nearest",
    "forward_score",
    "penalty",
]


def _select_card_features(features: set[str], max_features: int = 3) -> set[str]:
    """Keep a history card as a small operator, not a full-code summary."""
    selected = [feature for feature in _CARD_FEATURE_PRIORITY if feature in features]
    selected.extend(feature for feature in sorted(features) if feature not in selected)
    return set(selected[:max_features])


def _build_title(problem: str, features: set[str]) -> str:
    """Generate a human-readable card title."""
    prefix = problem.split("_")[0].upper()  # TSP, CVRP, etc.
    # Pick the 2-3 most distinctive features
    priority = ["regret", "farthest", "destination", "normalize", "adaptive_weights",
                "clustering", "centrality", "savings", "penalty", "lookahead"]
    selected = [f for f in priority if f in features][:3]
    if not selected:
        selected = sorted(features)[:2]
    label = " ".join(w.replace("_", " ").title() for w in selected)
    return f"{prefix} {label} Evolved Card"


def _build_summary(problem: str, features: set[str]) -> str:
    """Generate a one-line summary for retrieval scoring."""
    prefix = problem.split("_")[0].upper()
    priority = ["regret", "farthest", "destination", "normalize", "adaptive_weights",
                "clustering", "centrality", "savings"]
    selected = [f for f in priority if f in features][:3]
    if not selected:
        selected = sorted(features)[:2]
    strategy_desc = " + ".join(selected)
    return f"{prefix} construction heuristic evolved from best code: {strategy_desc}."


def _build_content(problem: str, features: set[str]) -> str:
    """Generate Skill Card content (When/Do/Fallback/Safety)."""
    prefix = problem.split("_")[0].upper()

    # When: combine relevant conditions
    when_parts = []
    for f in sorted(features):
        if f in _FEATURE_WHEN:
            when_parts.append(_FEATURE_WHEN[f])
    when = "; ".join(when_parts[:3]) if when_parts else f"constructing a {prefix} solution step by step."

    # Do: combine algorithmic steps
    do_parts = []
    for f in sorted(features):
        if f in _FEATURE_DO:
            do_parts.append(_FEATURE_DO[f])
    do = ". ".join(do_parts[:4]) if do_parts else "apply the evolved scoring formula from best code."

    return (
        f"Skill: {prefix.lower()}_evolved_{'_'.join(sorted(features)[:3])}\n"
        f"When: {when}\n"
        f"Do: {do}\n"
        f"Fallback: nearest neighbor if scores tie or few nodes remain.\n"
        f"Safety: return one valid node; do not mutate inputs; keep computation bounded."
    )


def synthesize_card(
    problem: str,
    code: str,
    features: set[str] | None = None,
    run_info: dict[str, Any] | None = None,
) -> CorpusItem:
    """Synthesize a Skill Card from best code and its detected features.

    Parameters
    ----------
    problem : str
        Problem identifier (e.g. ``"tsp_construct"``).
    code : str
        The best code from an evolutionary run.
    features : set[str] | None
        Pre-extracted features; if ``None``, extracted from *code*.
    run_info : dict | None
        Optional metadata (``run_dir``, ``objective``, ``generation``).
    """
    if features is None:
        features = extract_strategy_features(code)
    if not features:
        raise ValueError("No strategy features detected in code; cannot synthesize card.")
    card_features = _select_card_features(features)

    run_info = run_info or {}
    feature_hash = _feature_hash(card_features)
    card_id = f"history_{problem}_{feature_hash}"
    source_path = str(run_info.get("run_dir", "auto_synthesized"))

    return CorpusItem(
        id=card_id,
        kind="algorithm_card",
        title=_build_title(problem, card_features),
        tags=[problem.split("_")[0], "construct", "evolved"] + sorted(card_features),
        source_path=source_path,
        summary=_build_summary(problem, card_features),
        constraints=_PROBLEM_CONSTRAINTS.get(problem, []),
        content=_build_content(problem, card_features),
    )


# ---------------------------------------------------------------------------
# Corpus persistence
# ---------------------------------------------------------------------------

def append_card_to_corpus(card: CorpusItem, corpus_dir: str | Path) -> bool:
    """Append *card* to ``algorithm_cards.jsonl`` if not already present.

    Returns ``True`` if the card was written, ``False`` if it was a duplicate.
    """
    corpus_path = Path(corpus_dir) / "algorithm_cards.jsonl"
    existing = load_corpus(corpus_path) if corpus_path.exists() else []
    existing_ids = {item.id for item in existing}
    if card.id in existing_ids:
        return False
    existing.append(card)
    save_corpus(existing, corpus_path)
    return True
