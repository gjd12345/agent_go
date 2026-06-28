from __future__ import annotations

import re


_CAMEL_SPLIT_RE = re.compile(r"([a-z0-9])([A-Z])")
_CODE_FEATURE_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*")
_CODE_STOPWORDS = frozenset({
    # Go keywords
    "func", "return", "var", "int", "float64", "float32", "bool", "string",
    "nil", "len", "append", "make", "range", "for", "if", "else",
    "true", "false", "err", "error", "fmt", "math", "sort",
    "package", "import", "main", "type", "struct", "interface",
    "break", "continue", "switch", "case", "default", "defer", "go",
    "chan", "map", "select", "fallthrough", "goto", "const",
    # Python keywords/builtins
    "def", "self", "none", "class", "lambda", "yield", "pass",
    "try", "except", "finally", "raise", "with", "print",
    "numpy", "array", "list", "dict", "tuple", "set", "float",
    # Common API/interface variables (not strategy features)
    "item", "items", "bins", "remaining", "capacity",
    "current", "node", "scores", "score", "result",
    "destination", "unvisited", "visited", "nodes",
    "distance", "matrix", "demands", "depot",
    "rest", "index", "value", "values", "total",
    "obj", "args", "kwargs", "data", "output", "input",
})


def _split_identifier(token: str) -> list[str]:
    """Split camelCase, snake_case, and kebab-case into parts."""
    token = _CAMEL_SPLIT_RE.sub(r"\1_\2", token)
    token = token.replace("-", "_")
    return [part.lower() for part in token.split("_") if part]


def extract_code_features(code: str) -> set[str]:
    """Extract meaningful identifier tokens from code (Go or Python)."""
    if not code:
        return set()
    tokens = _CODE_FEATURE_RE.findall(code)
    features: set[str] = set()
    for token in tokens:
        for part in _split_identifier(token):
            if len(part) >= 3 and part not in _CODE_STOPWORDS:
                features.add(part)
    return features


def load_population_features(
    population: list[dict],
    top_fraction: float = 1.0,
) -> set[str]:
    """Extract strategy features from valid individuals in a population.

    Only considers individuals with objective != None.
    top_fraction limits to the best N% by objective (lower is better).
    """
    valid = [
        individual for individual in population
        if isinstance(individual, dict)
        and individual.get("objective") is not None
        and individual.get("code")
    ]
    if not valid:
        return set()
    valid.sort(key=lambda item: item["objective"])
    count = max(1, int(len(valid) * top_fraction))
    features: set[str] = set()
    for individual in valid[:count]:
        features |= extract_code_features(individual["code"])
    return features
