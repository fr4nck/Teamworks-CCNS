#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import NAMESPACE_URL, uuid5

from application.bootstrap.contract_salary_control_controller_factory import ContractSalaryControlControllerFactory
from application.control import ContractSalaryControlControllerRequest
from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.engine.seniority import check_ccns_seniority_amount
from domain.convention import (
    CCNSClassification,
    SalaryGridCatalog,
    SalaryGridEntry,
    SalaryGridVersion,
    SalaryMinimumPeriodicity,
    SmicTerritory,
    create_smic_catalog_2026,
)
from domain.convention.salary_grid_version_selector import SalaryGridVersionSelector
from infrastructure.persistence.ccns_data_reader import CcnsDataReader
from infrastructure.persistence.teamworks_contract_conversions import (
    as_date as _as_date,
    map_contract_type as _map_contract_type,
    map_employment_regime as _map_employment_regime,
    map_time_organization as _map_time_org,
)
from infrastructure.persistence.teamworks_contract_salary_control_provider import (
    HISTORICAL_FIXED_TERM_WITHOUT_END_DATE_REASON,
    TeamworksContractSalaryControlProvider,
    legacy_contract_uuid,
)
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


def _line_periodicity(line_record):
    minimum_type = line_record.minimum_type
    if isinstance(minimum_type, SalaryMinimumPeriodicity):
        return minimum_type
    normalized = str(minimum_type or SalaryMinimumPeriodicity.MONTHLY.value).strip().lower()
    try:
        return SalaryMinimumPeriodicity(normalized)
    except ValueError:
        return SalaryMinimumPeriodicity.MONTHLY


def _build_salary_grid_catalog(reader, grid_records):
    versions = []
    for grid_record in grid_records:
        line_records = reader.lire_lignes_grille(grid_record.IDtw_salary_grid)
        entries = tuple(
            SalaryGridEntry(
                CCNSClassification(
                    code=line.classification_code.strip().upper(),
                    label=line.classification_code.strip().upper(),
                ),
                Decimal(str(line.amount)),
                _line_periodicity(line),
                id=uuid5(NAMESPACE_URL, "teamworks-ccns:salary-grid-line:%s" % line.IDtw_salary_grid_line),
            )
            for line in line_records
            if line.classification_code and str(line.classification_code).strip()
        )
        if not entries:
            continue
        versions.append(
            SalaryGridVersion(
                code=grid_record.code,
                name=grid_record.label,
                effective_from=_as_date(grid_record.effective_date),
                effective_until=_as_date(grid_record.end_date),
                entries=entries,
                source_reference=grid_record.source_reference,
                id=uuid5(NAMESPACE_URL, "teamworks-ccns:salary-grid:%s" % grid_record.IDtw_salary_grid),
            )
        )
    return SalaryGridCatalog(tuple(versions)) if versions else None


def _salary_control_message(control_row):
    if control_row.status is ContractSalaryControlStatus.NON_COMPLIANT:
        return control_row.issue_message
    if control_row.status is ContractSalaryControlStatus.NOT_EVALUATED:
        return control_row.failure_message
    return "Rémunération conforme au minimum salarial applicable."


def _salary_control_anomaly(control_row):
    if control_row.status is ContractSalaryControlStatus.NON_COMPLIANT:
        return control_row.issue_code
    if control_row.status is ContractSalaryControlStatus.NOT_EVALUATED:
        reason = control_row.failure_reason.value if control_row.failure_reason is not None else "unknown"
        return "CONTROLE_SALARIAL_NON_EVALUABLE_%s" % reason.upper()
    return None


def _full_name(rec):
    return ((rec.prenom or "") + " " + (rec.nom or "")).strip() or ("Contrat %d" % rec.IDcontrat)


def _append_seniority_control(rec, control_date, anomalies, messages):
    if not rec.classification or not rec.classification.upper().startswith("G"):
        return
    provider = TeamworksContractSalaryControlProvider(data_reader=_NoReadReader(), records=(rec,))
    contract = next(iter(provider.list_for_salary_control()))
    contract = replace(contract, id=str(contract.id), person_id=str(contract.person_id))
    result, anomaly = check_ccns_seniority_amount(
        contract=contract,
        reference_date=control_date,
        smc_group_3_amount=1997.87,
        actual_seniority_amount=float(rec.prime_anciennete or 0.0),
    )
    messages.append(result.readable_message)
    if anomaly:
        anomalies.append(anomaly.code)


def _audit_row(rec, anomalies, messages):
    return AuditRow(
        IDcontrat=rec.IDcontrat,
        nom_complet=_full_name(rec),
        classification=rec.classification,
        type_contrat=rec.type_contrat,
        salaire_base=float(rec.salaire_base) if rec.salaire_base is not None else None,
        anomalies=anomalies,
        messages=messages,
    )


def _audit_row_without_salary_grid(rec, control_date):
    anomalies = ["CONTRAT_SANS_GRILLE"]
    messages = ["Grille salariale manquante"]
    _append_seniority_control(rec, control_date, anomalies, messages)
    return _audit_row(rec, anomalies, messages)


def _audit_row_from_record(rec, control_row, control_date):
    anomalies = []
    messages = []
    salary_anomaly = _salary_control_anomaly(control_row)
    if salary_anomaly:
        anomalies.append(salary_anomaly)
    salary_message = _salary_control_message(control_row)
    if salary_message:
        messages.append(salary_message)
    if (
        getattr(control_row, "failure_reason", None) is not None
        and control_row.failure_reason.value == "historical_fixed_term_missing_end_date"
    ):
        if HISTORICAL_FIXED_TERM_WITHOUT_END_DATE_REASON not in anomalies:
            anomalies.append(HISTORICAL_FIXED_TERM_WITHOUT_END_DATE_REASON)
        messages.append("La date de fin est obligatoire pour ce contrat à durée déterminée.")

    _append_seniority_control(rec, control_date, anomalies, messages)
    return _audit_row(rec, anomalies, messages)


class _NoReadReader:
    def lire_contrats(self, limit=None):
        raise AssertionError("lecture contrat inattendue")


def audit_contracts(limit=None, data_reader=None, reference_date=None):
    reader = data_reader or CcnsDataReader()
    close_reader = data_reader is None
    try:
        records = reader.lire_contrats(limit=limit)
        if not records:
            return []
        control_date = reference_date or date.today()
        grid_records = reader.lire_grilles()
        version_reader = getattr(reader, "lire_versions_grilles", None)
        grid_versions = version_reader() if callable(version_reader) else None
        selected_grid = _select_salary_grid_record(grid_records, control_date, grid_versions)
        catalog_grid_records = [selected_grid] if selected_grid is not None else []
        with DiagnosticPerformance.mesurer("transformation_python", "audit_contracts_ccns.construction_catalogue_grilles"):
            salary_grid_catalog = _build_salary_grid_catalog(reader, catalog_grid_records)
        if salary_grid_catalog is None:
            return [_audit_row_without_salary_grid(rec, control_date) for rec in records]

        provider = TeamworksContractSalaryControlProvider(reader, records=tuple(records))
        controller = ContractSalaryControlControllerFactory().create_from_provider(
            contract_provider=provider,
            salary_grid_catalog=salary_grid_catalog,
            smic_catalog=create_smic_catalog_2026(),
        )
        control_result = controller.execute(
            ContractSalaryControlControllerRequest(
                reference_date=control_date,
                territory=SmicTerritory.METROPOLITAN_FRANCE,
            )
        )
        if not control_result.successful:
            message = "; ".join(error.message for error in control_result.errors)
            raise RuntimeError("Contrôle salarial CCNS invalide: %s" % message)
        rows_by_contract_id = {row.contract_id: row for row in control_result.view_model.rows}
        with DiagnosticPerformance.mesurer(
            "transformation_python",
            "audit_contracts_ccns.traduction_audit_rows",
            {"contrats": len(records)},
        ):
            return [
                _audit_row_from_record(rec, rows_by_contract_id[legacy_contract_uuid(rec.IDcontrat)], control_date)
                for rec in records
            ]
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
