# -*- coding: utf-8 -*-
"""La sauvegarde Teamworks ne doit jamais lister tous les dossiers Noethys."""
import ast
import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "teamworks/Utils/UTILS_Sauvegarde_perimetre.py"
DIALOG = ROOT / "teamworks/Dlg/DLG_Sauvegarde.py"
ENGINE = ROOT / "teamworks/Utils/UTILS_Sauvegarde.py"
AUTO = ROOT / "teamworks/Utils/UTILS_Sauvegarde_auto.py"


def _scope():
    spec = importlib.util.spec_from_file_location("backup_scope_test", SCOPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _method(name, namespace):
    tree = ast.parse(DIALOG.read_text(encoding="utf-8"))
    cls = next(
        n for n in tree.body if isinstance(n, ast.ClassDef)
        and n.name == "CTRL_Donnees"
    )
    method = next(
        n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name
    )
    code = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
    scope = dict(namespace)
    exec(compile(code, str(DIALOG), "exec"), scope)
    return scope[name]


def test_local_only_current_file_and_attached_data_are_allowed():
    module = _scope()
    allowed = module.composants_du_dossier("teamworks")
    assert allowed == {
        "locaux": (
            "teamworks_TDATA.dat",
            "teamworks_TPHOTOS.dat",
            "teamworks_TDOCUMENTS.dat",
        ),
        "reseau": (),
    }
    assert module.valider_selection(
        "teamworks", locaux=allowed["locaux"]
    ) == (True, "")
    assert not module.valider_selection(
        "teamworks", locaux=["ALSH Pêle Mêle_TDATA.dat"]
    )[0]
    assert not module.valider_selection(
        "teamworks", locaux=["Mairies_TPHOTOS.dat"]
    )[0]
    assert not module.valider_selection(
        "teamworks", reseau=["teamworks_tdata"]
    )[0]


def test_network_current_database_is_the_only_one_allowed():
    module = _scope()
    name = "3306;db.example;pelito;#64#abcd[RESEAU]teamworks"
    credentials = {"port": 3306, "host": "db.example",
                   "user": "pelito", "password": "secret"}
    allowed = module.composants_du_dossier(name)
    assert allowed["locaux"] == ()
    assert allowed["reseau"] == (
        "teamworks_tdata", "teamworks_tphotos", "teamworks_tdocuments"
    )
    assert module.valider_selection(
        name, reseau=list(allowed["reseau"]), connexion=credentials
    )[0]
    assert not module.valider_selection(
        name, reseau=["mairies_tdata"], connexion=credentials
    )[0]
    assert not module.valider_selection(
        name, reseau=["teamworks_tdata"],
        connexion=dict(credentials, host="other-server")
    )[0]
    assert not module.valider_selection(
        name, reseau=["teamworks_tdata"], connexion=None
    )[0]


def test_empty_or_invalid_current_context_fails_closed():
    module = _scope()
    for name in (None, "", "../Mairies", "D:/Noethys/file",
                 "3306;server[RESEAU]teamworks"):
        assert module.analyser_fichier_actif(name) is None
        assert not module.valider_selection(
            name, locaux=["Mairies_TDATA.dat"]
        )[0]


def test_local_tree_does_not_enumerate_other_dossiers(tmp_path):
    module = _scope()
    for name in ("Mairies_TDATA.dat", "ALSH Pêle Mêle_TDATA.dat",
                 "teamworks_TDATA.dat"):
        (tmp_path / name).write_bytes(b"fixture")
    namespace = {
        "PerimetreSauvegarde": module,
        "UTILS_Fichiers": SimpleNamespace(
            GetRepData=lambda filename: str(tmp_path / filename)),
        "os": os,
    }
    method = _method("GetListeFichiersLocaux", namespace)
    self = SimpleNamespace(
        parent=SimpleNamespace(fichier_actif="teamworks"),
    )
    assert method(self) == ["teamworks"]
    self.parent.fichier_actif = "3306;host;user;secret[RESEAU]teamworks"
    assert method(self) == []


def test_network_tree_filters_entire_mysql_server_to_current_database():
    module = _scope()
    active = "3306;localhost;pelito;secret[RESEAU]teamworks"
    credentials = {"port": 3306, "host": "localhost", "user": "pelito"}
    namespace = {
        "PerimetreSauvegarde": module,
        "UTILS_Sauvegarde": SimpleNamespace(GetListeFichiersReseau=lambda conn: [
            "mairies_tdata", "alsht_tdata", "teamworks_tphotos",
            "teamworks_tdata", "autre_tdocuments",
        ]),
    }
    method = _method("GetListeFichiersReseau", namespace)
    self = SimpleNamespace(parent=SimpleNamespace(
        fichier_actif=active, dictConnexion=credentials
    ))
    names, bases = method(self)
    assert names == ["teamworks"]
    assert bases == ["teamworks_tdata", "teamworks_tphotos"]
    self.parent.dictConnexion = dict(credentials, host="remote")
    assert method(self) == ([], [])


def test_engine_blocks_old_automated_profiles_before_creating_a_zip():
    source = ENGINE.read_text(encoding="utf-8")
    guard = source.index("PerimetreSauvegarde.valider_selection(")
    creation = source.index("fichierZip = zipfile.ZipFile(")
    assert guard < creation
    assert "if not autorise:" in source
    assert "dlg.ShowModal()" in source[guard:creation]
    assert "UTILS_Sauvegarde.Sauvegarde(" in AUTO.read_text(encoding="utf-8")


def test_ui_no_longer_offers_a_global_list_of_files():
    source = DIALOG.read_text(encoding="utf-8")
    assert 'os.listdir(UTILS_Fichiers.GetRepData())' not in source
    assert 'self.fichier_actif = PerimetreSauvegarde.fichier_actif()' in source
    assert 'self.check_locaux.Show(mode == "local")' in source
    assert 'self.check_reseau.Show(mode == "reseau")' in source
    assert "wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER" in source
