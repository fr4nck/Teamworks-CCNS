from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "poc" / "qt-theme"
if str(POC) not in sys.path:
    sys.path.insert(0, str(POC))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QStandardItemModel  # noqa: E402

from domain.repositories.individual_activity_data import (  # noqa: E402
    PresenceCategoryRecord,
    PresenceRecord,
    VacationPeriodRecord,
)
from individual_activity_presenter import IndividualActivityPresenter  # noqa: E402
from production_read_adapter import TeamworksProductionReadAdapter  # noqa: E402


class _NoopReader:
    def close(self) -> None:
        return None


class _PresenceReader(_NoopReader):
    def lire_presences_personne(self, person_id):
        assert int(person_id) == 12
        return [PresenceRecord(501, "2026-09-15", "08:00", "17:36", 7, "ALSH")]

    def lire_categories_presences(self):
        return [PresenceCategoryRecord(7, "Travail", "#123456")]

    def lire_periodes_vacances(self):
        return [VacationPeriodRecord(3, "Toussaint", 2026, "2026-10-17", "2026-11-02")]


def _production_adapter() -> TeamworksProductionReadAdapter:
    return TeamworksProductionReadAdapter(
        person_reader=_NoopReader(),
        contract_reader=_NoopReader(),
        activity_reader=_PresenceReader(),
    )


def test_production_adapter_reuses_activity_reader_for_presences() -> None:
    adapter = _production_adapter()
    try:
        views = adapter.list_presences(12)
    finally:
        adapter.close()

    assert len(views) == 1
    view = views[0]
    assert view.key == 501
    assert view.category_id == 7
    assert view.schedule == "8h00-17h36"
    assert view.duration == "9h36"
    assert view.label == "Travail (ALSH)"
    assert view.revision


def test_presenter_populates_and_clears_presence_model_with_hidden_identity() -> None:
    adapter = _production_adapter()
    try:
        view = adapter.list_presences(12)[0]
    finally:
        adapter.close()

    page = SimpleNamespace(source_model=QStandardItemModel(0, 5))
    tabs = SimpleNamespace(
        questionnaire_page=None,
        presences_page=page,
        scenarios_page=None,
        expenses_page=None,
    )
    presenter = IndividualActivityPresenter(tabs)

    presenter.set_payload({"presences": (view,)})
    assert page.source_model.rowCount() == 1
    assert page.source_model.item(0, 2).text() == "8h00-17h36"
    for column in range(page.source_model.columnCount()):
        payload = page.source_model.item(0, column).data(Qt.ItemDataRole.UserRole)
        assert payload is view
        assert payload.key == 501

    presenter.clear()
    assert page.source_model.rowCount() == 0


def test_individual_worker_includes_presences_in_payload_contract() -> None:
    source = (POC / "deferred_activity.py").read_text(encoding="utf-8")
    assert "adapter.list_presences(self.person_id)" in source
    assert '"presences": presences' in source
