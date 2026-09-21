"""Écritures métier des déplacements de frais, indépendantes de wx et Qt."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional, Protocol

from application.services.transactional_write import (
    WriteCode,
    WriteResult,
    invalid_target_result,
    is_valid_target_id,
)


@dataclass(frozen=True)
class TripSnapshot:
    trip_id: int
    person_id: int
    travel_date: date
    purpose: str
    departure_postcode: str
    departure_city: str
    arrival_postcode: str
    arrival_city: str
    distance: Decimal
    round_trip: bool
    tariff_per_km: Decimal
    reimbursement_id: Optional[int]


@dataclass(frozen=True)
class TripCommand:
    person_id: int
    travel_date: date
    purpose: str
    departure_postcode: str
    departure_city: str
    arrival_postcode: str
    arrival_city: str
    distance: Decimal
    round_trip: bool
    tariff_per_km: Decimal
    trip_id: Optional[int] = None
    confirm_empty_purpose: bool = False
    confirm_zero_distance: bool = False
    confirm_zero_tariff: bool = False


@dataclass(frozen=True)
class TripDeleteCommand:
    person_id: int
    trip_id: int
    confirmed: bool = False


class TripWritePort(Protocol):
    def person_exists(self, person_id: int) -> bool:
        ...

    def read_trip(self, trip_id: int) -> Optional[TripSnapshot]:
        ...

    def insert_trip(self, command: TripCommand) -> int:
        ...

    def update_trip(self, command: TripCommand) -> int:
        ...

    def delete_unassigned_trip(self, trip_id: int, person_id: int) -> int:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...


def _safe_rollback(port: TripWritePort) -> None:
    try:
        port.rollback()
    except Exception:
        pass


def _clean_text(value: object) -> str:
    return "" if value is None else str(value).strip()


def validate_trip_command(command: TripCommand) -> tuple[str, ...]:
    errors: list[str] = []

    if not is_valid_target_id(command.person_id):
        errors.append("Identifiant historique de la personne invalide.")
    if command.trip_id is not None and not is_valid_target_id(command.trip_id):
        errors.append("Identifiant historique du déplacement invalide.")
    if type(command.travel_date) is not date:
        errors.append("La date du déplacement est obligatoire.")

    purpose = _clean_text(command.purpose)
    if not purpose and not command.confirm_empty_purpose:
        errors.append("Confirmez explicitement le déplacement sans objet.")

    for value, label in (
        (command.departure_postcode, "Le code postal de départ est obligatoire."),
        (command.departure_city, "La ville de départ est obligatoire."),
        (command.arrival_postcode, "Le code postal d'arrivée est obligatoire."),
        (command.arrival_city, "La ville d'arrivée est obligatoire."),
    ):
        if not _clean_text(value):
            errors.append(label)

    for postcode, label in (
        (command.departure_postcode, "Le code postal de départ est invalide."),
        (command.arrival_postcode, "Le code postal d'arrivée est invalide."),
    ):
        text = _clean_text(postcode)
        if text and (len(text) != 5 or not text.isdigit()):
            errors.append(label)

    if type(command.distance) is not Decimal or command.distance < Decimal("0"):
        errors.append("La distance du déplacement est invalide.")
    elif command.distance == Decimal("0") and not command.confirm_zero_distance:
        errors.append("Confirmez explicitement le déplacement à 0 km.")

    if type(command.tariff_per_km) is not Decimal or command.tariff_per_km < Decimal("0"):
        errors.append("Le tarif kilométrique est invalide.")
    elif command.tariff_per_km == Decimal("0") and not command.confirm_zero_tariff:
        errors.append("Confirmez explicitement le tarif kilométrique à 0 €.")

    if type(command.round_trip) is not bool:
        errors.append("L'indicateur aller-retour est invalide.")

    return tuple(errors)


def _same_trip_values(snapshot: TripSnapshot, command: TripCommand) -> bool:
    return (
        snapshot.person_id == command.person_id
        and snapshot.travel_date == command.travel_date
        and snapshot.purpose == _clean_text(command.purpose)
        and snapshot.departure_postcode == _clean_text(command.departure_postcode)
        and snapshot.departure_city == _clean_text(command.departure_city)
        and snapshot.arrival_postcode == _clean_text(command.arrival_postcode)
        and snapshot.arrival_city == _clean_text(command.arrival_city)
        and snapshot.distance == command.distance
        and snapshot.round_trip is command.round_trip
        and snapshot.tariff_per_km == command.tariff_per_km
    )


def save_trip(
    port: TripWritePort,
    *,
    command: TripCommand,
) -> WriteResult[TripSnapshot]:
    """Crée ou modifie un déplacement sans jamais altérer son remboursement existant."""

    errors = validate_trip_command(command)
    if errors:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message=" ".join(errors),
            target_id=command.trip_id,
        )

    try:
        if not port.person_exists(command.person_id):
            return WriteResult(
                ok=False,
                code=WriteCode.TARGET_NOT_FOUND,
                message="La personne sélectionnée n'existe plus.",
                target_id=command.trip_id,
            )

        trip_id = command.trip_id
        previous_reimbursement_id = None
        if trip_id is None:
            trip_id = port.insert_trip(command)
            if not is_valid_target_id(trip_id):
                _safe_rollback(port)
                return WriteResult(
                    ok=False,
                    code=WriteCode.INVALID_TARGET_ID,
                    message="La création du déplacement n'a pas retourné d'identifiant valide.",
                )
        else:
            existing = port.read_trip(trip_id)
            if existing is None or existing.person_id != command.person_id:
                return WriteResult(
                    ok=False,
                    code=WriteCode.TARGET_NOT_FOUND,
                    message="Le déplacement sélectionné n'existe plus pour cette personne.",
                    target_id=trip_id,
                )
            previous_reimbursement_id = existing.reimbursement_id
            affected = int(port.update_trip(command))
            if affected != 1:
                _safe_rollback(port)
                return WriteResult(
                    ok=False,
                    code=(
                        WriteCode.TARGET_NOT_FOUND
                        if affected == 0
                        else WriteCode.UNEXPECTED_ROWCOUNT
                    ),
                    message="Nombre de déplacements modifiés inattendu : %s." % affected,
                    target_id=trip_id,
                )

        port.commit()
    except Exception as exc:
        _safe_rollback(port)
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Enregistrement du déplacement impossible : %s" % exc,
            target_id=trip_id if "trip_id" in locals() and is_valid_target_id(trip_id) else None,
        )

    try:
        snapshot = port.read_trip(trip_id)
        if snapshot is None:
            raise LookupError("Déplacement introuvable après commit.")
        if not _same_trip_values(snapshot, command):
            raise LookupError("La relecture ne confirme pas les valeurs du déplacement.")
        if command.trip_id is None:
            if snapshot.reimbursement_id not in (None, 0):
                raise LookupError("Un nouveau déplacement a été rattaché sans demande.")
        elif snapshot.reimbursement_id != previous_reimbursement_id:
            raise LookupError("Le remboursement du déplacement a changé pendant la modification.")
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.READBACK_ERROR,
            message="Déplacement validé, mais relecture impossible : %s" % exc,
            target_id=trip_id,
            committed=True,
        )

    return WriteResult(
        ok=True,
        code=WriteCode.OK,
        message="Déplacement enregistré et relu.",
        target_id=trip_id,
        value=snapshot,
        committed=True,
    )


def delete_trip(
    port: TripWritePort,
    *,
    command: TripDeleteCommand,
) -> WriteResult[bool]:
    """Supprime uniquement un déplacement encore libre au moment exact du DELETE."""

    if not is_valid_target_id(command.trip_id):
        return invalid_target_result(command.trip_id)
    if not is_valid_target_id(command.person_id):
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message="Identifiant historique de la personne invalide.",
            target_id=command.trip_id,
        )
    if not command.confirmed:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message="La suppression du déplacement doit être confirmée explicitement.",
            target_id=command.trip_id,
        )

    try:
        snapshot = port.read_trip(command.trip_id)
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Lecture du déplacement impossible avant suppression : %s" % exc,
            target_id=command.trip_id,
        )

    if snapshot is None or snapshot.person_id != command.person_id:
        return WriteResult(
            ok=False,
            code=WriteCode.TARGET_NOT_FOUND,
            message="Le déplacement sélectionné n'existe plus pour cette personne.",
            target_id=command.trip_id,
        )
    if snapshot.reimbursement_id not in (None, 0):
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message=(
                "Ce déplacement est rattaché au remboursement n°%s et ne peut pas être supprimé."
                % snapshot.reimbursement_id
            ),
            target_id=command.trip_id,
        )

    try:
        affected = int(port.delete_unassigned_trip(command.trip_id, command.person_id))
        if affected == 0:
            current = port.read_trip(command.trip_id)
            _safe_rollback(port)
            if current is not None and current.reimbursement_id not in (None, 0):
                return WriteResult(
                    ok=False,
                    code=WriteCode.VALIDATION_ERROR,
                    message=(
                        "Le déplacement a été rattaché au remboursement n°%s entre-temps ; "
                        "suppression refusée."
                        % current.reimbursement_id
                    ),
                    target_id=command.trip_id,
                )
            return WriteResult(
                ok=False,
                code=WriteCode.TARGET_NOT_FOUND,
                message="Le déplacement a disparu avant la suppression.",
                target_id=command.trip_id,
            )
        if affected != 1:
            _safe_rollback(port)
            return WriteResult(
                ok=False,
                code=WriteCode.UNEXPECTED_ROWCOUNT,
                message="Nombre de déplacements supprimés inattendu : %s." % affected,
                target_id=command.trip_id,
            )
        port.commit()
    except Exception as exc:
        _safe_rollback(port)
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Suppression du déplacement impossible : %s" % exc,
            target_id=command.trip_id,
        )

    try:
        if port.read_trip(command.trip_id) is not None:
            raise LookupError("Le déplacement est encore présent après commit.")
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.READBACK_ERROR,
            message="Suppression validée, mais contrôle d'absence impossible : %s" % exc,
            target_id=command.trip_id,
            committed=True,
        )

    return WriteResult(
        ok=True,
        code=WriteCode.OK,
        message="Déplacement supprimé et absence confirmée.",
        target_id=command.trip_id,
        value=True,
        committed=True,
    )
