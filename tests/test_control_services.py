from datetime import date, datetime

from application.control.dashboard_service import ControlDashboardService
from application.control.contract_control_service import ContractControlService
from application.control.assignment_control_service import AssignmentControlService
from domain.activity.assignment import Assignment
from domain.contracts.contract import Contract
from domain.contracts.contract_type import ContractType
from domain.contracts.employment_regime import EmploymentRegime
from domain.contracts.time_organization import TimeOrganization
from domain.engine.anomaly import Anomaly
from domain.engine.anomaly_level import AnomalyLevel
from domain.engine.calculation_result import CalculationResult
from domain.engine.result_status import ResultStatus


def _contract() -> Contract:
    return Contract(
        person_id="person-1",
        contract_type=ContractType.CDI,
        employment_regime=EmploymentRegime.CCNS_STANDARD,
        time_organization=TimeOrganization.WEEKLY_CONSTANT,
        start_date=date(2026, 9, 1),
        ccns_classification_code="G3",
        salary_grid_code="CCNS-2026",
        base_salary_amount=1800.0,
        salary_unit="monthly",
    )


def _assignment(contract_id: str) -> Assignment:
    return Assignment(
        person_id="person-1",
        period_id="period-1",
        activity_id="activity-1",
        title="Séance sport",
        starts_at=datetime(2026, 9, 7, 18, 0),
        ends_at=datetime(2026, 9, 7, 21, 0),
        contract_id=contract_id,
        prep_ratio=0.3333,
        auto_prep_minutes=60,
    )


def test_dashboard_service_builds_counters_and_rows():
    anomaly = Anomaly(
        object_type="contract",
        object_id="contract-1",
        contract_id="contract-1",
        level=AnomalyLevel.ATTENTION,
        code="MINIMUM_CCNS_NON_ATTEINT",
        message="Rémunération inférieure au minimum.",
        detection_date=date(2026, 9, 7),
    )
    result = CalculationResult(
        object_type="contract",
        object_id="contract-1",
        contract_id="contract-1",
        rule_code="MINIMUM_FROM_GRID",
        status=ResultStatus.WARNING,
        readable_message="Rémunération inférieure au minimum de grille",
    )
    service = ControlDashboardService()
    counters = service.build_counters(anomalies=[anomaly], calculation_results=[result])
    rows = service.build_rows(anomalies=[anomaly])
    assert len(counters) == 5
    assert rows[0].code == "MINIMUM_CCNS_NON_ATTEINT"


def test_contract_control_view_contains_results_and_anomalies():
    contract = _contract()
    result = CalculationResult(
        object_type="contract",
        object_id=contract.id,
        contract_id=contract.id,
        person_id=contract.person_id,
        rule_code="MINIMUM_FROM_GRID",
        status=ResultStatus.WARNING,
        readable_message="Rémunération inférieure au minimum de grille",
    )
    anomaly = Anomaly(
        object_type="contract",
        object_id=contract.id,
        contract_id=contract.id,
        person_id=contract.person_id,
        level=AnomalyLevel.ATTENTION,
        code="MINIMUM_CCNS_NON_ATTEINT",
        message="Rémunération inférieure au minimum.",
        detection_date=date(2026, 9, 7),
    )
    service = ContractControlService()
    view = service.build_view(contract=contract, calculation_results=[result], anomalies=[anomaly])
    assert "MINIMUM_CCNS_NON_ATTEINT" in view.anomaly_codes
    assert "Rémunération inférieure au minimum de grille" in view.result_messages


def test_assignment_control_view_detects_main_support():
    contract = _contract()
    assignment = _assignment(contract.id)
    result = CalculationResult(
        object_type="assignment",
        object_id=assignment.id,
        assignment_id=assignment.id,
        person_id=assignment.person_id,
        rule_code="PREPA_SPORT_1_3",
        status=ResultStatus.INFO,
        readable_message="Préparation calculée",
    )
    service = AssignmentControlService()
    view = service.build_view(assignment=assignment, calculation_results=[result], anomalies=[])
    assert view.main_support_type == "contract"
    assert view.auto_prep_minutes == 60
