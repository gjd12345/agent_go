from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from .schemas import CorpusItem


_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_KIND_PRIORITY = {
    "algorithm_card": 0,
    "failure_case": 1,
    "api_constraint": 2,
    "code_example": 3,
}


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text)]


def _weighted_terms(item: CorpusItem) -> Counter[str]:
    terms: Counter[str] = Counter()
    terms.update({token: 3 for token in _tokens(item.title)})
    for tag in item.tags:
        terms.update({token: 3 for token in _tokens(tag)})
    terms.update({token: 2 for token in _tokens(item.summary)})
    for constraint in item.constraints:
        terms.update({token: 2 for token in _tokens(constraint)})
    return terms


def score_item(query: str, item: CorpusItem) -> int:
    query_terms = _tokens(query)
    if not query_terms:
        return 0
    weighted = _weighted_terms(item)
    return sum(weighted.get(term, 0) for term in query_terms)


def score_corpus(query: str, corpus: list[CorpusItem]) -> list[tuple[int, CorpusItem]]:
    scored = [(score_item(query, item), item) for item in corpus]
    scored.sort(
        key=lambda pair: (
            -pair[0],
            _KIND_PRIORITY.get(pair[1].kind, 99),
            pair[1].id,
        )
    )
    return scored


def retrieve(query: str, corpus: list[CorpusItem], top_k: int = 3) -> list[CorpusItem]:
    if not corpus or top_k <= 0:
        return []

    scored = [(score, item) for score, item in score_corpus(query, corpus) if score > 0]
    return [item for _, item in scored[:top_k]]


# ---------------------------------------------------------------------------
# Phase 4a: Outcome/population-aware rerank
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RerankConfig:
    candidate_k: int | None = None
    boost_multiplier: float = 1.5
    suppress_multiplier: float = 0.3
    population_overlap_penalty: float = 0.5


_FEATURE_STOPWORDS = frozenset({
    "algorithm", "card", "history", "construct", "online",
    "api", "safety", "evolved", "insertships", "bp", "obp",
    "tsp", "cvrp", "vrp",
})


def _extract_card_features(item: CorpusItem) -> set[str]:
    tag_features = {
        tag.lower()
        for tag in item.tags
        if len(tag) >= 3 and tag.lower() not in _FEATURE_STOPWORDS
    }
    if tag_features:
        return tag_features
    raw: set[str] = set()
    raw.update(_tokens(item.id))
    raw.update(_tokens(item.title))
    raw.update(_tokens(item.summary))
    return {t for t in raw if len(t) >= 3 and t not in _FEATURE_STOPWORDS}


def _outcome_decision(summary: object) -> str:
    if isinstance(summary, dict):
        return str(summary.get("decision", "neutral"))
    return str(getattr(summary, "decision", "neutral"))


def retrieve_with_rerank(
    query: str,
    corpus: list[CorpusItem],
    top_k: int = 3,
    *,
    outcome_summaries: dict[str, object] | None = None,
    population_features: set[str] | None = None,
    config: RerankConfig | None = None,
) -> list[CorpusItem]:
    """2-stage retrieval: keyword coarse top-N → outcome/diversity rerank → top-k."""
    if not corpus or top_k <= 0:
        return []

    if not outcome_summaries and not population_features:
        return retrieve(query, corpus, top_k=top_k)

    config = config or RerankConfig()
    candidate_k = config.candidate_k or min(len(corpus), max(top_k * 3, 10))

    candidates = retrieve(query, corpus, top_k=candidate_k)
    if not candidates:
        return []

    scored: list[tuple[float, CorpusItem]] = []
    for item in candidates:
        base_score = float(score_item(query, item))
        multiplier = 1.0

        if outcome_summaries and item.id in outcome_summaries:
            decision = _outcome_decision(outcome_summaries[item.id])
            if decision == "boost":
                multiplier *= config.boost_multiplier
            elif decision == "suppress":
                multiplier *= config.suppress_multiplier

        if population_features:
            card_features = _extract_card_features(item)
            if card_features:
                normalized_pop = {f.lower() for f in population_features}
                overlap = len(card_features & normalized_pop) / len(card_features)
                multiplier *= 1.0 - overlap * config.population_overlap_penalty

        scored.append((base_score * multiplier, item))

    scored.sort(
        key=lambda pair: (
            -pair[0],
            _KIND_PRIORITY.get(pair[1].kind, 99),
            pair[1].id,
        )
    )
    return [item for _, item in scored[:top_k]]


def score_corpus_with_rerank(
    query: str,
    corpus: list[CorpusItem],
    *,
    outcome_summaries: dict[str, object] | None = None,
    population_features: set[str] | None = None,
    config: RerankConfig | None = None,
) -> list[dict]:
    """Score all items with rerank debug info for trace recording."""
    config = config or RerankConfig()
    normalized_pop = {f.lower() for f in population_features} if population_features else set()

    results = []
    for item in corpus:
        base_score = float(score_item(query, item))
        if base_score <= 0:
            continue
        multiplier = 1.0
        decision = "neutral"
        overlap = 0.0

        if outcome_summaries and item.id in outcome_summaries:
            decision = _outcome_decision(outcome_summaries[item.id])
            if decision == "boost":
                multiplier *= config.boost_multiplier
            elif decision == "suppress":
                multiplier *= config.suppress_multiplier

        if normalized_pop:
            card_features = _extract_card_features(item)
            if card_features:
                overlap = len(card_features & normalized_pop) / len(card_features)
                multiplier *= 1.0 - overlap * config.population_overlap_penalty

        results.append({
            "id": item.id,
            "kind": item.kind,
            "base_score": base_score,
            "outcome_decision": decision,
            "population_overlap": round(overlap, 3),
            "multiplier": round(multiplier, 4),
            "final_score": round(base_score * multiplier, 4),
        })

    results.sort(key=lambda r: (-r["final_score"], r["id"]))
    return results
