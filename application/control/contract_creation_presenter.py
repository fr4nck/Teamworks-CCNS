from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from domain.contracts.contract_creation_rules import CEEQualification, ConventionCode
from domain.contracts.contract_type import ContractType


CEE_QUALIFICATION_LABELS = {
    CEEQualification.BAFA_HOLDER: "BAFA titulaire",
    CEEQualification.BAFA_TRAINEE: "BAFA stagiaire",
    CEEQualification.UNQUALIFIED: "Non diplômé",
    CEEQualification.EQUIVALENT: "Qualification équivalente",
    CEEQualification.BAFD_HOLDER: "BAFD titulaire",
    CEEQualification.BAFD_TRAINEE: "BAFD stagiaire",
}


@dataclass(frozen=True, slots=True)
class ContractCreationViewState:
    convention: ConventionCode
    contract_type: ContractType
    classification_family: Optional[str]
    classification_label: str
    classification_required: bool
    show_classification: bool
    show_cee_qualification: bool
    show_point_value: bool
    trial_period_managed_by_rules: bool
    cee_qualification_choices: tuple[tuple[CEEQualification, str], ...] = ()
    warning: str = ""


class ContractCreationPresenter:
    """Traduit les règles métier en état d'affichage pour l'assistant historique.

    Cette couche ne lit ni n'écrit la base. Elle permet de moderniser l'écran wx
    sans modifier le schéma SQL des contrats existants.
    """

    def build_state(
        self,
        *,
        convention: ConventionCode,
        contract_type: ContractType,
        legacy_classification_present: bool = False,
    ) -> ContractCreationViewState:
        if not isinstance(convention, ConventionCode):
            raise TypeError("convention doit être un ConventionCode.")
        if not isinstance(contract_type, ContractType):
            raise TypeError("contract_type doit être un ContractType.")

        if contract_type == ContractType.CEE:
            warning = ""
            if legacy_classification_present:
                warning = (
                    "Ce contrat CEE historique contient une ancienne classification. "
                    "Elle reste conservée pour la compatibilité mais n'est plus utilisée comme classification conventionnelle."
                )
            return ContractCreationViewState(
                convention=convention,
                contract_type=contract_type,
                classification_family=None,
                classification_label="Qualification / statut CEE :",
                classification_required=False,
                show_classification=False,
                show_cee_qualification=True,
                show_point_value=False,
                trial_period_managed_by_rules=True,
                cee_qualification_choices=tuple(CEE_QUALIFICATION_LABELS.items()),
                warning=warning,
            )

        family = self._classification_family(convention)
        label = "Classification :"
        if convention == ConventionCode.CCNS:
            label = "Classification CCNS :"
        elif convention == ConventionCode.ECLAT:
            label = "Classification ÉCLAT :"
        elif convention == ConventionCode.CENTRES_SOCIAUX:
            label = "Classification Centres sociaux :"

        classification_required = (
            family is not None
            and contract_type not in {ContractType.INTERNSHIP, ContractType.CIVIC_SERVICE}
        )

        return ContractCreationViewState(
            convention=convention,
            contract_type=contract_type,
            classification_family=family,
            classification_label=label,
            classification_required=classification_required,
            show_classification=family is not None,
            show_cee_qualification=False,
            # L'ancien champ « valeur du point » n'est pas un pivot générique.
            # Les moteurs conventionnels calculeront le minimum selon leur propre grille.
            show_point_value=False,
            trial_period_managed_by_rules=True,
        )

    @staticmethod
    def _classification_family(convention: ConventionCode) -> Optional[str]:
        if convention == ConventionCode.CCNS:
            return "CCNS_GROUPS"
        if convention == ConventionCode.ECLAT:
            return "ECLAT_CLASSIFICATIONS"
        if convention == ConventionCode.CENTRES_SOCIAUX:
            return "CENTRES_SOCIAUX_CLASSIFICATIONS"
        return None
