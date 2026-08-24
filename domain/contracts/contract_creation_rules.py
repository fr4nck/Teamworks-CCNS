from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Mapping, Optional

from domain.contracts.contract_type import ContractType


class ConventionCode(str, Enum):
    CCNS = "CCNS"
    ECLAT = "ECLAT"
    CENTRES_SOCIAUX = "CENTRES_SOCIAUX"
    OTHER = "OTHER"


class CEEQualification(str, Enum):
    BAFA_HOLDER = "BAFA_HOLDER"
    BAFA_TRAINEE = "BAFA_TRAINEE"
    UNQUALIFIED = "UNQUALIFIED"
    EQUIVALENT = "EQUIVALENT"
    BAFD_HOLDER = "BAFD_HOLDER"
    BAFD_TRAINEE = "BAFD_TRAINEE"


@dataclass(frozen=True, slots=True)
class ContractCreationContext:
    convention: ConventionCode
    contract_type: ContractType
    function_code: str = ""
    classification_code: Optional[str] = None
    cee_qualification: Optional[CEEQualification] = None


@dataclass(frozen=True, slots=True)
class CEERateDecision:
    qualification: CEEQualification
    employer_daily_rate: Decimal
    legal_minimum_daily_rate: Decimal
    effective_daily_rate: Decimal
    compliant: bool
    messages: tuple[str, ...] = ()


@dataclass(slots=True)
class ContractCreationRules:
    """Règles de saisie de contrat indépendantes de l'UI et de la base historique.

    Les barèmes CEE restent fournis par l'employeur. Le minimum légal est injecté
    au moment du contrôle afin d'éviter de coder en dur une valeur susceptible
    d'évoluer.
    """

    cee_employer_daily_rates: Mapping[CEEQualification, Decimal] = field(default_factory=dict)

    def validate_context(self, context: ContractCreationContext) -> tuple[str, ...]:
        errors: list[str] = []

        if not isinstance(context.convention, ConventionCode):
            errors.append("Convention inconnue.")
        if not isinstance(context.contract_type, ContractType):
            errors.append("Type de contrat inconnu.")

        if context.contract_type == ContractType.CEE:
            if context.cee_qualification is None:
                errors.append("La qualification CEE est obligatoire.")
            if context.classification_code:
                errors.append("Un CEE ne doit pas utiliser une classification conventionnelle CCNS.")
        else:
            if context.cee_qualification is not None:
                errors.append("La qualification CEE n'est autorisée que pour un contrat CEE.")

        if (
            context.convention == ConventionCode.CCNS
            and context.contract_type != ContractType.CEE
            and context.contract_type not in {ContractType.INTERNSHIP, ContractType.CIVIC_SERVICE}
            and not context.classification_code
        ):
            errors.append("La classification CCNS est obligatoire pour ce contrat.")

        return tuple(errors)

    def resolve_cee_daily_rate(
        self,
        qualification: CEEQualification,
        *,
        legal_minimum_daily_rate: Decimal,
    ) -> CEERateDecision:
        if not isinstance(qualification, CEEQualification):
            raise TypeError("qualification doit être un CEEQualification.")
        if type(legal_minimum_daily_rate) is not Decimal:
            raise TypeError("legal_minimum_daily_rate doit être un Decimal strict.")
        if legal_minimum_daily_rate < Decimal("0.00"):
            raise ValueError("legal_minimum_daily_rate ne peut pas être négatif.")

        employer_rate = self.cee_employer_daily_rates.get(qualification)
        if employer_rate is None:
            return CEERateDecision(
                qualification=qualification,
                employer_daily_rate=Decimal("0.00"),
                legal_minimum_daily_rate=legal_minimum_daily_rate,
                effective_daily_rate=legal_minimum_daily_rate,
                compliant=False,
                messages=("Aucun barème employeur CEE n'est configuré pour cette qualification.",),
            )

        if type(employer_rate) is not Decimal:
            raise TypeError("Les barèmes employeur CEE doivent être des Decimal stricts.")
        if employer_rate < Decimal("0.00"):
            raise ValueError("Un barème employeur CEE ne peut pas être négatif.")

        compliant = employer_rate >= legal_minimum_daily_rate
        messages: list[str] = []
        if not compliant:
            messages.append("Le barème employeur est inférieur au minimum légal CEE applicable.")

        return CEERateDecision(
            qualification=qualification,
            employer_daily_rate=employer_rate,
            legal_minimum_daily_rate=legal_minimum_daily_rate,
            effective_daily_rate=max(employer_rate, legal_minimum_daily_rate),
            compliant=compliant,
            messages=tuple(messages),
        )

    def allowed_classification_family(self, context: ContractCreationContext) -> Optional[str]:
        """Indique quelle famille de classification doit être proposée par l'UI."""
        if context.contract_type == ContractType.CEE:
            return None
        if context.convention == ConventionCode.CCNS:
            return "CCNS_GROUPS"
        if context.convention == ConventionCode.ECLAT:
            return "ECLAT_CLASSIFICATIONS"
        if context.convention == ConventionCode.CENTRES_SOCIAUX:
            return "CENTRES_SOCIAUX_CLASSIFICATIONS"
        return None
