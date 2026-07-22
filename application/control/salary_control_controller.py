from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from application.control.salary_control_consultation_use_case import (
    ConsultContractSalaryControlQuery,
    ConsultContractSalaryControlUseCase,
)
from application.presentation.salary_control_presenter import (
    ContractSalaryControlPresenter,
    ContractSalaryControlViewModel,
)
from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.contracts.contract_salary_control_query import ContractSalaryControlSortField, SortDirection
from domain.convention.smic import SmicTerritory


class ContractSalaryControlControllerErrorCode(str, Enum):
    INVALID_REFERENCE_DATE = "INVALID_REFERENCE_DATE"
    INVALID_TERRITORY = "INVALID_TERRITORY"
    INVALID_CONTRACT_IDS = "INVALID_CONTRACT_IDS"
    INVALID_EMPLOYEE_IDS = "INVALID_EMPLOYEE_IDS"
    INVALID_STATUSES = "INVALID_STATUSES"
    INVALID_SEARCH_TEXT = "INVALID_SEARCH_TEXT"
    INVALID_SHORTFALL_RANGE = "INVALID_SHORTFALL_RANGE"
    INVALID_SORT = "INVALID_SORT"
    INVALID_PAGINATION = "INVALID_PAGINATION"
    INVALID_REQUEST = "INVALID_REQUEST"


@dataclass(frozen=True, slots=True)
class ContractSalaryControlControllerError:
    code: ContractSalaryControlControllerErrorCode
    field: Optional[str]
    message: str
    technical_error_type: Optional[str] = None

    def __post_init__(self) -> None:
        if type(self.code) is not ContractSalaryControlControllerErrorCode:
            raise TypeError("code doit être un ContractSalaryControlControllerErrorCode.")
        if self.field is not None and type(self.field) is not str:
            raise TypeError("field doit être None ou une chaîne.")
        if type(self.message) is not str or not self.message.strip():
            raise ValueError("message doit être une chaîne non vide.")
        if self.technical_error_type is not None and type(self.technical_error_type) is not str:
            raise TypeError("technical_error_type doit être None ou une chaîne.")


@dataclass(frozen=True, slots=True)
class ContractSalaryControlControllerResult:
    successful: bool
    view_model: Optional[ContractSalaryControlViewModel]
    errors: tuple[ContractSalaryControlControllerError, ...] = ()

    def __post_init__(self) -> None:
        if type(self.successful) is not bool:
            raise TypeError("successful doit être un bool strict.")
        if self.view_model is not None and type(self.view_model) is not ContractSalaryControlViewModel:
            raise TypeError("view_model doit être None ou un ContractSalaryControlViewModel.")
        if type(self.errors) is not tuple:
            raise TypeError("errors doit être un tuple strict.")
        if any(type(error) is not ContractSalaryControlControllerError for error in self.errors):
            raise TypeError("errors doit contenir des ContractSalaryControlControllerError.")
        if self.successful:
            if self.view_model is None or self.errors:
                raise ValueError("Un succès doit contenir un view_model et aucune erreur.")
        elif self.view_model is not None or not self.errors:
            raise ValueError("Un échec attendu doit contenir des erreurs et aucun view_model.")

    @classmethod
    def success(cls, view_model: ContractSalaryControlViewModel) -> ContractSalaryControlControllerResult:
        return cls(True, view_model, ())

    @classmethod
    def failure(
        cls,
        errors: tuple[ContractSalaryControlControllerError, ...],
    ) -> ContractSalaryControlControllerResult:
        return cls(False, None, errors)


@dataclass(frozen=True, slots=True)
class ContractSalaryControlControllerRequest:
    reference_date: date
    territory: Optional[SmicTerritory] = None
    contract_ids: tuple[UUID, ...] = ()
    employee_ids: tuple[UUID, ...] = ()
    statuses: tuple[ContractSalaryControlStatus, ...] = ()
    search_text: Optional[str] = None
    minimum_shortfall_amount: Optional[Decimal] = None
    maximum_shortfall_amount: Optional[Decimal] = None
    sort_field: ContractSalaryControlSortField = ContractSalaryControlSortField.SOURCE_ORDER
    sort_direction: SortDirection = SortDirection.ASCENDING
    offset: int = 0
    limit: Optional[int] = None

    def to_application_query(self) -> ConsultContractSalaryControlQuery:
        query = ConsultContractSalaryControlQuery(
            reference_date=self.reference_date,
            territory=self.territory,
            contract_ids=self.contract_ids,
            employee_ids=self.employee_ids,
            statuses=self.statuses,
            search_text=self.search_text,
            minimum_shortfall_amount=self.minimum_shortfall_amount,
            maximum_shortfall_amount=self.maximum_shortfall_amount,
            sort_field=self.sort_field,
            sort_direction=self.sort_direction,
            offset=self.offset,
            limit=self.limit,
        )
        query.to_domain_query()
        return query

    def first_page(self) -> ContractSalaryControlControllerRequest:
        return replace(self, offset=0)


@dataclass(frozen=True, slots=True)
class ContractSalaryControlController:
    use_case: ConsultContractSalaryControlUseCase
    presenter: ContractSalaryControlPresenter

    def __post_init__(self) -> None:
        if type(self.use_case) is not ConsultContractSalaryControlUseCase:
            raise TypeError("use_case doit être un ConsultContractSalaryControlUseCase.")
        if type(self.presenter) is not ContractSalaryControlPresenter:
            raise TypeError("presenter doit être un ContractSalaryControlPresenter.")

    def execute(
        self,
        request: ContractSalaryControlControllerRequest,
    ) -> ContractSalaryControlControllerResult:
        if type(request) is not ContractSalaryControlControllerRequest:
            raise TypeError("request doit être un ContractSalaryControlControllerRequest.")
        try:
            query = request.to_application_query()
        except (TypeError, ValueError) as exc:
            return ContractSalaryControlControllerResult.failure((_request_error_from_exception(exc),))
        application_result = self.use_case.execute(query)
        view_model = self.presenter.present(application_result)
        return ContractSalaryControlControllerResult.success(view_model)


def _request_error_from_exception(exc: TypeError | ValueError) -> ContractSalaryControlControllerError:
    text = str(exc)
    field, code = _classify_request_error(text)
    return ContractSalaryControlControllerError(
        code=code,
        field=field,
        message=_message_for(code),
        technical_error_type=type(exc).__name__,
    )


def _classify_request_error(text: str) -> tuple[Optional[str], ContractSalaryControlControllerErrorCode]:
    checks = (
        ("reference_date", ContractSalaryControlControllerErrorCode.INVALID_REFERENCE_DATE, ("date",)),
        ("territory", ContractSalaryControlControllerErrorCode.INVALID_TERRITORY, ("territory",)),
        ("contract_ids", ContractSalaryControlControllerErrorCode.INVALID_CONTRACT_IDS, ("contract_ids",)),
        ("employee_ids", ContractSalaryControlControllerErrorCode.INVALID_EMPLOYEE_IDS, ("employee_ids",)),
        ("statuses", ContractSalaryControlControllerErrorCode.INVALID_STATUSES, ("statuses",)),
        ("search_text", ContractSalaryControlControllerErrorCode.INVALID_SEARCH_TEXT, ("search_text",)),
        (
            "minimum_shortfall_amount",
            ContractSalaryControlControllerErrorCode.INVALID_SHORTFALL_RANGE,
            ("minimum_shortfall_amount", "maximum_shortfall_amount"),
        ),
        ("sort_field", ContractSalaryControlControllerErrorCode.INVALID_SORT, ("sort_field", "sort_direction")),
        ("offset", ContractSalaryControlControllerErrorCode.INVALID_PAGINATION, ("offset", "limit")),
    )
    for field, code, markers in checks:
        if any(marker in text for marker in markers):
            return field, code
    return None, ContractSalaryControlControllerErrorCode.INVALID_REQUEST


def _message_for(code: ContractSalaryControlControllerErrorCode) -> str:
    return {
        ContractSalaryControlControllerErrorCode.INVALID_REFERENCE_DATE: "La date de référence est invalide.",
        ContractSalaryControlControllerErrorCode.INVALID_TERRITORY: "Le territoire est invalide.",
        ContractSalaryControlControllerErrorCode.INVALID_CONTRACT_IDS: "Le filtre des contrats est invalide.",
        ContractSalaryControlControllerErrorCode.INVALID_EMPLOYEE_IDS: "Le filtre des salariés est invalide.",
        ContractSalaryControlControllerErrorCode.INVALID_STATUSES: "Le filtre des statuts est invalide.",
        ContractSalaryControlControllerErrorCode.INVALID_SEARCH_TEXT: "Le texte de recherche est invalide.",
        ContractSalaryControlControllerErrorCode.INVALID_SHORTFALL_RANGE: "Les bornes de manque salarial sont invalides.",
        ContractSalaryControlControllerErrorCode.INVALID_SORT: "Le tri demandé est invalide.",
        ContractSalaryControlControllerErrorCode.INVALID_PAGINATION: "La pagination demandée est invalide.",
        ContractSalaryControlControllerErrorCode.INVALID_REQUEST: "La demande de consultation est invalide.",
    }[code]
