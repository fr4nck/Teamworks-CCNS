from __future__ import annotations

from domain.activity.assignment import Assignment
from domain.engine.anomaly import Anomaly
from domain.engine.calculation_result import CalculationResult
from application.control.models import AssignmentControlView


class AssignmentControlService:
    def build_view(
        self,
        *,
        assignment: Assignment,
        calculation_results: list[CalculationResult],
        anomalies: list[Anomaly],
    ) -> AssignmentControlView:
        assignment_results = [r for r in calculation_results if r.assignment_id == assignment.id]
        assignment_anomalies = [a for a in anomalies if a.assignment_id == assignment.id and not a.resolved]

        support_type = None
        if assignment.contract_id:
            support_type = "contract"
        elif assignment.stage_pfmp_id:
            support_type = "stage_pfmp"
        elif assignment.service_civique_id:
            support_type = "service_civique"
        elif assignment.volunteer_engagement_id:
            support_type = "volunteer"

        return AssignmentControlView(
            assignment_id=assignment.id,
            person_id=assignment.person_id,
            activity_id=assignment.activity_id,
            gross_duration_minutes=assignment.gross_duration_minutes,
            auto_prep_minutes=assignment.auto_prep_minutes,
            main_support_type=support_type,
            result_messages=[r.readable_message for r in assignment_results],
            anomaly_codes=[a.code for a in assignment_anomalies],
        )
