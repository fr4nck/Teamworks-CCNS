#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Adaptateur du publiposteur pour les contrats TW-184.

Le publiposteur vanilla reste inchangé pour toutes les autres catégories.
Seule la liste des fichiers de modèles est filtrée selon le régime du contrat.
Les fichiers sans métadonnées restent visibles comme modèles historiques.
"""

import GestionDB
from Dlg import DLG_Publiposteur as _base
from Utils import UTILS_Contrats_modeles_documents


class ListCtrl_fichiers(_base.ListCtrl_fichiers):
    def GetListeDocuments(self):
        fichiers = super(ListCtrl_fichiers, self).GetListeDocuments()
        if _base.DICT_DONNEES.get("CATEGORIE") != "contrat":
            return fichiers
        contrat = _base.DICT_DONNEES.get(1, {})
        noms = [valeurs[0] for _, valeurs in sorted(fichiers.items())]
        DB = GestionDB.DB()
        try:
            compatibles = set(
                UTILS_Contrats_modeles_documents.FilterFilenames(DB, noms, contrat)
            )
        finally:
            DB.Close()
        resultat = {}
        index = 1
        for _, valeurs in sorted(fichiers.items()):
            if valeurs[0] in compatibles:
                resultat[index] = valeurs
                index += 1
        return resultat


class Dialog(_base.Dialog):
    """Publiposteur standard avec liste de modèles filtrée pour un contrat."""

    def __init__(self, *args, **kwargs):
        original = _base.ListCtrl_fichiers
        _base.ListCtrl_fichiers = ListCtrl_fichiers
        try:
            _base.Dialog.__init__(self, *args, **kwargs)
        finally:
            # Les autres usages du publiposteur restent strictement vanilla.
            _base.ListCtrl_fichiers = original
