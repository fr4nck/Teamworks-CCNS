#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Évolutions additives du schéma historique des contrats.

Ce module reste volontairement compatible avec les anciennes bases SQLite et
MySQL/MariaDB utilisées par Teamworks. Il ne supprime, ne renomme et ne
réinterprète aucune colonne historique.
"""

CEE_QUALIFICATION_COLUMN = "cee_qualification"
CEE_QUALIFICATION_TYPE = "VARCHAR(32)"


def EnsureCEEQualificationColumn(DB):
    """Ajoute la qualification CEE si la base historique ne la possède pas.

    ``DB`` est une instance compatible avec ``GestionDB.DB``. La vérification
    préalable évite volontairement ``ADD COLUMN IF NOT EXISTS``, non retenu
    pour garantir la compatibilité avec MySQL/MariaDB 5.5.

    Renvoie True si la colonne a été créée, False si elle existait déjà.
    """
    if DB is None:
        raise ValueError("DB est requis")

    champs = DB.GetListeChamps2("contrats")
    noms = [champ[0] for champ in champs]
    if CEE_QUALIFICATION_COLUMN in noms:
        return False

    DB.AjoutChamp(
        nomTable="contrats",
        nomChamp=CEE_QUALIFICATION_COLUMN,
        typeChamp=CEE_QUALIFICATION_TYPE,
    )
    return True
