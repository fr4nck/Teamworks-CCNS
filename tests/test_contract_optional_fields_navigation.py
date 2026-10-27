from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks/Dlg/DLG_Creation_contrat.py"
FIELDS = ROOT / "teamworks/Dlg/DLG_Contrat_champs_specifiques.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_only_main_contract_screen_is_visible_by_default():
    source = _source(DIALOG)
    assert 'self.listePages = ("Page2",)' in source
    assert "self.pageVisible = 2" in source
    assert "self.page2 = Page2(self.panel_base)" in source
    assert "self.page3 = Page3(self.panel_base)" in source
    assert "self.page4.Hide()" in source
    assert "self.page6.Hide()" in source
    assert 'texte=_(u"Valider")' in source
    assert "self.page1.Show(True)" not in source
    assert "self.bouton_retour" not in source


def test_legacy_custom_fields_are_advanced_not_a_required_step():
    source = _source(DIALOG)
    modal = _source(FIELDS)
    assert "self.bouton_options.Show(bool(self.page4.listCtrl_champs.dictChamps))" in source
    assert "def OnBoutonChampsSpecifiques(self, event):" in source
    assert "self.dictChamps.update(dlg.champs)" in source
    assert "if key not in definitions" in source
    assert "self.page4.MAJ_ListCtrl()" in source
    assert "wx.CheckBox(" in modal
    assert "self.champs = selected" in modal
    assert "self.EndModal(wx.ID_CANCEL)" in modal


def test_engine_managed_legacy_fields_are_hidden_contextually():
    source = _source(DIALOG)
    assert 'mots_cles_masques.add("BRUTJOUR")' in source
    assert 'mots_cles_masques.update(("HEBDO", "BRUTMENS", "ANNUEL"))' in source


def test_only_one_validation_action_preserves_final_transaction():
    source = _source(DIALOG)
    assert "if not self.ValidationPages():" in source
    assert "if not self.page6.Validation():" in source
    assert "self.Terminer()" in source
    assert "self._enregistrement_en_cours = True" in source
    assert "self._enregistrement_en_cours = False" in source
    assert "def Onbouton_retour(" not in source
