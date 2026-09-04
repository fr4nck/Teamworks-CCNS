from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "poc" / "qt-theme" / "pilot_generalities.py"
PERSON_READER = ROOT / "infrastructure" / "persistence" / "person_reader.py"


def test_individual_payload_is_ignored_when_selection_has_changed() -> None:
    source = PILOT.read_text(encoding="utf-8")

    assert "if person_id != self._activity_selected_person_id:" in source
    assert "return" in source[source.index("if person_id != self._activity_selected_person_id:") :]


def test_activity_result_only_updates_status_for_current_person() -> None:
    source = PILOT.read_text(encoding="utf-8")

    assert "if person_id == self._activity_selected_person_id:" in source
    assert "self._apply_individual_payload(person_id, payload)" in source


def test_new_selection_is_queued_while_previous_worker_is_running() -> None:
    source = PILOT.read_text(encoding="utf-8")

    assert "if self._activity_thread is not None and self._activity_thread.isRunning():" in source
    assert "self._activity_pending_person_id = person_id" in source
    assert "pending == self._activity_selected_person_id" in source


def test_generalities_reader_uses_explicit_projection_without_nir_or_select_star() -> None:
    source = PERSON_READER.read_text(encoding="utf-8")
    method = source[source.index("def lire_generalites") : source.index("def lire_coordonnees")]

    assert "num_secu" not in method.lower()
    assert "select *" not in method.lower()
    assert "SELECT personnes.IDpersonne" in method
