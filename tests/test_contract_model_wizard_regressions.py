from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL_PAGE1 = ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_modele_contrat_p1.py"
MODEL_PAGE3 = ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_modele_contrat_p3.py"
MODEL_DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Creation_modele_contrat.py"
CONTRACT_PAGE2 = ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_contrat_p2.py"


def test_model_wizard_keeps_legacy_custom_field_controls() -> None:
    source = MODEL_PAGE1.read_text(encoding="utf-8")

    assert "self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)" in source
    assert "Créer un nouveau champ" in source
    assert "Modifier" in source
    assert "Supprimer" in source
    assert "self.SortItems(self.columnSorter)" in source
    assert "Vous n'avez sélectionné aucun champ" in source
    assert "self.bouton_champs.SetToolTip" in source


def test_model_wizard_reads_tuple_based_schema_correctly() -> None:
    source = MODEL_DIALOG.read_text(encoding="utf-8")

    assert "UTILS_Contrats_schema.EnsureContractModelColumns(DB)" in source
    assert "noms_champs = [champ[0] for champ in champs]" in source
    assert 'nom in noms_champs' in source


def test_model_wizard_writes_modern_discriminants_when_columns_exist() -> None:
    source = MODEL_PAGE3.read_text(encoding="utf-8")

    assert "UTILS_Contrats_schema.EnsureContractModelColumns(DB)" in source
    assert 'noms_champs = [champ[0] for champ in DB.GetListeChamps2("contrats_modeles")]' in source
    assert "if nom in noms_champs:" in source
    for field in ("convention_code", "ccns_group", "cee_qualification"):
        assert field in source


def test_cee_targeting_does_not_invent_a_cee_collective_convention() -> None:
    source = MODEL_PAGE1.read_text(encoding="utf-8")

    assert 'dictModeles["cee_qualification"] = cible' in source
    assert 'dictModeles["convention_code"] = "CEE"' not in source


def test_generic_cee_model_is_distinguished_from_legacy_model() -> None:
    source = MODEL_PAGE1.read_text(encoding="utf-8")

    assert "self.dictTypeCodes" in source
    assert "self.IsCEEType(IDtype)" in source
    assert 'classification in (None, "")' in source
    assert 'convention in (None, "")' in source
    assert "self.choice_convention.SetSelection(2)" in source


def test_cee_targeting_requires_cee_contract_type() -> None:
    source = MODEL_PAGE1.read_text(encoding="utf-8")

    assert "if mode == 2 and not self.IsCEEType(type_contrat):" in source
    assert "Le ciblage CEE nécessite un type de contrat CEE." in source
    assert "if mode == 1 and self.IsCEEType(type_contrat):" in source


def test_contract_wizard_applies_modern_model_discriminants() -> None:
    source = CONTRACT_PAGE2.read_text(encoding="utf-8")

    assert "UTILS_Contrats_schema.EnsureContractModelColumns(DB)" in source
    assert "SELECT IDclassification, IDtype, convention_code, ccns_group, cee_qualification" in source
    assert 'contrat["convention_code"] = convention_code' in source
    assert 'contrat["ccns_group"] = ccns_group' in source
    assert 'contrat["cee_qualification"] = cee_qualification' in source
    assert "self.GetGrandParent().dictChamps.clear()" in source
    assert "self.GetGrandParent().page3.RefreshContractRules()" in source
