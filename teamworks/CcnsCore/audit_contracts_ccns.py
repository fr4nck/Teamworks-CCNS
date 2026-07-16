#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
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
from domain.convention.salary_grid_version_selector import SalaryGridVersionSelector
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


def _grid_is_applicable(grid_record, reference_date):
    effective_date = _as_date(grid_record.effective_date) or date.min
    end_date = _as_date(grid_record.end_date)
    if reference_date < effective_date:
        return False
    if end_date and reference_date > end_date:
        return False
    return True


def _fallback_salary_grid_record(grid_records, reference_date):
    applicable = [grid for grid in grid_records if _grid_is_applicable(grid, reference_date)]
    if applicable:
        return sorted(
            applicable,
            key=lambda grid: (-(_as_date(grid.effective_date) or date.min).toordinal(), int(grid.IDtw_salary_grid)),
        )[0]
    return sorted(
        grid_records,
        key=lambda grid: ((_as_date(grid.effective_date) or date.max), int(grid.IDtw_salary_grid)),
    )[0]


def _diagnose_salary_grid_selection(event, grid_records, reference_date, selected_grid=None, extra=None):
    payload = {
        "evenement": event,
        "grilles": len(grid_records),
        "reference_date": reference_date.isoformat(),
    }
    if selected_grid is not None:
        payload.update(
            {
                "IDtw_salary_grid": selected_grid.IDtw_salary_grid,
                "code": selected_grid.code,
                "effective_date": str(selected_grid.effective_date),
            }
        )
    if extra:
        payload.update(extra)
    DiagnosticPerformance.enregistrer_mesure(
        "transformation_python",
        "audit_contracts_ccns.selection_grille.%s" % event,
        1.0,
        payload,
    )


def _select_salary_grid_record(grid_records, reference_date, grid_versions=None):
    """Sélectionne une grille réelle avec repli déterministe et diagnostic."""
    if not grid_records:
        _diagnose_salary_grid_selection("aucune_grille_reelle", grid_records, reference_date)
        return None

    selected_grid = None
    versions = tuple(grid_versions or ())
    if not versions:
        _diagnose_salary_grid_selection("aucune_version", grid_records, reference_date)
    else:
        selector = SalaryGridVersionSelector.from_iterable(versions)
        applicable_versions = [version for version in versions if version.is_applicable_on(reference_date)]
        if not applicable_versions:
            _diagnose_salary_grid_selection(
                "aucune_version_applicable",
                grid_records,
                reference_date,
                extra={"versions": len(versions)},
            )
        else:
            selected_version = max(applicable_versions, key=lambda version: (version.effective_date, version.version))
            # Conserver l'instrumentation de sélection du sélecteur dédié.
            selector.find_applicable_version(selected_version.grid_code, reference_date)
            matching_grids = [grid for grid in grid_records if grid.code == selected_version.grid_code]
            _diagnose_salary_grid_selection(
                "version_selectionnee",
                grid_records,
                reference_date,
                extra={"grid_code": selected_version.grid_code, "version": selected_version.version},
            )
            if matching_grids:
                if len(matching_grids) > 1:
                    _diagnose_salary_grid_selection(
                        "doublon_code_grille",
                        matching_grids,
                        reference_date,
                        extra={"grid_code": selected_version.grid_code},
                    )
                selected_grid = _fallback_salary_grid_record(matching_grids, reference_date)
            else:
                _diagnose_salary_grid_selection(
                    "version_sans_grille_reelle",
                    grid_records,
                    reference_date,
                    extra={"grid_code": selected_version.grid_code, "version": selected_version.version},
                )

    if selected_grid is None:
        selected_grid = _fallback_salary_grid_record(grid_records, reference_date)
        _diagnose_salary_grid_selection("repli_grille", grid_records, reference_date, selected_grid)

    _diagnose_salary_grid_selection("grille_selectionnee", grid_records, reference_date, selected_grid)
    return selected_grid


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
        version_reader = getattr(reader, "lire_versions_grilles", None)
        grid_versions = version_reader() if callable(version_reader) else None
        grid_record = _select_salary_grid_record(grid_records, control_date, grid_versions)
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
                end_date = _safe_date(date_fin)

                try:
                    contract = Contract(
                        id=str(IDcontrat),
                        person_id="legacy-%d" % IDcontrat,
                        contract_type=contract_type,
                        employment_regime=employment_regime,
                        time_organization=time_organization,
                        start_date=_safe_date(date_debut),
                        end_date=end_date,
                        weekly_reference_hours=float(temps_hebdo) if temps_hebdo is not None else None,
                        ccns_classification_code=classification,
                        salary_grid_code=salary_grid.code if salary_grid else None,
                        base_salary_amount=float(salaire_base) if salaire_base is not None else None,
                        salary_unit="monthly",
                        contract_status="legacy",
                        work_ratio=1.0,
                    )
                except ValueError as error:
                    if str(error) != "end_date is required for fixed-term contracts":
                        raise
                    results.append(
                        AuditRow(
                            IDcontrat=IDcontrat,
                            nom_complet=full_name,
                            classification=classification,
                            type_contrat=type_contrat_label,
                            salaire_base=float(salaire_base) if salaire_base is not None else None,
                            anomalies=["CONTRAT_A_DUREE_DETERMINEE_SANS_DATE_FIN"],
                            messages=["La date de fin est obligatoire pour ce contrat à durée déterminée."],
                        )
                    )
                    continue

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
