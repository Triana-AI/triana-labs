"""Executable population membership artifacts for frozen measurements."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Any


CLASSIFIER_VERSION = "population-classifier-v0.1"
_WORD_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to",
    "user", "customer", "request", "requests", "want", "wants", "with",
}


@dataclass(frozen=True, slots=True)
class PopulationClassifier:
    """A small, inspectable classifier that can run on unseen trace text."""

    population_id: str
    population_label: str
    include_terms: tuple[str, ...]
    exclude_terms: tuple[str, ...]
    minimum_matches: int
    unknown_on_empty: bool
    compiler_version: str = CLASSIFIER_VERSION

    @property
    def artifact_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(asdict(self), sort_keys=True).encode("utf-8")
        ).hexdigest()

    def classify(self, text: str | None) -> str:
        normalized = _tokens(text or "")
        if not normalized:
            return "UNKNOWN" if self.unknown_on_empty else "OUT"
        if any(term in normalized for term in self.exclude_terms):
            return "OUT"
        matches = sum(term in normalized for term in self.include_terms)
        return "IN" if matches >= self.minimum_matches else "OUT"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"artifact_hash": self.artifact_hash}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "PopulationClassifier":
        """Reconstruct a frozen classifier from its to_dict() form.

        artifact_hash is a derived property, not a field; drop it on the way in.
        """
        allowed = {
            "population_id",
            "population_label",
            "include_terms",
            "exclude_terms",
            "minimum_matches",
            "unknown_on_empty",
            "compiler_version",
        }
        payload = {key: item for key, item in value.items() if key in allowed}
        for key in ("include_terms", "exclude_terms"):
            payload[key] = tuple(payload.get(key, ()))
        return cls(**payload)


def compile_population_classifier(population: dict[str, Any]) -> PopulationClassifier:
    """Compile deterministic vocabulary from a reviewed population definition."""
    source = " ".join(
        [
            str(population.get("label", "")),
            str(population.get("definition", "")),
            *[str(value) for value in population.get("representative_demands", [])],
            *[str(value) for value in population.get("member_labels", [])],
        ]
    )
    counts: dict[str, int] = {}
    for token in _token_list(source):
        if token in _STOPWORDS or len(token) < 3:
            continue
        counts[token] = counts.get(token, 0) + 1
    required = []
    for demand in population.get("representative_demands", [])[:4]:
        required.extend(
            token for token in _token_list(str(demand))
            if token not in _STOPWORDS and len(token) >= 3
        )
    ranked = [token for token, _ in sorted(counts.items(), key=lambda row: (-row[1], row[0]))]
    include_terms = tuple(dict.fromkeys([*required, *ranked]))[:40]
    return PopulationClassifier(
        population_id=str(population["population_id"]),
        population_label=str(population["label"]),
        include_terms=include_terms,
        exclude_terms=(),
        minimum_matches=1,
        unknown_on_empty=True,
    )


def classifier_fixture_results(
    classifier: PopulationClassifier,
    population: dict[str, Any],
) -> dict[str, Any]:
    """Exercise positive, negative, empty, malformed, and repeat fixtures."""
    positives = [str(value) for value in population.get("representative_demands", [])[:3]]
    if not positives:
        positives = [str(population.get("label", ""))]
    fixtures = [
        *[("positive", value, "IN") for value in positives],
        ("negative", "Quantum volcano weather forecast unrelated topic.", "OUT"),
        ("empty", "", "UNKNOWN"),
        ("malformed", "{} [] null", "OUT"),
    ]
    rows = []
    for kind, text, expected in fixtures:
        first = classifier.classify(text)
        second = classifier.classify(text)
        rows.append(
            {
                "kind": kind,
                "text": text,
                "expected": expected,
                "observed": first,
                "stable": first == second,
                "passed": first == expected,
            }
        )
    return {
        "classifier_hash": classifier.artifact_hash,
        "fixtures": rows,
        "all_stable": all(row["stable"] for row in rows),
        "all_passed": all(row["passed"] for row in rows),
    }


def _tokens(value: str) -> set[str]:
    return set(_WORD_RE.findall(value.lower()))


def _token_list(value: str) -> list[str]:
    return _WORD_RE.findall(value.lower())
