from __future__ import annotations

from dataclasses import dataclass, field
from functools import cmp_to_key
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from domain.contracts.contract_salary_control_projection import (
    ContractSalaryControlProjection,
    ContractSalaryControlRow,
    ContractSalaryControlStatus,
)
from domain.contracts.contract_salary_evaluation import ContractSalaryEvaluationFailureReason, _strict_uuid
from domain.convention import ApplicableSalaryMinimumSource
from domain.convention.smic import SmicTerritory

_CENT = Decimal("0.01")
_ZERO = Decimal("0.00")


class SortDirection(str, Enum):
    ASCENDING = "ascending"
    DESCENDING = "descending"


class ContractSalaryControlSortField(str, Enum):
    SOURCE_ORDER = "source_order"
    STATUS = "status"
    CONTRACT_ID = "contract_id"
    EMPLOYEE_ID = "employee_id"
    CLASSIFICATION_CODE = "classification_code"
    REMUNERATION_AMOUNT = "remuneration_amount"
    APPLICABLE_MINIMUM_AMOUNT = "applicable_minimum_amount"
    SHORTFALL_AMOUNT = "shortfall_amount"
    MINIMUM_SOURCE = "minimum_source"
    TERRITORY = "territory"
    FAILURE_REASON = "failure_reason"


def _strict_tuple(value: object, field_name: str, item_type: type) -> tuple:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} doit être un tuple strict.")
    seen = set()
    for item in value:
        if type(item) is not item_type:
            raise TypeError(f"{field_name} doit contenir uniquement des {item_type.__name__}.")
        if item in seen:
            raise ValueError(f"{field_name} ne doit pas contenir de doublons.")
        seen.add(item)
    return value


def _strict_non_empty_str_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} doit être un tuple strict.")
    cleaned_values: list[str] = []
    seen = set()
    for item in value:
        if type(item) is not str:
            raise TypeError(f"{field_name} doit contenir uniquement des chaînes.")
        cleaned = item.strip()
        if not cleaned:
            raise ValueError(f"{field_name} ne doit pas contenir de chaîne vide.")
        if cleaned in seen:
            raise ValueError(f"{field_name} ne doit pas contenir de doublons.")
        seen.add(cleaned)
        cleaned_values.append(cleaned)
    return tuple(cleaned_values)


def _strict_optional_amount(value: object, field_name: str) -> Optional[Decimal]:
    if value is None:
        return None
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} doit être None ou un Decimal strict.")
    if value != value.quantize(_CENT, rounding=ROUND_HALF_UP):
        raise ValueError(f"{field_name} doit être quantifié à deux décimales.")
    if value < _ZERO:
        raise ValueError(f"{field_name} doit être positif ou nul.")
    return value


@dataclass(frozen=True, slots=True)
class ContractSalaryControlQuery:
    statuses: tuple[ContractSalaryControlStatus, ...] = ()
    employee_ids: tuple[UUID, ...] = ()
    contract_ids: tuple[UUID, ...] = ()
    classification_codes: tuple[str, ...] = ()
    minimum_sources: tuple[ApplicableSalaryMinimumSource, ...] = ()
    territories: tuple[SmicTerritory, ...] = ()
    failure_reasons: tuple[ContractSalaryEvaluationFailureReason, ...] = ()
    has_shortfall: Optional[bool] = None
    minimum_shortfall_amount: Optional[Decimal] = None
    maximum_shortfall_amount: Optional[Decimal] = None
    search_text: Optional[str] = None
    sort_field: ContractSalaryControlSortField = ContractSalaryControlSortField.SOURCE_ORDER
    sort_direction: SortDirection = SortDirection.ASCENDING
    offset: int = 0
    limit: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "statuses", _strict_tuple(self.statuses, "statuses", ContractSalaryControlStatus))
        object.__setattr__(self, "employee_ids", _strict_tuple(self.employee_ids, "employee_ids", UUID))
        object.__setattr__(self, "contract_ids", _strict_tuple(self.contract_ids, "contract_ids", UUID))
        object.__setattr__(self, "classification_codes", _strict_non_empty_str_tuple(self.classification_codes, "classification_codes"))
        object.__setattr__(self, "minimum_sources", _strict_tuple(self.minimum_sources, "minimum_sources", ApplicableSalaryMinimumSource))
        object.__setattr__(self, "territories", _strict_tuple(self.territories, "territories", SmicTerritory))
        object.__setattr__(self, "failure_reasons", _strict_tuple(self.failure_reasons, "failure_reasons", ContractSalaryEvaluationFailureReason))
        if self.has_shortfall is not None and type(self.has_shortfall) is not bool:
            raise TypeError("has_shortfall doit être None ou un bool strict.")
        minimum = _strict_optional_amount(self.minimum_shortfall_amount, "minimum_shortfall_amount")
        maximum = _strict_optional_amount(self.maximum_shortfall_amount, "maximum_shortfall_amount")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError("minimum_shortfall_amount ne peut pas être supérieur à maximum_shortfall_amount.")
        if self.search_text is not None:
            if type(self.search_text) is not str:
                raise TypeError("search_text doit être None ou une chaîne.")
            cleaned = self.search_text.strip()
            if not cleaned:
                raise ValueError("search_text ne peut pas être vide après normalisation.")
            object.__setattr__(self, "search_text", cleaned)
        if type(self.sort_field) is not ContractSalaryControlSortField:
            raise TypeError("sort_field doit être un ContractSalaryControlSortField.")
        if type(self.sort_direction) is not SortDirection:
            raise TypeError("sort_direction doit être un SortDirection.")
        if type(self.offset) is not int:
            raise TypeError("offset doit être un int strict.")
        if self.offset < 0:
            raise ValueError("offset doit être supérieur ou égal à zéro.")
        if self.limit is not None:
            if type(self.limit) is not int:
                raise TypeError("limit doit être None ou un int strict.")
            if self.limit <= 0:
                raise ValueError("limit doit être strictement positif.")


@dataclass(frozen=True, slots=True)
class ContractSalaryControlPage:
    query: ContractSalaryControlQuery
    source_projection: ContractSalaryControlProjection
    filtered_rows: tuple[ContractSalaryControlRow, ...]
    rows: tuple[ContractSalaryControlRow, ...]
    total_source_count: int
    total_filtered_count: int
    offset: int
    limit: Optional[int]
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if type(self.query) is not ContractSalaryControlQuery:
            raise TypeError("query doit être un ContractSalaryControlQuery.")
        if type(self.source_projection) is not ContractSalaryControlProjection:
            raise TypeError("source_projection doit être un ContractSalaryControlProjection.")
        for name in ("filtered_rows", "rows"):
            value = getattr(self, name)
            if type(value) is not tuple:
                raise TypeError(f"{name} doit être un tuple strict.")
            if any(type(row) is not ContractSalaryControlRow for row in value):
                raise TypeError(f"{name} doit contenir des ContractSalaryControlRow.")
        if type(self.total_source_count) is not int or type(self.total_filtered_count) is not int or type(self.offset) is not int:
            raise TypeError("Les compteurs et offset doivent être des int stricts.")
        if self.limit is not None and type(self.limit) is not int:
            raise TypeError("limit doit être None ou un int strict.")
        _strict_uuid(self.id, "id")

    @property
    def returned_count(self) -> int:
        return len(self.rows)

    @property
    def has_previous_page(self) -> bool:
        return self.offset > 0

    @property
    def has_next_page(self) -> bool:
        return self.offset + self.returned_count < self.total_filtered_count

    @property
    def next_offset(self) -> Optional[int]:
        return self.offset + self.returned_count if self.has_next_page else None

    @property
    def previous_offset(self) -> Optional[int]:
        if self.offset == 0:
            return None
        page_size = self.limit if self.limit is not None else self.returned_count
        return max(0, self.offset - page_size)

    @property
    def compliant_count(self) -> int:
        return len(self.rows_for_status(ContractSalaryControlStatus.COMPLIANT))

    @property
    def non_compliant_count(self) -> int:
        return len(self.rows_for_status(ContractSalaryControlStatus.NON_COMPLIANT))

    @property
    def not_evaluated_count(self) -> int:
        return len(self.rows_for_status(ContractSalaryControlStatus.NOT_EVALUATED))

    @property
    def total_shortfall_amount(self) -> Decimal:
        return sum((row.shortfall_amount for row in self.filtered_rows), _ZERO).quantize(_CENT, rounding=ROUND_HALF_UP)

    @property
    def valid(self) -> bool:
        return all(row.status is ContractSalaryControlStatus.COMPLIANT for row in self.filtered_rows)

    @property
    def is_empty(self) -> bool:
        return self.returned_count == 0

    def row_for_contract(self, contract_id: UUID) -> Optional[ContractSalaryControlRow]:
        contract = _strict_uuid(contract_id, "contract_id")
        matches = tuple(row for row in self.filtered_rows if row.contract_id == contract)
        if len(matches) > 1:
            raise ValueError("Plusieurs lignes correspondent au même contract_id.")
        return matches[0] if matches else None

    def rows_for_employee(self, employee_id: UUID) -> tuple[ContractSalaryControlRow, ...]:
        employee = _strict_uuid(employee_id, "employee_id")
        return tuple(row for row in self.filtered_rows if row.employee_id == employee)

    def rows_for_status(self, status: ContractSalaryControlStatus) -> tuple[ContractSalaryControlRow, ...]:
        if type(status) is not ContractSalaryControlStatus:
            raise TypeError("status doit être un ContractSalaryControlStatus.")
        return tuple(row for row in self.filtered_rows if row.status is status)


@dataclass(frozen=True, slots=True)
class ContractSalaryControlQueryService:
    def execute(self, projection: ContractSalaryControlProjection, query: ContractSalaryControlQuery) -> ContractSalaryControlPage:
        if type(projection) is not ContractSalaryControlProjection:
            raise TypeError("projection doit être un ContractSalaryControlProjection.")
        if type(query) is not ContractSalaryControlQuery:
            raise TypeError("query doit être un ContractSalaryControlQuery.")
        indexed = tuple(enumerate(projection.rows))
        filtered = tuple((index, row) for index, row in indexed if self._matches(row, query))
        sorted_rows = self._sort(filtered, query)
        if query.limit is None:
            page_rows = sorted_rows[query.offset:]
        else:
            page_rows = sorted_rows[query.offset: query.offset + query.limit]
        return ContractSalaryControlPage(query, projection, sorted_rows, page_rows, projection.total_count, len(sorted_rows), query.offset, query.limit)

    def _matches(self, row: ContractSalaryControlRow, query: ContractSalaryControlQuery) -> bool:
        if query.statuses and row.status not in query.statuses:
            return False
        if query.employee_ids and row.employee_id not in query.employee_ids:
            return False
        if query.contract_ids and row.contract_id not in query.contract_ids:
            return False
        if query.classification_codes and row.classification_code not in query.classification_codes:
            return False
        if query.minimum_sources and row.minimum_source not in query.minimum_sources:
            return False
        if query.territories and row.territory not in query.territories:
            return False
        if query.failure_reasons and row.failure_reason not in query.failure_reasons:
            return False
        if query.has_shortfall is True and not row.shortfall_amount > _ZERO:
            return False
        if query.has_shortfall is False and row.shortfall_amount != _ZERO:
            return False
        if query.minimum_shortfall_amount is not None and row.shortfall_amount < query.minimum_shortfall_amount:
            return False
        if query.maximum_shortfall_amount is not None and row.shortfall_amount > query.maximum_shortfall_amount:
            return False
        if query.search_text is not None:
            needle = query.search_text.casefold()
            values = (row.classification_code, row.failure_message, row.issue_code, row.issue_message)
            if not any(value is not None and needle in value.casefold() for value in values):
                return False
        return True

    def _sort(self, indexed_rows: tuple[tuple[int, ContractSalaryControlRow], ...], query: ContractSalaryControlQuery) -> tuple[ContractSalaryControlRow, ...]:
        reverse = query.sort_direction is SortDirection.DESCENDING
        if query.sort_field is ContractSalaryControlSortField.SOURCE_ORDER:
            ordered = tuple(reversed(indexed_rows)) if reverse else indexed_rows
            return tuple(row for _, row in ordered)

        def normalized(value: object) -> object:
            if isinstance(value, UUID):
                return value.int
            if isinstance(value, Enum):
                return value.value
            return value

        def compare(left: tuple[int, ContractSalaryControlRow], right: tuple[int, ContractSalaryControlRow]) -> int:
            left_index, left_row = left
            right_index, right_row = right
            left_value = self._sort_value(left_row, query.sort_field)
            right_value = self._sort_value(right_row, query.sort_field)
            if left_value is None and right_value is not None:
                return 1
            if left_value is not None and right_value is None:
                return -1
            if left_value is not None and right_value is not None:
                normalized_left = normalized(left_value)
                normalized_right = normalized(right_value)
                if normalized_left < normalized_right:  # type: ignore[operator]
                    return -1 if not reverse else 1
                if normalized_left > normalized_right:  # type: ignore[operator]
                    return 1 if not reverse else -1
            if left_index < right_index:
                return -1
            if left_index > right_index:
                return 1
            return 0

        return tuple(row for _, row in sorted(indexed_rows, key=cmp_to_key(compare)))

    def _sort_value(self, row: ContractSalaryControlRow, field: ContractSalaryControlSortField) -> object:
        if field is ContractSalaryControlSortField.STATUS:
            return row.status
        if field is ContractSalaryControlSortField.CONTRACT_ID:
            return row.contract_id
        if field is ContractSalaryControlSortField.EMPLOYEE_ID:
            return row.employee_id
        if field is ContractSalaryControlSortField.CLASSIFICATION_CODE:
            return row.classification_code
        if field is ContractSalaryControlSortField.REMUNERATION_AMOUNT:
            return row.remuneration_amount
        if field is ContractSalaryControlSortField.APPLICABLE_MINIMUM_AMOUNT:
            return row.applicable_minimum_amount
        if field is ContractSalaryControlSortField.SHORTFALL_AMOUNT:
            return row.shortfall_amount
        if field is ContractSalaryControlSortField.MINIMUM_SOURCE:
            return row.minimum_source
        if field is ContractSalaryControlSortField.TERRITORY:
            return row.territory
        if field is ContractSalaryControlSortField.FAILURE_REASON:
            return row.failure_reason
        raise ValueError("Champ de tri non supporté.")
