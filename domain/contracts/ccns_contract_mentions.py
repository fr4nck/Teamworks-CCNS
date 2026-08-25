from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
from types import MappingProxyType
from typing import Mapping, Optional

from domain.contracts.contract_type import ContractType
from domain.contracts.employment_regime import EmploymentRegime
from domain.contracts.time_organization import TimeOrganization


class ContractMentionCode(str, Enum):
    CONTRACT_NATURE = "contract_nature"
    EMPLOYER_LEGAL_NAME = "employer_legal_name"
    EMPLOYER_ADDRESS = "employer_address"
    EMPLOYEE_LAST_NAME = "employee_last_name"
    EMPLOYEE_FIRST_NAME = "employee_first_name"
    EMPLOYEE_NATIONALITY = "employee_nationality"
    WORK_AUTHORIZATION = "work_authorization"
    EMPLOYEE_IDENTIFICATION = "employee_identification"
    HIRE_DATE = "hire_date"
    WORKPLACE = "workplace"
    JOB_TITLE = "job_title"
    CCNS_CLASSIFICATION_GROUP = "ccns_classification_group"
    BASE_SALARY = "base_salary"
    REMUNERATION_COMPONENTS = "remuneration_components"
    REFERENCE_WORKING_TIME = "reference_working_time"
    SPECIAL_WORKING_CONDITIONS = "special_working_conditions"
    WEEKLY_REST_TERMS = "weekly_rest_terms"
    BENEFITS_IN_KIND = "benefits_in_kind"
    TRIAL_PERIOD_TERMS = "trial_period_terms"
    SOCIAL_SECURITY_BODY = "social_security_body"
    SOCIAL_SECURITY_REGISTRATION = "social_security_registration"
    RETIREMENT_FUND = "retirement_fund"
    WELFARE_FUND = "welfare_fund"
    COLLECTIVE_AGREEMENT_REFERENCE = "collective_agreement_reference"
    COLLECTIVE_AGREEMENT_CONSULTATION = "collective_agreement_consultation"

    PART_TIME_REFERENCE_PERIOD = "part_time_reference_period"
    PART_TIME_DISTRIBUTION = "part_time_distribution"
    PART_TIME_DISTRIBUTION_CHANGE_CASES = "part_time_distribution_change_cases"
    PART_TIME_DISTRIBUTION_CHANGE_NATURE = "part_time_distribution_change_nature"
    PART_TIME_NOTICE_PERIOD = "part_time_notice_period"
    PART_TIME_EXCEPTIONAL_NOTICE_RULE = "part_time_exceptional_notice_rule"
    PART_TIME_COMPLEMENTARY_HOURS_LIMITS = "part_time_complementary_hours_limits"
    PART_TIME_DAILY_SCHEDULE_COMMUNICATION = "part_time_daily_schedule_communication"
    PART_TIME_PLANNING_DELIVERY_DEADLINE = "part_time_planning_delivery_deadline"

    CDII_MINIMUM_ANNUAL_WORKING_TIME = "cdii_minimum_annual_working_time"
    CDII_WORK_PERIODS = "cdii_work_periods"
    CDII_HOURS_WITHIN_PERIODS = "cdii_hours_within_periods"
    CDII_PERIOD_MODIFICATION_CONDITIONS = "cdii_period_modification_conditions"
    CDII_ANNUAL_CYCLE_START_DATE = "cdii_annual_cycle_start_date"


@dataclass(frozen=True, slots=True)
class ContractMentionRequirement:
    code: ContractMentionCode
    label: str
    source_reference: str
    conditional: bool = False

    def __post_init__(self) -> None:
        if type(self.code) is not ContractMentionCode:
            raise TypeError("code doit être un ContractMentionCode.")
        if type(self.label) is not str or not self.label.strip():
            raise ValueError("label est obligatoire.")
        if type(self.source_reference) is not str or not self.source_reference.strip():
            raise ValueError("source_reference est obligatoire.")
        if type(self.conditional) is not bool:
            raise TypeError("conditional doit être un booléen.")


@dataclass(frozen=True, slots=True)
class ContractTermsSnapshot:
    """Photographie des mentions disponibles pour un contrat.

    ``values`` est volontairement générique : le moteur réglementaire ne dépend pas
    des contrôles wx ni du schéma historique Teamworks. La couche d'intégration
    convertira ensuite les champs de la fiche contrat vers ces codes stables.
    """

    contract_type: ContractType
    employment_regime: EmploymentRegime
    time_organization: TimeOrganization
    weekly_reference_hours: Optional[Decimal]
    work_ratio: Optional[Decimal]
    is_foreign_worker: Optional[bool]
    values: Mapping[ContractMentionCode, object]

    def __post_init__(self) -> None:
        if type(self.contract_type) is not ContractType:
            raise TypeError("contract_type doit être un ContractType.")
        if type(self.employment_regime) is not EmploymentRegime:
            raise TypeError("employment_regime doit être un EmploymentRegime.")
        if type(self.time_organization) is not TimeOrganization:
            raise TypeError("time_organization doit être un TimeOrganization.")
        if self.weekly_reference_hours is not None:
            if type(self.weekly_reference_hours) is not Decimal:
                raise TypeError("weekly_reference_hours doit être un Decimal strict ou None.")
            if self.weekly_reference_hours < Decimal("0.00"):
                raise ValueError("weekly_reference_hours ne peut pas être négatif.")
        if self.work_ratio is not None:
            if type(self.work_ratio) is not Decimal:
                raise TypeError("work_ratio doit être un Decimal strict ou None.")
            if not Decimal("0.00") < self.work_ratio <= Decimal("1.00"):
                raise ValueError("work_ratio doit être strictement positif et inférieur ou égal à 1.")
        if self.is_foreign_worker is not None and type(self.is_foreign_worker) is not bool:
            raise TypeError("is_foreign_worker doit être un booléen ou None.")
        if not isinstance(self.values, Mapping):
            raise TypeError("values doit être un mapping.")
        normalized: dict[ContractMentionCode, object] = {}
        for key, value in self.values.items():
            if type(key) is not ContractMentionCode:
                raise TypeError("Chaque clé de values doit être un ContractMentionCode.")
            normalized[key] = value
        object.__setattr__(self, "values", MappingProxyType(normalized))

    @property
    def is_standard_ccns_scope(self) -> bool:
        return self.employment_regime in {
            EmploymentRegime.CCNS_STANDARD,
            EmploymentRegime.CCNS_MODULATION,
            EmploymentRegime.CCNS_CDII,
        } and self.contract_type not in {
            item
            for item in (
                ContractType.CEE,
                ContractType.APPRENTICESHIP,
                getattr(ContractType, "INTERNSHIP", None),
                getattr(ContractType, "CIVIC_SERVICE", None),
            )
            if item is not None
        }

    @property
    def is_part_time(self) -> bool:
        if self.work_ratio is not None:
            return self.work_ratio < Decimal("1.00")
        if self.weekly_reference_hours is not None:
            return self.weekly_reference_hours < Decimal("35.00")
        return False

    @property
    def is_cdii(self) -> bool:
        return (
            self.contract_type is ContractType.CDII
            or self.employment_regime is EmploymentRegime.CCNS_CDII
            or self.time_organization is TimeOrganization.INTERMITTENCE
        )


@dataclass(frozen=True, slots=True)
class ContractComplianceResult:
    applicable: bool
    requirements: tuple[ContractMentionRequirement, ...]
    missing_requirements: tuple[ContractMentionRequirement, ...]
    present_requirement_codes: tuple[ContractMentionCode, ...]
    unresolved_conditional_codes: tuple[ContractMentionCode, ...] = ()

    @property
    def is_compliant(self) -> bool:
        return self.applicable and not self.missing_requirements and not self.unresolved_conditional_codes

    @property
    def missing_codes(self) -> tuple[ContractMentionCode, ...]:
        return tuple(item.code for item in self.missing_requirements)

    def missing_from_source(self, source_reference: str) -> tuple[ContractMentionRequirement, ...]:
        return tuple(item for item in self.missing_requirements if item.source_reference == source_reference)


ARTICLE_4_2_1 = "CCNS 1er mars 2026, article 4.2.1"
ARTICLE_4_5_2 = "CCNS 1er mars 2026, article 4.5.2"
ARTICLE_5_1_5_3 = "CCNS 1er mars 2026, article 5.1.5.3"


_BASE_REQUIREMENTS = (
    ContractMentionRequirement(ContractMentionCode.CONTRACT_NATURE, "Nature du contrat", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.EMPLOYER_LEGAL_NAME, "Raison sociale de l'employeur", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.EMPLOYER_ADDRESS, "Adresse de l'employeur", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.EMPLOYEE_LAST_NAME, "Nom du salarié", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.EMPLOYEE_FIRST_NAME, "Prénom du salarié", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.EMPLOYEE_NATIONALITY, "Nationalité du salarié", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.EMPLOYEE_IDENTIFICATION, "Numéro national d'identification ou, à défaut, date et lieu de naissance", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.HIRE_DATE, "Date d'embauche", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.WORKPLACE, "Lieu de travail", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.JOB_TITLE, "Dénomination de l'emploi", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.CCNS_CLASSIFICATION_GROUP, "Groupe de classification", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.BASE_SALARY, "Salaire de base", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.REMUNERATION_COMPONENTS, "Différents éléments de la rémunération", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.REFERENCE_WORKING_TIME, "Durée de travail de référence", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.SPECIAL_WORKING_CONDITIONS, "Conditions particulières de travail et sujétions particulières", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.WEEKLY_REST_TERMS, "Modalités de prise du repos hebdomadaire", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.BENEFITS_IN_KIND, "Avantages en nature et modalités de cessation", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.TRIAL_PERIOD_TERMS, "Modalités de la période d'essai", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.SOCIAL_SECURITY_BODY, "Organisme de versement des cotisations de sécurité sociale", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.SOCIAL_SECURITY_REGISTRATION, "Numéro sous lequel les cotisations de sécurité sociale sont versées", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.RETIREMENT_FUND, "Caisse de retraite complémentaire", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.WELFARE_FUND, "Caisse de prévoyance", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.COLLECTIVE_AGREEMENT_REFERENCE, "Référence à la Convention collective nationale du sport", ARTICLE_4_2_1),
    ContractMentionRequirement(ContractMentionCode.COLLECTIVE_AGREEMENT_CONSULTATION, "Modalités de consultation de la convention collective sur le lieu de travail", ARTICLE_4_2_1),
)

_FOREIGN_WORKER_REQUIREMENT = ContractMentionRequirement(
    ContractMentionCode.WORK_AUTHORIZATION,
    "Type et numéro du titre valant autorisation de travail pour un salarié étranger",
    ARTICLE_4_2_1,
    conditional=True,
)

_PART_TIME_REQUIREMENTS = (
    ContractMentionRequirement(ContractMentionCode.PART_TIME_REFERENCE_PERIOD, "Période de référence du temps partiel", ARTICLE_5_1_5_3),
    ContractMentionRequirement(ContractMentionCode.PART_TIME_DISTRIBUTION, "Répartition de la durée du travail", ARTICLE_5_1_5_3),
    ContractMentionRequirement(ContractMentionCode.PART_TIME_DISTRIBUTION_CHANGE_CASES, "Cas permettant une modification de la répartition", ARTICLE_5_1_5_3),
    ContractMentionRequirement(ContractMentionCode.PART_TIME_DISTRIBUTION_CHANGE_NATURE, "Nature des modifications possibles de la répartition", ARTICLE_5_1_5_3),
    ContractMentionRequirement(ContractMentionCode.PART_TIME_NOTICE_PERIOD, "Délai de prévenance des modifications", ARTICLE_5_1_5_3),
    ContractMentionRequirement(ContractMentionCode.PART_TIME_EXCEPTIONAL_NOTICE_RULE, "Règle de réduction exceptionnelle du délai de prévenance", ARTICLE_5_1_5_3),
    ContractMentionRequirement(ContractMentionCode.PART_TIME_COMPLEMENTARY_HOURS_LIMITS, "Limites concernant les heures complémentaires", ARTICLE_5_1_5_3),
    ContractMentionRequirement(ContractMentionCode.PART_TIME_DAILY_SCHEDULE_COMMUNICATION, "Modalités de communication écrite des horaires de chaque journée travaillée", ARTICLE_5_1_5_3),
    ContractMentionRequirement(ContractMentionCode.PART_TIME_PLANNING_DELIVERY_DEADLINE, "Délai de transmission du planning", ARTICLE_5_1_5_3),
)

_CDII_REQUIREMENTS = (
    ContractMentionRequirement(ContractMentionCode.CDII_MINIMUM_ANNUAL_WORKING_TIME, "Durée minimale annuelle de travail", ARTICLE_4_5_2),
    ContractMentionRequirement(ContractMentionCode.CDII_WORK_PERIODS, "Périodes de travail", ARTICLE_4_5_2),
    ContractMentionRequirement(ContractMentionCode.CDII_HOURS_WITHIN_PERIODS, "Répartition des heures de travail à l'intérieur des périodes", ARTICLE_4_5_2),
    ContractMentionRequirement(ContractMentionCode.CDII_PERIOD_MODIFICATION_CONDITIONS, "Conditions de modification des périodes de travail", ARTICLE_4_5_2),
    ContractMentionRequirement(ContractMentionCode.CDII_ANNUAL_CYCLE_START_DATE, "Date de début du cycle annuel de 12 mois", ARTICLE_4_5_2),
)


class CCNSContractComplianceService:
    """Évalue les mentions contractuelles exigées par les articles ciblés de la CCNS.

    Ce service contrôle uniquement la présence des données. Il ne prétend pas encore
    valider la formulation juridique du document généré : ce second niveau pourra être
    ajouté sans modifier les codes stables des mentions.
    """

    def requirements_for(self, snapshot: ContractTermsSnapshot) -> tuple[ContractMentionRequirement, ...]:
        if type(snapshot) is not ContractTermsSnapshot:
            raise TypeError("snapshot doit être un ContractTermsSnapshot.")
        if not snapshot.is_standard_ccns_scope:
            return ()
        requirements = list(_BASE_REQUIREMENTS)
        if snapshot.is_foreign_worker is True:
            requirements.append(_FOREIGN_WORKER_REQUIREMENT)
        if snapshot.is_part_time:
            requirements.extend(_PART_TIME_REQUIREMENTS)
        if snapshot.is_cdii:
            requirements.extend(_CDII_REQUIREMENTS)
        return tuple(requirements)

    def evaluate(self, snapshot: ContractTermsSnapshot) -> ContractComplianceResult:
        if type(snapshot) is not ContractTermsSnapshot:
            raise TypeError("snapshot doit être un ContractTermsSnapshot.")
        requirements = self.requirements_for(snapshot)
        if not snapshot.is_standard_ccns_scope:
            return ContractComplianceResult(
                applicable=False,
                requirements=(),
                missing_requirements=(),
                present_requirement_codes=(),
                unresolved_conditional_codes=(),
            )
        missing: list[ContractMentionRequirement] = []
        present: list[ContractMentionCode] = []
        for requirement in requirements:
            value = snapshot.values.get(requirement.code)
            if _is_present(value):
                present.append(requirement.code)
            else:
                missing.append(requirement)
        unresolved = (
            (ContractMentionCode.WORK_AUTHORIZATION,)
            if snapshot.is_foreign_worker is None
            else ()
        )
        return ContractComplianceResult(
            applicable=True,
            requirements=requirements,
            missing_requirements=tuple(missing),
            present_requirement_codes=tuple(present),
            unresolved_conditional_codes=unresolved,
        )


def _is_present(value: object) -> bool:
    if value is None:
        return False
    if type(value) is str:
        return bool(value.strip())
    if isinstance(value, (tuple, list, set, frozenset, dict)):
        return bool(value)
    return True
