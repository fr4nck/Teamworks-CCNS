#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Optional


from domain.contracts.contract import Contract
from domain.contracts.contract_type import ContractType
from domain.contracts.employment_regime import EmploymentRegime
from domain.contracts.time_organization import TimeOrganization
from domain.engine.simple_checks import (
    check_contract_has_classification,
    check_contract_has_salary_grid,
)
from domain.engine.minimum_checks import check_contract_minimum_from_grid
from domain.engine.seniority import check_ccns_seniority_amount
from domain.convention.salary_grid import SalaryGrid
from domain.convention.salary_grid_line import SalaryGridLine
from domain.convention.minimum_type import MinimumType
from domain.convention.salary_grid_version import SalaryGridVersion
from infrastructure.persistence.ccns_data_reader import CcnsDataReader
from teamworks.Utils import UTILS_Diagnostic_performance as DiagnosticPerformance


@dataclass(frozen=True)
class SelectedGridRecord:
    grid_record: object | None
    fallback_reason: str | None = None


@dataclass
class AuditRow:
    IDcontrat: int
    nom_complet: str
    classification: Optional[str]
    type_contrat: Optional[str]
    salaire_base: Optional[float]
    anomalies: list[str]
    messages: list[str]


def _safe_date(value):
    return value if value else None


def _map_contract_type(label):
    mapping = {
        "CDI": ContractType.CDI,
        "CDD": ContractType.CDD,
        "CDII": ContractType.CDII,
        "APPRENTISSAGE": ContractType.APPRENTICESHIP,
        "CEE": ContractType.CEE,
    }
    if not label:
        return ContractType.OTHER
    return mapping.get(label.upper(), ContractType.OTHER)


def _map_employment_regime(contract_type):
    if contract_type == ContractType.CEE:
        return EmploymentRegime.CEE
    if contract_type == ContractType.APPRENTICESHIP:
        return EmploymentRegime.APPRENTICE
    if contract_type == ContractType.CDII:
        return EmploymentRegime.CCNS_CDII
    return EmploymentRegime.CCNS_STANDARD


def _map_time_org(contract_type):
    if contract_type == ContractType.CEE:
        return TimeOrganization.DAILY_CEE
    return TimeOrganization.WEEKLY_CONSTANT



def _as_date(value):
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        return date.fromisoformat(value)
    return None


def _grid_sort_key(grid_record):
    return (_as_date(grid_record.effective_date) or date.min, grid_record.IDtw_salary_grid)


def _fallback_grid_record(grid_records: Iterable[object], reference_date: date):
    records = sorted(grid_records, key=_grid_sort_key)
    applicable = [
        item
        for item in records
        if (_as_date(item.effective_date) is None or _as_date(item.effective_date) <= reference_date)
        and (_as_date(item.end_date) is None or reference_date <= _as_date(item.end_date))
    ]
    if applicable:
        return applicable[-1]
    return records[0] if records else None


def _select_applicable_version(versions: Iterable[SalaryGridVersion], reference_date: date) -> SalaryGridVersion | None:
    candidates = [version for version in versions if version.is_applicable_on(reference_date)]
    if not candidates:
        return None
    return max(candidates, key=lambda version: (version.effective_date, version.version, version.grid_code))


def _select_grid_record(grid_records: Iterable[object], versions: Iterable[SalaryGridVersion], reference_date: date) -> SelectedGridRecord:
    grids = list(grid_records)
    version_items = list(versions)
    with DiagnosticPerformance.mesurer(
        "transformation_python",
        "audit_contracts_ccns.selection_version",
        {"versions": len(version_items)},
    ):
        selected_version = _select_applicable_version(version_items, reference_date)

    if selected_version is None:
        with DiagnosticPerformance.mesurer(
            "transformation_python",
            "audit_contracts_ccns.recherche_grille",
            {"grilles": len(grids), "grid_code": None},
        ):
            selected_grid = _fallback_grid_record(grids, reference_date)
        reason = "aucune_version_applicable" if version_items else None
        if reason:
            DiagnosticPerformance.enregistrer_mesure(
                "transformation_python",
                "audit_contracts_ccns.recours_repli",
                0.0,
                {"motif": reason},
            )
        return SelectedGridRecord(selected_grid, reason)

    with DiagnosticPerformance.mesurer(
        "transformation_python",
        "audit_contracts_ccns.recherche_grille",
        {"grilles": len(grids), "grid_code": selected_version.grid_code},
    ):
        matching_grids = [item for item in grids if item.code == selected_version.grid_code]

    if len(matching_grids) == 1:
        return SelectedGridRecord(matching_grids[0])

    if len(matching_grids) > 1:
        selected_grid = sorted(matching_grids, key=lambda item: item.IDtw_salary_grid)[0]
        reason = "grille_dupliquee"
    else:
        selected_grid = _fallback_grid_record(grids, reference_date)
        reason = "version_sans_grille_reelle"

    DiagnosticPerformance.enregistrer_mesure(
        "transformation_python",
        "audit_contracts_ccns.recours_repli",
        0.0,
        {"motif": reason, "grid_code": selected_version.grid_code},
    )
    return SelectedGridRecord(selected_grid, reason)


def _read_grid_versions(reader) -> list[SalaryGridVersion]:
    read_versions = getattr(reader, "lire_versions_grilles", None)
    if read_versions is None:
        return []
    return list(read_versions())

def _build_salary_grid(grid_record, line_records):
    if grid_record is None:
        return None, []

    grid = SalaryGrid(
        id=str(grid_record.IDtw_salary_grid),
        code=grid_record.code,
        label=grid_record.label,
        convention_code=grid_record.convention_code or "CCNS",
        employment_regime_code=grid_record.employment_regime_code,
        effective_date=grid_record.effective_date,
        end_date=grid_record.end_date,
        source_reference=grid_record.source_reference,
    )

    lines = []
    for item in line_records:
        try:
            minimum_type = MinimumType(item.minimum_type)
        except Exception:
            minimum_type = MinimumType.MONTHLY
        lines.append(
            SalaryGridLine(
                id=str(item.IDtw_salary_grid_line),
                salary_grid_id=str(item.IDtw_salary_grid),
                classification_code=item.classification_code,
                minimum_type=minimum_type,
                amount=item.amount,
                unit=item.unit,
                age_min=item.age_min,
                age_max=item.age_max,
                execution_year_min=item.execution_year_min,
                execution_year_max=item.execution_year_max,
                notes=item.notes or "",
            )
        )
    return grid, lines


def audit_contracts(limit=None, data_reader=None, reference_date=None):
    reader = data_reader or CcnsDataReader()
    close_reader = data_reader is None
    try:
        records = reader.lire_contrats(limit=limit)
        control_date = reference_date or date.today()
        grid_records = reader.lire_grilles()
        grid_versions = _read_grid_versions(reader)
        selected_grid = _select_grid_record(grid_records, grid_versions, control_date)
        grid_record = selected_grid.grid_record
        line_records = reader.lire_lignes_grille(grid_record.IDtw_salary_grid) if grid_record else []
        with DiagnosticPerformance.mesurer("transformation_python", "audit_contracts_ccns.construction_grille"):
            salary_grid, salary_grid_lines = _build_salary_grid(grid_record, line_records)
        results = []
        controles_simples = (check_contract_has_classification, check_contract_has_salary_grid)

        with DiagnosticPerformance.mesurer("transformation_python", "audit_contracts_ccns.controles", {"contrats": len(records)}):
            for rec in records:
                IDcontrat = rec.IDcontrat
                date_debut = rec.date_debut
                date_fin = rec.date_fin
                salaire_base = rec.salaire_base
                temps_hebdo = rec.temps_hebdo
                prime_anciennete = rec.prime_anciennete
                prenom = rec.prenom
                nom = rec.nom
                classification = rec.classification
                type_contrat_label = rec.type_contrat

                full_name = ((prenom or "") + " " + (nom or "")).strip() or ("Contrat %d" % IDcontrat)
                contract_type = _map_contract_type(type_contrat_label)
                employment_regime = _map_employment_regime(contract_type)
                time_organization = _map_time_org(contract_type)

                contract = Contract(
                    id=str(IDcontrat),
                    person_id="legacy-%d" % IDcontrat,
                    contract_type=contract_type,
                    employment_regime=employment_regime,
                    time_organization=time_organization,
                    start_date=_safe_date(date_debut),
                    end_date=_safe_date(date_fin),
                    weekly_reference_hours=float(temps_hebdo) if temps_hebdo is not None else None,
                    ccns_classification_code=classification,
                    salary_grid_code=salary_grid.code if salary_grid else None,
                    base_salary_amount=float(salaire_base) if salaire_base is not None else None,
                    salary_unit="monthly",
                    contract_status="legacy",
                    work_ratio=1.0,
                )

                anomalies = []
                messages = []

                if selected_grid.fallback_reason:
                    messages.append("Sélection grille CCNS en repli : %s" % selected_grid.fallback_reason)

                for checker in controles_simples:
                    result, anomaly = checker(contract)
                    messages.append(result.readable_message)
                    if anomaly:
                        anomalies.append(anomaly.code)

                if salary_grid:
                    result, anomaly = check_contract_minimum_from_grid(
                        contract=contract,
                        salary_grid=salary_grid,
                        salary_grid_lines=salary_grid_lines,
                        reference_date=control_date,
                    )
                    messages.append(result.readable_message)
                    if anomaly:
                        anomalies.append(anomaly.code)

                if classification and classification.upper().startswith("G"):
                    result, anomaly = check_ccns_seniority_amount(
                        contract=contract,
                        reference_date=control_date,
                        smc_group_3_amount=1997.87,
                        actual_seniority_amount=float(prime_anciennete or 0.0),
                    )
                    messages.append(result.readable_message)
                    if anomaly:
                        anomalies.append(anomaly.code)

                results.append(
                    AuditRow(
                        IDcontrat=IDcontrat,
                        nom_complet=full_name,
                        classification=classification,
                        type_contrat=type_contrat_label,
                        salaire_base=float(salaire_base) if salaire_base is not None else None,
                        anomalies=anomalies,
                        messages=messages,
                    )
                )

        return results
    finally:
        if close_reader:
            reader.close()


if __name__ == "__main__":
    rows = audit_contracts(limit=50)
    print("Audit CCNS Teamworks termine")
    print("Contrats lus :", len(rows))
    for row in rows:
        print("")
        print("[%s] %s" % (row.IDcontrat, row.nom_complet))
        print("- classification :", row.classification)
        print("- type :", row.type_contrat)
        print("- anomalies :", ", ".join(row.anomalies) if row.anomalies else "aucune")
