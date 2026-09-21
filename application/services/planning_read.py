"""Lecture neutre du Planning à partir des Présences.

Le module ne dépend ni de wxPython ni de Qt ni de GestionDB. Il expose une
projection métier stable que plusieurs interfaces peuvent consommer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from application.services.read_result import (
    ReadCompleteness,
    ReadIssue,
    ReadIssueCode,
    ReadResult,
    ReadRetryPolicy,
    ReadSourceRequirement,
    optional_source_unavailable,
    required_source_unavailable,
)


@dataclass(frozen=True)
class PresenceQuery:
    start_date: date
    end_date: date
    person_ids: tuple[int, ...] = ()
    category_ids: tuple[int, ...] = ()


@dataclass(frozen=True)
class PlanningPresence:
    presence_id: int
    person_id: int
    presence_date: date
    start_time: str
    end_time: str
    duration_minutes: int
    category_id: int
    title: str


@dataclass(frozen=True)
class PlanningPerson:
    person_id: int
    display_name: str


@dataclass(frozen=True)
class PresenceCategory:
    category_id: int
    name: str
    color: str = ""


@dataclass(frozen=True)
class VacationPeriod:
    vacation_id: int
    name: str
    start_date: date
    end_date: date


@dataclass(frozen=True)
class PlanningSnapshot:
    query: PresenceQuery
    presences: tuple[PlanningPresence, ...]
    people: tuple[PlanningPerson, ...]
    categories: tuple[PresenceCategory, ...]
    vacations: tuple[VacationPeriod, ...] = ()


class PlanningReadPort(Protocol):
    def read_presences(
        self,
        query: PresenceQuery,
    ) -> tuple[PlanningPresence, ...]:
        ...

    def read_people(
        self,
        query: PresenceQuery,
    ) -> tuple[PlanningPerson, ...]:
        ...

    def read_categories(
        self,
        query: PresenceQuery,
    ) -> tuple[PresenceCategory, ...]:
        ...

    def read_vacations(
        self,
        query: PresenceQuery,
    ) -> tuple[VacationPeriod, ...]:
        ...


def _invalid_query(message: str) -> ReadResult[PlanningSnapshot]:
    return ReadResult.failed(
        issues=(
            ReadIssue(
                code=ReadIssueCode.INVALID_QUERY,
                message=message,
                source="query",
                requirement=ReadSourceRequirement.REQUIRED,
                retry_policy=ReadRetryPolicy.NEVER,
            ),
        ),
    )


def validate_presence_query(query: PresenceQuery) -> ReadResult[PlanningSnapshot] | None:
    if type(query.start_date) is not date or type(query.end_date) is not date:
        return _invalid_query("La période du planning est invalide.")

    if query.end_date < query.start_date:
        return _invalid_query(
            "La date de fin du planning doit être postérieure ou égale à la date de début."
        )

    for person_id in query.person_ids:
        if (
            not isinstance(person_id, int)
            or isinstance(person_id, bool)
            or person_id <= 0
        ):
            return _invalid_query("Un identifiant de personne est invalide.")

    for category_id in query.category_ids:
        if (
            not isinstance(category_id, int)
            or isinstance(category_id, bool)
            or category_id <= 0
        ):
            return _invalid_query("Un identifiant de catégorie est invalide.")

    return None


def read_planning(
    port: PlanningReadPort,
    *,
    query: PresenceQuery,
) -> ReadResult[PlanningSnapshot]:
    """Lit un snapshot Planning sans confondre lecture et transaction d'écriture."""

    invalid = validate_presence_query(query)
    if invalid is not None:
        return invalid

    required_values: dict[str, object] = {}
    required_issues: list[ReadIssue] = []

    required_sources = (
        ("presences", port.read_presences, "Les présences n'ont pas pu être chargées."),
        ("people", port.read_people, "Les personnes n'ont pas pu être chargées."),
        ("categories", port.read_categories, "Les catégories n'ont pas pu être chargées."),
    )

    for source, reader, message in required_sources:
        try:
            required_values[source] = tuple(reader(query))
        except Exception as exc:
            required_issues.append(
                required_source_unavailable(
                    source=source,
                    message=message,
                    diagnostic=repr(exc),
                    retry_policy=ReadRetryPolicy.AUTOMATIC_ONCE,
                )
            )

    if required_issues:
        return ReadResult.failed(
            issues=tuple(required_issues),
        )

    optional_issues: list[ReadIssue] = []
    vacations: tuple[VacationPeriod, ...] = ()

    try:
        vacations = tuple(port.read_vacations(query))
    except Exception as exc:
        optional_issues.append(
            optional_source_unavailable(
                source="vacations",
                message="Les périodes de vacances n'ont pas pu être chargées.",
                diagnostic=repr(exc),
                retry_policy=ReadRetryPolicy.AUTOMATIC_ONCE,
            )
        )

    snapshot = PlanningSnapshot(
        query=query,
        presences=required_values["presences"],
        people=required_values["people"],
        categories=required_values["categories"],
        vacations=vacations,
    )

    if optional_issues:
        return ReadResult.partial_result(
            value=snapshot,
            issues=tuple(optional_issues),
        )

    return ReadResult.complete(snapshot)
