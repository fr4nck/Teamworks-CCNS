from pathlib import Path


PERSONNES = Path("teamworks/Ol/OL_personnes.py")
CORE = Path("teamworks/Ol/OL_personnes_core.py")


def test_active_person_list_routes_delete_through_shared_use_case():
    source = PERSONNES.read_text(encoding="utf-8")
    assert "def Supprimer(self):" in source
    assert "check_person_deletion(person_id, repository)" in source
    assert "result = delete_person(person_id, repository)" in source
    assert "GestionDBPersonDeleteRepository()" in source


def test_active_delete_handles_second_guard_result():
    source = PERSONNES.read_text(encoding="utf-8")
    assert "if not result.allowed:" in source
    assert "blocking_messages[result.blocking_reason]" in source


def test_core_no_longer_contains_shared_delete_imports():
    source = CORE.read_text(encoding="utf-8")
    assert "application.services.person_delete" not in source
    assert "GestionDBPersonDeleteRepository" not in source
