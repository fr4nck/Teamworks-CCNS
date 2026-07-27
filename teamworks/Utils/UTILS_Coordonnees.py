#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Normalisation des coordonnées saisies par les utilisateurs.

Les fonctions de ce module sont indépendantes de wxPython afin d'être
réutilisables dans les formulaires, les imports et les tests.
"""

from __future__ import annotations

import re
import unicodedata


_SEPARATEURS_TELEPHONE = re.compile(r"[\s.()\-\u00a0\u202f]+")


def normaliser_texte(valeur):
    """Retourne une chaîne Unicode NFC sans espaces périphériques."""
    if valeur is None:
        return ""
    texte = str(valeur).strip()
    return unicodedata.normalize("NFC", texte)


def normaliser_email(valeur):
    """Normalise une adresse électronique sans altérer sa partie locale."""
    texte = normaliser_texte(valeur)
    if not texte:
        return ""
    if "@" not in texte:
        raise ValueError("Adresse électronique invalide")
    local, domaine = texte.rsplit("@", 1)
    if not local or not domaine or "." not in domaine:
        raise ValueError("Adresse électronique invalide")
    return "%s@%s" % (local, domaine.lower())


def normaliser_telephone(valeur):
    """Normalise un numéro français ou international.

    Les espaces, points, parenthèses, tirets et espaces insécables sont
    acceptés. Les numéros français en +33 sont convertis au format national
    afin de conserver la présentation historique de Teamworks.
    """
    texte = normaliser_texte(valeur)
    if not texte:
        return ""

    compact = _SEPARATEURS_TELEPHONE.sub("", texte)
    if compact.startswith("00"):
        compact = "+" + compact[2:]

    if compact.startswith("+33"):
        compact = "0" + compact[3:]

    if compact.startswith("+"):
        chiffres = compact[1:]
        if not chiffres.isdigit() or not 8 <= len(chiffres) <= 15:
            raise ValueError("Numéro de téléphone invalide")
        return "+" + chiffres

    if not compact.isdigit():
        raise ValueError("Numéro de téléphone invalide")

    if len(compact) == 10 and compact.startswith("0"):
        return ".".join(compact[index:index + 2] for index in range(0, 10, 2))

    if not 8 <= len(compact) <= 15:
        raise ValueError("Numéro de téléphone invalide")

    return compact
