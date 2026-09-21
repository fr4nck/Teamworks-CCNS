"""Métier et écritures transactionnelles des Présences, sans wx ni Qt."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from application.services.transactional_write import WriteCode, WriteResult, is_valid_target_id
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


@dataclass(frozen=True)
class PresenceDeleteCommand:
    presence_id: int
    confirmed: bool = False


class PresenceWritePort(Protocol):
    def person_exists(self, person_id: int) -> bool:
        ...

    def presence_exists(self, presence_id: int) -> bool:
        ...

    def read_presence(self, presence_id: int) -> PresenceSnapshot | None:
        ...

    def has_overlap(
        self,
        *,
        person_id: int,
        presence_date: date,
        start_time: str,
        end_time: str,
        exclude_presence_id: int | None = None,
    ) -> bool:
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
    ) -> int:
        ...

    def delete_presence(self, presence_id: int) -> int:
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


def _validate_time_window(start_time: object, end_time: object) -> tuple[str, ...]:
    errors: list[str] = []

    start = parse_clock_time(start_time, "heure_debut")
    end = parse_clock_time(end_time, "heure_fin")

    if not start.ok:
        errors.append(start.error.message if start.error else "Heure de début invalide.")
    if not end.ok:
        errors.append(end.error.message if end.error else "Heure de fin invalide.")
    if not start.ok or not end.ok:
        return tuple(errors)

    if end.value_minutes < start.value_minutes:
        errors.append("L'heure de fin doit être supérieure à l'heure de début.")
        return tuple(errors)

    duration = end.value_minutes - start.value_minutes
    if duration < _MIN_DURATION_MINUTES:
        errors.append("La durée de la présence doit être au minimum de 15 minutes.")

    return tuple(errors)


def _validate_category_id(category_id: object) -> tuple[str, ...]:
    if not is_valid_target_id(category_id):
        return ("La catégorie de présence est obligatoire.",)
    return ()


def _validate_title(title: object) -> tuple[str, ...]:
    normalized = normalize_presence_title(title)
    if len(normalized) > 200:
        return ("La légende de la présence ne peut pas dépasser 200 caractères.",)
    return ()


def validate_presence_create_command(command: PresenceCreateCommand) -> tuple[str, ...]:
    errors: list[str] = []
    if not command.targets:
        errors.append("Au moins une date et une personne doivent être sélectionnées.")

    for target in command.targets:
        if not is_valid_target_id(target.person_id):
            errors.append("Une personne sélectionnée possède un identifiant invalide.")
        if type(target.presence_date) is not date:
            errors.append("Une date de présence est invalide.")

    errors.extend(_validate_time_window(command.start_time, command.end_time))
    errors.extend(_validate_category_id(command.category_id))
    errors.extend(_validate_title(command.title))
    return tuple(errors)


def validate_presence_update_command(command: PresenceUpdateCommand) -> tuple[str, ...]:
    errors: list[str] = []
    if not is_valid_target_id(command.presence_id):
        errors.append("Identifiant historique de présence invalide.")
    errors.extend(_validate_time_window(command.start_time, command.end_time))
    errors.extend(_validate_category_id(command.category_id))
    errors.extend(_validate_title(command.title))
    return tuple(errors)


def _safe_rollback(port: PresenceWritePort) -> None:
    try:
        port.rollback()
    except Exception:
        pass


def create_presences(
    port: PresenceWritePort,
    *,
    command: PresenceCreateCommand,
) -> WriteResult[PresenceBatchSnapshot]:
    """Crée un lot de présences avec un seul commit.

    Un chevauchement est un skip métier individuel, comme dans le parcours wx
    historique. Toute panne technique annule en revanche toutes les insertions
    du lot.
    """

    errors = validate_presence_create_command(command)
    if errors:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message=" ".join(errors),
        )

    normalized_title = normalize_presence_title(command.title)
    created_ids: list[int] = []
    skipped: list[PresenceTarget] = []

    try:
        for target in command.targets:
            if not port.person_exists(target.person_id):
                raise LookupError(
                    "La personne n°%d n'existe plus." % target.person_id
                )

            if port.has_overlap(
                person_id=target.person_id,
                presence_date=target.presence_date,
                start_time=command.start_time,
                end_time=command.end_time,
            ):
                skipped.append(target)
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
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Création des présences impossible : %s" % exc,
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
        return WriteResult(
            ok=False,
            code=WriteCode.READBACK_ERROR,
            message="Présences validées, mais relecture impossible : %s" % exc,
            committed=True,
        )

    return WriteResult(
        ok=True,
        code=WriteCode.OK,
        message="%d présence(s) créée(s), %d chevauchement(s) ignoré(s)."
        % (len(created), len(skipped)),
        value=PresenceBatchSnapshot(
            created=tuple(created),
            skipped_overlaps=tuple(skipped),
        ),
        committed=True,
    )


def update_presence(
    port: PresenceWritePort,
    *,
    command: PresenceUpdateCommand,
) -> WriteResult[PresenceSnapshot]:
    """Modifie les horaires, la catégorie et la légende d'une présence."""

    errors = validate_presence_update_command(command)
    if errors:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message=" ".join(errors),
            target_id=command.presence_id if is_valid_target_id(command.presence_id) else None,
        )

    try:
        current = port.read_presence(command.presence_id)
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Lecture de la présence impossible : %s" % exc,
            target_id=command.presence_id,
        )

    if current is None:
        return WriteResult(
            ok=False,
            code=WriteCode.TARGET_NOT_FOUND,
            message="La présence sélectionnée n'existe plus.",
            target_id=command.presence_id,
        )

    try:
        if port.has_overlap(
            person_id=current.person_id,
            presence_date=current.presence_date,
            start_time=command.start_time,
            end_time=command.end_time,
            exclude_presence_id=command.presence_id,
        ):
            return WriteResult(
                ok=False,
                code=WriteCode.VALIDATION_ERROR,
                message="Les horaires modifiés chevauchent une autre présence de la même personne.",
                target_id=command.presence_id,
            )

        affected = int(
            port.update_presence(
                presence_id=command.presence_id,
                start_time=command.start_time,
                end_time=command.end_time,
                category_id=command.category_id,
                title=normalize_presence_title(command.title),
            )
        )
        if affected == 0:
            _safe_rollback(port)
            return WriteResult(
                ok=False,
                code=WriteCode.TARGET_NOT_FOUND,
                message="La présence a disparu avant l'enregistrement.",
                target_id=command.presence_id,
            )
        if affected != 1:
            _safe_rollback(port)
            return WriteResult(
                ok=False,
                code=WriteCode.UNEXPECTED_ROWCOUNT,
                message="Nombre de présences modifiées inattendu : %d." % affected,
                target_id=command.presence_id,
            )
        port.commit()
    except Exception as exc:
        _safe_rollback(port)
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Modification de la présence impossible : %s" % exc,
            target_id=command.presence_id,
        )

    try:
        snapshot = port.read_presence(command.presence_id)
        if snapshot is None:
            raise LookupError("Présence introuvable après commit.")
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.READBACK_ERROR,
            message="Présence validée, mais relecture impossible : %s" % exc,
            target_id=command.presence_id,
            committed=True,
        )

    return WriteResult(
        ok=True,
        code=WriteCode.OK,
        message="Présence modifiée et relue.",
        target_id=command.presence_id,
        value=snapshot,
        committed=True,
    )


def delete_presence(
    port: PresenceWritePort,
    *,
    command: PresenceDeleteCommand,
) -> WriteResult[bool]:
    """Supprime une présence après confirmation explicite."""

    if not is_valid_target_id(command.presence_id):
        return WriteResult(
            ok=False,
            code=WriteCode.INVALID_TARGET_ID,
            message="Identifiant historique de présence invalide.",
        )
    if command.confirmed is not True:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message="La suppression de la présence doit être confirmée explicitement.",
            target_id=command.presence_id,
        )

    try:
        if not port.presence_exists(command.presence_id):
            return WriteResult(
                ok=False,
                code=WriteCode.TARGET_NOT_FOUND,
                message="La présence sélectionnée n'existe plus.",
                target_id=command.presence_id,
            )

        affected = int(port.delete_presence(command.presence_id))
        if affected == 0:
            _safe_rollback(port)
            return WriteResult(
                ok=False,
                code=WriteCode.TARGET_NOT_FOUND,
                message="La présence a disparu avant la suppression.",
                target_id=command.presence_id,
            )
        if affected != 1:
            _safe_rollback(port)
            return WriteResult(
                ok=False,
                code=WriteCode.UNEXPECTED_ROWCOUNT,
                message="Nombre de présences supprimées inattendu : %d." % affected,
                target_id=command.presence_id,
            )
        port.commit()
    except Exception as exc:
        _safe_rollback(port)
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Suppression de la présence impossible : %s" % exc,
            target_id=command.presence_id,
        )

    try:
        if port.read_presence(command.presence_id) is not None:
            raise LookupError("La présence est encore relue après commit.")
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.READBACK_ERROR,
            message="Présence supprimée, mais contrôle d'absence impossible : %s" % exc,
            target_id=command.presence_id,
            committed=True,
        )

    return WriteResult(
        ok=True,
        code=WriteCode.OK,
        message="Présence supprimée et absence confirmée.",
        target_id=command.presence_id,
        value=True,
        committed=True,
    )
