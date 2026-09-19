"""Contrat minimal pour exécuter une écriture métier transactionnelle.

Ce module ne dépend d'aucun toolkit UI ni d'un moteur SQL particulier.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, Optional, TypeVar


T = TypeVar("T")


class WriteCode:
    OK = "OK"
    INVALID_TARGET_ID = "INVALID_TARGET_ID"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    TARGET_NOT_FOUND = "TARGET_NOT_FOUND"
    UNEXPECTED_ROWCOUNT = "UNEXPECTED_ROWCOUNT"
    DATABASE_ERROR = "DATABASE_ERROR"
    READBACK_ERROR = "READBACK_ERROR"


@dataclass(frozen=True)
class WriteResult(Generic[T]):
    ok: bool
    code: str
    message: str
    target_id: Optional[int] = None
    value: Optional[T] = None
    committed: bool = False


def invalid_target_result(target_id: object) -> WriteResult[object]:
    return WriteResult(
        ok=False,
        code=WriteCode.INVALID_TARGET_ID,
        message="Identifiant métier cible invalide.",
        target_id=target_id if isinstance(target_id, int) and not isinstance(target_id, bool) else None,
    )


def is_valid_target_id(target_id: object) -> bool:
    return isinstance(target_id, int) and not isinstance(target_id, bool) and target_id > 0


def _safe_rollback(rollback: Callable[[], None]) -> None:
    try:
        rollback()
    except Exception:
        # Le rollback est une tentative de remise en cohérence. L'erreur métier
        # initiale reste prioritaire et doit être remontée au caller.
        pass


def execute_transactional_insert(
    *,
    write: Callable[[], int],
    commit: Callable[[], None],
    rollback: Callable[[], None],
    readback: Callable[[int], T],
) -> WriteResult[T]:
    """Exécute un INSERT atomique, exige un ID créé valide, puis relit la cible."""

    created_id = None
    try:
        created_id = write()
        if not is_valid_target_id(created_id):
            _safe_rollback(rollback)
            return WriteResult(
                ok=False,
                code=WriteCode.INVALID_TARGET_ID,
                message="L'écriture n'a pas retourné d'identifiant métier valide.",
            )
        commit()
    except Exception as exc:
        _safe_rollback(rollback)
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Création en base impossible : %s" % exc,
            target_id=created_id if is_valid_target_id(created_id) else None,
        )

    try:
        value = readback(created_id)
        if value is None:
            raise LookupError("La cible créée est introuvable après commit.")
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.READBACK_ERROR,
            message="Création validée, mais relecture impossible : %s" % exc,
            target_id=created_id,
            committed=True,
        )

    return WriteResult(
        ok=True,
        code=WriteCode.OK,
        message="Création validée.",
        target_id=created_id,
        value=value,
        committed=True,
    )


def execute_transactional_update(
    *,
    target_id: object,
    target_exists: Callable[[], bool],
    write: Callable[[], int],
    commit: Callable[[], None],
    rollback: Callable[[], None],
    readback: Callable[[], T],
) -> WriteResult[T]:
    """Exécute une mise à jour atomique et vérifie sa cible.

    La relecture intervient après le commit. Si elle échoue, l'écriture reste
    signalée comme commitée : on ne prétend pas pouvoir rollbacker un commit
    déjà confirmé.
    """

    if not is_valid_target_id(target_id):
        return invalid_target_result(target_id)

    try:
        exists = bool(target_exists())
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Vérification de la cible impossible : %s" % exc,
            target_id=target_id,
        )

    if not exists:
        return WriteResult(
            ok=False,
            code=WriteCode.TARGET_NOT_FOUND,
            message="La cible n'existe plus.",
            target_id=target_id,
        )

    try:
        affected = int(write())
        if affected == 0:
            _safe_rollback(rollback)
            return WriteResult(
                ok=False,
                code=WriteCode.TARGET_NOT_FOUND,
                message="La cible a disparu avant l'écriture.",
                target_id=target_id,
            )
        if affected != 1:
            _safe_rollback(rollback)
            return WriteResult(
                ok=False,
                code=WriteCode.UNEXPECTED_ROWCOUNT,
                message="Nombre de lignes modifiées inattendu : %s." % affected,
                target_id=target_id,
            )
        commit()
    except Exception as exc:
        _safe_rollback(rollback)
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Écriture en base impossible : %s" % exc,
            target_id=target_id,
        )

    try:
        value = readback()
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.READBACK_ERROR,
            message="Écriture validée, mais relecture impossible : %s" % exc,
            target_id=target_id,
            committed=True,
        )

    return WriteResult(
        ok=True,
        code=WriteCode.OK,
        message="Écriture validée.",
        target_id=target_id,
        value=value,
        committed=True,
    )
