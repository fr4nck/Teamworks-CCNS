from __future__ import annotations

import hashlib
import json
import sqlite3

import pytest

from teamworks.CcnsCore.migration_remboursements_deplacements import (
    MigrationBloquee,
    RollbackRefuse,
    SnapshotInvalide,
    appliquer_base_sqlite,
    planifier_base_sqlite,
    restaurer_snapshot_sqlite,
)


def _creer_schema(connexion: sqlite3.Connection) -> None:
    connexion.executescript(
        """
        CREATE TABLE remboursements (
            IDremboursement INTEGER PRIMARY KEY,
            IDpersonne INTEGER,
            date TEXT,
            montant REAL,
            listeIDdeplacement TEXT
        );
        CREATE TABLE deplacements (
            IDdeplacement INTEGER PRIMARY KEY,
            date TEXT,
            IDpersonne INTEGER,
            objet TEXT,
            distance REAL,
            tarif_km REAL,
            IDremboursement INTEGER
        );
        """
    )


def _base(tmp_path):
    chemin = tmp_path / "teamworks.dat"
    connexion = sqlite3.connect(chemin)
    _creer_schema(connexion)
    return chemin, connexion


def _remb(connexion, identifiant, personne=1, liste=""):
    connexion.execute(
        "INSERT INTO remboursements "
        "(IDremboursement, IDpersonne, date, montant, listeIDdeplacement) "
        "VALUES (?, ?, '2026-09-05', 10, ?)",
        (identifiant, personne, liste),
    )


def _dep(connexion, identifiant, remboursement, personne=1):
    connexion.execute(
        "INSERT INTO deplacements "
        "(IDdeplacement, date, IDpersonne, objet, distance, tarif_km, IDremboursement) "
        "VALUES (?, '2026-09-05', ?, 'trajet', 10, 0.5, ?)",
        (identifiant, personne, remboursement),
    )


def _relations(chemin):
    connexion = sqlite3.connect(chemin)
    try:
        enfants = connexion.execute(
            "SELECT IDdeplacement, IDpersonne, IDremboursement FROM deplacements ORDER BY IDdeplacement"
        ).fetchall()
        parents = connexion.execute(
            "SELECT IDremboursement, IDpersonne, listeIDdeplacement FROM remboursements ORDER BY IDremboursement"
        ).fetchall()
        return enfants, parents
    finally:
        connexion.close()


def test_plan_strict_regenere_uniquement_les_projections(tmp_path) -> None:
    chemin, connexion = _base(tmp_path)
    _remb(connexion, 1, liste="2-1-1-bad-")
    _remb(connexion, 2, liste="1-999")
    _dep(connexion, 1, 1)
    _dep(connexion, 2, 1)
    connexion.commit()
    connexion.close()

    plan = planifier_base_sqlite(chemin)

    assert plan.applicable
    assert plan.actions_enfants == ()
    assert [(x.identifiant, x.apres) for x in plan.actions_projections] == [
        (1, "1-2"),
        (2, ""),
    ]
    assert any("token(s)" in x for x in plan.avertissements)
    assert any("absent(s)" in x for x in plan.avertissements)


def test_reference_enfant_orpheline_bloque_toute_migration(tmp_path) -> None:
    chemin, connexion = _base(tmp_path)
    _dep(connexion, 7, 999)
    connexion.commit()
    connexion.close()

    plan = planifier_base_sqlite(chemin)

    assert not plan.applicable
    assert [x.type_blocage for x in plan.blocages] == ["reference_enfant_orpheline"]
    avant = chemin.read_bytes()
    with pytest.raises(MigrationBloquee):
        appliquer_base_sqlite(chemin, chemin_snapshot=tmp_path / "snapshot.json")
    assert chemin.read_bytes() == avant
    assert not (tmp_path / "snapshot.json").exists()


@pytest.mark.parametrize("valeur", ["", "abc", -1, 1.5, b"1"])
def test_id_enfant_invalide_est_bloquant(tmp_path, valeur) -> None:
    chemin, connexion = _base(tmp_path)
    _remb(connexion, 1, liste="1")
    _dep(connexion, 1, valeur)
    connexion.commit()
    connexion.close()

    plan = planifier_base_sqlite(chemin)

    assert not plan.applicable
    assert any(x.type_blocage == "id_remboursement_enfant_invalide" for x in plan.blocages)


@pytest.mark.parametrize("personne_enfant,personne_parent", [(1, 2), (None, 1), (1, None), (None, None)])
def test_personne_canonique_non_verifiable_ou_incoherente_bloque(
    tmp_path, personne_enfant, personne_parent
) -> None:
    chemin, connexion = _base(tmp_path)
    _remb(connexion, 1, personne=personne_parent, liste="1")
    _dep(connexion, 1, 1, personne=personne_enfant)
    connexion.commit()
    connexion.close()

    plan = planifier_base_sqlite(chemin)

    assert not plan.applicable
    assert any(x.type_blocage == "personne_canonique_incoherente" for x in plan.blocages)


def test_recuperation_parent_unique_est_explicitement_opt_in(tmp_path) -> None:
    chemin, connexion = _base(tmp_path)
    _remb(connexion, 1, liste="7")
    _dep(connexion, 7, 0)
    connexion.commit()
    connexion.close()

    strict = planifier_base_sqlite(chemin)
    recuperation = planifier_base_sqlite(chemin, recuperer_parent_unique=True)

    assert strict.applicable
    assert strict.actions_enfants == ()
    assert strict.actions_projections[0].apres == ""
    assert recuperation.applicable
    assert [(x.identifiant, x.apres) for x in recuperation.actions_enfants] == [(7, 1)]
    assert recuperation.actions_projections == ()


def test_revendications_multiples_sur_enfant_libre_sont_nettoyees_en_mode_strict(tmp_path) -> None:
    chemin, connexion = _base(tmp_path)
    _remb(connexion, 1, liste="7")
    _remb(connexion, 2, liste="7")
    _dep(connexion, 7, None)
    connexion.commit()
    connexion.close()

    plan = planifier_base_sqlite(chemin)

    assert plan.applicable
    assert plan.actions_enfants == ()
    assert [(x.identifiant, x.apres) for x in plan.actions_projections] == [(1, ""), (2, "")]
    assert any("multiples" in x for x in plan.avertissements)


def test_application_atomique_cree_snapshot_et_verifie_etat_final(tmp_path) -> None:
    chemin, connexion = _base(tmp_path)
    _remb(connexion, 1, liste="2")
    _remb(connexion, 2, liste="1")
    _dep(connexion, 1, 1)
    _dep(connexion, 2, 0)
    connexion.commit()
    connexion.close()
    snapshot = tmp_path / "backup.json"

    resultat = appliquer_base_sqlite(chemin, chemin_snapshot=snapshot)

    assert snapshot.is_file()
    assert resultat.snapshot == snapshot
    assert _relations(chemin) == ([(1, 1, 1), (2, 1, 0)], [(1, 1, "1"), (2, 1, "")])
    document = json.loads(snapshot.read_text(encoding="utf-8"))
    assert document["format"] == "teamworks-remboursements-deplacements-snapshot"
    assert document["before_state_sha256"] == resultat.plan.etat_avant_sha256
    assert document["planned_after_state_sha256"] == resultat.etat_apres_sha256


def test_mode_recuperation_met_a_jour_enfant_et_projection_dans_la_meme_transaction(tmp_path) -> None:
    chemin, connexion = _base(tmp_path)
    _remb(connexion, 1, liste="7")
    _dep(connexion, 7, None)
    connexion.commit()
    connexion.close()

    appliquer_base_sqlite(
        chemin,
        recuperer_parent_unique=True,
        chemin_snapshot=tmp_path / "backup.json",
    )

    assert _relations(chemin) == ([(7, 1, 1)], [(1, 1, "7")])


def test_erreur_sql_en_milieu_application_rollbacke_toutes_les_ecritures(tmp_path) -> None:
    chemin, connexion = _base(tmp_path)
    _remb(connexion, 1, liste="7")
    _dep(connexion, 7, 0)
    connexion.executescript(
        """
        CREATE TRIGGER bloquer_projection
        BEFORE UPDATE OF listeIDdeplacement ON remboursements
        BEGIN
            SELECT RAISE(ABORT, 'panne injectee');
        END;
        """
    )
    connexion.commit()
    connexion.close()
    avant = _relations(chemin)

    with pytest.raises(sqlite3.DatabaseError):
        appliquer_base_sqlite(
            chemin,
            recuperer_parent_unique=False,
            chemin_snapshot=tmp_path / "backup.json",
        )

    assert _relations(chemin) == avant


def test_rollback_restaure_exactement_null_zero_et_projection_brute(tmp_path) -> None:
    chemin, connexion = _base(tmp_path)
    _remb(connexion, 1, liste="2-2-bad-")
    _dep(connexion, 1, None)
    _dep(connexion, 2, 0)
    connexion.commit()
    connexion.close()
    original = _relations(chemin)
    snapshot = tmp_path / "backup.json"

    appliquer_base_sqlite(chemin, chemin_snapshot=snapshot)
    assert _relations(chemin) != original
    resultat = restaurer_snapshot_sqlite(chemin, snapshot)

    assert _relations(chemin) == original
    document = json.loads(snapshot.read_text(encoding="utf-8"))
    assert resultat.etat_restaure_sha256 == document["before_state_sha256"]


def test_rollback_refuse_si_relations_ont_change_depuis_la_migration(tmp_path) -> None:
    chemin, connexion = _base(tmp_path)
    _remb(connexion, 1, liste="2")
    _dep(connexion, 1, 1)
    connexion.commit()
    connexion.close()
    snapshot = tmp_path / "backup.json"
    appliquer_base_sqlite(chemin, chemin_snapshot=snapshot)

    connexion = sqlite3.connect(chemin)
    _dep(connexion, 9, 0)
    connexion.commit()
    connexion.close()
    avant_rollback = _relations(chemin)

    with pytest.raises(RollbackRefuse):
        restaurer_snapshot_sqlite(chemin, snapshot)

    assert _relations(chemin) == avant_rollback


def test_snapshot_altere_est_refuse_avant_toute_ecriture(tmp_path) -> None:
    chemin, connexion = _base(tmp_path)
    _remb(connexion, 1, liste="2")
    _dep(connexion, 1, 1)
    connexion.commit()
    connexion.close()
    snapshot = tmp_path / "backup.json"
    appliquer_base_sqlite(chemin, chemin_snapshot=snapshot)
    avant = _relations(chemin)

    texte = snapshot.read_text(encoding="utf-8")
    snapshot.write_text(texte.replace('"IDdeplacement": 1', '"IDdeplacement": 99', 1), encoding="utf-8")

    with pytest.raises(SnapshotInvalide):
        restaurer_snapshot_sqlite(chemin, snapshot)
    assert _relations(chemin) == avant


def test_planification_fichier_est_strictement_lecture_seule(tmp_path) -> None:
    chemin, connexion = _base(tmp_path)
    _remb(connexion, 1, liste="2")
    _dep(connexion, 1, 1)
    connexion.commit()
    connexion.close()
    avant = hashlib.sha256(chemin.read_bytes()).hexdigest()

    planifier_base_sqlite(chemin)

    apres = hashlib.sha256(chemin.read_bytes()).hexdigest()
    assert apres == avant


def test_apply_ne_cree_jamais_une_base_absente(tmp_path) -> None:
    chemin = tmp_path / "absente.dat"

    with pytest.raises(sqlite3.OperationalError):
        appliquer_base_sqlite(chemin, chemin_snapshot=tmp_path / "backup.json")

    assert not chemin.exists()


def test_projection_canonique_trop_longue_bloque_au_lieu_de_depasser_varchar_historique(tmp_path) -> None:
    chemin, connexion = _base(tmp_path)
    _remb(connexion, 1, liste="")
    # 100 IDs à 4 chiffres produisent largement plus de 300 caractères.
    for identifiant in range(1000, 1100):
        _dep(connexion, identifiant, 1)
    connexion.commit()
    connexion.close()

    plan = planifier_base_sqlite(chemin)

    assert not plan.applicable
    assert any(
        x.type_blocage == "projection_depasse_longueur_historique"
        for x in plan.blocages
    )


def test_application_ne_modifie_pas_le_schema(tmp_path) -> None:
    chemin, connexion = _base(tmp_path)
    _remb(connexion, 1, liste="2")
    _dep(connexion, 1, 1)
    connexion.commit()
    schema_avant = connexion.execute(
        "SELECT type, name, sql FROM sqlite_master ORDER BY type, name"
    ).fetchall()
    connexion.close()

    appliquer_base_sqlite(chemin, chemin_snapshot=tmp_path / "backup.json")

    connexion = sqlite3.connect(chemin)
    try:
        schema_apres = connexion.execute(
            "SELECT type, name, sql FROM sqlite_master ORDER BY type, name"
        ).fetchall()
    finally:
        connexion.close()
    assert schema_apres == schema_avant


def test_rollback_refuse_un_snapshot_provenant_dune_autre_base(tmp_path) -> None:
    chemin, connexion = _base(tmp_path)
    _remb(connexion, 1, liste="2")
    _dep(connexion, 1, 1)
    connexion.commit()
    connexion.close()
    snapshot = tmp_path / "backup.json"
    appliquer_base_sqlite(chemin, chemin_snapshot=snapshot)

    autre = tmp_path / "copie.dat"
    autre.write_bytes(chemin.read_bytes())

    with pytest.raises(RollbackRefuse):
        restaurer_snapshot_sqlite(autre, snapshot)
