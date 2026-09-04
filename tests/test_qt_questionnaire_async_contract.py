from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "poc" / "qt-theme"
PILOT = POC / "pilot_generalities.py"
PRESENTER = POC / "individual_activity_presenter.py"
DEFERRED = POC / "deferred_activity.py"
TABS = POC / "legacy_individual_tabs.py"


def test_questionnaire_page_is_kept_for_reload() -> None:
    source = TABS.read_text(encoding="utf-8")

    assert "self.questionnaire_page = None" in source
    assert "self.questionnaire_page = QuestionnairePage()" in source
    assert "return self.questionnaire_page" in source


def test_questionnaire_is_cleared_immediately_on_person_change() -> None:
    pilot = PILOT.read_text(encoding="utf-8")
    presenter = PRESENTER.read_text(encoding="utf-8")

    request = pilot[pilot.index("def _request_activity") : pilot.index("def _start_activity_load")]
    assert request.index("self.activity_presenter.clear()") < request.index("isRunning()")
    assert "questionnaire_page.model.setRowCount(0)" in presenter


def test_questionnaire_payload_is_applied_only_after_current_person_guard() -> None:
    pilot = PILOT.read_text(encoding="utf-8")
    apply_method = pilot[pilot.index("def _apply_individual_payload") : pilot.index("def _on_activity_loaded")]

    guard = apply_method.index("if person_id != self._activity_selected_person_id:")
    reject = apply_method.index("return", guard)
    apply_payload = apply_method.index("self.activity_presenter.set_payload(payload)")
    assert guard < reject < apply_payload


def test_questionnaire_is_loaded_by_async_worker_and_presented() -> None:
    deferred = DEFERRED.read_text(encoding="utf-8")
    presenter = PRESENTER.read_text(encoding="utf-8")

    assert "questionnaire = tuple(questionnaire_adapter.list_questionnaire(self.person_id))" in deferred
    assert '"questionnaire": questionnaire' in deferred
    assert 'payload.get("questionnaire", ())' in presenter
    assert "(view.question, view.answer)" in presenter


def test_pending_person_is_reloaded_after_stale_worker_finishes() -> None:
    pilot = PILOT.read_text(encoding="utf-8")

    assert "self._activity_pending_person_id = person_id" in pilot
    assert "pending == self._activity_selected_person_id" in pilot
    assert "self._start_activity_load(pending)" in pilot
