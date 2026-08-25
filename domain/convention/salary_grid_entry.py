from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP, localcontext
from enum import Enum
from uuid import UUID, uuid4

from domain.convention.classification import CCNSClassification


class SalaryMinimumPeriodicity(str, Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


def _quantize_money(value: Decimal) -> Decimal:
    """Quantifie un montant sans dépendre du contexte Decimal global.

    Le runtime historique Teamworks peut modifier la précision globale de
    ``decimal``. Les règles conventionnelles doivent rester déterministes,
    notamment pour les minima annuels G7/G8.
    """
    digits = len(value.as_tuple().digits)
    with localcontext() as context:
        context.prec = max(28, digits + 4)
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True, slots=True)
class SalaryGridEntry:
    classification_group: CCNSClassification
    amount: Decimal
    periodicity: SalaryMinimumPeriodicity
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if type(self.classification_group) is not CCNSClassification:
            raise TypeError("classification_group doit être un CCNSClassification.")
        if type(self.amount) is not Decimal:
            raise TypeError("amount doit être un Decimal strict.")
        if self.amount <= Decimal("0"):
            raise ValueError("amount doit être strictement supérieur à zéro.")
        if type(self.periodicity) is not SalaryMinimumPeriodicity:
            raise TypeError("periodicity doit être un SalaryMinimumPeriodicity.")
        if type(self.id) is not UUID:
            raise TypeError("id doit être un UUID strict.")
        object.__setattr__(self, "amount", _quantize_money(self.amount))

    def validate_ccns_periodicity(self) -> None:
        code = self.classification_group.code.strip().upper()
        if code in {f"G{number}" for number in range(1, 7)} and self.periodicity is not SalaryMinimumPeriodicity.MONTHLY:
            raise ValueError("Les groupes 1 à 6 doivent avoir un minimum mensuel.")
        if code in {"G7", "G8"} and self.periodicity is not SalaryMinimumPeriodicity.ANNUAL:
            raise ValueError("Les groupes 7 et 8 doivent avoir un minimum annuel.")

    def is_monthly(self) -> bool:
        return self.periodicity is SalaryMinimumPeriodicity.MONTHLY

    def is_annual(self) -> bool:
        return self.periodicity is SalaryMinimumPeriodicity.ANNUAL
