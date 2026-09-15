#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compatibilité structurelle des bases historiques Teamworks.

La version distribuée de Teamworks-CCNS (0.9.x) n'est pas le numéro historique
du schéma (2.x). Les migrations de données doivent donc se baser sur une
version de schéma distincte, tandis que les réparations structurelles restent
idempotentes.
"""


VERSION_SCHEMA_CIBLE = (2, 1, 2, 0)
NOM_PARAMETRE_SCHEMA = "schema_version"
VERSION_HISTORIQUE_DEFAUT = (1, 0, 5, 2)


TABLES_REQUISES = (
    "questionnaire_questions",
    "questionnaire_categories",
    "questionnaire_choix",
    "questionnaire_reponses",
    "profils",
    "profils_parametres",
    "sauvegardes_auto",
    "modeles_emails",
    "adresses_mail",
    "tw_people",
    "tw_legal_profiles",
    "tw_contract_types",
    "tw_employment_regimes",
    "tw_time_organizations",
    "tw_contracts",
    "tw_ccns_classifications",
    "tw_salary_grids",
    "tw_salary_grid_lines",
    "tw_calculation_rules",
    "tw_calculation_results",
    "tw_anomalies",
    "tw_individual_counters",
)


CHAMPS_REQUIS = {
    "adresses_mail": (
        ("nom_adresse", "VARCHAR(200)"),
        ("connexionAuthentifiee", "INTEGER"),
        ("startTLS", "INTEGER"),
        ("utilisateur", "VARCHAR(200)"),
        ("moteur", "VARCHAR(200)"),
        ("parametres", "VARCHAR(1000)"),
    ),
}


def _noms_champs(db, nom_table):
    return {description[0] for description in db.GetListeChamps2(nom_table)}


def LireVersionsFichier(db):
    """Lit en une requête les marqueurs de version stockés dans le fichier."""
    db.ExecuterReq(
        'SELECT nom, parametre FROM parametres '
        'WHERE categorie="fichier" AND nom IN ("version", "schema_version");'
    )
    return {nom: valeur for nom, valeur in db.ResultatReq()}


def DeterminerVersionSchema(db, convertir_version):
    """Retourne ``(version_schema, source)`` sans confondre 0.9.x et le schéma 2.x.

    - ``schema_version`` est prioritaire quand il existe ;
    - un ancien ``version`` commençant par 1 ou 2 est un marqueur de schéma
      historique et peut encore piloter les migrations historiques ;
    - un ``version`` commençant par 0 appartient à la lignée Teamworks-CCNS et
      ne doit jamais être comparé aux seuils historiques 2.x ;
    - en l'absence totale de marqueur, on conserve le fallback historique 1.0.5.2.
    """
    versions = LireVersionsFichier(db)
    if NOM_PARAMETRE_SCHEMA in versions:
        return convertir_version(versions[NOM_PARAMETRE_SCHEMA]), NOM_PARAMETRE_SCHEMA

    version_fichier = versions.get("version")
    if version_fichier in (None, ""):
        return VERSION_HISTORIQUE_DEFAUT, "fallback_historique"

    version_tuple = convertir_version(version_fichier)
    if version_tuple and version_tuple[0] == 0:
        return None, "produit_ccns"
    return version_tuple, "version_historique"


def MemoriserVersionSchema(db, version_schema=VERSION_SCHEMA_CIBLE):
    """Mémorise la version de schéma séparément de la version du logiciel."""
    valeur = ".".join(str(element) for element in version_schema)
    db.ExecuterReq(
        'SELECT IDparametre FROM parametres '
        'WHERE categorie="fichier" AND nom="%s";' % NOM_PARAMETRE_SCHEMA
    )
    lignes = db.ResultatReq()
    if lignes:
        db.ReqMAJ(
            "parametres",
            [("parametre", valeur)],
            "IDparametre",
            lignes[0][0],
        )
    else:
        db.ReqInsert(
            "parametres",
            [
                ("categorie", "fichier"),
                ("nom", NOM_PARAMETRE_SCHEMA),
                ("parametre", valeur),
            ],
        )
    return valeur


def Assurer(
    db,
    dico_tables,
    tables_requises=TABLES_REQUISES,
    champs_requis=CHAMPS_REQUIS,
):
    """Crée uniquement les structures manquantes et vérifie chaque réparation.

    Retourne un rapport sans modifier les données métier. Une réparation qui ne
    produit pas effectivement la table ou le champ attendu lève RuntimeError au
    lieu de laisser l'application poursuivre avec un schéma incohérent.
    """
    tables_creees = []
    champs_ajoutes = []

    for nom_table in tables_requises:
        if nom_table not in dico_tables:
            raise RuntimeError("Définition de table absente : %s" % nom_table)
        if not db.IsTableExists(nom_table):
            db.CreationTable(nom_table, dico_tables)
            if not db.IsTableExists(nom_table):
                raise RuntimeError("Création de table non effective : %s" % nom_table)
            tables_creees.append(nom_table)

    for nom_table, descriptions in champs_requis.items():
        if not db.IsTableExists(nom_table):
            raise RuntimeError("Table requise absente : %s" % nom_table)
        noms = _noms_champs(db, nom_table)
        for nom_champ, type_champ in descriptions:
            if nom_champ in noms:
                continue
            db.AjoutChamp(nom_table, nom_champ, type_champ)
            noms = _noms_champs(db, nom_table)
            if nom_champ not in noms:
                raise RuntimeError(
                    "Ajout de champ non effectif : %s.%s" % (nom_table, nom_champ)
                )
            champs_ajoutes.append("%s.%s" % (nom_table, nom_champ))

    if tables_creees or champs_ajoutes:
        db.Commit()

    return {
        "tables_creees": tuple(tables_creees),
        "champs_ajoutes": tuple(champs_ajoutes),
    }
