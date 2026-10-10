from pathlib import Path


CTRL = Path("teamworks/Ctrl/CTRL_Personnes.py")
OL = Path("teamworks/Ol/OL_personnes_core.py")
COMMON = Path("teamworks/Ctrl/CTRL_ObjectListView.py")


def test_individus_uses_stable_generic_view_id():
    source = CTRL.read_text(encoding="utf-8")
    assert 'view_id="personnes.main"' in source


def test_individus_has_no_deferred_column_autosize():
    source = CTRL.read_text(encoding="utf-8")
    assert "AjusterColonnes" not in source
    assert "OnTailleListe" not in source
    assert "listCtrl_personnes.Bind(wx.EVT_SIZE" not in source
    assert "wx.CallAfter(self.InitialiserSeparateur)" not in source


def test_individus_keeps_existing_default_widths():
    source = OL.read_text(encoding="utf-8")
    assert '[_(u"Qualifications"), "left", 90, "qualifications"' in source
    assert '[_(u"Téléphones"), "left", 200, "telephones"' in source


def test_person_refresh_does_not_rebuild_columns_unless_configuration_changed():
    source = OL.read_text(encoding="utf-8")
    assert "self._colonnes_a_reconstruire" in source
    assert "if self._colonnes_a_reconstruire:" in source
    assert "self.SetObjects(self.donnees)" in source
    assert "self.DefinirPreferencesColonnes" in source


def test_common_object_list_view_owns_persistence_contract():
    source = COMMON.read_text(encoding="utf-8")
    assert 'kwargs.pop("view_id", None)' in source
    assert "def _RestaurerEtatVueColonnes" in source
    assert "def _SauverEtatVueColonnes" in source
    assert "self.SetColumnsOrder(ordre)" in source
    assert "UTILS_Etat_vues.adapter_largeur" in source


def test_modern_persons_retains_its_existing_preference_store():
    source = Path("teamworks/Ol/OL_personnes.py").read_text(encoding="utf-8")
    assert 'kwds.pop("view_id", None)' in source
    assert 'wx_personnes_etat_colonnes_v1' in source
    assert 'UTILS_Etat_colonnes.fusionner_colonnes' in source
    assert 'self.SetObjects(self.donnees)' in source
