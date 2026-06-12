from __future__ import annotations

from collections import Counter

from domain.engine.anomaly import Anomaly
from domain.engine.calculation_result import CalculationResult
from application.control.models import DashboardCounter, ControlRow


class ControlDashboardService:
    def build_counters(
        self,
        *,
        anomalies: list[Anomaly],
        calculation_results: list[CalculationResult],
    ) -> list[DashboardCounter]:
        anomaly_counter = Counter(a.level.value for a in anomalies if not a.resolved)

        return [
            DashboardCounter(code="results_total", label="Résultats de calcul", value=len(calculation_results)),
            DashboardCounter(code="anomalies_total", label="Anomalies actives", value=len([a for a in anomalies if not a.resolved])),
            DashboardCounter(code="blocking_total", label="Bloquantes", value=anomaly_counter.get("BLOCKING", 0)),
            DashboardCounter(code="attention_total", label="Attention", value=anomaly_counter.get("ATTENTION", 0)),
            DashboardCounter(code="info_total", label="Info", value=anomaly_counter.get("INFO", 0)),
        ]

    def build_rows(self, *, anomalies: list[Anomaly]) -> list[ControlRow]:
        ordered = sorted(
            anomalies,
            key=lambda a: (
                a.resolved,
                a.level.value,
                a.code,
                a.object_type,
                a.object_id,
            ),
        )
        return [
            ControlRow(
                anomaly_id=a.id,
                level=a.level.value,
                code=a.code,
                object_type=a.object_type,
                object_id=a.object_id,
                person_id=a.person_id,
                contract_id=a.contract_id,
                assignment_id=a.assignment_id,
                message=a.message,
                is_resolved=a.resolved,
            )
            for a in ordered
        ]
