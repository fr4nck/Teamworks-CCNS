"""Écritures métier des remboursements de frais, indépendantes de wx et Qt."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional, Protocol

from application.services.transactional_write import (
    WriteCode,
    WriteResult,
    execute_transactional_delete,
    invalid_target_result,
    is_valid_target_id,
)


@dataclass(frozen=True)
class ReimbursementSnapshot:
    reimbursement_id: int
    person_id: int
    payment_date: date
    amount: Decimal
    trip_ids: tuple[int, ...]


@dataclass(frozen=True)
class ReimbursementCommand:
    person_id: int
    payment_date: date
    amount: Decimal
    checked_trip_ids: tuple[int, ...]
    unchecked_trip_ids: tuple[int, ...] = ()
    reimbursement_id: Optional[int] = None
    confirm_zero_amount: bool = False


@dataclass(frozen=True)
class ReimbursementDeleteCommand:
    person_id: int
    reimbursement_id: int
    confirmed: bool = False
    confirm_attached_trips: bool = False


class ReimbursementWritePort(Protocol):
    def person_exists(self, person_id: int) -> bool:
        ...

    def reimbursement_exists(self, reimbursement_id: int) -> bool:
        ...

    def insert_reimbursement(
        self, person_id: int, payment_date: date, amount: Decimal
    ) -> int:
        ...

    def update_reimbursement(
        self,
        reimbursement_id: int,
        person_id: int,
        payment_date: date,
        amount: Decimal,
    ) -> int:
        ...

    def read_trip_assignment(
        self, trip_id: int, person_id: int
    ) -> tuple[bool, Optional[int]]:
        ...

    def assign_trip(self, trip_id: int, reimbursement_id: int) -> int:
        ...

    def detach_trip_if_owned(self, trip_id: int, reimbursement_id: int) -> int:
        ...

    def list_trip_ids(
        self, person_id: int, reimbursement_id: int
    ) -> tuple[int, ...]:
        ...

    def update_legacy_trip_list(
        self, reimbursement_id: int, trip_ids_text: str
    ) -> int:
        ...

    def read_reimbursement(
        self, reimbursement_id: int
    ) -> Optional[ReimbursementSnapshot]:
        ...

    def detach_all_trips(self, reimbursement_id: int) -> int:
        ...

    def delete_reimbursement(self, reimbursement_id: int, person_id: int) -> int:
        ...

    def has_trip_assignment(self, reimbursement_id: int) -> bool:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...


def _valid_ids(values: tuple[int, ...]) -> bool:
    return all(is_valid_target_id(value) for value in values)


def validate_reimbursement_command(command: ReimbursementCommand) -> tuple[str, ...]:
    errors: list[str] = []

    if not is_valid_target_id(command.person_id):
        errors.append("Identifiant historique de la personne invalide.")
    if command.reimbursement_id is not None and not is_valid_target_id(
        command.reimbursement_id
    ):
        errors.append("Identifiant historique du remboursement invalide.")
    if type(command.payment_date) is not date:
        errors.append("La date du remboursement est obligatoire.")
    if type(command.amount) is not Decimal or command.amount < Decimal("0"):
        errors.append("Le montant du remboursement est invalide.")
    elif command.amount == Decimal("0") and not command.confirm_zero_amount:
        errors.append("Confirmez explicitement le remboursement à 0 €.")

    if not _valid_ids(command.checked_trip_ids):
        errors.append("La liste des déplacements cochés contient un identifiant invalide.")
    if not _valid_ids(command.unchecked_trip_ids):
        errors.append("La liste des déplacements décochés contient un identifiant invalide.")

    checked = set(command.checked_trip_ids)
    unchecked = set(command.unchecked_trip_ids)
    if len(checked) != len(command.checked_trip_ids):
        errors.append("Un déplacement coché est présent plusieurs fois.")
    if len(unchecked) != len(command.unchecked_trip_ids):
        errors.append("Un déplacement décoché est présent plusieurs fois.")
    if checked & unchecked:
        errors.append("Un déplacement ne peut pas être coché et décoché simultanément.")

    return tuple(errors)


def _safe_rollback(port: ReimbursementWritePort) -> None:
    try:
        port.rollback()
    except Exception:
        pass


def save_reimbursement(
    port: ReimbursementWritePort,
    *,
    command: ReimbursementCommand,
) -> WriteResult[ReimbursementSnapshot]:
    """Crée ou modifie un remboursement et réconcilie ses déplacements atomiquement."""

    errors = validate_reimbursement_command(command)
    if errors:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message=" ".join(errors),
            target_id=command.reimbursement_id,
        )

    try:
        if not port.person_exists(command.person_id):
            return WriteResult(
                ok=False,
                code=WriteCode.TARGET_NOT_FOUND,
                message="La personne sélectionnée n'existe plus.",
                target_id=command.reimbursement_id,
            )

        reimbursement_id = command.reimbursement_id
        if reimbursement_id is None:
            reimbursement_id = port.insert_reimbursement(
                command.person_id,
                command.payment_date,
                command.amount,
            )
            if not is_valid_target_id(reimbursement_id):
                _safe_rollback(port)
                return WriteResult(
                    ok=False,
                    code=WriteCode.INVALID_TARGET_ID,
                    message="La création du remboursement n'a pas retourné d'identifiant valide.",
                )
        else:
            if not port.reimbursement_exists(reimbursement_id):
                return WriteResult(
                    ok=False,
                    code=WriteCode.TARGET_NOT_FOUND,
                    message="Le remboursement sélectionné n'existe plus.",
                    target_id=reimbursement_id,
                )
            affected = int(
                port.update_reimbursement(
                    reimbursement_id,
                    command.person_id,
                    command.payment_date,
                    command.amount,
                )
            )
            if affected != 1:
                _safe_rollback(port)
                return WriteResult(
                    ok=False,
                    code=(
                        WriteCode.TARGET_NOT_FOUND
                        if affected == 0
                        else WriteCode.UNEXPECTED_ROWCOUNT
                    ),
                    message="Nombre de remboursements modifiés inattendu : %s." % affected,
                    target_id=reimbursement_id,
                )

        for trip_id in command.checked_trip_ids:
            found, current_reimbursement_id = port.read_trip_assignment(
                trip_id, command.person_id
            )
            if not found:
                raise RuntimeError(
                    "Le déplacement n°%d n'existe plus pour cette personne." % trip_id
                )

            allowed = (None, 0)
            if command.reimbursement_id is not None:
                allowed = allowed + (reimbursement_id,)
            if current_reimbursement_id not in allowed:
                raise RuntimeError(
                    "Le déplacement n°%d a été rattaché à un autre remboursement entre-temps."
                    % trip_id
                )
            if current_reimbursement_id != reimbursement_id:
                affected = int(port.assign_trip(trip_id, reimbursement_id))
                if affected != 1:
                    raise RuntimeError(
                        "Le rattachement du déplacement n°%d a affecté %d ligne(s)."
                        % (trip_id, affected)
                    )

        for trip_id in command.unchecked_trip_ids:
            affected = int(port.detach_trip_if_owned(trip_id, reimbursement_id))
            if affected not in (0, 1):
                raise RuntimeError(
                    "Le détachement du déplacement n°%d a affecté %d ligne(s)."
                    % (trip_id, affected)
                )

        canonical_trip_ids = tuple(
            sorted(port.list_trip_ids(command.person_id, reimbursement_id))
        )
        expected_trip_ids = tuple(sorted(command.checked_trip_ids))
        if canonical_trip_ids != expected_trip_ids:
            raise RuntimeError(
                "Les déplacements rattachés ont changé pendant l'enregistrement."
            )

        historical_text = "-".join(str(trip_id) for trip_id in canonical_trip_ids)
        affected = int(
            port.update_legacy_trip_list(reimbursement_id, historical_text)
        )
        if affected != 1:
            raise RuntimeError(
                "La mise à jour du miroir historique a affecté %d ligne(s)." % affected
            )

        port.commit()
    except Exception as exc:
        _safe_rollback(port)
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Enregistrement du remboursement impossible : %s" % exc,
            target_id=(
                reimbursement_id
                if "reimbursement_id" in locals()
                and is_valid_target_id(reimbursement_id)
                else None
            ),
        )

    try:
        snapshot = port.read_reimbursement(reimbursement_id)
        if snapshot is None:
            raise LookupError("Remboursement introuvable après commit.")
        if tuple(sorted(snapshot.trip_ids)) != expected_trip_ids:
            raise LookupError(
                "La relecture ne confirme pas les déplacements rattachés."
            )
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.READBACK_ERROR,
            message="Remboursement validé, mais relecture impossible : %s" % exc,
            target_id=reimbursement_id,
            committed=True,
        )

    return WriteResult(
        ok=True,
        code=WriteCode.OK,
        message="Remboursement enregistré et relu.",
        target_id=reimbursement_id,
        value=snapshot,
        committed=True,
    )


def delete_reimbursement(
    port: ReimbursementWritePort,
    *,
    command: ReimbursementDeleteCommand,
) -> WriteResult[bool]:
    """Supprime un remboursement et détache ses déplacements dans une transaction unique."""

    if not is_valid_target_id(command.reimbursement_id):
        return invalid_target_result(command.reimbursement_id)
    if not is_valid_target_id(command.person_id):
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message="Identifiant historique de la personne invalide.",
            target_id=command.reimbursement_id,
        )
    if not command.confirmed:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message="La suppression du remboursement doit être confirmée explicitement.",
            target_id=command.reimbursement_id,
        )

    try:
        snapshot = port.read_reimbursement(command.reimbursement_id)
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Lecture du remboursement impossible avant suppression : %s" % exc,
            target_id=command.reimbursement_id,
        )

    if snapshot is None or snapshot.person_id != command.person_id:
        return WriteResult(
            ok=False,
            code=WriteCode.TARGET_NOT_FOUND,
            message="Le remboursement sélectionné n'existe plus pour cette personne.",
            target_id=command.reimbursement_id,
        )

    if snapshot.trip_ids and not command.confirm_attached_trips:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message=(
                "Le remboursement possède %d déplacement(s) rattaché(s) : "
                "leur détachement doit être confirmé explicitement."
            )
            % len(snapshot.trip_ids),
            target_id=command.reimbursement_id,
        )

    def _target_exists() -> bool:
        current = port.read_reimbursement(command.reimbursement_id)
        return current is not None and current.person_id == command.person_id

    def _write() -> int:
        port.detach_all_trips(command.reimbursement_id)
        return int(
            port.delete_reimbursement(
                command.reimbursement_id,
                command.person_id,
            )
        )

    def _readback_exists() -> bool:
        if port.read_reimbursement(command.reimbursement_id) is not None:
            return True
        return bool(port.has_trip_assignment(command.reimbursement_id))

    result = execute_transactional_delete(
        target_id=command.reimbursement_id,
        target_exists=_target_exists,
        write=_write,
        commit=port.commit,
        rollback=port.rollback,
        readback_exists=_readback_exists,
    )
    if result.ok:
        return WriteResult(
            ok=True,
            code=WriteCode.OK,
            message="Remboursement supprimé, déplacements détachés et absence confirmée.",
            target_id=command.reimbursement_id,
            value=True,
            committed=True,
        )
    return result
