from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path
import os
import sys

import appdirs


_FIELDS = {
    "nom_officiel": "",
    "nom_usage": "",
    "adresse": "",
    "code_postal": "",
    "ville": "",
    "telephone": "",
    "email": "",
    "email_rh": "",
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


def _runtime_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2] / "teamworks"


def _user_config_directory() -> Path:
    portable = _runtime_directory() / "Portable"
    if portable.is_dir():
        return portable
    return (
        Path(appdirs.user_config_dir(appname=None, appauthor=False, roaming=True))
        / "teamworks"
    )


def _read_organization_profile() -> dict[str, str]:
    values = dict(_FIELDS)
    path = _user_config_directory() / "Customize.ini"
    if not path.is_file():
        return values

    parser = ConfigParser()
    try:
        parser.read(path, encoding="utf-8")
    except (OSError, UnicodeError):
        return values

    if not parser.has_section("organisation"):
        return values

    for key in values:
        if parser.has_option("organisation", key):
            values[key] = parser.get("organisation", key) or ""
    return values


def _association_logo_path() -> str:
    path = _user_config_directory() / "Customize.ini"
    parser = ConfigParser()
    try:
        parser.read(path, encoding="utf-8")
    except (OSError, UnicodeError):
        return ""
    if not parser.has_option("branding", "logo_association"):
        return ""

    raw = parser.get("branding", "logo_association") or ""
    if not raw:
        return ""
    logo = Path(raw)
    if not logo.is_absolute():
        logo = _user_config_directory() / "Branding" / logo
    if not logo.is_file() or logo.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
        return ""
    return str(logo)


def load_organization_mail_merge_profile() -> dict[str, str]:
    """Lit le même profil Structure que wx sans importer wxPython."""

    p = _read_organization_profile()
    return {
        "raison_sociale": p["nom_officiel"] or p["nom_usage"],
        "nom_usage": p["nom_usage"],
        "adresse": p["adresse"],
        "code_postal": p["code_postal"],
        "ville": p["ville"],
        "telephone": p["telephone"],
        "email": p["email"],
        "email_rh": p["email_rh"] or p["email"],
        "site_web": p["site_web"],
        "rna": p["rna"],
        "siren": p["siren"],
        "siret": p["siret"],
        "ape_naf": p["ape_naf"],
        "agrement_js": p["agrement_js"],
        "agrement_js_date": p["agrement_js_date"],
        "assureur": p["assureur"],
        "police_assurance": p["police_assurance"],
        "assurance_echeance": p["assurance_echeance"],
        "representant_legal": p["representant_legal"],
        "representant_fonction": p["representant_fonction"],
        "declaration_prefecture": p["declaration_prefecture"],
        "reference_joafe": p["reference_joafe"],
        "logo": _association_logo_path(),
    }
