import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELECTION = ROOT / "teamworks/Utils/UTILS_Selection_metier.py"
DLG = ROOT / "teamworks/Dlg/DLG_Selection_liste.py"
PERSONNES = ROOT / "teamworks/Ol/OL_personnes.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def _charger_selection():
    spec = importlib.util.spec_from_file_location("selection_metier_test", SELECTION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_id_explicite_survit_a_une_premiere_colonne_non_numerique():
    module = _charger_selection()
    lignes = module.associer_identifiants(
        [["06 12 34 56 78", "Alice"], ["09 99 88 77 66", "Bob"]],
        [41, 52],
    )
    assert [identifiant for identifiant, _ in lignes] == [41, 52]
    assert lignes[0][1][0] == "06 12 34 56 78"


def test_id_explicite_ne_depend_pas_de_l_ordre_ou_visibilite_des_colonnes():
    module = _charger_selection()
    configurations = (
        [["Nom A", "Téléphone A"]],
        [["Téléphone A", "Nom A"]],
        [["Nom A"]],
        [[True, "Nom A", "Téléphone A"]],
    )
    for valeurs in configurations:
        lignes = module.associer_identifiants(valeurs, [1234])
        assert lignes[0][0] == 1234
        assert lignes[0][1] == valeurs[0]


def test_changement_de_configuration_garde_le_meme_id_metier():
    module = _charger_selection()
    avant = module.associer_identifiants([["Nom", "Téléphones"]], [77])
    apres = module.associer_identifiants([["Téléphones", "Nom", "Email"]], [77])
    assert avant[0][0] == apres[0][0] == 77


def test_dialogue_lit_itemdata_et_non_la_premiere_cellule():
    source = _source(DLG)
    assert "listeIDs=None" in source
    assert "UTILS_Selection_metier.associer_identifiants" in source
    assert "self.GetItemData(index)" in source
    assert "ID = int(valeurs[0])" not in source
    assert "self.GetItem(index, 0).GetText()" not in source


def test_publipostage_transporte_track_idpersonne_explicitement():
    source = _source(PERSONNES)
    assert "listeIDs = [objet.IDpersonne for objet in objets]" in source
    assert "listeIDs=listeIDs" in source
    assert "self.GetFilteredObjects()" in source


def test_fichiers_modifies_compilent():
    for path in (SELECTION, DLG, PERSONNES):
        compile(_source(path), str(path), "exec")
