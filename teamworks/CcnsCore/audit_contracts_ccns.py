#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

import GestionDB

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


def _fetch_salary_grid(db):
    req = """
    SELECT IDtw_salary_grid, code, label, convention_code, employment_regime_code, effective_date, end_date, source_reference
    FROM tw_salary_grids
    ORDER BY IDtw_salary_grid
    LIMIT 1;
    """
    db.ExecuterReq(req)
    rows = db.ResultatReq()
    if not rows:
        return None, []

    row = rows[0]
    grid = SalaryGrid(
        id=str(row[0]),
        code=row[1],
        label=row[2],
        convention_code=row[3] or "CCNS",
        employment_regime_code=row[4],
        effective_date=row[5],
        end_date=row[6],
        source_reference=row[7],
    )

    req = """
    SELECT IDtw_salary_grid_line, classification_code, minimum_type, amount, unit,
           age_min, age_max, execution_year_min, execution_year_max, notes
    FROM tw_salary_grid_lines
    WHERE IDtw_salary_grid=%d;
    """ % row[0]
    db.ExecuterReq(req)
    rows = db.ResultatReq()
    lines = []
    for item in rows:
        try:
            minimum_type = MinimumType(item[2])
        except Exception:
            minimum_type = MinimumType.MONTHLY
        lines.append(
            SalaryGridLine(
                id=str(item[0]),
                salary_grid_id=str(row[0]),
                classification_code=item[1],
                minimum_type=minimum_type,
                amount=item[3],
                unit=item[4],
                age_min=item[5],
                age_max=item[6],
                execution_year_min=item[7],
                execution_year_max=item[8],
                notes=item[9] or "",
            )
        )
    return grid, lines


def audit_contracts(limit=None):
    db = GestionDB.DB()

    req = """
    SELECT
        contrats.IDcontrat,
        contrats.date_debut,
        contrats.date_fin,
        contrats.salaire_base,
        contrats.temps_hebdo,
        contrats.prime_anciennete,
        individus.prenom,
        individus.nom,
        contrats_class.nom AS classification,
        contrats_types.nom AS type_contrat
    FROM contrats
    LEFT JOIN individus ON individus.IDindividu = contrats.IDpersonne
    LEFT JOIN contrats_class ON contrats_class.IDclassification = contrats.IDclassification
    LEFT JOIN contrats_types ON contrats_types.IDtype = contrats.IDtype
    ORDER BY contrats.IDcontrat;
    """
    if limit:
        req = req.replace("ORDER BY contrats.IDcontrat;", "ORDER BY contrats.IDcontrat LIMIT %d;" % int(limit))

    db.ExecuterReq(req)
    records = db.ResultatReq()

    salary_grid, salary_grid_lines = _fetch_salary_grid(db)
    results = []

    for rec in records:
        (
            IDcontrat,
            date_debut,
            date_fin,
            salaire_base,
            temps_hebdo,
            prime_anciennete,
            prenom,
            nom,
            classification,
            type_contrat_label,
        ) = rec

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

        for checker in (check_contract_has_classification, check_contract_has_salary_grid):
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
                reference_date=date.today(),
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

    db.Close()
    return results


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
