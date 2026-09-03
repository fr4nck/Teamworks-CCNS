#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Règles pures pour les champs internationaux de la fiche Généralités.

Ce module ne dépend pas de wx : il centralise les décisions France/étranger
pour éviter que la base locale des communes françaises devienne bloquante.
"""

from __future__ import annotations


def est_france(nom_pays):
    return (nom_pays or "").strip().casefold() == "france"


def normalise_code_postal(valeur, pays="France"):
    """Conserve les CP étrangers tels quels et normalise uniquement la France."""
    texte = "" if valeur is None else str(valeur).strip()
    if not texte:
        return ""
    if not est_france(pays):
        return texte
    chiffres = "".join(car for car in texte if car.isdigit())
    if len(chiffres) <= 5:
        return chiffres.zfill(5)
    return texte


def ville_locale_obligatoire(pays="France"):
    """La base Villes.db3 n'est une référence de saisie que pour la France."""
    return est_france(pays)


def departement_nir_attendu(pays_naissance="France", code_postal=""):
    """Retourne le code département NIR attendu, ou None s'il est indéterminable."""
    if not est_france(pays_naissance):
        return "99"
    cp = "" if code_postal is None else str(code_postal).strip()
    if len(cp) < 2:
        return None
    return cp[:2]


def nir_lieu_compatible(code_nir, pays_naissance="France", code_postal=""):
    attendu = departement_nir_attendu(pays_naissance, code_postal)
    if attendu is None:
        return True
    return str(code_nir) == attendu
