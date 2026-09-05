"""Régressions d'intégrité des frais de déplacement wxPython.

Ces tests extraient les méthodes métier ciblées sans importer wxPython. Ils couvrent
les défauts Vanilla confirmés autour du calcul kilométrique et de la relation
Déplacement ↔ Remboursement.
"""

from __future__ import annotations

import ast
import copy
import datetime
import decimal
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
DEPLACEMENT = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_deplacement.py"
REMBOURSEMENT = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_remboursement.py"
PAGE_FRAIS = ROOT / "teamworks" / "Ctrl" / "CTRL_Page_frais.py"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _method_node(path: Path, class_name: str, method_name: str) -> ast.FunctionDef:
    tree = ast.parse(_source(path))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == method_name:
                    return item
    raise AssertionError(f"Méthode introuvable : {class_name}.{method_name}")


def _method_source(path: Path, class_name: str, method_name: str) -> str:
    source = _source(path)
    node = _method_node(path, class_name, method_name)
    lines = source.splitlines()
    return "\n".join(lines[node.lineno - 1 : node.end_lineno])


def _load_method(path: Path, class_name: str, method_name: str, globals_=None):
    node = copy.deepcopy(_method_node(path, class_name, method_name))
    node.decorator_list = []
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = dict(globals_ or {})
    exec(compile(module, str(path), "exec"), namespace)
    return namespace[method_name]


class _Control:
    def __init__(self, value=None, selection=0):
        self.value = value
        self.selection = selection
        self.label = None

    def GetValue(self):  # noqa: N802 - API wx historique
        return self.value

    def GetCurrentSelection(self):  # noqa: N802
        return self.selection

    def SetLabel(self, label):  # noqa: N802
        self.label = label


class _DB:
    """Doublure SQLite avec sémantique commit=False de GestionDB."""

    def __init__(self, connexion: sqlite3.Connection, *, fail_after_child=False):
        self.connexion = connexion
        self.cursor = connexion.cursor()
        self.fail_after_child = fail_after_child
        self.child_updates = 0
        self.closed = False

    def ReqInsert(self, table, values, commit=True):  # noqa: N802
        columns = [name for name, _ in values]
        payload = [value for _, value in values]
        placeholders = ", ".join("?" for _ in payload)
        self.cursor.execute(
            "INSERT INTO %s (%s) VALUES (%s)"
            % (table, ", ".join(columns), placeholders),
            payload,
        )
        if commit:
            self.connexion.commit()
        return self.cursor.lastrowid

    def ReqMAJ(self, table, values, key, key_value, commit=True):  # noqa: N802
        if table == "deplacements":
            self.child_updates += 1
            if self.fail_after_child and self.child_updates == 1:
                raise RuntimeError("panne injectée pendant le rattachement")
        assignments = ", ".join("%s=?" % name for name, _ in values)
        payload = [value for _, value in values]
        self.cursor.execute(
            "UPDATE %s SET %s WHERE %s=?" % (table, assignments, key),
            payload + [key_value],
        )
        if commit:
            self.connexion.commit()

    def Commit(self):  # noqa: N802
        self.connexion.commit()

    def Close(self):  # noqa: N802
        self.closed = True


def _database() -> sqlite3.Connection:
    connexion = sqlite3.connect(":memory:")
    connexion.executescript(
        """
        CREATE TABLE remboursements (
            IDremboursement INTEGER PRIMARY KEY AUTOINCREMENT,
            IDpersonne INTEGER,
            date TEXT,
            montant REAL,
            listeIDdeplacement TEXT
        );
        CREATE TABLE deplacements (
            IDdeplacement INTEGER PRIMARY KEY,
            IDpersonne INTEGER,
            IDremboursement INTEGER
        );
        INSERT INTO deplacements VALUES (7, 1, 0);
        INSERT INTO deplacements VALUES (8, 1, NULL);
        """
    )
    connexion.commit()
    return connexion


def _dialogue_remboursement(checked=(7, 8), unchecked=(), IDremboursement=None):
    return SimpleNamespace(
        IDremboursement=IDremboursement,
        dictPersonnes={0: 1},
        ctrl_date=_Control(),
        ctrl_utilisateur=_Control(selection=0),
        ctrl_montant=_Control("52.80"),
        ctrl_deplacements=SimpleNamespace(
            ListeItemsCoches=lambda: (list(checked), list(unchecked))
        ),
        GetDatePickerValue=lambda _ctrl: datetime.date(2026, 9, 5),
    )


def test_calcul_kilometrique_ne_reduit_plus_globalement_decimal_a_deux_chiffres() -> None:
    source = _source(DEPLACEMENT)
    assert "decimal.getcontext().prec = 2" not in source

    calcul = _load_method(
        DEPLACEMENT,
        "SaisieDeplacement",
        "CalcMontantRmbst",
        globals_={"decimal": decimal},
    )
    double = SimpleNamespace(
        ctrl_distance=_Control("123"),
        ctrl_tarif=_Control("0.55"),
        ctrl_montant=_Control(),
        ValideControleFloat=lambda _controle: True,
    )
    calcul(double)
    assert double.ctrl_montant.label == "67.65 €"


def test_modifier_un_deplacement_ne_detache_plus_son_remboursement() -> None:
    source = _method_source(DEPLACEMENT, "SaisieDeplacement", "SauvegardeDeplacement")
    commun, creation = source.split("if self.IDdeplacement is None:", 1)
    assert '("IDremboursement", 0)' not in commun
    assert '("IDremboursement", 0)' in creation


def test_sauvegarde_remboursement_utilise_une_seule_transaction() -> None:
    source = _method_source(REMBOURSEMENT, "SaisieRemboursement", "Sauvegarde")
    assert source.count("GestionDB.DB()") == 1
    assert source.count("DB.Commit()") == 1
    assert source.count("commit=False") >= 3
    assert "DB.connexion.rollback()" in source
    assert source.index('ReqInsert("remboursements"') < source.index('("IDremboursement", ID)')


def test_creation_remboursement_et_rattachements_sont_commites_ensemble() -> None:
    connexion = _database()
    db = _DB(connexion)
    sauvegarde = _load_method(
        REMBOURSEMENT,
        "SaisieRemboursement",
        "Sauvegarde",
        globals_={"GestionDB": SimpleNamespace(DB=lambda: db)},
    )

    IDremboursement = sauvegarde(_dialogue_remboursement())

    parent = connexion.execute(
        "SELECT listeIDdeplacement FROM remboursements WHERE IDremboursement=?",
        (IDremboursement,),
    ).fetchone()
    enfants = connexion.execute(
        "SELECT IDdeplacement, IDremboursement FROM deplacements ORDER BY IDdeplacement"
    ).fetchall()
    assert parent == ("7-8",)
    assert enfants == [(7, IDremboursement), (8, IDremboursement)]
    assert db.closed is True


def test_panne_pendant_rattachement_annule_aussi_le_parent() -> None:
    connexion = _database()
    db = _DB(connexion, fail_after_child=True)
    sauvegarde = _load_method(
        REMBOURSEMENT,
        "SaisieRemboursement",
        "Sauvegarde",
        globals_={"GestionDB": SimpleNamespace(DB=lambda: db)},
    )

    with pytest.raises(RuntimeError, match="panne injectée"):
        sauvegarde(_dialogue_remboursement())

    assert connexion.execute("SELECT COUNT(*) FROM remboursements").fetchone()[0] == 0
    assert connexion.execute(
        "SELECT IDdeplacement, IDremboursement FROM deplacements ORDER BY IDdeplacement"
    ).fetchall() == [(7, 0), (8, None)]
    assert db.closed is True


def test_editeur_traite_null_comme_non_rembourse_et_garde_son_propre_lot() -> None:
    source = _method_source(REMBOURSEMENT, "ListCtrl_deplacements", "Importation")
    assert "COALESCE(IDremboursement, 0)=0" in source
    assert "COALESCE(IDremboursement, 0) IN (0, %d)" in source
    assert "IDremboursement not in (None, 0" in source


def test_liste_principale_lit_les_rattachements_depuis_deplacements() -> None:
    source = _method_source(PAGE_FRAIS, "ListCtrl_remboursements", "Importation")
    assert "listeIDdeplacement" not in source
    assert "SELECT IDdeplacement, IDremboursement FROM deplacements" in source
    assert "dictDeplacements.setdefault(IDremboursement, []).append(IDdeplacement)" in source


def test_liste_historique_reste_projection_de_compatibilite_a_ecriture() -> None:
    sauvegarde = _method_source(REMBOURSEMENT, "SaisieRemboursement", "Sauvegarde")
    import_dialogue = _method_source(REMBOURSEMENT, "SaisieRemboursement", "Importation")
    assert 'texteID = "-".join(str(ID) for ID in listeIDcoches)' in sauvegarde
    assert '("listeIDdeplacement", texteID)' in sauvegarde
    assert "listeIDdeplacement" not in import_dialogue


def test_suppression_remboursement_detache_et_supprime_avant_commit_unique() -> None:
    source = _method_source(PAGE_FRAIS, "Panel", "SupprimerRemboursement")
    assert "UPDATE deplacements SET IDremboursement=0 WHERE IDremboursement=%d" in source
    assert 'DB.ReqDEL(' in source
    assert "commit=False" in source
    assert source.count("DB.Commit()") == 1
    assert "DB.connexion.rollback()" in source
