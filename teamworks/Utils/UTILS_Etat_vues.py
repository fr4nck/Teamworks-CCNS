#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Persistance locale et versionnée de l'état visuel des vues métier.

Le stockage reste strictement utilisateur (Customize.ini) et ne touche jamais
aux bases métier. Les fonctions de normalisation sont indépendantes de wx afin
de rester testables sur la CI Linux.
"""

import json


SECTION = "ui_views"
VERSION_ETAT = 1
LARGEUR_MIN = 24
LARGEUR_MAX = 2400


def _uniques(valeurs):
    resultat = []
    vus = set()
    for valeur in valeurs or []:
        if not isinstance(valeur, str) or not valeur or valeur in vus:
            continue
        resultat.append(valeur)
        vus.add(valeur)
    return resultat


def fusionner_ordre_visible(ordre_existant, ordre_visible):
    """Remplace l'ordre des colonnes visibles sans perdre les colonnes masquées."""
    ordre_existant = _uniques(ordre_existant)
    ordre_visible = _uniques(ordre_visible)
    visibles = set(ordre_visible)
    iterateur = iter(ordre_visible)
    resultat = []

    for code in ordre_existant:
        if code in visibles:
            try:
                resultat.append(next(iterateur))
            except StopIteration:
                continue
        else:
            resultat.append(code)

    for code in iterateur:
        if code not in resultat:
            resultat.append(code)
    for code in ordre_visible:
        if code not in resultat:
            resultat.append(code)
    return resultat


def normaliser_etat_colonnes(
    etat,
    colonnes_disponibles,
    ordre_defaut=None,
    visibilite_defaut=None,
):
    """Filtre un état persisté et complète proprement les colonnes nouvelles."""
    disponibles = _uniques(colonnes_disponibles)
    disponibles_set = set(disponibles)

    ordre_base = [
        code for code in _uniques(ordre_defaut or disponibles)
        if code in disponibles_set
    ]
    for code in disponibles:
        if code not in ordre_base:
            ordre_base.append(code)

    visibilite = {
        code: bool((visibilite_defaut or {}).get(code, True))
        for code in disponibles
    }

    def defaut():
        return {
            "version": VERSION_ETAT,
            "order": list(ordre_base),
            "widths": {},
            "visible": dict(visibilite),
            "scale": 1.0,
        }

    if not isinstance(etat, dict):
        return defaut()
    version = etat.get("version", VERSION_ETAT)
    if version != VERSION_ETAT:
        return defaut()

    ordre = [
        code for code in _uniques(etat.get("order", []))
        if code in disponibles_set
    ]
    for code in ordre_base:
        if code not in ordre:
            ordre.append(code)

    visible_brut = etat.get("visible", {})
    if isinstance(visible_brut, dict):
        for code, valeur in visible_brut.items():
            if code in disponibles_set and isinstance(valeur, bool):
                visibilite[code] = valeur

    largeurs = {}
    largeurs_brutes = etat.get("widths", {})
    if isinstance(largeurs_brutes, dict):
        for code, valeur in largeurs_brutes.items():
            if code not in disponibles_set:
                continue
            try:
                largeur = int(valeur)
            except (TypeError, ValueError):
                continue
            if largeur == 0:
                largeurs[code] = 0
            elif largeur > 0:
                largeurs[code] = max(LARGEUR_MIN, min(LARGEUR_MAX, largeur))

    try:
        echelle = float(etat.get("scale", 1.0))
    except (TypeError, ValueError):
        echelle = 1.0
    if not 0.5 <= echelle <= 4.0:
        echelle = 1.0

    return {
        "version": VERSION_ETAT,
        "order": ordre,
        "widths": largeurs,
        "visible": visibilite,
        "scale": echelle,
    }


def adapter_largeur(largeur, echelle_source=1.0, echelle_cible=1.0):
    """Adapte une largeur persistée à un autre facteur DPI, avec bornes sûres."""
    try:
        largeur = int(largeur)
    except (TypeError, ValueError):
        return None
    if largeur == 0:
        return 0
    if largeur < 0:
        return None

    try:
        source = float(echelle_source)
        cible = float(echelle_cible)
    except (TypeError, ValueError):
        source, cible = 1.0, 1.0
    if not 0.5 <= source <= 4.0:
        source = 1.0
    if not 0.5 <= cible <= 4.0:
        cible = 1.0

    largeur = int(round(largeur * cible / source))
    return max(LARGEUR_MIN, min(LARGEUR_MAX, largeur))


def charger_etat_vue(identifiant):
    if not identifiant:
        return {}
    try:
        from Utils import UTILS_Customize
        brut = UTILS_Customize.GetValeur(
            SECTION,
            identifiant,
            "",
            ajouter_si_manquant=False,
        )
        if not brut:
            return {}
        etat = json.loads(brut)
        return etat if isinstance(etat, dict) else {}
    except Exception:
        return {}


def sauver_etat_vue(identifiant, etat):
    if not identifiant or not isinstance(etat, dict):
        return False
    try:
        from Utils import UTILS_Customize
        UTILS_Customize.SetValeur(
            SECTION,
            identifiant,
            json.dumps(etat, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )
        return True
    except Exception:
        return False
