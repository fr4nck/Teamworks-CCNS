# -*- coding: utf-8 -*-

import sqlite3

import pytest

from teamworks.Utils.UTILS_ScenarioTransactions import (
    ScenarioReferenceError,
    dupliquer_scenario_atomique,
    sauvegarder_scenario_atomique,
    supprimer_scenario_atomique,
)


class CurseurInjecte(object):
    def __init__(self, curseur, predicate, exception, echec_au=2):
        self._curseur = curseur
        self._predicate = predicate
        self._exception = exception
        self._compteur = 0
        self._echec_au = echec_au

    def execute(self, sql, params=()):
        if self._predicate(sql):
            self._compteur += 1
            if self._compteur == self._echec_au:
                raise self._exception
        self._curseur.execute(sql, params)
        return self

    def fetchone(self):
        return self._curseur.fetchone()

    def fetchall(self):
        return self._curseur.fetchall()

    @property
    def lastrowid(self):
        return self._curseur.lastrowid


class DBTest(object):
    def __init__(self, connexion):
        self.connexion = connexion
        self.cursor = connexion.cursor()
        self.isNetwork = False

    def Commit(self):
        self.connexion.commit()


@pytest.fixture
def db():
    connexion = sqlite3.connect(":memory:")
    connexion.execute(
        "CREATE TABLE scenarios ("
        "IDscenario INTEGER PRIMARY KEY AUTOINCREMENT, "
        "IDpersonne INTEGER, nom TEXT, description TEXT, mode_heure INTEGER, "
        "detail_mois INTEGER, date_debut TEXT, date_fin TEXT, toutes_categories INTEGER)"
    )
    connexion.execute(
        "CREATE TABLE scenarios_cat ("
        "IDscenario_cat INTEGER PRIMARY KEY AUTOINCREMENT, "
        "IDscenario INTEGER, IDcategorie INTEGER, prevision TEXT, report TEXT, "
        "date_debut_realise TEXT, date_fin_realise TEXT)"
    )
    connexion.commit()
    return DBTest(connexion)


def _creer_source(db):
    cur = db.connexion.execute(
        "INSERT INTO scenarios "
        "(IDpersonne, nom, description, mode_heure, detail_mois, date_debut, date_fin, toutes_categories) "
        "VALUES (1, 'Source', '', 0, 0, '2026-01-01', '2026-12-31', 1)"
    )
    IDscenario = cur.lastrowid
    db.connexion.executemany(
        "INSERT INTO scenarios_cat "
        "(IDscenario, IDcategorie, prevision, report, date_debut_realise, date_fin_realise) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            (IDscenario, 10, '+01:00', '', None, None),
            (IDscenario, 20, '+02:00', '', None, None),
        ],
    )
    db.connexion.commit()
    return IDscenario


def _donnees_scenario(nom):
    return [
        ("IDpersonne", 1),
        ("nom", nom),
        ("description", ""),
        ("mode_heure", 0),
        ("detail_mois", 0),
        ("date_debut", "2026-01-01"),
        ("date_fin", "2026-12-31"),
        ("toutes_categories", 1),
    ]


def _categorie(IDscenario_cat, prevision):
    return {
        "IDscenario_cat": IDscenario_cat,
        "prevision": prevision,
        "report": "",
        "date_debut_realise": None,
        "date_fin_realise": None,
    }


def test_dupliquer_copie_parent_et_categories_avec_un_commit(db):
    source = _creer_source(db)

    copie = dupliquer_scenario_atomique(db, source)

    assert db.connexion.execute(
        "SELECT nom FROM scenarios WHERE IDscenario=?", (copie,)
    ).fetchone() == ("Copie de Source",)
    assert db.connexion.execute(
        "SELECT COUNT(*) FROM scenarios_cat WHERE IDscenario=?", (copie,)
    ).fetchone()[0] == 2


def test_dupliquer_rollback_si_une_categorie_echoue(db):
    source = _creer_source(db)
    db.cursor = CurseurInjecte(
        db.cursor,
        lambda sql: sql.startswith("INSERT INTO scenarios_cat"),
        sqlite3.IntegrityError("panne injectée"),
    )

    with pytest.raises(sqlite3.IntegrityError):
        dupliquer_scenario_atomique(db, source)

    assert db.connexion.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0] == 1
    assert db.connexion.execute("SELECT COUNT(*) FROM scenarios_cat").fetchone()[0] == 2


def test_suppression_refuse_un_scenario_reference(db):
    source = _creer_source(db)
    autre = db.connexion.execute(
        "INSERT INTO scenarios "
        "(IDpersonne, nom, description, mode_heure, detail_mois, date_debut, date_fin, toutes_categories) "
        "VALUES (1, 'Autre', '', 0, 0, '2026-01-01', '2026-12-31', 1)"
    ).lastrowid
    db.connexion.execute(
        "INSERT INTO scenarios_cat "
        "(IDscenario, IDcategorie, prevision, report, date_debut_realise, date_fin_realise) "
        "VALUES (?, 30, '+01:00', ?, NULL, NULL)",
        (autre, "A%d;30;+01:00" % source),
    )
    db.connexion.commit()

    with pytest.raises(ScenarioReferenceError):
        supprimer_scenario_atomique(db, source)

    assert db.connexion.execute(
        "SELECT COUNT(*) FROM scenarios WHERE IDscenario=?", (source,)
    ).fetchone()[0] == 1


def test_suppression_rollback_si_parent_echoue_apres_enfants(db):
    source = _creer_source(db)
    db.cursor = CurseurInjecte(
        db.cursor,
        lambda sql: sql.startswith("DELETE FROM scenarios"),
        sqlite3.OperationalError("panne injectée"),
        echec_au=2,
    )

    with pytest.raises(sqlite3.OperationalError):
        supprimer_scenario_atomique(db, source)

    assert db.connexion.execute(
        "SELECT COUNT(*) FROM scenarios WHERE IDscenario=?", (source,)
    ).fetchone()[0] == 1
    assert db.connexion.execute(
        "SELECT COUNT(*) FROM scenarios_cat WHERE IDscenario=?", (source,)
    ).fetchone()[0] == 2


def test_sauvegarde_rollback_si_synchronisation_categorie_echoue(db):
    source = _creer_source(db)
    avant_nom = db.connexion.execute(
        "SELECT nom FROM scenarios WHERE IDscenario=?", (source,)
    ).fetchone()[0]
    ids = [row[0] for row in db.connexion.execute(
        "SELECT IDscenario_cat FROM scenarios_cat WHERE IDscenario=? ORDER BY IDscenario_cat",
        (source,),
    ).fetchall()]

    virtuel = {
        10: _categorie(ids[0], "+03:00"),
        20: _categorie(ids[1], "+04:00"),
    }
    db.cursor = CurseurInjecte(
        db.cursor,
        lambda sql: sql.startswith("UPDATE scenarios_cat"),
        sqlite3.OperationalError("panne injectée"),
    )

    with pytest.raises(sqlite3.OperationalError):
        sauvegarder_scenario_atomique(db, source, _donnees_scenario("Modifié"), virtuel)

    assert db.connexion.execute(
        "SELECT nom FROM scenarios WHERE IDscenario=?", (source,)
    ).fetchone()[0] == avant_nom
    assert db.connexion.execute(
        "SELECT prevision FROM scenarios_cat WHERE IDscenario=? ORDER BY IDscenario_cat",
        (source,),
    ).fetchall() == [("+01:00",), ("+02:00",)]


def test_creation_rollback_si_deuxieme_categorie_echoue(db):
    virtuel = {
        10: _categorie(None, "+01:00"),
        20: _categorie(None, "+02:00"),
    }
    db.cursor = CurseurInjecte(
        db.cursor,
        lambda sql: sql.startswith("INSERT INTO scenarios_cat"),
        sqlite3.IntegrityError("panne injectée"),
    )

    with pytest.raises(sqlite3.IntegrityError):
        sauvegarder_scenario_atomique(db, None, _donnees_scenario("Nouveau"), virtuel)

    assert db.connexion.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0] == 0
    assert db.connexion.execute("SELECT COUNT(*) FROM scenarios_cat").fetchone()[0] == 0
