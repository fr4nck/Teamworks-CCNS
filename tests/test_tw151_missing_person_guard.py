from pathlib import Path

from application.services.person_summary import get_person_summary


ROOT = Path(__file__).resolve().parents[1]


class MissingPersonRepository:
    def get_identity(self, person_id):
        return None

    def get_coordinates(self, person_id):
        raise AssertionError("coordinates must not be loaded for a missing person")

    def get_contracts(self, person_id):
        raise AssertionError("contracts must not be loaded for a missing person")


def test_person_summary_guards_missing_person_behaviorally():
    assert get_person_summary(999999, MissingPersonRepository()) is None


def test_ctrl_personnes_keeps_missing_person_guard():
    source = (ROOT / "teamworks/Ctrl/CTRL_Personnes.py").read_text(encoding="utf-8")
    assert "summary = get_person_summary(" in source
    assert "if summary is None:\n            return" in source
