"""Concept métier minimal d'avenant rattaché à un contrat existant.

Un avenant ne crée pas un second CDI/CDD. Il décrit une modification de clauses
sur le même contrat historique. Les opérations qui produisent un nouveau contrat
(CDD_RENEWAL, CDD_TO_CDI) restent dans ``contract_operation``.
"""

from __future__ import annotations

from enum import Enum


class ContractAmendmentKind(str, Enum):
    """Nature dominante des clauses modifiées par un avenant."""

    CONTRACT_TERM = "CONTRACT_TERM"
    WORKING_TIME = "WORKING_TIME"
    REMUNERATION = "REMUNERATION"
    CLASSIFICATION = "CLASSIFICATION"
    QUALIFICATION = "QUALIFICATION"
    MULTI_CLAUSE = "MULTI_CLAUSE"


_FIELD_KIND = {
    "start_date": ContractAmendmentKind.CONTRACT_TERM,
    "end_date": ContractAmendmentKind.CONTRACT_TERM,
    "break_date": ContractAmendmentKind.CONTRACT_TERM,
    "weekly_hours": ContractAmendmentKind.WORKING_TIME,
    "gross_monthly_salary": ContractAmendmentKind.REMUNERATION,
    "gross_annual_salary": ContractAmendmentKind.REMUNERATION,
    "ccns_group": ContractAmendmentKind.CLASSIFICATION,
    "cee_qualification": ContractAmendmentKind.QUALIFICATION,
}


def amendment_kind_for_fields(changed_fields: tuple[str, ...]) -> ContractAmendmentKind:
    """Déduit une nature stable depuis les champs réellement modifiés."""

    kinds = {_FIELD_KIND[name] for name in changed_fields if name in _FIELD_KIND}
    if len(kinds) == 1:
        return next(iter(kinds))
    return ContractAmendmentKind.MULTI_CLAUSE
