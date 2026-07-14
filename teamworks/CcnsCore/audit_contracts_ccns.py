#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


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
from infrastructure.persistence.ccns_data_reader import CcnsDataReader
from teamworks.Utils import UTILS_Diagnostic_performance as DiagnosticPerformance


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


def audit_contracts(limit=None, data_reader=None):
    reader = data_reader or CcnsDataReader()
    close_reader = data_reader is None
    try:
        records = reader.lire_contrats(limit=limit)
        grid_records = reader.lire_grilles(limit=1)
        grid_record = grid_records[0] if grid_records else None
        line_records = reader.lire_lignes_grille(grid_record.IDtw_salary_grid) if grid_record else []
        with DiagnosticPerformance.mesurer("transformation_python", "audit_contracts_ccns.construction_grille"):
            salary_grid, salary_grid_lines = _build_salary_grid(grid_record, line_records)
        results = []
        reference_date = date.today()
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
                    )
                    messages.append(result.readable_message)
                    if anomaly:
                        anomalies.append(anomaly.code)

                if classification and classification.upper().startswith("G"):
                    result, anomaly = check_ccns_seniority_amount(
                        contract=contract,
                        reference_date=reference_date,
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
