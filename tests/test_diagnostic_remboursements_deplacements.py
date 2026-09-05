from __future__ import annotations

import hashlib
import sqlite3

from teamworks.CcnsCore.diagnostic_remboursements_deplacements import (
    Classification,
    analyser_base_sqlite,
    analyser_connexion,
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


def _ajouter_remboursement(connexion, IDremboursement, IDpersonne=1, liste=""):
    connexion.execute(
        "INSERT INTO remboursements "
        "(IDremboursement, IDpersonne, date, montant, listeIDdeplacement) "
        "VALUES (?, ?, '2026-09-01', 10.0, ?)",
        (IDremboursement, IDpersonne, liste),
    )


def _ajouter_deplacement(connexion, IDdeplacement, IDremboursement, IDpersonne=1):
    connexion.execute(
        "INSERT INTO deplacements "
        "(IDdeplacement, date, IDpersonne, objet, distance, tarif_km, IDremboursement) "
        "VALUES (?, '2026-09-01', ?, 'trajet', 10.0, 0.5, ?)",
        (IDdeplacement, IDpersonne, IDremboursement),
    )


def _projection(rapport, IDremboursement):
    return next(
        x for x in rapport.projections_canoniques if x.IDremboursement == IDremboursement
    )


def _types(rapport):
    return [cas.type_cas for cas in rapport.cas]


def test_base_coherente_restitue_la_projection_canonique() -> None:
    connexion = sqlite3.connect(":memory:")
    _creer_schema(connexion)
    _ajouter_remboursement(connexion, 1, liste="1-2")
    _ajouter_deplacement(connexion, 1, 1)
    _ajouter_deplacement(connexion, 2, 1)
    connexion.commit()

    rapport = analyser_connexion(connexion)

    projection = _projection(rapport, 1)
    assert projection.canonique_ids == (1, 2)
    assert projection.canonique_texte == "1-2"
    assert projection.classification == Classification.COHERENT
    assert rapport.deplacements_reference_orpheline == ()
    assert rapport.revendications_projection_incoherentes == ()
    assert rapport.revendications_multiples == ()


def test_reference_enfant_vers_remboursement_inexistant_est_orpheline() -> None:
    connexion = sqlite3.connect(":memory:")
    _creer_schema(connexion)
    _ajouter_deplacement(connexion, 7, 999)
    connexion.commit()

    rapport = analyser_connexion(connexion)

    assert rapport.deplacements_reference_orpheline == (7,)
    cas = next(x for x in rapport.cas if x.type_cas == "reference_enfant_orpheline")
    assert cas.classification == Classification.REFERENCE_ORPHELINE
    assert cas.avant == "IDremboursement=999"
    assert "non résolu" in cas.canonique_propose


def test_projection_revendiquant_null_et_zero_est_obsolete_et_les_valeurs_restent_distinctes() -> None:
    connexion = sqlite3.connect(":memory:")
    _creer_schema(connexion)
    _ajouter_remboursement(connexion, 1, liste="1-2")
    _ajouter_deplacement(connexion, 1, None)
    _ajouter_deplacement(connexion, 2, 0)
    connexion.commit()

    rapport = analyser_connexion(connexion)

    assert rapport.deplacements_idremboursement_null == (1,)
    assert rapport.deplacements_idremboursement_zero == (2,)
    assert len(rapport.revendications_projection_incoherentes) == 2
    assert {
        x.classification for x in rapport.revendications_projection_incoherentes
    } == {Classification.PROJECTION_OBSOLETE}
    projection = _projection(rapport, 1)
    assert projection.canonique_ids == ()
    assert projection.canonique_texte == ""
    assert projection.classification == Classification.PROJECTION_OBSOLETE


def test_projection_contredisant_un_pointeur_valide_est_un_conflit() -> None:
    connexion = sqlite3.connect(":memory:")
    _creer_schema(connexion)
    _ajouter_remboursement(connexion, 1, liste="7")
    _ajouter_remboursement(connexion, 2, liste="7")
    _ajouter_deplacement(connexion, 7, 2)
    connexion.commit()

    rapport = analyser_connexion(connexion)

    conflit = next(
        x
        for x in rapport.revendications_projection_incoherentes
        if x.entite == "remboursement 1"
    )
    assert conflit.classification == Classification.CONFLIT_ARBITRAGE
    assert "remboursement 2" in conflit.canonique_propose
    assert _projection(rapport, 1).canonique_ids == ()
    assert _projection(rapport, 2).canonique_ids == (7,)


def test_deplacement_revendique_par_plusieurs_listes_parent_est_un_conflit() -> None:
    connexion = sqlite3.connect(":memory:")
    _creer_schema(connexion)
    _ajouter_remboursement(connexion, 1, liste="7")
    _ajouter_remboursement(connexion, 2, liste="7")
    _ajouter_remboursement(connexion, 3, liste="7")
    _ajouter_deplacement(connexion, 7, 2)
    connexion.commit()

    rapport = analyser_connexion(connexion)

    assert len(rapport.revendications_multiples) == 1
    cas = rapport.revendications_multiples[0]
    assert cas.classification == Classification.CONFLIT_ARBITRAGE
    assert "[1, 2, 3]" in cas.avant
    assert cas.canonique_propose == "IDremboursement canonique=2"


def test_projection_canonique_ajoute_les_enfants_manquants_et_retire_les_revendications_obsoletes() -> None:
    connexion = sqlite3.connect(":memory:")
    _creer_schema(connexion)
    _ajouter_remboursement(connexion, 1, liste="2")
    _ajouter_deplacement(connexion, 1, 1)
    _ajouter_deplacement(connexion, 2, 0)
    connexion.commit()

    rapport = analyser_connexion(connexion)

    projection = _projection(rapport, 1)
    assert projection.avant_ids == (2,)
    assert projection.canonique_ids == (1,)
    assert projection.canonique_texte == "1"
    assert projection.classification == Classification.PROJECTION_OBSOLETE


def test_projection_mal_formee_dupliquee_et_reference_absente_sont_toutes_signalees() -> None:
    connexion = sqlite3.connect(":memory:")
    _creer_schema(connexion)
    _ajouter_remboursement(connexion, 1, liste="1-1-999-bad-")
    _ajouter_deplacement(connexion, 1, 1)
    connexion.commit()

    rapport = analyser_connexion(connexion)

    assert "projection_invalide" in _types(rapport)
    assert "projection_dupliquee" in _types(rapport)
    absent = next(
        x for x in rapport.cas if x.type_cas == "projection_reference_deplacement_absent"
    )
    assert absent.classification == Classification.REFERENCE_ORPHELINE
    projection = _projection(rapport, 1)
    assert projection.canonique_ids == (1,)
    assert projection.classification == Classification.CONFLIT_ARBITRAGE


def test_incoherence_de_personne_demande_un_arbitrage_sans_changer_le_pointeur_propose() -> None:
    connexion = sqlite3.connect(":memory:")
    _creer_schema(connexion)
    _ajouter_remboursement(connexion, 1, IDpersonne=2, liste="7")
    _ajouter_deplacement(connexion, 7, 1, IDpersonne=1)
    connexion.commit()

    rapport = analyser_connexion(connexion)

    cas = next(x for x in rapport.cas if x.type_cas == "personnes_incoherentes")
    assert cas.classification == Classification.CONFLIT_ARBITRAGE
    assert _projection(rapport, 1).canonique_ids == (7,)
    assert _projection(rapport, 1).classification == Classification.CONFLIT_ARBITRAGE


def test_ordre_non_canonique_est_detecte_et_regenere_de_facon_deterministe() -> None:
    connexion = sqlite3.connect(":memory:")
    _creer_schema(connexion)
    _ajouter_remboursement(connexion, 1, liste="2-1")
    _ajouter_deplacement(connexion, 1, 1)
    _ajouter_deplacement(connexion, 2, 1)
    connexion.commit()

    rapport = analyser_connexion(connexion)

    projection = _projection(rapport, 1)
    assert projection.canonique_texte == "1-2"
    assert projection.classification == Classification.PROJECTION_OBSOLETE


def test_rapport_texte_montre_explicitement_avant_vers_canonique() -> None:
    connexion = sqlite3.connect(":memory:")
    _creer_schema(connexion)
    _ajouter_remboursement(connexion, 1, liste="7")
    _ajouter_deplacement(connexion, 7, 0)
    connexion.commit()

    texte = analyser_connexion(connexion).render_text()

    assert "Avant → état canonique proposé" in texte
    assert "'7' → ''" in texte
    assert "projection obsolète" in texte


def test_analyse_connexion_n_execute_aucune_ecriture_sql() -> None:
    connexion = sqlite3.connect(":memory:")
    _creer_schema(connexion)
    _ajouter_remboursement(connexion, 1, liste="1")
    _ajouter_deplacement(connexion, 1, 1)
    connexion.commit()

    ecritures = []
    interdits = {
        sqlite3.SQLITE_INSERT,
        sqlite3.SQLITE_UPDATE,
        sqlite3.SQLITE_DELETE,
    }

    def autoriser(action, arg1, arg2, base, source):
        if action in interdits:
            ecritures.append((action, arg1, arg2))
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    connexion.set_authorizer(autoriser)
    rapport = analyser_connexion(connexion)

    assert rapport.nombre_deplacements == 1
    assert ecritures == []


def test_analyse_fichier_sqlite_ouvre_la_base_en_lecture_seule(tmp_path) -> None:
    chemin = tmp_path / "teamworks.dat"
    connexion = sqlite3.connect(chemin)
    _creer_schema(connexion)
    _ajouter_remboursement(connexion, 1, liste="1")
    _ajouter_deplacement(connexion, 1, 1)
    connexion.commit()
    connexion.close()
    empreinte_avant = hashlib.sha256(chemin.read_bytes()).hexdigest()

    rapport = analyser_base_sqlite(chemin)

    empreinte_apres = hashlib.sha256(chemin.read_bytes()).hexdigest()
    assert rapport.nombre_deplacements == 1
    assert empreinte_apres == empreinte_avant
