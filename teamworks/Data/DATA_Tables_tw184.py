#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extension canonique du schéma historique pour le moteur de contrats TW-184.

Le fichier ``DATA_Tables.py`` reste volontairement le socle historique. Cette
extension ne supprime ni ne renomme aucune donnée existante : elle complète le
schéma canonique avec les colonnes additives et les tables employeur introduites
par TW-184. Les tables employeur ne sont pas ajoutées aux groupes d'import de
base par défaut.
"""


CONTRACT_COLUMNS = (
    ("cee_qualification", "VARCHAR(32)", u"Qualification CEE", u"Qualification/statut CEE du contrat"),
    ("convention_code", "VARCHAR(32)", u"Convention", u"Code de la convention applicable"),
    ("ccns_group", "VARCHAR(8)", u"Groupe CCNS", u"Groupe de classification CCNS"),
    ("weekly_hours", "REAL", u"Heures hebdo", u"Durée hebdomadaire contractuelle"),
    ("gross_monthly_salary", "REAL", u"Salaire mensuel brut", u"Salaire mensuel brut contractuel"),
    ("gross_annual_salary", "REAL", u"Salaire annuel brut", u"Salaire annuel brut contractuel"),
    ("operation_type", "VARCHAR(24)", u"Opération", u"Type d'opération sur le contrat"),
    ("previous_contract_id", "INTEGER", u"Contrat précédent", u"ID du contrat précédent lié"),
    ("trial_period_value", "INTEGER", u"Période d'essai", u"Valeur de la période d'essai"),
    ("trial_period_unit", "VARCHAR(8)", u"Unité essai", u"Unité de la période d'essai"),
)

MODEL_COLUMNS = (
    ("cee_qualification", "VARCHAR(32)", u"Qualification CEE", u"Qualification/statut CEE ciblé"),
    ("convention_code", "VARCHAR(32)", u"Convention", u"Code de la convention ciblée"),
    ("ccns_group", "VARCHAR(8)", u"Groupe CCNS", u"Groupe CCNS ciblé"),
)

EMPLOYER_TABLES = {
    "contrats_cee_baremes": [
        ("IDbareme", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID", u"ID du barème"),
        ("qualification", "VARCHAR(32)", u"Qualification", u"Qualification/statut CEE"),
        ("montant_journalier", "REAL", u"Montant journalier", u"Barème brut journalier employeur"),
        ("date_debut", "DATE", u"Début validité", u"Date de début d'application du barème"),
    ],
    "contrats_documents_modeles": [
        ("IDdocument_modele", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID", u"ID du modèle documentaire"),
        ("nom_fichier", "VARCHAR(255)", u"Fichier", u"Nom du fichier de publipostage"),
        ("convention_code", "VARCHAR(32)", u"Convention", u"Convention ciblée"),
        ("ccns_group", "VARCHAR(8)", u"Groupe CCNS", u"Groupe CCNS ciblé, vide = générique"),
        ("cee_qualification", "VARCHAR(32)", u"Qualification CEE", u"Qualification CEE ciblée, vide = générique"),
    ],
}


def _extend_columns(db_data, table_name, columns):
    rows = db_data[table_name]
    existing = {row[0]: row[1] for row in rows}
    for column in columns:
        name, type_name = column[:2]
        if name in existing:
            if existing[name] != type_name:
                raise ValueError(
                    "Type canonique incohérent pour %s.%s : %s != %s"
                    % (table_name, name, existing[name], type_name)
                )
            continue
        rows.append(column)


def _ensure_table(db_data, table_name, columns):
    if table_name not in db_data:
        db_data[table_name] = list(columns)
        return
    existing = {row[0]: row[1] for row in db_data[table_name]}
    expected = {row[0]: row[1] for row in columns}
    if existing != expected:
        raise ValueError("Schéma canonique incohérent pour la table %s" % table_name)


def ApplyContractSchema(db_data):
    """Complète ``DB_DATA`` de façon idempotente avec le schéma TW-184."""
    _extend_columns(db_data, "contrats", CONTRACT_COLUMNS)
    _extend_columns(db_data, "contrats_modeles", MODEL_COLUMNS)
    for table_name, columns in EMPLOYER_TABLES.items():
        _ensure_table(db_data, table_name, columns)
    return db_data
