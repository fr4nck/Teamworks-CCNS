"""Première frontière d'écriture Contrats indépendante de wx et Qt."""

from __future__ import annotations

from typing import Protocol

from application.services.transactional_write import (
    WriteCode,
    WriteResult,
    execute_transactional_update,
    invalid_target_result,
    is_valid_target_id,
)


ALLOWED_INDICATOR_FIELDS = frozenset(("signature", "due"))
ALLOWED_INDICATOR_VALUES = frozenset(("", "Oui"))


class ContractIndicatorWritePort(Protocol):
    def contract_exists(self, contract_id: int) -> bool:
        ...

    def update_indicator(self, contract_id: int, field: str, value: str) -> int:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...

    def read_indicator(self, contract_id: int, field: str) -> str:
        ...


def update_contract_indicator(
    port: ContractIndicatorWritePort,
    *,
    contract_id: object,
    field: str,
    value: str,
) -> WriteResult[str]:
    """Met à jour un indicateur historique du contrat par ID stable."""

    if not is_valid_target_id(contract_id):
        return invalid_target_result(contract_id)

    if field not in ALLOWED_INDICATOR_FIELDS:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message="Indicateur contrat non autorisé : %s." % field,
            target_id=contract_id,
        )

    if value not in ALLOWED_INDICATOR_VALUES:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message="Valeur d'indicateur contrat invalide.",
            target_id=contract_id,
        )

    if port is None:
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Aucun adaptateur d'écriture disponible.",
            target_id=contract_id,
        )

    return execute_transactional_update(
        target_id=contract_id,
        target_exists=lambda: port.contract_exists(contract_id),
        write=lambda: port.update_indicator(contract_id, field, value),
        commit=port.commit,
        rollback=port.rollback,
        readback=lambda: port.read_indicator(contract_id, field),
    )
