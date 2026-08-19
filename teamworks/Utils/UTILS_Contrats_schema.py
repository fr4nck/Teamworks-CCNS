#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Évolutions additives du schéma historique des contrats.

Ce module reste volontairement compatible avec les anciennes bases SQLite et
MySQL/MariaDB utilisées par Teamworks. Il ne supprime, ne renomme et ne
réinterprète aucune colonne historique.
"""

CEE_QUALIFICATION_COLUMN = "cee_qualification"
CEE_QUALIFICATION_TYPE = "VARCHAR(32)"
CONVENTION_CODE_COLUMN = "convention_code"
CONVENTION_CODE_TYPE = "VARCHAR(32)"
CCNS_GROUP_COLUMN = "ccns_group"
CCNS_GROUP_TYPE = "VARCHAR(8)"
WEEKLY_HOURS_COLUMN = "weekly_hours"
WEEKLY_HOURS_TYPE = "REAL"
GROSS_MONTHLY_SALARY_COLUMN = "gross_monthly_salary"
GROSS_MONTHLY_SALARY_TYPE = "REAL"

ADDITIVE_COLUMNS = (
    (CEE_QUALIFICATION_COLUMN, CEE_QUALIFICATION_TYPE),
    (CONVENTION_CODE_COLUMN, CONVENTION_CODE_TYPE),
    (CCNS_GROUP_COLUMN, CCNS_GROUP_TYPE),
    (WEEKLY_HOURS_COLUMN, WEEKLY_HOURS_TYPE),
    (GROSS_MONTHLY_SALARY_COLUMN, GROSS_MONTHLY_SALARY_TYPE),
)

MODEL_ADDITIVE_COLUMNS = (
    (CEE_QUALIFICATION_COLUMN, CEE_QUALIFICATION_TYPE),
    (CONVENTION_CODE_COLUMN, CONVENTION_CODE_TYPE),
    (CCNS_GROUP_COLUMN, CCNS_GROUP_TYPE),
)


def _ensure_column(DB, table_name, name, type_name):
    if DB is None:
        raise ValueError("DB est requis")
    champs = DB.GetListeChamps2(table_name)
    noms = [champ[0] for champ in champs]
    if name in noms:
        return False
    DB.AjoutChamp(nomTable=table_name, nomChamp=name, typeChamp=type_name)
    return True


def EnsureCEEQualificationColumn(DB):
    """Ajoute la qualification CEE si la base historique ne la possède pas."""
    return _ensure_column(DB, "contrats", CEE_QUALIFICATION_COLUMN, CEE_QUALIFICATION_TYPE)


def EnsureContractEngineColumns(DB):
    """Ajoute les colonnes TW-184 manquantes, sans conversion des anciennes lignes.

    La vérification préalable évite volontairement ``ADD COLUMN IF NOT EXISTS``
    afin de conserver la compatibilité avec MySQL/MariaDB 5.5.

    Renvoie le tuple des noms de colonnes effectivement créées.
    """
    created = []
    for name, type_name in ADDITIVE_COLUMNS:
        if _ensure_column(DB, "contrats", name, type_name):
            created.append(name)
    return tuple(created)


def EnsureContractModelColumns(DB):
    """Ajoute les discriminants TW-184 aux modèles de contrat.

    Les anciens modèles restent valides avec les trois colonnes à ``NULL``.
    Aucun modèle existant n'est reclassé automatiquement.
    """
    created = []
    for name, type_name in MODEL_ADDITIVE_COLUMNS:
        if _ensure_column(DB, "contrats_modeles", name, type_name):
            created.append(name)
    return tuple(created)
