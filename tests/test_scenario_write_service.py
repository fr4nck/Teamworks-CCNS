# -*- coding: utf-8 -*-

from __future__ import annotations

import sqlite3
from datetime import date

import pytest

from application.services.scenario_write import (
    ScenarioCategoryCommand,
    ScenarioSaveCommand,
    delete_scenario,
    duplicate_scenario,
    save_scenario,
)
from application.services.transactional_write import WriteCode
from infrastructure.persistence.scenario_write_adapter import (
    GestionDbScenarioWriteAdapter,
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
    connexion.execute(
        "INSERT INTO personnes (IDpersonne, nom) VALUES (1, 'Test')"
    )
    connexion.commit()
    return DBTest(connexion)


@pytest.fixture
def port(db):
    return GestionDbScenarioWriteAdapter(db)


def _category(
    category_id,
    *,
    forecast="+01:00",
    report="",
    scenario_category_id=None,
):
    return ScenarioCategoryCommand(
        category_id=category_id,
        forecast=forecast,
        report=report,
        scenario_category_id=scenario_category_id,
    )


def _command(
    name="Scenario source",
    *,
    scenario_id=None,
    categories=None,
    start=date(2026, 1, 1),
    end=date(2026, 12, 31),
):
    return ScenarioSaveCommand(
        person_id=1,
        name=name,
        description="Description",
        hour_mode=0,
        month_detail=0,
        start_date=start,
        end_date=end,
        all_categories=True,
        categories=tuple(categories or ()),
        scenario_id=scenario_id,
    )


def test_creation_parent_et_categories_commit_unique(db, port):
    result = save_scenario(
        port,
        command=_command(
            categories=[
                _category(10, forecast="+01:00"),
                _category(20, forecast="+02:00"),
            ]
        ),
    )

    assert result.ok is True
    assert result.committed is True
    assert result.code == WriteCode.OK
    assert db.commit_count == 1
    assert result.value is not None
    assert result.value.name == "Scenario source"
    assert [item.category_id for item in result.value.categories] == [10, 20]
    assert db.connexion.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0] == 1
    assert db.connexion.execute("SELECT COUNT(*) FROM scenarios_cat").fetchone()[0] == 2


def test_modification_synchronise_ajout_mise_a_jour_et_suppression(db, port):
    created = save_scenario(
        port,
        command=_command(
            categories=[
                _category(10, forecast="+01:00"),
                _category(20, forecast="+02:00"),
            ]
        ),
    )
    scenario_id = created.target_id
    first_id, second_id = [
        row[0]
        for row in db.connexion.execute(
            "SELECT IDscenario_cat FROM scenarios_cat "
            "WHERE IDscenario=? ORDER BY IDcategorie",
            (scenario_id,),
        ).fetchall()
    ]

    result = save_scenario(
        port,
        command=_command(
            "Scenario modifie",
            scenario_id=scenario_id,
            categories=[
                _category(
                    10,
                    forecast="+03:00",
                    scenario_category_id=first_id,
                ),
                _category(30, forecast="+05:00"),
            ],
        ),
    )

    assert result.ok is True
    assert db.commit_count == 2
    assert db.connexion.execute(
        "SELECT nom FROM scenarios WHERE IDscenario=?", (scenario_id,)
    ).fetchone() == ("Scenario modifie",)
    assert db.connexion.execute(
        "SELECT IDcategorie, prevision FROM scenarios_cat "
        "WHERE IDscenario=? ORDER BY IDcategorie",
        (scenario_id,),
    ).fetchall() == [(10, "+03:00"), (30, "+05:00")]
    assert db.connexion.execute(
        "SELECT COUNT(*) FROM scenarios_cat WHERE IDscenario_cat=?", (second_id,)
    ).fetchone()[0] == 0


def test_modification_refuse_categorie_appartenant_a_un_autre_scenario(db, port):
    first = save_scenario(
        port,
        command=_command(
            "Premier",
            categories=[_category(10)],
        ),
    )
    second = save_scenario(
        port,
        command=_command(
            "Second",
            categories=[_category(20)],
        ),
    )
    foreign_category_id = db.connexion.execute(
        "SELECT IDscenario_cat FROM scenarios_cat WHERE IDscenario=?",
        (second.target_id,),
    ).fetchone()[0]

    result = save_scenario(
        port,
        command=_command(
            "Ne doit pas rester",
            scenario_id=first.target_id,
            categories=[
                _category(
                    10,
                    forecast="+09:00",
                    scenario_category_id=foreign_category_id,
                )
            ],
        ),
    )

    assert result.ok is False
    assert result.code == WriteCode.DATABASE_ERROR
    assert result.committed is False
    assert db.connexion.execute(
        "SELECT nom FROM scenarios WHERE IDscenario=?", (first.target_id,)
    ).fetchone() == ("Premier",)
    assert db.connexion.execute(
        "SELECT prevision FROM scenarios_cat WHERE IDscenario=?", (second.target_id,)
    ).fetchone() == ("+01:00",)


def test_creation_rollback_si_ecriture_categorie_echoue(db, port, monkeypatch):
    def fail_insert(*_args, **_kwargs):
        raise sqlite3.IntegrityError("panne injectee")

    monkeypatch.setattr(port, "insert_scenario_category", fail_insert)

    result = save_scenario(
        port,
        command=_command(categories=[_category(10)]),
    )

    assert result.ok is False
    assert result.code == WriteCode.DATABASE_ERROR
    assert db.commit_count == 0
    assert db.connexion.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0] == 0
    assert db.connexion.execute("SELECT COUNT(*) FROM scenarios_cat").fetchone()[0] == 0


def test_duplication_copie_parent_et_categories_avec_un_commit_supplementaire(db, port):
    source = save_scenario(
        port,
        command=_command(
            "Source",
            categories=[
                _category(10, forecast="+01:00"),
                _category(20, forecast="+02:00"),
            ],
        ),
    )

    result = duplicate_scenario(port, scenario_id=source.target_id)

    assert result.ok is True
    assert result.committed is True
    assert result.target_id != source.target_id
    assert result.value is not None
    assert result.value.name == "Copie de Source"
    assert [item.category_id for item in result.value.categories] == [10, 20]
    assert db.commit_count == 2


def test_duplication_rollback_si_copie_categorie_echoue(db, port, monkeypatch):
    source = save_scenario(
        port,
        command=_command(
            "Source",
            categories=[_category(10), _category(20)],
        ),
    )
    original_insert = port.insert_scenario_category
    calls = {"count": 0}

    def fail_second(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 2:
            raise sqlite3.IntegrityError("panne injectee")
        return original_insert(*args, **kwargs)

    monkeypatch.setattr(port, "insert_scenario_category", fail_second)

    result = duplicate_scenario(port, scenario_id=source.target_id)

    assert result.ok is False
    assert result.code == WriteCode.DATABASE_ERROR
    assert db.connexion.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0] == 1
    assert db.connexion.execute("SELECT COUNT(*) FROM scenarios_cat").fetchone()[0] == 2


def test_suppression_refuse_scenario_reference_par_un_report(db, port):
    source = save_scenario(
        port,
        command=_command("Source", categories=[_category(10)]),
    )
    other = save_scenario(
        port,
        command=_command(
            "Autre",
            categories=[
                _category(
                    30,
                    report="A%d;30;+01:00" % source.target_id,
                )
            ],
        ),
    )

    result = delete_scenario(
        port,
        scenario_id=source.target_id,
        confirmed=True,
    )

    assert other.ok is True
    assert result.ok is False
    assert result.code == WriteCode.VALIDATION_ERROR
    assert result.committed is False
    assert port.read_scenario(source.target_id) is not None


def test_suppression_supprime_categories_puis_parent_et_confirme_absence(db, port):
    source = save_scenario(
        port,
        command=_command(
            "Source",
            categories=[_category(10), _category(20)],
        ),
    )

    result = delete_scenario(
        port,
        scenario_id=source.target_id,
        confirmed=True,
    )

    assert result.ok is True
    assert result.committed is True
    assert result.value is True
    assert db.connexion.execute(
        "SELECT COUNT(*) FROM scenarios WHERE IDscenario=?", (source.target_id,)
    ).fetchone()[0] == 0
    assert db.connexion.execute(
        "SELECT COUNT(*) FROM scenarios_cat WHERE IDscenario=?", (source.target_id,)
    ).fetchone()[0] == 0


def test_suppression_exige_confirmation_explicite(db, port):
    source = save_scenario(port, command=_command("Source"))

    result = delete_scenario(
        port,
        scenario_id=source.target_id,
        confirmed=False,
    )

    assert result.ok is False
    assert result.code == WriteCode.VALIDATION_ERROR
    assert result.committed is False
    assert port.read_scenario(source.target_id) is not None


def test_validation_refuse_periode_inversee_sans_acces_ecriture(db, port):
    result = save_scenario(
        port,
        command=_command(
            start=date(2026, 12, 31),
            end=date(2026, 1, 1),
        ),
    )

    assert result.ok is False
    assert result.code == WriteCode.VALIDATION_ERROR
    assert db.commit_count == 0
    assert db.connexion.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0] == 0


def test_echec_readback_apres_commit_est_signale_comme_commite(db, port, monkeypatch):
    monkeypatch.setattr(
        port,
        "read_scenario",
        lambda _scenario_id: (_ for _ in ()).throw(RuntimeError("readback casse")),
    )

    result = save_scenario(
        port,
        command=_command("Source"),
    )

    assert result.ok is False
    assert result.code == WriteCode.READBACK_ERROR
    assert result.committed is True
    assert db.commit_count == 1
    assert db.connexion.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0] == 1
