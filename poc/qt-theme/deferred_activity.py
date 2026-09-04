from __future__ import annotations

import time
import traceback

from PySide6.QtCore import QObject, Signal, Slot


class ProductionIndividualActivityLoader(QObject):
    """Charge les détails individuels avec une connexion propre au worker.

    Le nom historique de la classe est conservé pour éviter un refactoring du
    lanceur ; le payload contient Généralités, Questionnaire, Scénarios et Frais.
    """

    loaded = Signal(object, object)
    failed = Signal(object, str)

    def __init__(self, person_id: int):
        super().__init__()
        self.person_id = person_id

    @Slot()
    def run(self) -> None:
        adapter = None
        questionnaire_adapter = None
        started = time.perf_counter()
        try:
            from production_read_adapter import build_production_adapter
            from questionnaire_read_adapter import QuestionnaireProductionReadAdapter

            adapter = build_production_adapter()
            questionnaire_adapter = QuestionnaireProductionReadAdapter()
            generalities = adapter.get_person_generalities(self.person_id)
            questionnaire = tuple(questionnaire_adapter.list_questionnaire(self.person_id))
            scenarios = tuple(adapter.list_scenarios(self.person_id))
            trips = tuple(adapter.list_trips(self.person_id))
            reimbursements = tuple(adapter.list_reimbursements(self.person_id))
            payload = {
                "generalities": generalities,
                "questionnaire": questionnaire,
                "scenarios": scenarios,
                "trips": trips,
                "reimbursements": reimbursements,
                "seconds": time.perf_counter() - started,
                "timings": dict(getattr(adapter, "startup_timings", {}) or {}),
            }
            self.loaded.emit(self.person_id, payload)
        except Exception:
            self.failed.emit(self.person_id, traceback.format_exc())
        finally:
            if questionnaire_adapter is not None:
                try:
                    questionnaire_adapter.close()
                except Exception:
                    pass
            if adapter is not None:
                try:
                    adapter.close()
                except Exception:
                    pass
