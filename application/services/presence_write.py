"""Métier et écritures transactionnelles des Présences, sans wx ni Qt."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from application.services.service_result import (
    BatchDisposition,
    BatchIssue,
    BatchItemRef,
    BatchReport,
    ServiceError,
    ServiceErrorCode,
    ServiceResult,
)
from application.services.transactional_write import is_valid_target_id
from domain.common.duration import parse_clock_time


_MIN_DURATION_MINUTES = 15


@dataclass(frozen=True)
class PresenceSnapshot:
    presence_id: int
    person_id: int
    presence_date: date
    start_time: str
    end_time: str
    category_id: int
    title: str
    revision: str = ""


@dataclass(frozen=True)
class PresenceTarget:
    person_id: int
    presence_date: date


@dataclass(frozen=True)
class PresenceBatchSnapshot:
    created: tuple[PresenceSnapshot, ...]
    skipped_overlaps: tuple[PresenceTarget, ...]


@dataclass(frozen=True)
class PresenceCreateCommand:
    targets: tuple[PresenceTarget, ...]
    start_time: str
    end_time: str
    category_id: int
    title: str = ""


@dataclass(frozen=True)
class PresenceUpdateCommand:
    presence_id: int
    start_time: str
    end_time: str
    category_id: int
    title: str = ""
    expected_revision: str | None = None


@dataclass(frozen=True)
class PresenceDeleteCommand:
    presence_id: int
    confirmed: bool = False
    expected_revision: str | None = None


class PresenceWritePort(Protocol):
    def person_exists(self, person_id: int) -> bool:
        ...

    def presence_exists(self, presence_id: int) -> bool:
        ...

    def read_presence(self, presence_id: int) -> PresenceSnapshot | None:
        ...

    def find_overlap(
        self,
        *,
        person_id: int,
        presence_date: date,
        start_time: str,
        end_time: str,
        exclude_presence_id: int | None = None,
    ) -> int | None:
        ...

    def insert_presence(
        self,
        *,
        person_id: int,
        presence_date: date,
        start_time: str,
        end_time: str,
        category_id: int,
        title: str,
    ) -> int:
        ...

    def update_presence(
        self,
        *,
        presence_id: int,
        start_time: str,
        end_time: str,
        category_id: int,
        title: str,
        expected: PresenceSnapshot | None = None,
    ) -> int:
        ...

    def delete_presence(
        self,
        presence_id: int,
        *,
        expected: PresenceSnapshot | None = None,
    ) -> int:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...


def normalize_presence_title(value: object) -> str:
    """Reproduit le contrat historique de normalisation de la légende."""
    if value is None:
        return ""
    text = str(value).strip()
    if text in ("", "()", "( )"):
        return ""
    return text


def _validation_error(field: str, message: str) -> ServiceError:
    return ServiceError(
        code=ServiceErrorCode.VALIDATION_ERROR,
        message=message,
        field=field,
    )


def _validate_time_window(
    start_time: object,
    end_time: object,
) -> tuple[ServiceError, ...]:
    errors: list[ServiceError] = []

    start = parse_clock_time(start_time, "start_time")
    end = parse_clock_time(end_time, "end_time")

    if not start.ok:
        errors.append(
            _validation_error(
                "start_time",
                start.error.message if start.error else "Heure de début invalide.",
            )
        )
    if not end.ok:
        errors.append(
            _validation_error(
                "end_time",
                end.error.message if end.error else "Heure de fin invalide.",
            )
        )
    if not start.ok or not end.ok:
        return tuple(errors)

    if end.value_minutes < start.value_minutes:
        errors.append(
            _validation_error(
                "end_time",
                "L'heure de fin doit être supérieure à l'heure de début.",
            )
        )
        return tuple(errors)

    duration = end.value_minutes - start.value_minutes
    if duration < _MIN_DURATION_MINUTES:
        errors.append(
            _validation_error(
                "duration",
                "La durée de la présence doit être au minimum de 15 minutes.",
            )
        )

    return tuple(errors)


def validate_presence_create_command(
    command: PresenceCreateCommand,
) -> tuple[ServiceError, ...]:
    errors: list[ServiceError] = []

    if not command.targets:
        errors.append(
            _validation_error(
                "targets",
                "Au moins une date et une personne doivent être sélectionnées.",
            )
        )

    for target in command.targets:
        if not is_valid_target_id(target.person_id):
            errors.append(
                _validation_error(
                    "person_id",
                    "Une personne sélectionnée possède un identifiant invalide.",
                )
            )
        if type(target.presence_date) is not date:
            errors.append(
                _validation_error(
                    "presence_date",
                    "Une date de présence est invalide.",
                )
            )

    errors.extend(_validate_time_window(command.start_time, command.end_time))

    if not is_valid_target_id(command.category_id):
        errors.append(
            _validation_error(
                "category_id",
                "La catégorie de présence est obligatoire.",
            )
        )

    if len(normalize_presence_title(command.title)) > 200:
        errors.append(
            _validation_error(
                "title",
                "La légende de la présence ne peut pas dépasser 200 caractères.",
            )
        )

    return tuple(errors)


def validate_presence_update_command(
    command: PresenceUpdateCommand,
) -> tuple[ServiceError, ...]:
    errors: list[ServiceError] = []

    if not is_valid_target_id(command.presence_id):
        errors.append(
            ServiceError(
                code=ServiceErrorCode.INVALID_TARGET_ID,
                message="Identifiant historique de présence invalide.",
                field="presence_id",
            )
        )

    errors.extend(_validate_time_window(command.start_time, command.end_time))

    if not is_valid_target_id(command.category_id):
        errors.append(
            _validation_error(
                "category_id",
                "La catégorie de présence est obligatoire.",
            )
        )

    if len(normalize_presence_title(command.title)) > 200:
        errors.append(
            _validation_error(
                "title",
                "La légende de la présence ne peut pas dépasser 200 caractères.",
            )
        )

    return tuple(errors)


def _collapse_validation_errors(errors: tuple[ServiceError, ...]) -> ServiceError:
    first = errors[0]
    return ServiceError(
        code=first.code,
        message=" ".join(error.message for error in errors),
        field=first.field,
        target_id=first.target_id,
    )


def _safe_rollback(port: PresenceWritePort) -> None:
    try:
        port.rollback()
    except Exception:
        pass


def create_presences(
    port: PresenceWritePort,
    *,
    command: PresenceCreateCommand,
) -> ServiceResult[PresenceBatchSnapshot]:
    """Crée un lot de présences avec un seul commit.

    Un chevauchement est un skip métier individuel. Toute panne technique
    annule en revanche toutes les insertions du lot.
    """

    errors = validate_presence_create_command(command)
    if errors:
        return ServiceResult.failure(
            error=_collapse_validation_errors(errors),
        )

    normalized_title = normalize_presence_title(command.title)

    try:
        for target in command.targets:
            if not port.person_exists(target.person_id):
                return ServiceResult.failure(
                    error=ServiceError(
                        code=ServiceErrorCode.TARGET_NOT_FOUND,
                        message="La personne sélectionnée n'existe plus.",
                        field="person_id",
                        target_id=target.person_id,
                    ),
                )
    except Exception as exc:
        return ServiceResult.failure(
            error=ServiceError(
                code=ServiceErrorCode.DATABASE_ERROR,
                message="La vérification des personnes a échoué.",
                retryable=True,
                diagnostic=repr(exc),
            ),
        )

    created_ids: list[int] = []
    skipped: list[PresenceTarget] = []
    batch_issues: list[BatchIssue] = []

    try:
        for index, target in enumerate(command.targets):
            conflicting_presence_id = port.find_overlap(
                person_id=target.person_id,
                presence_date=target.presence_date,
                start_time=command.start_time,
                end_time=command.end_time,
            )
            if conflicting_presence_id is not None:
                skipped.append(target)
                batch_issues.append(
                    BatchIssue(
                        item=BatchItemRef(
                            index=index,
                            person_id=target.person_id,
                            presence_date=target.presence_date,
                        ),
                        disposition=BatchDisposition.SKIPPED,
                        error=ServiceError(
                            code=ServiceErrorCode.OVERLAP_CONFLICT,
                            message=(
                                "Une présence existe déjà sur cette plage horaire."
                            ),
                            field="schedule",
                            conflicting_target_id=conflicting_presence_id,
                        ),
                    )
                )
                continue

            presence_id = port.insert_presence(
                person_id=target.person_id,
                presence_date=target.presence_date,
                start_time=command.start_time,
                end_time=command.end_time,
                category_id=command.category_id,
                title=normalized_title,
            )
            if not is_valid_target_id(presence_id):
                raise RuntimeError(
                    "La création d'une présence n'a pas retourné d'identifiant valide."
                )
            created_ids.append(presence_id)

        port.commit()
    except Exception as exc:
        _safe_rollback(port)
        return ServiceResult.failure(
            error=ServiceError(
                code=ServiceErrorCode.DATABASE_ERROR,
                message="La création des présences a échoué.",
                retryable=True,
                diagnostic=repr(exc),
            ),
            committed=False,
        )

    try:
        created: list[PresenceSnapshot] = []
        for presence_id in created_ids:
            snapshot = port.read_presence(presence_id)
            if snapshot is None:
                raise LookupError(
                    "La présence n°%d est introuvable après commit." % presence_id
                )
            created.append(snapshot)
    except Exception as exc:
        return ServiceResult.failure(
            error=ServiceError(
                code=ServiceErrorCode.READBACK_ERROR,
                message=(
                    "L'enregistrement a été validé mais sa relecture a échoué."
                ),
                retryable=False,
                diagnostic=repr(exc),
            ),
            committed=True,
        )

    batch = BatchReport(
        requested_count=len(command.targets),
        succeeded_count=len(created),
        skipped_count=len(skipped),
        rejected_count=0,
        issues=tuple(batch_issues),
    )

    return ServiceResult.success(
        value=PresenceBatchSnapshot(
            created=tuple(created),
            skipped_overlaps=tuple(skipped),
        ),
        committed=True,
        batch=batch,
    )


def update_presence(
    port: PresenceWritePort,
    *,
    command: PresenceUpdateCommand,
) -> ServiceResult[PresenceSnapshot]:
    """Modifie une présence avec protection contre les écrasements concurrents."""

    errors = validate_presence_update_command(command)
    if errors:
        return ServiceResult.failure(
            error=_collapse_validation_errors(errors),
            target_id=(
                command.presence_id
                if is_valid_target_id(command.presence_id)
                else None
            ),
        )

    try:
        current = port.read_presence(command.presence_id)
    except Exception as exc:
        return ServiceResult.failure(
            error=ServiceError(
                code=ServiceErrorCode.DATABASE_ERROR,
                message="La lecture de la présence a échoué.",
                target_id=command.presence_id,
                retryable=True,
                diagnostic=repr(exc),
            ),
            target_id=command.presence_id,
        )

    if current is None:
        return ServiceResult.failure(
            error=ServiceError(
                code=ServiceErrorCode.TARGET_NOT_FOUND,
                message="La présence sélectionnée n'existe plus.",
                target_id=command.presence_id,
            ),
            target_id=command.presence_id,
        )

    if (
        command.expected_revision
        and command.expected_revision != current.revision
    ):
        return ServiceResult.failure(
            error=ServiceError(
                code=ServiceErrorCode.CONCURRENT_MODIFICATION,
                message=(
                    "La présence a été modifiée depuis son affichage. "
                    "Rechargez-la avant de réessayer."
                ),
                target_id=command.presence_id,
                expected_revision=command.expected_revision,
                actual_revision=current.revision,
            ),
            target_id=command.presence_id,
        )

    normalized_title = normalize_presence_title(command.title)
    if (
        current.start_time == command.start_time
        and current.end_time == command.end_time
        and current.category_id == command.category_id
        and current.title == normalized_title
    ):
        return ServiceResult.success(
            value=current,
            target_id=command.presence_id,
            committed=False,
        )

    try:
        conflicting_presence_id = port.find_overlap(
            person_id=current.person_id,
            presence_date=current.presence_date,
            start_time=command.start_time,
            end_time=command.end_time,
            exclude_presence_id=command.presence_id,
        )
        if conflicting_presence_id is not None:
            return ServiceResult.failure(
                error=ServiceError(
                    code=ServiceErrorCode.OVERLAP_CONFLICT,
                    message=(
                        "Les horaires modifiés chevauchent une autre présence "
                        "de la même personne."
                    ),
                    field="schedule",
                    target_id=command.presence_id,
                    conflicting_target_id=conflicting_presence_id,
                ),
                target_id=command.presence_id,
            )

        affected = int(
            port.update_presence(
                presence_id=command.presence_id,
                start_time=command.start_time,
                end_time=command.end_time,
                category_id=command.category_id,
                title=normalized_title,
                expected=current,
            )
        )
        if affected == 0:
            actual = port.read_presence(command.presence_id)
            _safe_rollback(port)
            if actual is None:
                return ServiceResult.failure(
                    error=ServiceError(
                        code=ServiceErrorCode.TARGET_NOT_FOUND,
                        message="La présence a disparu avant l'enregistrement.",
                        target_id=command.presence_id,
                    ),
                    target_id=command.presence_id,
                )
            return ServiceResult.failure(
                error=ServiceError(
                    code=ServiceErrorCode.CONCURRENT_MODIFICATION,
                    message=(
                        "La présence a changé pendant l'enregistrement. "
                        "Rechargez-la avant de réessayer."
                    ),
                    target_id=command.presence_id,
                    expected_revision=current.revision,
                    actual_revision=actual.revision,
                ),
                target_id=command.presence_id,
            )
        if affected != 1:
            _safe_rollback(port)
            return ServiceResult.failure(
                error=ServiceError(
                    code=ServiceErrorCode.UNEXPECTED_ROWCOUNT,
                    message="Le nombre de présences modifiées est inattendu.",
                    target_id=command.presence_id,
                    diagnostic="rowcount=%d" % affected,
                ),
                target_id=command.presence_id,
            )
        port.commit()
    except Exception as exc:
        _safe_rollback(port)
        return ServiceResult.failure(
            error=ServiceError(
                code=ServiceErrorCode.DATABASE_ERROR,
                message="La modification de la présence a échoué.",
                target_id=command.presence_id,
                retryable=True,
                diagnostic=repr(exc),
            ),
            target_id=command.presence_id,
        )

    try:
        snapshot = port.read_presence(command.presence_id)
        if snapshot is None:
            raise LookupError("Présence introuvable après commit.")
    except Exception as exc:
        return ServiceResult.failure(
            error=ServiceError(
                code=ServiceErrorCode.READBACK_ERROR,
                message="L'enregistrement a été validé mais sa relecture a échoué.",
                target_id=command.presence_id,
                retryable=False,
                diagnostic=repr(exc),
            ),
            target_id=command.presence_id,
            committed=True,
        )

    return ServiceResult.success(
        value=snapshot,
        target_id=command.presence_id,
        committed=True,
    )

def delete_presence(
    port: PresenceWritePort,
    *,
    command: PresenceDeleteCommand,
) -> ServiceResult[bool]:
    """Supprime une présence avec confirmation et concurrence optimiste."""

    if not is_valid_target_id(command.presence_id):
        return ServiceResult.failure(
            error=ServiceError(
                code=ServiceErrorCode.INVALID_TARGET_ID,
                message="Identifiant historique de présence invalide.",
                field="presence_id",
            ),
        )

    if command.confirmed is not True:
        return ServiceResult.failure(
            error=ServiceError(
                code=ServiceErrorCode.VALIDATION_ERROR,
                message="La suppression de la présence doit être confirmée explicitement.",
                field="confirmation",
                target_id=command.presence_id,
            ),
            target_id=command.presence_id,
        )

    try:
        current = port.read_presence(command.presence_id)
        if current is None:
            return ServiceResult.failure(
                error=ServiceError(
                    code=ServiceErrorCode.TARGET_NOT_FOUND,
                    message="La présence sélectionnée n'existe plus.",
                    target_id=command.presence_id,
                ),
                target_id=command.presence_id,
            )

        if (
            command.expected_revision
            and command.expected_revision != current.revision
        ):
            return ServiceResult.failure(
                error=ServiceError(
                    code=ServiceErrorCode.CONCURRENT_MODIFICATION,
                    message=(
                        "La présence a été modifiée depuis son affichage. "
                        "Rechargez-la avant de la supprimer."
                    ),
                    target_id=command.presence_id,
                    expected_revision=command.expected_revision,
                    actual_revision=current.revision,
                ),
                target_id=command.presence_id,
            )

        affected = int(
            port.delete_presence(
                command.presence_id,
                expected=current,
            )
        )
        if affected == 0:
            actual = port.read_presence(command.presence_id)
            _safe_rollback(port)
            if actual is None:
                return ServiceResult.failure(
                    error=ServiceError(
                        code=ServiceErrorCode.TARGET_NOT_FOUND,
                        message="La présence a disparu avant la suppression.",
                        target_id=command.presence_id,
                    ),
                    target_id=command.presence_id,
                )
            return ServiceResult.failure(
                error=ServiceError(
                    code=ServiceErrorCode.CONCURRENT_MODIFICATION,
                    message=(
                        "La présence a changé pendant la suppression. "
                        "Rechargez-la avant de réessayer."
                    ),
                    target_id=command.presence_id,
                    expected_revision=current.revision,
                    actual_revision=actual.revision,
                ),
                target_id=command.presence_id,
            )
        if affected != 1:
            _safe_rollback(port)
            return ServiceResult.failure(
                error=ServiceError(
                    code=ServiceErrorCode.UNEXPECTED_ROWCOUNT,
                    message="Le nombre de présences supprimées est inattendu.",
                    target_id=command.presence_id,
                    diagnostic="rowcount=%d" % affected,
                ),
                target_id=command.presence_id,
            )
        port.commit()
    except Exception as exc:
        _safe_rollback(port)
        return ServiceResult.failure(
            error=ServiceError(
                code=ServiceErrorCode.DATABASE_ERROR,
                message="La suppression de la présence a échoué.",
                target_id=command.presence_id,
                retryable=True,
                diagnostic=repr(exc),
            ),
            target_id=command.presence_id,
        )

    try:
        if port.read_presence(command.presence_id) is not None:
            raise LookupError("La présence est encore relue après commit.")
    except Exception as exc:
        return ServiceResult.failure(
            error=ServiceError(
                code=ServiceErrorCode.READBACK_ERROR,
                message="La suppression a été validée mais son contrôle final a échoué.",
                target_id=command.presence_id,
                retryable=False,
                diagnostic=repr(exc),
            ),
            target_id=command.presence_id,
            committed=True,
        )

    return ServiceResult.success(
        value=True,
        target_id=command.presence_id,
        committed=True,
    )
