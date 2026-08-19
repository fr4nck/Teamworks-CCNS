from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Creation_contrat.py"


def test_optional_contract_fields_are_presented_as_optional() -> None:
    source = DIALOG.read_text(encoding="utf-8")

    assert "3. Informations complémentaires (optionnel)" in source
    assert "Les données déjà gérées par le contrat sont renseignées automatiquement." in source
    assert "4. Saisie des informations complémentaires" in source


def test_engine_managed_legacy_fields_are_hidden_contextually() -> None:
    source = DIALOG.read_text(encoding="utf-8")

    # CEE : le forfait journalier vient du barème employeur.
    assert 'mots_cles_masques.add("BRUTJOUR")' in source
    # CCNS : durée hebdomadaire et brut mensuel sont des champs standards.
    assert 'mots_cles_masques.update(("HEBDO", "BRUTMENS"))' in source


def test_empty_optional_selection_skips_fill_page_without_confirmation() -> None:
    source = DIALOG.read_text(encoding="utf-8")

    assert "Vous n'avez sélectionné aucun champ" not in source
    assert 'if len(self.listCtrl_champs.selections) == 0:' in source
    assert 'self.GetGrandParent().dictChamps = {}' in source
    assert 'if self.pageVisible == 4 and not self._HasSelectedCustomFields():' in source
    assert 'self.pageVisible = 6' in source


def test_back_navigation_skips_unvisited_fill_page() -> None:
    source = DIALOG.read_text(encoding="utf-8")

    assert 'if self.pageVisible == 6 and not self._HasSelectedCustomFields():' in source
    assert 'self.pageVisible = 4' in source
    assert 'if self.pageVisible < self.nbrePages:' in source
