#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Utilitaires partagés pour les présences et activités."""


def normaliser_intitule_presence(valeur):
    """Retourne une légende de présence propre."""
    if valeur is None:
        return ""

    texte = str(valeur).strip()
    if texte in ("", "()", "( )"):
        return ""

    return texte


def formater_libelle_activite(nom_categorie, intitule=None):
    """Formate une activité avec sa légende optionnelle."""
    categorie = "" if nom_categorie is None else str(nom_categorie).strip()
    legende = normaliser_intitule_presence(intitule)

    if legende:
        return "%s (%s)" % (categorie, legende)

    return categorie
