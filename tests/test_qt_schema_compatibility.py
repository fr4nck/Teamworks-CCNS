"""Précontrôle de schéma Qt et évolution CCNS contrôlée, sur GestionDB réel.

Les bases utilisées sont des copies temporaires de la fixture fictive
``Static/Exemples/Exemple_TDATA.dat`` ; aucune base réelle n'est ouverte.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "poc" / "qt-theme", ROOT / "teamworks", ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from Data import DATA_Tables  # noqa: E402
from Utils import UTILS_Contrats_schema  # noqa: E402

from infrastructure.persistence.contract_schema_evolution import (  # noqa: E402
    add_contract_engine_columns,
)
from infrastructure.persistence.qt_schema_compatibility import (  # noqa: E402
    BLOQUANT,
    CONTRACT_ENGINE_COLUMNS,
    EVOLUTION,
    QT_REQUIRED_SCHEMA,
    check_schema,
)

FIXTURE = ROOT / "teamworks" / "Static" / "Exemples" / "Exemple_TDATA.dat"


@pytest.fixture
def GestionDB(monkeypatch):
    """Vrai GestionDB et ses dépendances, même si d'autres tests ont laissé des faux.

    Certains tests installent des ``SimpleNamespace`` dans ``sys.modules`` ou sur
    les paquets ``Utils``/``Data`` ; ils sont retirés le temps du test puis restaurés.
    """
    import importlib
    import types

    for name, module in list(sys.modules.items()):
        if module is not None and not isinstance(module, types.ModuleType):
            monkeypatch.delitem(sys.modules, name)
    for package_name in ("Utils", "Data", "infrastructure.persistence"):
        package = sys.modules.get(package_name)
        if isinstance(package, types.ModuleType):
            for attr, value in list(vars(package).items()):
                if isinstance(value, types.SimpleNamespace):
                    monkeypatch.delattr(package, attr)
    current = sys.modules.get("GestionDB")
    if current is not None and not getattr(current, "__file__", None):
        monkeypatch.delitem(sys.modules, "GestionDB")
    try:
        import appdirs  # noqa: F401  (dépendance de GestionDB/UTILS_Fichiers)
        legacy_runtime = True
    except ImportError:
        legacy_runtime = False
    if not legacy_runtime:
        # CI Linux minimale : GestionDB réel inimportable ; le job Windows natif
        # exécute ces mêmes tests sur le vrai module.
        module = types.SimpleNamespace(DB=_SqliteGestionDbShim)
    else:
        module = importlib.import_module("GestionDB")
    monkeypatch.setitem(sys.modules, "GestionDB", module)
    return module

class _SqliteGestionDbShim:
    """Sous-ensemble fidèle de GestionDB.DB (SQLite local) pour les CI sans appdirs."""

    def __init__(self, nomFichier="", suffixe=None, modeCreation=False):
        import sqlite3

        self.nomFichier = nomFichier
        self.isNetwork = False
        self.connexion = sqlite3.connect(nomFichier)
        self.cursor = self.connexion.cursor()
        self.echec = 0

    def ExecuterReq(self, req):
        self.cursor.execute(req)
        return 1

    def ResultatReq(self):
        return self.cursor.fetchall()

    def GetListeTables(self):
        self.ExecuterReq("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        return self.ResultatReq()

    def GetListeChamps2(self, nomTable=""):
        self.ExecuterReq("PRAGMA table_info('%s');" % nomTable)
        return [(row[1], row[2]) for row in self.ResultatReq()]

    def AjoutChamp(self, nomTable="", nomChamp="", typeChamp=""):
        from infrastructure.persistence.legacy_table_ddl import legacy_add_column_query

        self.ExecuterReq(legacy_add_column_query(nomTable, nomChamp, typeChamp))
        self.connexion.commit()

    def ReqInsert(self, nomTable, listeDonnees, commit=True):
        fields = ", ".join(name for name, _ in listeDonnees)
        marks = ", ".join("?" for _ in listeDonnees)
        self.cursor.execute("INSERT INTO %s (%s) VALUES (%s)" % (nomTable, fields, marks),
                            tuple(value for _, value in listeDonnees))
        if commit:
            self.connexion.commit()
        return int(self.cursor.lastrowid)

    def Commit(self):
        self.connexion.commit()

    def Close(self):
        self.connexion.close()


@pytest.fixture
def base(tmp_path, GestionDB):
    target = tmp_path / "Recette_TDATA.dat"
    shutil.copyfile(FIXTURE, target)
    return target


def _open(path):
    db = sys.modules["GestionDB"].DB(nomFichier=str(path), suffixe=None)
    assert db.echec == 0
    return db


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_inventory_matches_full_teamworks_schema():
    """Une base entièrement à jour ne doit jamais être refusée par le précontrôle."""
    for table, columns in QT_REQUIRED_SCHEMA.items():
        assert table in DATA_Tables.DB_DATA, table
        known = {name for name, *_ in DATA_Tables.DB_DATA[table]}
        assert set(columns) <= known, (table, set(columns) - known)
    assert CONTRACT_ENGINE_COLUMNS == UTILS_Contrats_schema.ADDITIVE_COLUMNS


def test_example_base_is_compatible_and_check_never_writes(base):
    before = _digest(base)
    db = _open(base)
    try:
        report = check_schema(db)
    finally:
        db.Close()
    assert _digest(base) == before
    assert report.compatible is True
    assert report.contract_writes_ready is False
    assert set(report.missing_contract_columns) == {n for n, _ in CONTRACT_ENGINE_COLUMNS}
    assert "colonnes CCNS" in report.summary()


def test_missing_required_table_or_column_is_blocking_and_explained(base):
    with sqlite3.connect(base) as c:
        c.execute("DROP TABLE presences")
        c.execute("ALTER TABLE scenarios RENAME TO scenarios_old")
        c.execute("CREATE TABLE scenarios (IDscenario INTEGER PRIMARY KEY, IDpersonne INTEGER)")
    db = _open(base)
    try:
        report = check_schema(db)
    finally:
        db.Close()
    assert report.compatible is False
    text = report.blocking_text()
    assert "Table « presences » absente." in text
    assert "scenarios" in text and "description" in text and "date_debut" in text
    assert "UpgradeDB" in text
    assert {i.table for i in report.issues if i.level == BLOQUANT} == {"presences", "scenarios"}


def test_teamworks1_file_is_refused(base):
    with sqlite3.connect(base) as c:
        c.execute("UPDATE parametres SET parametre='1.0.5.2' WHERE categorie='fichier' AND nom='version'")
        if c.total_changes == 0:
            c.execute("INSERT INTO parametres (categorie, nom, parametre) VALUES ('fichier','version','1.0.5.2')")
    db = _open(base)
    try:
        report = check_schema(db)
    finally:
        db.Close()
    assert report.compatible is False
    assert "Teamworks 1" in report.blocking_text()


def test_evolution_backs_up_adds_only_columns_and_is_idempotent(base):
    with sqlite3.connect(base) as c:
        contracts_before = c.execute("SELECT * FROM contrats ORDER BY IDcontrat").fetchall()
        people_before = c.execute("SELECT * FROM personnes ORDER BY IDpersonne").fetchall()
    db = _open(base)
    try:
        result = add_contract_engine_columns(db, now=datetime(2026, 10, 29, 10, 0, 0))
        assert result.ok, result.message
        assert set(result.created) == {n for n, _ in CONTRACT_ENGINE_COLUMNS}
        backup = Path(result.backup_path)
        assert backup.name == "Recette_TDATA.avant-colonnes-ccns-20261029-100000-000000.bak"
        with sqlite3.connect(backup) as b:
            assert b.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert b.execute("SELECT * FROM contrats ORDER BY IDcontrat").fetchall() == contracts_before
            assert "ccns_group" not in {r[1] for r in b.execute("PRAGMA table_info(contrats)")}
        assert check_schema(db).contract_writes_ready is True

        again = add_contract_engine_columns(db, now=datetime(2026, 10, 29, 11, 0, 0))
        assert again.ok and again.created == () and again.backup_path is None
    finally:
        db.Close()
    with sqlite3.connect(base) as c:
        rows = c.execute("SELECT * FROM contrats ORDER BY IDcontrat").fetchall()
        assert [row[: len(contracts_before[0])] for row in rows] == contracts_before
        assert all(value is None for row in rows for value in row[len(contracts_before[0]):])
        assert c.execute("SELECT * FROM personnes ORDER BY IDpersonne").fetchall() == people_before
    assert len(list(base.parent.glob("*.bak"))) == 1


def test_evolution_refused_on_incompatible_base_without_any_write(base):
    with sqlite3.connect(base) as c:
        c.execute("DROP TABLE cat_presences")
    before = _digest(base)
    db = _open(base)
    try:
        result = add_contract_engine_columns(db)
    finally:
        db.Close()
    assert result.ok is False and "incompatible" in result.message
    assert _digest(base) == before
    assert not list(base.parent.glob("*.bak"))


class _EngineCursor:
    """Réponse MySQL ≥ 5.5 à la requête information_schema, moteur InnoDB par défaut."""

    def __init__(self, db):
        self._db = db
        self._rows = []

    def execute(self, req, params=()):
        assert "information_schema.TABLES" in req and "DATABASE()" in req
        self._rows = [(name, self._db.engines.get(name, "InnoDB")) for name in params]

    def fetchall(self):
        return self._rows


class _NetworkDb:
    """MySQL simulé à partir du schéma de la fixture : seule l'absence d'ALTER compte."""

    isNetwork = True

    engines: dict[str, str] = {}

    def __init__(self, path):
        self._c = sqlite3.connect(path)
        self._rows = []
        self.alters = []
        self.cursor = _EngineCursor(self)

    def GetListeTables(self):
        return self._c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()

    def GetListeChamps2(self, table):
        return [(r[1], r[2]) for r in self._c.execute(f"PRAGMA table_info({table})")]

    def ExecuterReq(self, req):
        # Comme GestionDB en réseau : « () » est réécrit, ce qui casse DATABASE().
        req = req.replace("()", "(10000000, 10000001)")
        if "information_schema" in req:
            return 0
        self._rows = self._c.execute(req).fetchall()
        return 1

    def ResultatReq(self):
        return self._rows

    def AjoutChamp(self, **kwargs):
        self.alters.append(kwargs)


def test_network_base_is_never_altered_automatically(base):
    db = _NetworkDb(base)
    result = add_contract_engine_columns(db)
    assert result.ok is False
    assert "MySQL" in result.message and "administrateur" in result.message
    assert db.alters == []


class _MyIsamNetworkDb(_NetworkDb):
    engines = {"contrats": "MyISAM"}


def test_network_tables_without_transactions_make_the_base_refused(base):
    report = check_schema(_MyIsamNetworkDb(base))
    assert not report.compatible
    assert "contrats" in report.blocking_text() and "InnoDB" in report.blocking_text()
    assert check_schema(_NetworkDb(base)).compatible


def test_refuse_database_does_not_block_in_autoclose_mode(monkeypatch):
    import launcher

    monkeypatch.setenv("TEAMWORKS_QT_AUTOCLOSE_MS", "100")
    assert launcher.refuse_database(None, "Table « presences » absente.") == 3



def test_network_precheck_refusal_hides_encoded_password(monkeypatch, GestionDB, tmp_path):
    """Une erreur réseau ne doit jamais afficher la référence legacy complète."""
    import launcher
    import Utils
    from types import ModuleType
    from infrastructure.persistence import current_database_config

    # Linux minimal n'installe pas appdirs : remplacer uniquement l'adaptateur
    # de chemins, sans importer UTILS_Fichiers ni changer les dependances.
    fake_files = ModuleType("Utils.UTILS_Fichiers")
    fake_files.GetRepUtilisateur = lambda filename: str(tmp_path / filename)
    monkeypatch.setitem(sys.modules, "Utils.UTILS_Fichiers", fake_files)
    monkeypatch.setattr(Utils, "UTILS_Fichiers", fake_files, raising=False)

    token = "#64#c2VjcmV0LXRlc3Q="
    reference = f"3306;127.0.0.1;recette;{token}[RESEAU]recette"

    class FailedNetworkDb:
        nomFichier = reference + "_TDATA"
        isNetwork = True
        echec = 1
        erreur = RuntimeError("Connexion MySQL impossible")

        def Close(self):
            pass

    monkeypatch.setattr(GestionDB, "DB", lambda: FailedNetworkDb())
    monkeypatch.setattr(launcher, "import_chemins_safely", lambda: None)
    monkeypatch.setattr(
        current_database_config,
        "read_current_database_name",
        lambda path: reference,
    )

    report, message = launcher.precheck_production_database()
    assert report is None
    assert "127.0.0.1:3306" in message
    assert "recette_tdata" in message
    assert token not in message
    assert "[RESEAU]" not in message
