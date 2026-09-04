from __future__ import annotations

from PySide6.QtGui import QStandardItem


def _replace_rows(model, rows) -> None:
    model.setRowCount(0)
    for values in rows:
        items = [QStandardItem(str(value or "")) for value in values]
        for item in items:
            item.setEditable(False)
        model.appendRow(items)


class IndividualActivityPresenter:
    """Injecte des DTO déjà formatés dans les modèles Qt, sans règle métier."""

    def __init__(self, legacy_tabs):
        self._legacy_tabs = legacy_tabs

    def clear(self) -> None:
        questionnaire_page = getattr(self._legacy_tabs, "questionnaire_page", None)
        scenarios_page = getattr(self._legacy_tabs, "scenarios_page", None)
        expenses_page = getattr(self._legacy_tabs, "expenses_page", None)
        if questionnaire_page is not None:
            questionnaire_page.model.setRowCount(0)
        if scenarios_page is not None:
            scenarios_page.model.setRowCount(0)
        if expenses_page is not None:
            expenses_page.trip_model.setRowCount(0)
            expenses_page.reimbursement_model.setRowCount(0)

    def set_payload(self, payload: dict) -> None:
        questionnaire_page = getattr(self._legacy_tabs, "questionnaire_page", None)
        scenarios_page = getattr(self._legacy_tabs, "scenarios_page", None)
        expenses_page = getattr(self._legacy_tabs, "expenses_page", None)
        if questionnaire_page is not None:
            _replace_rows(
                questionnaire_page.model,
                ((view.question, view.answer) for view in payload.get("questionnaire", ())),
            )
        if scenarios_page is not None:
            _replace_rows(
                scenarios_page.model,
                (
                    (view.name, view.period, view.description)
                    for view in payload.get("scenarios", ())
                ),
            )
        if expenses_page is not None:
            _replace_rows(
                expenses_page.trip_model,
                (
                    (
                        view.number,
                        view.date,
                        view.purpose,
                        view.route,
                        view.distance,
                        view.tariff,
                        view.amount,
                        view.reimbursement,
                    )
                    for view in payload.get("trips", ())
                ),
            )
            _replace_rows(
                expenses_page.reimbursement_model,
                (
                    (view.number, view.date, view.amount, view.attached_trips)
                    for view in payload.get("reimbursements", ())
                ),
            )
