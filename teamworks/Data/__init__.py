# -*- coding: utf-8 -*-
"""Extensions additives du schéma Teamworks historique.

``DATA_Tables.py`` reste volontairement proche du fichier vanilla. Les
extensions Teamworks-CCNS sont appliquées ici dès l'import du package ``Data``
avant que ``GestionDB`` ne conserve une référence vers ``DATA_Tables.DB_DATA``.

C'est important pour les créations *et* les réparations de tables : une
réparation basée uniquement sur le schéma historique ne doit jamais supprimer
les colonnes TW-184 déjà présentes dans une base réelle.
"""

from . import DATA_Tables


def _extend_table(table_name, columns):
    schema = DATA_Tables.DB_DATA[table_name]
    existing = {column[0] for column in schema}
    for column in columns:
        if column[0] not in existing:
            schema.append(column)
            existing.add(column[0])


def _ensure_table(table_name, columns):
    if table_name not in DATA_Tables.DB_DATA:
        DATA_Tables.DB_DATA[table_name] = list(columns)


def _apply_tw184_contract_schema():
    _extend_table(
        "contrats",
        (
            ("cee_qualification", "VARCHAR(32)", u"Qualification CEE", u"Qualification/statut CEE"),
            ("convention_code", "VARCHAR(32)", u"Convention", u"Code de la convention applicable"),
            ("ccns_group", "VARCHAR(8)", u"Groupe CCNS", u"Groupe de classification CCNS"),
            ("weekly_hours", "REAL", u"Durée hebdo", u"Durée hebdomadaire de référence"),
            ("gross_monthly_salary", "REAL", u"Salaire brut mensuel", u"Rémunération brute mensuelle"),
            ("gross_annual_salary", "REAL", u"Salaire brut annuel", u"Rémunération brute annuelle"),
            ("operation_type", "VARCHAR(24)", u"Nature opération", u"Nouveau contrat, renouvellement CDD ou CDD vers CDI"),
            ("previous_contract_id", "INTEGER", u"Contrat précédent", u"Contrat précédent lié à l'opération"),
            ("trial_period_value", "INTEGER", u"Période d'essai", u"Valeur structurée de la période d'essai"),
            ("trial_period_unit", "VARCHAR(8)", u"Unité essai", u"DAY ou MONTH"),
        ),
    )
    _extend_table(
        "contrats_modeles",
        (
            ("cee_qualification", "VARCHAR(32)", u"Qualification CEE", u"Qualification/statut CEE ciblé"),
            ("convention_code", "VARCHAR(32)", u"Convention", u"Convention ciblée"),
            ("ccns_group", "VARCHAR(8)", u"Groupe CCNS", u"Groupe CCNS ciblé"),
        ),
    )
    _ensure_table(
        "contrats_cee_baremes",
        (
            ("IDbareme", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID", u"ID du barème"),
            ("qualification", "VARCHAR(32)", u"Qualification", u"Qualification/statut CEE"),
            ("montant_journalier", "REAL", u"Montant journalier", u"Barème brut journalier employeur"),
            ("date_debut", "DATE", u"Début validité", u"Date de début d'application du barème"),
        ),
    )
    _ensure_table(
        "contrats_documents_modeles",
        (
            ("IDdocument_modele", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID", u"ID du modèle documentaire"),
            ("nom_fichier", "VARCHAR(255)", u"Fichier", u"Nom du fichier de publipostage"),
            ("convention_code", "VARCHAR(32)", u"Convention", u"Convention ciblée"),
            ("ccns_group", "VARCHAR(8)", u"Groupe CCNS", u"Groupe CCNS ciblé, vide = générique"),
            ("cee_qualification", "VARCHAR(32)", u"Qualification CEE", u"Qualification CEE ciblée, vide = générique"),
        ),
    )


_apply_tw184_contract_schema()
