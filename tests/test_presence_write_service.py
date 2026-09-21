# -*- coding: utf-8 -*-

from __future__ import annotations

import sqlite3
from datetime import date

import pytest

from application.services.presence_write import (
    PresenceCreateCommand,
    PresenceDeleteCommand,
    PresenceTarget,
    PresenceUpdateCommand,
    create_presences,
    delete_presence,
    normalize_presence_title,
    update_presence,
)
from application.services.transactional_write import WriteCode
from infrastructure.persistence.presence_write_adapter import (
    GestionDbPresenceWriteAdapter,
)


class DBTest:
    def __init__(self, connexion):
        self.connexion = connexion
        self.cursor = connexion.cursor()
        self.isNetwork = False
        self.echec = 0
        self.commit_count = 0

    def Commit(self):
        self.connexion.commit()
        self.commit_count += 1


@pytest.fixture
def db():
    connexion = sqlite3.connect(":memory:")
    connexion.execute(
        "CREATE TABLE personnes ("
        "IDpersonne INTEGER PRIMARY KEY, nom TEXT)"
    )
    connexion.execute(
        "CREATE TABLE presences ("
        "IDpresence INTEGER PRIMARY KEY AUTOINCREMENT, "
        "IDpersonne INTEGER, date TEXT, heure_debut TEXT, heure_fin TEXT, "
        "IDcategorie INTEGER, intitule TEXT)"
    )
    connexion.executemany(
        "INSERT INTO personnes (IDpersonne, nom) VALUES (?, ?)",
        [(1, "Alice"), (2, "Bob")],
    )
    connexion.commit()
    return DBTest(connexion)


@pytest.fixture
def port(db):
    return GestionDbPresenceWriteAdapter(db)


def _create_command(
    targets,
    *,
    start="08:00",
    end="09:00",
    category_id=10,
    title="Accueil",
):
    return PresenceCreateCommand(
        targets=tuple(targets),
        start_time=start,
        end_time=end,
        category_id=category_id,
        title=title,
    )


def _insert_raw(
    db,
    *,
    person_id=1,
    day="2026-09-21",
    start="08:00",
    end="09:00",
    category_id=10,
    title="Existant",
):
    cursor = db.connexion.execute(
        "INSERT INTO presences "
        "(IDpersonne, date, heure_debut, heure_fin, IDcategorie, intitule) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (person_id, day, start, end, category_id, title),
    )
    db.connexion.commit()
    return cursor.lastrowid


def test_normalisation_legende_reprend_le_contrat_historique():
    assert normalize_presence_title(None) == ""
    assert normalize_presence_title("  ") == ""
    assert normalize_presence_title("()") == ""
    assert normalize_presence_title("( )") == ""
    assert normalize_presence_title("  Accueil matin  ") == "Accueil matin"


@pytest.mark.parametrize("value", ["24:00", "25:00", "08:60", "8h00"])
def test_creation_refuse_horaire_hors_contrat_sans_ecriture(db, port, value):
    result = create_presences(
        port,
        command=_create_command(
            [PresenceTarget(1, date(2026, 9, 21))],
            start=value,
            end="12:00",
        ),
    )

    assert result.ok is False
    assert result.code == WriteCode.VALIDATION_ERROR
    assert db.commit_count == 0
    assert db.connexion.execute("SELECT COUNT(*) FROM presences").fetchone()[0] == 0


def test_creation_refuse_fin_avant_debut(db, port):
    result = create_presences(
        port,
        command=_create_command(
            [PresenceTarget(1, date(2026, 9, 21))],
            start="09:00",
            end="08:30",
        ),
    )

    assert result.ok is False
    assert result.code == WriteCode.VALIDATION_ERROR
    assert db.commit_count == 0


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("08:00", "08:00"),
        ("08:00", "08:14"),
    ],
)
def test_creation_refuse_duree_inferieure_a_15_minutes(db, port, start, end):
    result = create_presences(
        port,
        command=_create_command(
            [PresenceTarget(1, date(2026, 9, 21))],
            start=start,
            end=end,
        ),
    )

    assert result.ok is False
    assert result.code == WriteCode.VALIDATION_ERROR
    assert db.commit_count == 0


def test_creation_accepte_exactement_15_minutes(db, port):
    result = create_presences(
        port,
        command=_create_command(
            [PresenceTarget(1, date(2026, 9, 21))],
            start="08:00",
            end="08:15",
        ),
    )

    assert result.ok is True
    assert result.committed is True
    assert len(result.value.created) == 1
    assert db.commit_count == 1


def test_creation_refuse_categorie_absente_ou_legende_trop_longue(db, port):
    missing_category = create_presences(
        port,
        command=_create_command(
            [PresenceTarget(1, date(2026, 9, 21))],
            category_id=0,
        ),
    )
    long_title = create_presences(
        port,
        command=_create_command(
            [PresenceTarget(1, date(2026, 9, 21))],
            title="x" * 201,
        ),
    )

    assert missing_category.ok is False
    assert missing_category.code == WriteCode.VALIDATION_ERROR
    assert long_title.ok is False
    assert long_title.code == WriteCode.VALIDATION_ERROR
    assert db.commit_count == 0


def test_lot_ignore_chevauchement_individuel_et_commit_les_autres(db, port):
    _insert_raw(
        db,
        person_id=1,
        day="2026-09-21",
        start="08:00",
        end="10:00",
    )

    result = create_presences(
        port,
        command=_create_command(
            [
                PresenceTarget(1, date(2026, 9, 21)),
                PresenceTarget(1, date(2026, 9, 22)),
            ],
            start="09:00",
            end="10:00",
            title="  Présence valide  ",
        ),
    )

    assert result.ok is True
    assert result.committed is True
    assert len(result.value.created) == 1
    assert result.value.created[0].presence_date == date(2026, 9, 22)
    assert result.value.created[0].title == "Présence valide"
    assert result.value.skipped_overlaps == (
        PresenceTarget(1, date(2026, 9, 21)),
    )
    assert db.commit_count == 1
    assert db.connexion.execute("SELECT COUNT(*) FROM presences").fetchone()[0] == 2


def test_bornes_jointives_ne_sont_pas_un_chevauchement(db, port):
    _insert_raw(
        db,
        person_id=1,
        day="2026-09-21",
        start="08:00",
        end="09:00",
    )

    result = create_presences(
        port,
        command=_create_command(
            [PresenceTarget(1, date(2026, 9, 21))],
            start="09:00",
            end="10:00",
        ),
    )

    assert result.ok is True
    assert len(result.value.created) == 1
    assert not result.value.skipped_overlaps


def test_lot_rollback_total_si_deuxieme_insert_echoue(db, port, monkeypatch):
    original = port.insert_presence
    calls = {"count": 0}

    def fail_second(**kwargs):
        calls["count"] += 1
        if calls["count"] == 2:
            raise sqlite3.IntegrityError("panne injectée")
        return original(**kwargs)

    monkeypatch.setattr(port, "insert_presence", fail_second)

    result = create_presences(
        port,
        command=_create_command(
            [
                PresenceTarget(1, date(2026, 9, 21)),
                PresenceTarget(1, date(2026, 9, 22)),
            ]
        ),
    )

    assert result.ok is False
    assert result.code == WriteCode.DATABASE_ERROR
    assert result.committed is False
    assert db.commit_count == 0
    assert db.connexion.execute("SELECT COUNT(*) FROM presences").fetchone()[0] == 0


def test_lot_refuse_personne_disparue_et_rollback_les_insertions_precedentes(
    db, port
):
    result = create_presences(
        port,
        command=_create_command(
            [
                PresenceTarget(1, date(2026, 9, 21)),
                PresenceTarget(999, date(2026, 9, 22)),
            ]
        ),
    )

    assert result.ok is False
    assert result.code == WriteCode.DATABASE_ERROR
    assert db.commit_count == 0
    assert db.connexion.execute("SELECT COUNT(*) FROM presences").fetchone()[0] == 0


def test_modification_refuse_chevauchement_et_ne_modifie_pas_la_base(db, port):
    target_id = _insert_raw(
        db,
        day="2026-09-21",
        start="08:00",
        end="09:00",
        title="Cible",
    )
    _insert_raw(
        db,
        day="2026-09-21",
        start="09:00",
        end="10:00",
        title="Voisine",
    )

    result = update_presence(
        port,
        command=PresenceUpdateCommand(
            presence_id=target_id,
            start_time="08:30",
            end_time="09:30",
            category_id=20,
            title="Modifiée",
        ),
    )

    assert result.ok is False
    assert result.code == WriteCode.VALIDATION_ERROR
    assert db.commit_count == 0
    assert db.connexion.execute(
        "SELECT heure_debut, heure_fin, IDcategorie, intitule "
        "FROM presences WHERE IDpresence=?",
        (target_id,),
    ).fetchone() == ("08:00", "09:00", 10, "Cible")


def test_modification_exclut_sa_propre_ligne_du_controle_chevauchement(db, port):
    target_id = _insert_raw(
        db,
        day="2026-09-21",
        start="08:00",
        end="09:00",
        title="Cible",
    )

    result = update_presence(
        port,
        command=PresenceUpdateCommand(
            presence_id=target_id,
            start_time="08:15",
            end_time="09:15",
            category_id=20,
            title="  Modifiée  ",
        ),
    )

    assert result.ok is True
    assert result.committed is True
    assert result.value.start_time == "08:15"
    assert result.value.end_time == "09:15"
    assert result.value.category_id == 20
    assert result.value.title == "Modifiée"
    assert db.commit_count == 1


def test_modification_cible_absente(db, port):
    result = update_presence(
        port,
        command=PresenceUpdateCommand(
            presence_id=999,
            start_time="08:00",
            end_time="09:00",
            category_id=10,
        ),
    )

    assert result.ok is False
    assert result.code == WriteCode.TARGET_NOT_FOUND
    assert db.commit_count == 0


def test_suppression_exige_confirmation_explicite(db, port):
    target_id = _insert_raw(db)

    result = delete_presence(
        port,
        command=PresenceDeleteCommand(
            presence_id=target_id,
            confirmed=False,
        ),
    )

    assert result.ok is False
    assert result.code == WriteCode.VALIDATION_ERROR
    assert port.read_presence(target_id) is not None
    assert db.commit_count == 0


def test_suppression_commit_et_confirme_absence(db, port):
    target_id = _insert_raw(db)

    result = delete_presence(
        port,
        command=PresenceDeleteCommand(
            presence_id=target_id,
            confirmed=True,
        ),
    )

    assert result.ok is True
    assert result.committed is True
    assert result.value is True
    assert port.read_presence(target_id) is None
    assert db.commit_count == 1


def test_readback_echoue_apres_commit_sans_faux_rollback(db, port, monkeypatch):
    original = port.read_presence
    calls = {"count": 0}

    def fail_after_commit(presence_id):
        calls["count"] += 1
        if calls["count"] >= 1:
            raise RuntimeError("readback cassé")
        return original(presence_id)

    monkeypatch.setattr(port, "read_presence", fail_after_commit)

    result = create_presences(
        port,
        command=_create_command(
            [PresenceTarget(1, date(2026, 9, 21))]
        ),
    )

    assert result.ok is False
    assert result.code == WriteCode.READBACK_ERROR
    assert result.committed is True
    assert db.commit_count == 1
    assert db.connexion.execute("SELECT COUNT(*) FROM presences").fetchone()[0] == 1
