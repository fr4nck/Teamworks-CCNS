import importlib.util
from pathlib import Path
import sqlite3
import sys
import types
import zipfile

import pytest

from teamworks.Utils import UTILS_RestaurationFichiers as restauration


SOURCE_SAUVEGARDE = Path("teamworks/Utils/UTILS_Sauvegarde.py")
FIXTURE_SQL = Path("tests/fixtures/teamworks_roundtrip.sql")


def _creer_fixture(path):
    script = FIXTURE_SQL.read_text(encoding="utf-8")
    with sqlite3.connect(path) as connexion:
        connexion.executescript(script)


def _identifiant(nom):
    return '"%s"' % nom.replace('"', '""')


def _cle_tri_ligne(ligne):
    return repr(tuple((type(valeur).__name__, valeur) for valeur in ligne))


def _snapshot_semantique(path):
    with sqlite3.connect(path) as connexion:
        master = tuple(
            connexion.execute(
                "SELECT type, name, tbl_name, sql FROM sqlite_master "
                "WHERE type IN ('table', 'index', 'trigger') "
                "AND name NOT LIKE 'sqlite_%' ORDER BY type, name"
            ).fetchall()
        )
        tables = [ligne[1] for ligne in master if ligne[0] == "table"]
        detail = {}
        for table in sorted(tables):
            infos = tuple(
                connexion.execute(
                    "PRAGMA table_info(%s)" % _identifiant(table)
                ).fetchall()
            )
            lignes = connexion.execute(
                "SELECT * FROM %s" % _identifiant(table)
            ).fetchall()
            detail[table] = {
                "table_info": infos,
                "row_count": len(lignes),
                "rows": tuple(sorted(lignes, key=_cle_tri_ligne)),
            }
        return {"sqlite_master": master, "tables": detail}


class _Dialogue:
    def __init__(self, *args, **kwargs):
        pass

    def ShowModal(self):
        return 1

    def Destroy(self):
        pass


class _Progression:
    def __init__(self, *args, **kwargs):
        pass

    def Update(self, *args, **kwargs):
        return True

    def Destroy(self):
        pass


def _charger_sauvegarde(monkeypatch, data_dir, temp_dir):
    wx = types.ModuleType("wx")
    wx.ID_YES = 1
    wx.ID_OK = 2
    for nom, valeur in {
        "OK": 1,
        "ICON_ERROR": 2,
        "YES_NO": 4,
        "CANCEL": 8,
        "NO_DEFAULT": 16,
        "ICON_EXCLAMATION": 32,
        "PD_SMOOTH": 64,
        "PD_AUTO_HIDE": 128,
        "PD_APP_MODAL": 256,
        "DD_DEFAULT_STYLE": 512,
        "DD_DIR_MUST_EXIST": 1024,
    }.items():
        setattr(wx, nom, valeur)
    wx.MessageDialog = _Dialogue
    wx.ProgressDialog = _Progression
    monkeypatch.setitem(sys.modules, "wx", wx)

    chemins = types.ModuleType("Chemins")
    monkeypatch.setitem(sys.modules, "Chemins", chemins)
    gestion_db = types.ModuleType("GestionDB")
    monkeypatch.setitem(sys.modules, "GestionDB", gestion_db)

    utils = types.ModuleType("Utils")
    utils.__path__ = []
    monkeypatch.setitem(sys.modules, "Utils", utils)

    traduction = types.ModuleType("Utils.UTILS_Traduction")
    traduction._ = lambda texte: texte
    monkeypatch.setitem(sys.modules, "Utils.UTILS_Traduction", traduction)

    fichiers = types.ModuleType("Utils.UTILS_Fichiers")
    fichiers.GetRepData = lambda fichier=None: str(
        data_dir if fichier is None else data_dir / fichier
    )
    fichiers.GetRepTemp = lambda fichier=None: str(
        temp_dir if fichier is None else temp_dir / fichier
    )
    fichiers.GetRepModeles = lambda fichier=None: str(
        temp_dir if fichier is None else temp_dir / fichier
    )
    fichiers.GetRepEditions = lambda fichier=None: str(
        temp_dir if fichier is None else temp_dir / fichier
    )

    modules = {
        "UTILS_Fichiers": fichiers,
        "UTILS_Config": types.ModuleType("Utils.UTILS_Config"),
        "UTILS_Cryptage_fichier": types.ModuleType("Utils.UTILS_Cryptage_fichier"),
        "UTILS_Envoi_email": types.ModuleType("Utils.UTILS_Envoi_email"),
        "UTILS_RestaurationFichiers": restauration,
    }
    for nom, module in modules.items():
        setattr(utils, nom, module)
        monkeypatch.setitem(sys.modules, "Utils.%s" % nom, module)

    spec = importlib.util.spec_from_file_location(
        "tw10_utils_sauvegarde",
        SOURCE_SAUVEGARDE,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assert_fixture_representative(snapshot):
    tables = snapshot["tables"]
    assert set(
        ("personnes", "coordonnees", "contrats", "presences", "valeurs_point")
    ).issubset(tables)
    assert tables["personnes"]["row_count"] == 2
    assert tables["coordonnees"]["row_count"] == 3
    assert tables["contrats"]["row_count"] == 2
    assert tables["presences"]["row_count"] == 2
    valeurs = repr(snapshot)
    for attendu in (
        "D'ÉTÉ",
        "Élodie",
        "漢字",
        "Ω",
        "",
        "None",
        "6.37",
        "7.125",
        "2026-03-04",
        "08:30:00",
    ):
        assert attendu in valeurs


def test_roundtrip_production_sauvegarde_restauration_preserve_semantique(
    tmp_path,
    monkeypatch,
):
    data_dir = tmp_path / "data"
    temp_dir = tmp_path / "temp"
    backup_dir = tmp_path / "backup"
    for repertoire in (data_dir, temp_dir, backup_dir):
        repertoire.mkdir()

    nom_base = "teamworks_roundtrip.dat"
    base = data_dir / nom_base
    _creer_fixture(base)
    snapshot_before = _snapshot_semantique(base)
    _assert_fixture_representative(snapshot_before)

    sauvegarde = _charger_sauvegarde(monkeypatch, data_dir, temp_dir)
    assert sauvegarde.Sauvegarde(
        listeFichiersLocaux=[nom_base],
        nom="roundtrip",
        repertoire=str(backup_dir),
    ) is True
    archive = backup_dir / "roundtrip.twd"
    assert zipfile.is_zipfile(archive)

    base.write_bytes(b"base active volontairement corrompue")
    resultat = sauvegarde.Restauration(
        fichier=str(archive),
        listeFichiersLocaux=[nom_base],
    )
    assert resultat == ["teamworks_roundtrip"]

    snapshot_after = _snapshot_semantique(base)
    assert snapshot_before == snapshot_after
    _assert_fixture_representative(snapshot_after)
    assert list(data_dir.glob(".teamworks-restore-*.tmp")) == []


def test_restauration_production_refuse_sqlite_invalide_et_preserve_base(
    tmp_path,
    monkeypatch,
):
    data_dir = tmp_path / "data"
    temp_dir = tmp_path / "temp"
    backup_dir = tmp_path / "backup"
    for repertoire in (data_dir, temp_dir, backup_dir):
        repertoire.mkdir()

    nom_base = "teamworks_roundtrip.dat"
    base = data_dir / nom_base
    _creer_fixture(base)
    snapshot_before = _snapshot_semantique(base)
    archive = backup_dir / "invalide.twd"
    with zipfile.ZipFile(archive, "w") as fichier_zip:
        fichier_zip.writestr(nom_base, b"pas une base sqlite")

    sauvegarde = _charger_sauvegarde(monkeypatch, data_dir, temp_dir)
    assert sauvegarde.Restauration(
        fichier=str(archive),
        listeFichiersLocaux=[nom_base],
    ) is False
    assert _snapshot_semantique(base) == snapshot_before
    assert list(data_dir.glob(".teamworks-restore-*.tmp")) == []


def test_restauration_production_zip_corrompu_ne_touche_pas_base(
    tmp_path,
    monkeypatch,
):
    data_dir = tmp_path / "data"
    temp_dir = tmp_path / "temp"
    backup_dir = tmp_path / "backup"
    for repertoire in (data_dir, temp_dir, backup_dir):
        repertoire.mkdir()

    nom_base = "teamworks_roundtrip.dat"
    base = data_dir / nom_base
    _creer_fixture(base)
    snapshot_before = _snapshot_semantique(base)
    archive = backup_dir / "corrompu.twd"
    archive.write_bytes(b"archive zip corrompue")

    sauvegarde = _charger_sauvegarde(monkeypatch, data_dir, temp_dir)
    with pytest.raises(zipfile.BadZipFile):
        sauvegarde.Restauration(
            fichier=str(archive),
            listeFichiersLocaux=[nom_base],
        )
    assert _snapshot_semantique(base) == snapshot_before
