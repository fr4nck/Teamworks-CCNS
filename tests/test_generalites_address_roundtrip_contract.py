from pathlib import Path


GENERALITES = Path("teamworks/Ctrl/CTRL_Page_generalites.py")


def test_adresse_est_ecrite_et_relue_sur_les_memes_colonnes():
    source = GENERALITES.read_text(encoding="utf-8")
    save = source.split("def Sauvegarde", 1)[1].split("def MaJ_Header_Fiche", 1)[0]
    load = source.split("def Importation", 1)[1].split("def _bitmap_drapeau", 1)[0]
    for column in ("adresse_resid", "cp_resid", "ville_resid"):
        assert column in save
        assert column in load


def test_adresse_libre_n_est_pas_conditionnee_a_une_selection_de_ville():
    source = GENERALITES.read_text(encoding="utf-8")
    save = source.split("def Sauvegarde", 1)[1].split("def MaJ_Header_Fiche", 1)[0]
    assert "self.text_adresse.GetValue()" in save
    assert "self.text_ville.GetValue()" in save


def test_mises_a_jour_entete_ne_dependant_plus_dune_profondeur_wx_fixe():
    source = GENERALITES.read_text(encoding="utf-8")
    assert "def _GetFicheIndividuelle" in source
    assert 'hasattr(courant, "label_hd_nomPrenom")' in source
    assert "self.GetParent().GetGrandParent().label_hd_nomPrenom" not in source
    assert "self.GetParent().GetGrandParent().label_hd_adresse" not in source
    assert "self.GetParent().GetGrandParent().label_hd_naiss" not in source
