#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Profil extensible de la structure utilisatrice, sans migration de base."""

from Utils import UTILS_Customize

SECTION = "organisation"

FIELDS = {
    "nom_officiel": "",
    "nom_usage": "",
    "adresse": "",
    "code_postal": "",
    "ville": "",
    "telephone": "",
    "email": "",
    "site_web": "",
    "rna": "",
    "siren": "",
    "siret": "",
    "ape_naf": "",
    "agrement_js": "",
    "agrement_js_date": "",
    "assureur": "",
    "police_assurance": "",
    "assurance_echeance": "",
    "representant_legal": "",
    "representant_fonction": "",
    "declaration_prefecture": "",
    "reference_joafe": "",
}

DOCUMENT_FLAGS = {
    "afficher_logo": True,
    "afficher_coordonnees": True,
    "afficher_rna": False,
    "afficher_siret": False,
    "afficher_agrement": False,
    "afficher_assurance": False,
}


def _to_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "oui", "on"}


def GetValeur(cle, default=""):
    if cle in FIELDS:
        default = FIELDS[cle]
    elif cle in DOCUMENT_FLAGS:
        default = DOCUMENT_FLAGS[cle]
    value = UTILS_Customize.GetValeur(SECTION, cle, default, ajouter_si_manquant=False)
    if cle in DOCUMENT_FLAGS:
        return _to_bool(value, default)
    return value or ""


def SetValeur(cle, value):
    if cle not in FIELDS and cle not in DOCUMENT_FLAGS:
        raise KeyError("Champ organisation inconnu : %s" % cle)
    if cle in DOCUMENT_FLAGS:
        value = "1" if bool(value) else "0"
    UTILS_Customize.SetValeur(SECTION, cle, value)


def GetProfil():
    profile = {key: GetValeur(key, default) for key, default in FIELDS.items()}
    profile.update({key: GetValeur(key, default) for key, default in DOCUMENT_FLAGS.items()})
    return profile


def SetProfil(values):
    for key, value in values.items():
        if key in FIELDS or key in DOCUMENT_FLAGS:
            SetValeur(key, value)


def BuildLignesEnteteDocument(profile):
    """Construit les mentions d'en-tête à partir d'un profil déjà chargé."""
    p = dict(FIELDS)
    p.update(DOCUMENT_FLAGS)
    p.update(profile or {})
    lines = []

    name = p["nom_usage"] or p["nom_officiel"]
    if name:
        lines.append(name)

    if _to_bool(p["afficher_coordonnees"], True):
        address = " ".join(x for x in [p["adresse"], p["code_postal"], p["ville"]] if x)
        if address:
            lines.append(address)
        contacts = " · ".join(x for x in [p["telephone"], p["email"], p["site_web"]] if x)
        if contacts:
            lines.append(contacts)

    legal = []
    if _to_bool(p["afficher_rna"]) and p["rna"]:
        legal.append("RNA %s" % p["rna"])
    if _to_bool(p["afficher_siret"]) and p["siret"]:
        legal.append("SIRET %s" % p["siret"])
    if _to_bool(p["afficher_agrement"]) and p["agrement_js"]:
        legal.append("Agrément %s" % p["agrement_js"])
    if _to_bool(p["afficher_assurance"]) and p["police_assurance"]:
        assurance = "Assurance %s" % p["police_assurance"]
        if p["assureur"]:
            assurance += " (%s)" % p["assureur"]
        legal.append(assurance)
    if legal:
        lines.append(" · ".join(legal))

    return lines


def GetLignesEnteteDocument():
    """Retourne les mentions optionnelles prêtes à afficher dans un en-tête."""
    return BuildLignesEnteteDocument(GetProfil())
