# -*- coding: utf-8 -*-

from __future__ import annotations

import sqlite3
from datetime import date

import pytest

from application.services.planning_read import (
    PresenceQuery,
    read_planning,
)
from application.services.read_result import (
    ReadCompleteness,
    ReadIssueCode,
    ReadRetryPolicy,
)
from infrastructure.persistence.planning_read_adapter import (
    GestionDbPlanningReadAdapter,
)


class DBTest:
    def __init__(self, connexion):
        self.connexion = connexion
        self.cursor = connexion.cursor()
        self.isNetwork = False
        self.echec = 0


@pytest.fixture
def db():
    connexion = sqlite3.connect(":memory:")
    connexion.execute(
        "CREATE TABLE personnes ("
        "IDpersonne INTEGER PRIMARY KEY, nom TEXT, prenom TEXT)"
    )
    connexion.execute(
        "CREATE TABLE cat_presences ("
        "IDcategorie INTEGER PRIMARY KEY, nom_categorie TEXT, couleur TEXT)"
    )
    connexion.execute(
        "CREATE TABLE presences ("
        "IDpresence INTEGER PRIMARY KEY AUTOINCREMENT, "
        "IDpersonne INTEGER, date TEXT, heure_debut TEXT, heure_fin TEXT, "
        "IDcategorie INTEGER, intitule TEXT)"
    )
    connexion.execute(
        "CREATE TABLE periodes_vacances ("
        "IDperiode INTEGER PRIMARY KEY, nom TEXT, annee INTEGER, "
        "date_debut TEXT, date_fin TEXT)"
    )

    connexion.executemany(
        "INSERT INTO personnes (IDpersonne, nom, prenom) VALUES (?, ?, ?)",
        [
            (1, "Martin", "Alice"),
            (2, "Bernard", "Bob"),
            (3, "Durand", "Chloé"),
        ],
    )
    connexion.executemany(
        "INSERT INTO cat_presences "
        "(IDcategorie, nom_categorie, couleur) VALUES (?, ?, ?)",
        [
            (10, "Travail", "#112233"),
            (20, "Réunion", "#445566"),
        ],
    )
    connexion.executemany(
        "INSERT INTO presences "
        "(IDpersonne, date, heure_debut, heure_fin, IDcategorie, intitule) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            (1, "2026-09-21", "08:00", "12:00", 10, "Matin"),
            (1, "2026-09-22", "09:00", "10:30", 20, "Équipe"),
            (2, "2026-09-21", "13:00", "17:00", 10, "Après-midi"),
            (3, "2026-10-01", "08:00", "09:00", 10, "Hors période"),
        ],
    )
    connexion.execute(
        "INSERT INTO periodes_vacances "
        "(IDperiode, nom, annee, date_debut, date_fin) "
        "VALUES (?, ?, ?, ?, ?)",
        (100, "Toussaint", 2026, "2026-10-17", "2026-11-02"),
    )
    connexion.commit()
    return DBTest(connexion)


@pytest.fixture
def port(db):
    return GestionDbPlanningReadAdapter(db)


def test_lecture_complete_multijours_multipersonnes(db, port):
    result = read_planning(
        port,
        query=PresenceQuery(
            start_date=date(2026, 9, 21),
            end_date=date(2026, 9, 22),
            person_ids=(1, 2),
        ),
    )

    assert result.completeness is ReadCompleteness.COMPLETE
    assert result.ok is True
    assert result.value is not None
    assert len(result.value.presences) == 3
    assert {item.person_id for item in result.value.presences} == {1, 2}
    assert {item.person_id for item in result.value.people} == {1, 2}
    assert len(result.value.categories) == 2
    assert result.value.vacations == ()
    assert result.value.presences[0].duration_minutes == 240
    assert not hasattr(result, "committed")


def test_filtre_categorie_ne_ramene_que_la_categorie_demandee(db, port):
    result = read_planning(
        port,
        query=PresenceQuery(
            start_date=date(2026, 9, 21),
            end_date=date(2026, 9, 22),
            person_ids=(1, 2),
            category_ids=(20,),
        ),
    )

    assert result.ok is True
    assert result.value is not None
    assert len(result.value.presences) == 1
    assert result.value.presences[0].category_id == 20
    assert tuple(item.category_id for item in result.value.categories) == (20,)


def test_planning_vide_est_une_lecture_complete_pas_un_echec(db, port):
    result = read_planning(
        port,
        query=PresenceQuery(
            start_date=date(2027, 1, 1),
            end_date=date(2027, 1, 2),
            person_ids=(1,),
        ),
    )

    assert result.completeness is ReadCompleteness.COMPLETE
    assert result.value is not None
    assert result.value.presences == ()
    assert result.issues == ()


def test_vacances_indisponibles_donnent_une_lecture_partielle(
    db, port, monkeypatch
):
    def fail_vacations(query):
        raise sqlite3.OperationalError("table vacances indisponible")

    monkeypatch.setattr(port, "read_vacations", fail_vacations)

    result = read_planning(
        port,
        query=PresenceQuery(
            start_date=date(2026, 9, 21),
            end_date=date(2026, 9, 22),
            person_ids=(1,),
        ),
    )

    assert result.completeness is ReadCompleteness.PARTIAL
    assert result.ok is True
    assert result.value is not None
    assert len(result.value.presences) == 2
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.code is ReadIssueCode.OPTIONAL_SOURCE_UNAVAILABLE
    assert issue.source == "vacations"
    assert issue.retry_policy is ReadRetryPolicy.AUTOMATIC_ONCE
    assert result.should_retry_automatically(0) is True
    assert result.should_retry_automatically(1) is False


def test_source_obligatoire_indisponible_fait_echouer_toute_lecture(
    db, port, monkeypatch
):
    def fail_presences(query):
        raise sqlite3.OperationalError("connexion perdue")

    monkeypatch.setattr(port, "read_presences", fail_presences)

    result = read_planning(
        port,
        query=PresenceQuery(
            start_date=date(2026, 9, 21),
            end_date=date(2026, 9, 22),
            person_ids=(1,),
        ),
    )

    assert result.completeness is ReadCompleteness.FAILED
    assert result.ok is False
    assert result.value is None
    assert result.primary_issue is not None
    assert result.primary_issue.code is ReadIssueCode.REQUIRED_SOURCE_UNAVAILABLE
    assert result.primary_issue.source == "presences"


def test_donnees_horaires_corrompues_ne_sont_pas_classees_panne_sql(db, port):
    db.connexion.execute(
        "INSERT INTO presences "
        "(IDpersonne, date, heure_debut, heure_fin, IDcategorie, intitule) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (1, "2026-09-23", "25:00", "26:00", 10, "Corrompue"),
    )
    db.connexion.commit()

    result = read_planning(
        port,
        query=PresenceQuery(
            start_date=date(2026, 9, 23),
            end_date=date(2026, 9, 23),
            person_ids=(1,),
        ),
    )

    assert result.completeness is ReadCompleteness.FAILED
    assert result.primary_issue is not None
    assert result.primary_issue.code is ReadIssueCode.SOURCE_DATA_INVALID
    assert result.primary_issue.source == "presences"
    assert result.primary_issue.retry_policy is ReadRetryPolicy.NEVER


def test_vacances_invalides_degradent_sans_bloquer_le_planning(db, port):
    db.connexion.execute(
        "INSERT INTO periodes_vacances "
        "(IDperiode, nom, annee, date_debut, date_fin) "
        "VALUES (?, ?, ?, ?, ?)",
        (101, "Cassée", 2026, "2026-09-30", "2026-09-20"),
    )
    db.connexion.commit()

    result = read_planning(
        port,
        query=PresenceQuery(
            start_date=date(2026, 9, 19),
            end_date=date(2026, 10, 1),
            person_ids=(1,),
        ),
    )

    assert result.completeness is ReadCompleteness.PARTIAL
    assert result.value is not None
    assert result.primary_issue is not None
    assert result.primary_issue.code is ReadIssueCode.SOURCE_DATA_INVALID
    assert result.primary_issue.source == "vacations"


@pytest.mark.parametrize(
    "query",
    [
        PresenceQuery(
            start_date=date(2026, 9, 22),
            end_date=date(2026, 9, 21),
        ),
        PresenceQuery(
            start_date=date(2026, 9, 21),
            end_date=date(2026, 9, 22),
            person_ids=(0,),
        ),
        PresenceQuery(
            start_date=date(2026, 9, 21),
            end_date=date(2026, 9, 22),
            category_ids=(-1,),
        ),
    ],
)
def test_requete_invalide_est_bloquante_et_non_retryable(db, port, query):
    result = read_planning(port, query=query)

    assert result.completeness is ReadCompleteness.FAILED
    assert result.primary_issue is not None
    assert result.primary_issue.code is ReadIssueCode.INVALID_QUERY
    assert result.primary_issue.retry_policy is ReadRetryPolicy.NEVER
    assert result.user_retry_allowed is False
