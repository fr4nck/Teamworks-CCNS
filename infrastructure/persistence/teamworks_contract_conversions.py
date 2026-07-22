from __future__ import annotations

from datetime import date, datetime

from domain.contracts.contract_type import ContractType
from domain.contracts.employment_regime import EmploymentRegime
from domain.contracts.time_organization import TimeOrganization


def as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None
    return None


def safe_date(value):
    return as_date(value)


def map_contract_type(label):
    mapping = {
        "CDI": ContractType.CDI,
        "CDD": ContractType.CDD,
        "CDII": ContractType.CDII,
        "APPRENTISSAGE": ContractType.APPRENTICESHIP,
        "APPRENTICESHIP": ContractType.APPRENTICESHIP,
        "CEE": ContractType.CEE,
        "STAGE": ContractType.INTERNSHIP,
        "INTERNSHIP": ContractType.INTERNSHIP,
        "SERVICE CIVIQUE": ContractType.CIVIC_SERVICE,
        "CIVIC_SERVICE": ContractType.CIVIC_SERVICE,
    }
    if not label:
        return ContractType.OTHER
    return mapping.get(label.upper(), ContractType.OTHER)


def map_employment_regime(contract_type):
    if contract_type == ContractType.CEE:
        return EmploymentRegime.CEE
    if contract_type == ContractType.APPRENTICESHIP:
        return EmploymentRegime.APPRENTICE
    if contract_type == ContractType.CIVIC_SERVICE:
        return EmploymentRegime.SERVICE_CIVIQUE
    if contract_type == ContractType.INTERNSHIP:
        return EmploymentRegime.STAGE_PFMP
    if contract_type == ContractType.CDII:
        return EmploymentRegime.CCNS_CDII
    return EmploymentRegime.CCNS_STANDARD


def map_time_organization(contract_type):
    if contract_type == ContractType.CEE:
        return TimeOrganization.DAILY_CEE
    return TimeOrganization.WEEKLY_CONSTANT
