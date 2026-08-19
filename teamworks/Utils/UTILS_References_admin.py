#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Références administratives RH internes de Teamworks CCNS.

Ces données sont un pense-bête administratif. Elles ne contiennent aucun secret
ni mot de passe et ne sont pas destinées à être imprimées automatiquement.
"""

from Utils import UTILS_Customize

SECTION = "references_administratives"

FIELDS = {
    "medecine_nom": "",
    "medecine_identifiant": "",
    "medecine_contact": "",
    "medecine_telephone": "",
    "medecine_email": "",
    "medecine_portail": "",
    "urssaf_organisme": "",
    "urssaf_identifiant": "",
    "mutuelle_organisme": "",
    "mutuelle_reference": "",
    "prevoyance_organisme": "",
    "prevoyance_reference": "",
    "opco_organisme": "",
    "opco_identifiant": "",
    "retraite_organisme": "",
    "retraite_identifiant": "",
    "assurance_employeur": "",
    "assurance_reference": "",
    "assurance_contact": "",
    "assurance_telephone": "",
    "assurance_email": "",
    "notes": "",
}


def GetValeur(cle, default=""):
    if cle in FIELDS:
        default = FIELDS[cle]
    value = UTILS_Customize.GetValeur(
        SECTION, cle, default, ajouter_si_manquant=False
    )
    return value or ""


def SetValeur(cle, value):
    if cle not in FIELDS:
        raise KeyError("Référence administrative inconnue : %s" % cle)
    UTILS_Customize.SetValeur(SECTION, cle, value or "")


def GetProfil():
    return {key: GetValeur(key, default) for key, default in FIELDS.items()}


def SetProfil(values):
    for key, value in values.items():
        if key in FIELDS:
            SetValeur(key, value)
