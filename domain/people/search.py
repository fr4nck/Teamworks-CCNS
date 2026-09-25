from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher
import re
import unicodedata

from domain.people.person import Person


@dataclass(frozen=True, slots=True)
class PersonSearchResult:
    person: Person
    kind: str
    score: int


def normalize_search_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.casefold().replace("’", "'")
    value = re.sub(r"[-']", " ", value)
    return " ".join(value.split())


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(normalize_search_text(value).split())


def _person_tokens(person: Person) -> tuple[str, ...]:
    return _tokens(f"{person.first_name} {person.last_name}")


def _tokens_fit_exactly(
    query_tokens: tuple[str, ...],
    person_tokens: tuple[str, ...],
) -> bool:
    query_counts = Counter(query_tokens)
    person_counts = Counter(person_tokens)
    return all(person_counts[token] >= count for token, count in query_counts.items())


def _tokens_fit_as_prefixes(
    query_tokens: tuple[str, ...],
    person_tokens: tuple[str, ...],
) -> bool:
    remaining = list(person_tokens)
    for token in query_tokens:
        for index, candidate in enumerate(remaining):
            if candidate.startswith(token):
                remaining.pop(index)
                break
        else:
            return False
    return True


def _certain_score(query_tokens: tuple[str, ...], person_tokens: tuple[str, ...]) -> int | None:
    if not query_tokens:
        return None
    if _tokens_fit_exactly(query_tokens, person_tokens):
        return 300
    # Les préfixes servent à la saisie abrégée ("dupo", "mar"), pas à
    # transformer un patronyme complet en un autre ("martin" != "martineau").
    # Chaque token de la personne ne peut satisfaire qu'un token de la requête.
    if all(len(token) <= 4 for token in query_tokens) and _tokens_fit_as_prefixes(
        query_tokens, person_tokens
    ):
        return 200
    return None


def _exact_simple_surname_bonus(
    query_tokens: tuple[str, ...],
    person: Person,
) -> int:
    if len(query_tokens) != 1:
        return 0
    surname_tokens = _tokens(person.last_name)
    return 10 if surname_tokens == query_tokens else 0


def _suggestion_score(query_tokens: tuple[str, ...], person_tokens: tuple[str, ...]) -> int | None:
    if not query_tokens or any(len(token) < 4 for token in query_tokens):
        return None
    unmatched = []
    for token in query_tokens:
        if token in person_tokens:
            continue
        ratios = [SequenceMatcher(None, token, candidate).ratio() for candidate in person_tokens]
        best = max(ratios, default=0.0)
        if best < 0.75:
            return None
        unmatched.append(best)
    if not unmatched:
        return None
    return 100 + round(sum(unmatched) / len(unmatched) * 50)


def search_people(query: str, people: list[Person]) -> list[PersonSearchResult]:
    query_tokens = _tokens(query)
    certain: list[PersonSearchResult] = []
    suggestions: list[PersonSearchResult] = []

    for person in people:
        person_tokens = _person_tokens(person)
        score = _certain_score(query_tokens, person_tokens)
        if score is not None:
            score += _exact_simple_surname_bonus(query_tokens, person)
            certain.append(PersonSearchResult(person, "certain", score))
            continue
        suggestion_score = _suggestion_score(query_tokens, person_tokens)
        if suggestion_score is not None:
            suggestions.append(PersonSearchResult(person, "suggestion", suggestion_score))

    key = lambda result: (-result.score, normalize_search_text(result.person.display_name), str(result.person.id))
    if certain:
        return sorted(certain, key=key)
    return sorted(suggestions, key=key)
