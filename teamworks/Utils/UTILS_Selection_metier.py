#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Contrats purs pour transporter des identifiants métier dans une liste UI."""


def associer_identifiants(liste_valeurs, liste_ids=None):
    """Retourne ``[(id_metier, valeurs_visuelles), ...]``.

    ``liste_ids`` est le contrat recommandé : l'identifiant ne dépend alors ni
    de l'ordre, ni de la visibilité, ni du contenu des colonnes. Le fallback
    historique sur la première valeur est conservé uniquement pour les anciens
    appelants génériques de ``DLG_Selection_liste`` qui ne fournissent pas encore
    d'identifiants explicites.
    """
    valeurs = list(liste_valeurs or [])
    if liste_ids is not None:
        ids = list(liste_ids)
        if len(ids) != len(valeurs):
            raise ValueError(
                "Le nombre d'identifiants métier ne correspond pas au nombre de lignes"
            )
        return [(int(ids[index]), ligne) for index, ligne in enumerate(valeurs)]

    resultat = []
    for ligne in valeurs:
        if not ligne:
            raise ValueError("Une ligne sans identifiant historique a été fournie")
        resultat.append((int(ligne[0]), ligne))
    return resultat
