from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import mysql.connector
import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("TEAMWORKS_MYSQL_INTEGRATION") != "1",
    reason="Recette MySQL désactivée",
)

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "anonymize_qt_vanilla_recipe_db.py"
DATABASE = "teamworks_anonymisation_ci_qt_vanilla_recette"


def _server_connection(database=None):
    kwargs = dict(
        host=os.getenv("TEAMWORKS_MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("TEAMWORKS_MYSQL_PORT", "3306")),
        user=os.getenv("TEAMWORKS_MYSQL_USER", "root"),
        password=os.getenv("TEAMWORKS_MYSQL_PASSWORD", ""),
        use_pure=True,
        ssl_disabled=True,
    )
    if database:
        kwargs["database"] = database
    return mysql.connector.connect(**kwargs)


def _create_fixture():
    connection = _server_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(f"DROP DATABASE IF EXISTS {DATABASE}")
        cursor.execute(
            f"CREATE DATABASE {DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    finally:
        cursor.close()
        connection.close()

    connection = _server_connection(DATABASE)
    cursor = connection.cursor()
    try:
        statements = [
            """
            CREATE TABLE personnes (
                IDpersonne INTEGER PRIMARY KEY,
                civilite VARCHAR(5),
                nom VARCHAR(100),
                nom_jfille VARCHAR(100),
                prenom VARCHAR(100),
                date_naiss DATE,
                cp_naiss INTEGER,
                ville_naiss VARCHAR(100),
                num_secu VARCHAR(21),
                adresse_resid VARCHAR(200),
                cp_resid INTEGER,
                ville_resid VARCHAR(100),
                memo VARCHAR(800),
                cadre_photo VARCHAR(200),
                texte_photo VARCHAR(300)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE coordonnees (
                IDcoord INTEGER PRIMARY KEY,
                IDpersonne INTEGER,
                categorie VARCHAR(100),
                texte VARCHAR(100),
                intitule VARCHAR(300),
                CONSTRAINT fk_coord_personne
                    FOREIGN KEY (IDpersonne) REFERENCES personnes(IDpersonne)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE contrats (
                IDcontrat INTEGER PRIMARY KEY,
                IDpersonne INTEGER,
                date_debut DATE,
                date_fin DATE,
                date_rupture DATE,
                salaire_brut_mensuel DECIMAL(10,2),
                CONSTRAINT fk_contrat_personne
                    FOREIGN KEY (IDpersonne) REFERENCES personnes(IDpersonne)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE presences (
                IDpresence INTEGER PRIMARY KEY,
                IDpersonne INTEGER,
                date DATE,
                intitule VARCHAR(200)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE deplacements (
                IDdeplacement INTEGER PRIMARY KEY,
                IDpersonne INTEGER,
                date DATE,
                objet VARCHAR(100),
                cp_depart VARCHAR(5),
                ville_depart VARCHAR(200),
                cp_arrivee VARCHAR(5),
                ville_arrivee VARCHAR(200),
                distance FLOAT,
                aller_retour VARCHAR(5),
                tarif_km FLOAT,
                IDremboursement INTEGER
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE remboursements (
                IDremboursement INTEGER PRIMARY KEY,
                IDpersonne INTEGER,
                date DATE,
                montant FLOAT,
                listeIDdeplacement VARCHAR(300)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE questionnaire_reponses (
                IDreponse INTEGER PRIMARY KEY,
                IDquestion INTEGER,
                IDindividu INTEGER,
                reponse VARCHAR(400)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE candidats (
                IDcandidat INTEGER PRIMARY KEY,
                civilite VARCHAR(5),
                nom VARCHAR(100),
                prenom VARCHAR(100),
                date_naiss DATE,
                adresse_resid VARCHAR(200),
                cp_resid INTEGER,
                ville_resid VARCHAR(200),
                memo VARCHAR(300)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE coords_candidats (
                IDcoord INTEGER PRIMARY KEY,
                IDcandidat INTEGER,
                categorie VARCHAR(50),
                texte VARCHAR(100),
                intitule VARCHAR(200)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE adresses_mail (
                IDadresse INTEGER PRIMARY KEY,
                adresse VARCHAR(200),
                nom_adresse VARCHAR(200),
                motdepasse VARCHAR(200),
                smtp VARCHAR(200),
                utilisateur VARCHAR(200),
                parametres VARCHAR(1000)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE profils_parametres (
                IDparametre INTEGER PRIMARY KEY,
                IDprofil INTEGER,
                nom VARCHAR(200),
                parametre TEXT,
                type_donnee VARCHAR(200)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE sauvegardes_auto (
                IDsauvegarde INTEGER PRIMARY KEY,
                nom VARCHAR(455),
                observations VARCHAR(455),
                sauvegarde_nom VARCHAR(455),
                sauvegarde_motdepasse VARCHAR(455),
                sauvegarde_repertoire VARCHAR(455),
                sauvegarde_emails VARCHAR(455)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE photos (
                IDphoto INTEGER PRIMARY KEY,
                IDindividu INTEGER,
                photo LONGBLOB
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE documents (
                IDdocument INTEGER PRIMARY KEY,
                IDpiece INTEGER,
                IDreponse INTEGER,
                document LONGBLOB,
                type VARCHAR(50),
                label VARCHAR(400)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE tw_people (
                IDtw_person INTEGER PRIMARY KEY,
                code_interne VARCHAR(50),
                nom_affiche VARCHAR(200),
                date_naissance DATE,
                actif INTEGER
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE tw_contracts (
                IDtw_contract INTEGER PRIMARY KEY,
                IDtw_person INTEGER,
                date_debut DATE,
                date_fin DATE,
                salaire_base DECIMAL(10,2)
            ) ENGINE=InnoDB
            """,
        ]
        for statement in statements:
            cursor.execute(statement)

        cursor.execute(
            """
            INSERT INTO personnes
            VALUES (7421, 'Mme', 'NomReelTest', 'NomJeuneFilleTest', 'PrenomReelTest',
                    '1989-07-08', 35000, 'Rennes', '289071234567890',
                    '10 rue Réelle', 35000, 'Rennes',
                    'Mémo personnel à supprimer', 'photo.jpg', 'portrait personnel')
            """
        )
        cursor.execute(
            """
            INSERT INTO coordonnees
            VALUES (1, 7421, 'Email', 'vraie.adresse@example.com', 'Email personnel')
            """
        )
        cursor.execute(
            """
            INSERT INTO contrats
            VALUES (8001, 7421, '2025-09-01', '2027-08-31', NULL, 2437.42)
            """
        )
        cursor.execute(
            "INSERT INTO presences VALUES (1, 7421, '2026-09-10', 'Réunion avec prénom réel')"
        )
        cursor.execute(
            """
            INSERT INTO deplacements
            VALUES (91, 7421, '2026-09-11', 'Visite domicile',
                    '35000', 'Rennes', '35590', 'Destination réelle',
                    23.5, 'True', 0.50, 81)
            """
        )
        cursor.execute(
            "INSERT INTO remboursements VALUES (81, 7421, '2026-09-15', 23.50, '91')"
        )
        cursor.execute(
            "INSERT INTO questionnaire_reponses VALUES (11, 2, 7421, 'Réponse personnelle libre')"
        )
        cursor.execute(
            """
            INSERT INTO candidats
            VALUES (51, 'M.', 'CandidatReel', 'PrenomCandidat', '2002-04-03',
                    'Adresse candidat', 35000, 'Rennes', 'Mémo candidat')
            """
        )
        cursor.execute(
            """
            INSERT INTO coords_candidats
            VALUES (12, 51, 'Email', 'candidat.reel@example.org', 'Email candidat')
            """
        )
        cursor.execute(
            """
            INSERT INTO adresses_mail
            VALUES (1, 'rh.reelle@example.org', 'RH réelle', 'super-secret',
                    'smtp.reel.example.org', 'login-reel', 'token=secret')
            """
        )
        cursor.execute(
            "INSERT INTO profils_parametres VALUES (1, 1, 'profil', 'email=vraie@example.org', 'str')"
        )
        cursor.execute(
            """
            INSERT INTO sauvegardes_auto
            VALUES (1, 'Sauvegarde réelle', 'Observation personnelle', 'prod',
                    'motdepasse', 'C:/secret', 'admin@example.org')
            """
        )
        cursor.execute("INSERT INTO photos VALUES (1, 7421, %s)", (b"photo-personnelle",))
        cursor.execute(
            "INSERT INTO documents VALUES (1, 1, 11, %s, 'pdf', 'Document personnel')",
            (b"document-personnel",),
        )
        cursor.execute(
            "INSERT INTO tw_people VALUES (99, 'INTERNE-REEL', 'Nom affiché réel', '1989-07-08', 1)"
        )
        cursor.execute(
            "INSERT INTO tw_contracts VALUES (199, 99, '2025-09-01', NULL, 2437.42)"
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def _drop_fixture():
    connection = _server_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(f"DROP DATABASE IF EXISTS {DATABASE}")
    finally:
        cursor.close()
        connection.close()


def test_mysql_recipe_copy_is_anonymized_without_breaking_business_relations(tmp_path):
    _create_fixture()
    report = tmp_path / "anonymization-report.json"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + str(ROOT / "teamworks")

    try:
        process = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "--database",
                DATABASE,
                "--confirm-database",
                DATABASE,
                "--apply",
                "--report",
                str(report),
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=90,
        )
        assert process.returncode == 0, process.stdout + "\n" + process.stderr

        payload = json.loads(report.read_text(encoding="utf-8"))
        assert payload["audit_issues"] == []
        assert payload["persons"] == 1
        assert payload["candidates"] == 1
        assert payload["tw_people"] == 1

        connection = _server_connection(DATABASE)
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT IDpersonne, nom, prenom, num_secu, memo, cadre_photo, texte_photo, "
                "date_naiss, adresse_resid FROM personnes"
            )
            person = cursor.fetchone()
            assert person[0] == 100001
            assert "Reel" not in person[1]
            assert "Reel" not in person[2]
            assert person[3:7] == ("", "", "", "")
            assert str(person[7]) != "1989-07-08"
            assert "Recette" in person[8]

            cursor.execute("SELECT IDpersonne, date_debut, salaire_brut_mensuel FROM contrats")
            contract = cursor.fetchone()
            assert contract[0] == person[0]
            assert str(contract[1]) != "2025-09-01"
            assert float(contract[2]) != 2437.42

            cursor.execute("SELECT IDindividu, reponse FROM questionnaire_reponses")
            questionnaire = cursor.fetchone()
            assert questionnaire == (person[0], "[ANONYMISE]")

            cursor.execute("SELECT texte FROM coordonnees")
            assert cursor.fetchone()[0].endswith("@example.test")

            cursor.execute("SELECT IDcandidat, nom, memo FROM candidats")
            candidate = cursor.fetchone()
            assert candidate[0] == 200001
            assert candidate[2] == ""

            cursor.execute("SELECT texte FROM coords_candidats")
            assert cursor.fetchone()[0].endswith("@example.test")

            cursor.execute(
                "SELECT adresse, motdepasse, smtp, utilisateur, parametres FROM adresses_mail"
            )
            mail = cursor.fetchone()
            assert mail == (
                "noreply@example.test",
                "",
                "smtp.example.test",
                "",
                "",
            )

            cursor.execute("SELECT parametre FROM profils_parametres")
            assert cursor.fetchone()[0] == ""

            cursor.execute("SELECT sauvegarde_motdepasse, sauvegarde_emails FROM sauvegardes_auto")
            assert cursor.fetchone() == ("", "")

            cursor.execute("SELECT COUNT(*) FROM photos")
            assert cursor.fetchone()[0] == 0
            cursor.execute("SELECT COUNT(*) FROM documents")
            assert cursor.fetchone()[0] == 0

            cursor.execute("SELECT IDtw_person, nom_affiche, code_interne FROM tw_people")
            tw_person = cursor.fetchone()
            assert tw_person[0] == 300001
            assert "réel" not in tw_person[1].lower()
            assert tw_person[2].startswith("TW-REC-")

            cursor.execute("SELECT IDtw_person, salaire_base FROM tw_contracts")
            tw_contract = cursor.fetchone()
            assert tw_contract[0] == tw_person[0]
            assert float(tw_contract[1]) != 2437.42
        finally:
            cursor.close()
            connection.close()
    finally:
        _drop_fixture()
