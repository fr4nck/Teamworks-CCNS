#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compatibilité structurelle des bases historiques Teamworks.

La version distribuée de Teamworks-CCNS (0.9.x) n'est pas le numéro historique
du schéma (2.x). Les réparations ci-dessous sont donc volontairement
idempotentes et indépendantes du numéro marketing de l'application.
"""


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

    return {
        "tables_creees": tuple(tables_creees),
        "champs_ajoutes": tuple(champs_ajoutes),
    }
