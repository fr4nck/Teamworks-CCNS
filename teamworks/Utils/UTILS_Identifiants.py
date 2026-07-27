#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Normalisation prudente des champs d'état civil et administratifs."""

from __future__ import annotations

import re
import unicodedata


_ESPACES = re.compile(r"[\s\u00a0\u202f]+")
_BIC = re.compile(r"^[A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?$")


def normaliser_texte_identite(valeur):
    """Normalise en NFC sans modifier la casse ni les caractères légitimes."""
    if valeur is None:
        return ""
    return unicodedata.normalize("NFC", str(valeur).strip())


def normaliser_adresse(valeur):
    """Normalise Unicode et espaces périphériques d'une adresse."""
    return normaliser_texte_identite(valeur)


def normaliser_pays(valeur):
    """Normalise un libellé de pays sans imposer de référentiel ni de casse."""
    return normaliser_texte_identite(valeur)


def normaliser_nir(valeur, verifier_cle=True):
    """Retourne un NIR compact de 15 caractères et vérifie sa clé.

    Les espaces sont tolérés. Les départements corses ``2A`` et ``2B`` sont
    conservés dans la valeur retournée et convertis en 19/18 uniquement pour
    le calcul réglementaire de la clé.
    """
    texte = normaliser_texte_identite(valeur).upper()
    compact = _ESPACES.sub("", texte).replace("-", "")
    if not compact:
        return ""
    if len(compact) != 15:
        raise ValueError("NIR invalide : 15 caractères attendus")

    corps, cle = compact[:13], compact[13:]
    if not cle.isdigit():
        raise ValueError("Clé NIR invalide")

    corps_calcul = corps
    if corps[5:7] == "2A":
        corps_calcul = corps[:5] + "19" + corps[7:]
    elif corps[5:7] == "2B":
        corps_calcul = corps[:5] + "18" + corps[7:]

    if not corps_calcul.isdigit():
        raise ValueError("Corps NIR invalide")

    if verifier_cle:
        cle_attendue = 97 - (int(corps_calcul) % 97)
        if int(cle) != cle_attendue:
            raise ValueError("Clé NIR incohérente")
    return compact


def normaliser_iban(valeur, verifier_cle=True):
    """Normalise un IBAN en majuscules et vérifie le contrôle modulo 97."""
    compact = _ESPACES.sub("", normaliser_texte_identite(valeur)).upper()
    if not compact:
        return ""
    if not (15 <= len(compact) <= 34) or not compact.isalnum():
        raise ValueError("IBAN invalide")
    if verifier_cle:
        rearrange = compact[4:] + compact[:4]
        numerique = "".join(str(ord(c) - 55) if c.isalpha() else c for c in rearrange)
        if int(numerique) % 97 != 1:
            raise ValueError("Clé IBAN incohérente")
    return compact


def normaliser_bic(valeur):
    """Normalise et valide sommairement un code BIC/SWIFT."""
    compact = _ESPACES.sub("", normaliser_texte_identite(valeur)).upper()
    if not compact:
        return ""
    if not _BIC.fullmatch(compact):
        raise ValueError("BIC invalide")
    return compact


def normaliser_identifiant_libre(valeur):
    """Normalise un identifiant administratif sans le convertir en entier."""
    return normaliser_texte_identite(valeur)
