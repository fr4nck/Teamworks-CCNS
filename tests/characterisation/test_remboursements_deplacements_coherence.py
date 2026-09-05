from __future__ import annotations

import datetime
import sqlite3
from types import SimpleNamespace

import pytest

from source_legacy import function_source, load_method_as_function, read_source


DEPLACEMENT = "teamworks/Dlg/DLG_Saisie_deplacement.py"
REMBOURSEMENT = "teamworks/Dlg/DLG_Saisie_remboursement.py"
PAGE_FRAIS = "teamworks/Ctrl/CTRL_Page_frais.py"
GESTION_DB = "teamworks/GestionDB.py"


class _Control:
    def __init__(self, value=None, selection=0):
        self.value = value
        self.selection = selection

    def GetValue(self):
        return self.value

    def GetCurrentSelection(self):
        return self.selection


class _DB:
    """Doublure SQLite reproduisant les commits par défaut de GestionDB."""

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.cursor = connection.cursor()

    def ExecuterReq(self, req):
        self.cursor.execute(req)

    def ResultatReq(self):
        return self.cursor.fetchall()

    def ReqInsert(self, table, values, commit=True):
        columns = [name for name, _ in values]
        payload = [value for _, value in values]
        placeholders = ", ".join("?" for _ in payload)
        self.cursor.execute(
            "INSERT INTO %s (%s) VALUES (%s)"
            % (table, ", ".join(columns), placeholders),
            payload,
        )
        if commit:
            self.connection.commit()
        return self.cursor.lastrowid

    def ReqMAJ(self, table, values, key, key_value, commit=True):
        payload = [value for _, value in values]
        assignments = ", ".join("%s=?" % name for name, _ in values)
        self.cursor.execute(
            "UPDATE %s SET %s WHERE %s=?" % (table, assignments, key),
            payload + [key_value],
        )
        if commit:
            self.connection.commit()

    def ReqDEL(self, table, key, key_value, commit=True):
        self.cursor.execute(
            "DELETE FROM %s WHERE %s=?" % (table, key),
            (key_value,),
        )
        if commit:
            self.connection.commit()

    def Commit(self):
        self.connection.commit()

    def Close(self):
        pass


class _Factory:
    def __init__(self, connection: sqlite3.Connection, fail_on_call=None):
        self.connection = connection
        self.fail_on_call = fail_on_call
        self.calls = 0

    def DB(self):
        self.calls += 1
        if self.fail_on_call == self.calls:
            raise RuntimeError("panne injectée entre les deux phases")
        return _DB(self.connection)


def _database() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        """
        CREATE TABLE remboursements (
            IDremboursement INTEGER PRIMARY KEY AUTOINCREMENT,
            IDpersonne INTEGER,
            date TEXT,
            montant REAL,
            listeIDdeplacement TEXT
        );
        CREATE TABLE deplacements (
            IDdeplacement INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            IDpersonne INTEGER,
            objet TEXT,
            cp_depart TEXT,
            ville_depart TEXT,
            cp_arrivee TEXT,
            ville_arrivee TEXT,
            distance REAL,
            aller_retour TEXT,
            tarif_km REAL,
            IDremboursement INTEGER
        );
        """
    )
    return connection


def _deplacement_dialogue(IDdeplacement: int):
    return SimpleNamespace(
        IDdeplacement=IDdeplacement,
        dictPersonnes={0: 1},
        ctrl_date=_Control(),
        ctrl_utilisateur=_Control(selection=0),
        ctrl_objet=_Control("trajet modifié"),
        ctrl_cp_depart=_Control("35000"),
        ctrl_ville_depart=_Control("RENNES"),
        ctrl_cp_arrivee=_Control("35500"),
        ctrl_ville_arrivee=_Control("VITRE"),
        ctrl_distance=_Control("48"),
        ctrl_aller_retour=_Control(False),
        ctrl_tarif=_Control("0.55"),
        GetDatePickerValue=lambda _ctrl: datetime.date(2026, 9, 2),
    )


def _remboursement_dialogue(*, IDremboursement, checked, unchecked=()):
    return SimpleNamespace(
        IDremboursement=IDremboursement,
        dictPersonnes={0: 1},
        ctrl_date=_Control(),
        ctrl_utilisateur=_Control(selection=0),
        ctrl_montant=_Control("26.40"),
        ctrl_deplacements=SimpleNamespace(
            ListeItemsCoches=lambda: (list(checked), list(unchecked))
        ),
        GetDatePickerValue=lambda _ctrl: datetime.date(2026, 9, 15),
    )


def test_modifier_un_deplacement_rembourse_cree_une_divergence_reelle() -> None:
    connection = _database()
    connection.execute(
        "INSERT INTO remboursements (IDremboursement, IDpersonne, date, montant, listeIDdeplacement) VALUES (3, 1, '2026-09-15', 26.40, '7')"
    )
    connection.execute(
        "INSERT INTO deplacements (IDdeplacement, date, IDpersonne, objet, cp_depart, ville_depart, cp_arrivee, ville_arrivee, distance, aller_retour, tarif_km, IDremboursement) VALUES (7, '2026-09-02', 1, 'trajet', '35000', 'RENNES', '35500', 'VITRE', 42, 'False', 0.50, 3)"
    )
    connection.commit()

    factory = _Factory(connection)
    save = load_method_as_function(
        DEPLACEMENT,
        "SaisieDeplacement",
        "SauvegardeDeplacement",
        globals_={"GestionDB": SimpleNamespace(DB=factory.DB)},
    )
    assert save(_deplacement_dialogue(7)) == 7

    child_pointer = connection.execute(
        "SELECT IDremboursement FROM deplacements WHERE IDdeplacement=7"
    ).fetchone()[0]
    parent_list = connection.execute(
        "SELECT listeIDdeplacement FROM remboursements WHERE IDremboursement=3"
    ).fetchone()[0]
    assert child_pointer == 0
    assert parent_list == "7"


def test_un_deplacement_detache_peut_etre_revendique_par_deux_listes_parentes() -> None:
    connection = _database()
    connection.execute(
        "INSERT INTO remboursements (IDremboursement, IDpersonne, date, montant, listeIDdeplacement) VALUES (3, 1, '2026-09-15', 26.40, '7')"
    )
    connection.execute(
        "INSERT INTO deplacements (IDdeplacement, date, IDpersonne, objet, cp_depart, ville_depart, cp_arrivee, ville_arrivee, distance, aller_retour, tarif_km, IDremboursement) VALUES (7, '2026-09-02', 1, 'trajet', '35000', 'RENNES', '35500', 'VITRE', 42, 'False', 0.50, 3)"
    )
    connection.commit()

    factory = _Factory(connection)
    save_move = load_method_as_function(
        DEPLACEMENT,
        "SaisieDeplacement",
        "SauvegardeDeplacement",
        globals_={"GestionDB": SimpleNamespace(DB=factory.DB)},
    )
    save_refund = load_method_as_function(
        REMBOURSEMENT,
        "SaisieRemboursement",
        "Sauvegarde",
        globals_={"GestionDB": SimpleNamespace(DB=factory.DB)},
    )

    save_move(_deplacement_dialogue(7))
    IDremboursement_b = save_refund(
        _remboursement_dialogue(IDremboursement=None, checked=[7])
    )

    assert IDremboursement_b != 3
    assert connection.execute(
        "SELECT IDremboursement FROM deplacements WHERE IDdeplacement=7"
    ).fetchone()[0] == IDremboursement_b
    assert connection.execute(
        "SELECT listeIDdeplacement FROM remboursements WHERE IDremboursement=3"
    ).fetchone()[0] == "7"
    assert connection.execute(
        "SELECT listeIDdeplacement FROM remboursements WHERE IDremboursement=?",
        (IDremboursement_b,),
    ).fetchone()[0] == "7"


def test_panne_avant_la_phase_deplacements_laisse_le_parent_seul_persiste() -> None:
    connection = _database()
    connection.execute(
        "INSERT INTO deplacements (IDdeplacement, date, IDpersonne, objet, cp_depart, ville_depart, cp_arrivee, ville_arrivee, distance, aller_retour, tarif_km, IDremboursement) VALUES (7, '2026-09-02', 1, 'trajet', '35000', 'RENNES', '35500', 'VITRE', 42, 'False', 0.50, 0)"
    )
    connection.commit()

    factory = _Factory(connection, fail_on_call=2)
    save = load_method_as_function(
        REMBOURSEMENT,
        "SaisieRemboursement",
        "Sauvegarde",
        globals_={"GestionDB": SimpleNamespace(DB=factory.DB)},
    )

    with pytest.raises(RuntimeError, match="panne injectée"):
        save(_remboursement_dialogue(IDremboursement=None, checked=[7]))

    refund = connection.execute(
        "SELECT IDremboursement, listeIDdeplacement FROM remboursements"
    ).fetchone()
    child_pointer = connection.execute(
        "SELECT IDremboursement FROM deplacements WHERE IDdeplacement=7"
    ).fetchone()[0]
    assert refund is not None
    assert refund[1] == "7"
    assert child_pointer == 0


def test_la_liste_principale_et_lediteur_ne_lisent_pas_la_meme_source() -> None:
    main_list = function_source(
        PAGE_FRAIS, "Importation", class_name="ListCtrl_remboursements"
    )
    editor_list = function_source(
        REMBOURSEMENT, "Importation", class_name="ListCtrl_deplacements"
    )
    editor_header = function_source(
        REMBOURSEMENT, "Importation", class_name="SaisieRemboursement"
    )

    assert "listeIDdeplacement.split" in main_list
    assert "IDremboursement=0 OR IDremboursement=%d" in editor_list
    assert "if IDremboursement != 0" in editor_list
    assert "listeIDdeplacement" in editor_header
    assert "listeIDdeplacement.split" not in editor_header


def test_les_deplacements_null_sont_non_rembourses_pour_certains_ecrans_mais_non_proposes() -> None:
    editor_list = function_source(
        REMBOURSEMENT, "Importation", class_name="ListCtrl_deplacements"
    )
    management_source = read_source("teamworks/Dlg/DLG_Gestion_frais.py")

    assert "IDremboursement in (None, 0)" in management_source
    assert "IDremboursement=0 ORDER BY date" in editor_list
    assert "IS NULL" not in editor_list


def test_les_operations_generiques_de_db_commitent_par_defaut() -> None:
    source = read_source(GESTION_DB)
    compact = " ".join(source.split())

    assert "def ReqInsert" in source and "commit=True" in compact
    assert "def ReqMAJ" in source and "commit=True" in compact
    assert "def ReqDEL" in source and "commit=True" in compact

    save = function_source(REMBOURSEMENT, "Sauvegarde", class_name="SaisieRemboursement")
    assert save.index('ReqInsert("remboursements"') < save.index("DB = GestionDB.DB()", save.index("DB.Close()") + 1)
    assert "DB.ReqMAJ(\n                \"deplacements\"" in save
