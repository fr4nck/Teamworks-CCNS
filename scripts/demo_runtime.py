from __future__ import annotations

from datetime import date, datetime

from application.bootstrap.bootstrap_runtime import build_runtime_container
from application.control.dashboard_service import ControlDashboardService
from application.control.contract_control_service import ContractControlService
from application.control.assignment_control_service import AssignmentControlService
from domain.people.person import Person
from domain.people.legal_profile import LegalProfile, AgeGroup, ConventionFrame
from domain.contracts.contract import Contract
from domain.contracts.contract_type import ContractType
from domain.contracts.employment_regime import EmploymentRegime
from domain.contracts.time_organization import TimeOrganization
from domain.activity.assignment import Assignment
from domain.engine.simple_checks import (
    check_contract_has_classification,
    check_contract_has_salary_grid,
)
from domain.engine.minimum_checks import check_contract_minimum_from_grid
from domain.engine.seniority import check_ccns_seniority_amount


def main() -> None:
    runtime = build_runtime_container()

    person = Person(
        code_internal="SAL-001",
        first_name="Gaelle",
        last_name="Martin",
        birth_date=date(1990, 5, 14),
    )
    runtime.people.add(person)

    profile = LegalProfile(
        person_id=person.id,
        is_minor=False,
        age_group=AgeGroup.ADULT,
        work_regime="ccns_standard",
        convention_frame=ConventionFrame.CCNS,
        training_time_included=True,
        contract_hours_basis=35.0,
    )
    runtime.legal_profiles.add(profile)

    contract = Contract(
        person_id=person.id,
        contract_type=ContractType.CDI,
        employment_regime=EmploymentRegime.CCNS_STANDARD,
        time_organization=TimeOrganization.WEEKLY_CONSTANT,
        start_date=date(2022, 1, 1),
        ccns_classification_code="G3",
        salary_grid_code="CCNS-2026",
        base_salary_amount=1800.0,
        salary_unit="monthly",
        weekly_reference_hours=15.0,
        work_ratio=1.0,
        contract_status="active",
    )
    runtime.contracts.add(contract)

    assignment = Assignment(
        person_id=person.id,
        period_id="period-demo",
        activity_id="activity-demo",
        title="Séance sport santé",
        starts_at=datetime(2026, 9, 7, 18, 0),
        ends_at=datetime(2026, 9, 7, 21, 0),
        break_minutes=0,
        prep_ratio=0.3333,
        contract_id=contract.id,
        status="PLANNED",  # acceptable for the demo even if enum is usually preferred
    )
    assignment.compute_gross_duration_minutes()
    assignment.compute_auto_prep_minutes()
    runtime.assignments.add(assignment)

    results = []
    anomalies = []

    for checker in (check_contract_has_classification, check_contract_has_salary_grid):
        result, anomaly = checker(contract)
        results.append(result)
        runtime.calculation_results.add(result)
        if anomaly:
            anomalies.append(anomaly)
            runtime.anomalies.add(anomaly)

    grid = runtime.salary_grids.get_by_code("CCNS-2026")
    grid_lines = runtime.salary_grid_lines.list_by_grid_id(grid.id) if grid else []
    result, anomaly = check_contract_minimum_from_grid(
        contract=contract,
        salary_grid=grid,
        salary_grid_lines=grid_lines,
    )
    results.append(result)
    runtime.calculation_results.add(result)
    if anomaly:
        anomalies.append(anomaly)
        runtime.anomalies.add(anomaly)

    result, anomaly = check_ccns_seniority_amount(
        contract=contract,
        reference_date=date(2026, 9, 1),
        smc_group_3_amount=1997.87,
        actual_seniority_amount=0.0,
    )
    results.append(result)
    runtime.calculation_results.add(result)
    if anomaly:
        anomalies.append(anomaly)
        runtime.anomalies.add(anomaly)

    dashboard = ControlDashboardService()
    counters = dashboard.build_counters(
        anomalies=runtime.anomalies.list_all(),
        calculation_results=runtime.calculation_results.list_all(),
    )
    rows = dashboard.build_rows(anomalies=runtime.anomalies.list_all())

    contract_view = ContractControlService().build_view(
        contract=contract,
        calculation_results=runtime.calculation_results.list_by_contract_id(contract.id),
        anomalies=runtime.anomalies.list_by_contract_id(contract.id),
    )
    assignment_view = AssignmentControlService().build_view(
        assignment=assignment,
        calculation_results=runtime.calculation_results.list_by_assignment_id(assignment.id),
        anomalies=runtime.anomalies.list_by_assignment_id(assignment.id),
    )

    print("=== COMPTEURS ===")
    for counter in counters:
        print(f"- {counter.label}: {counter.value}")

    print("\n=== ANOMALIES ===")
    for row in rows:
        print(f"- [{row.level}] {row.code}: {row.message}")

    print("\n=== CONTRAT ===")
    print(f"Classification: {contract_view.classification_code}")
    print(f"Grille: {contract_view.salary_grid_code}")
    print(f"Salaire de base: {contract_view.base_salary_amount} {contract_view.salary_unit}")
    print("Résultats:")
    for message in contract_view.result_messages:
        print(f"  - {message}")
    print("Codes anomalies:")
    for code in contract_view.anomaly_codes:
        print(f"  - {code}")

    print("\n=== AFFECTATION ===")
    print(f"Durée brute: {assignment_view.gross_duration_minutes} min")
    print(f"Préparation auto: {assignment_view.auto_prep_minutes} min")
    print(f"Support principal: {assignment_view.main_support_type}")


if __name__ == "__main__":
    main()
