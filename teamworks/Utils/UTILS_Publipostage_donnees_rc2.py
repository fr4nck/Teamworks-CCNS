# -*- coding: utf-8 -*-
"""Compléments RC2 du mapping des mots-clés de publipostage contrat."""

from __future__ import annotations

import datetime


def _as_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def normalize_public_document(keywords, data):
    """Garantit une valeur texte pour chaque balise annoncée au modèle."""
    result = dict(data or {})
    ordered = []
    seen = set()
    for keyword in keywords or ():
        if not isinstance(keyword, str) or keyword.startswith("_"):
            continue
        if keyword not in seen:
            ordered.append(keyword)
            seen.add(keyword)
        result[keyword] = _as_text(result.get(keyword, ""))
    for keyword, value in list(result.items()):
        if isinstance(keyword, str) and not keyword.startswith("_"):
            result[keyword] = _as_text(value)
    return ordered, result


def _parse_french_date(value):
    text = _as_text(value).strip()
    if not text:
        return None
    try:
        return datetime.datetime.strptime(text, "%d/%m/%Y").date()
    except (TypeError, ValueError):
        return None


def _ccns_group_label(group_code, date_debut):
    """Retourne le libellé métier du groupe sans inventer de valeur source."""
    code = _as_text(group_code).strip().upper()
    if not code:
        return ""
    reference_date = _parse_french_date(date_debut)
    if reference_date is None:
        return code
    try:
        from application.control.ccns_contract_compliance import CCNSContractCompliancePresenter

        choice = next(
            (
                item
                for item in CCNSContractCompliancePresenter().group_choices(reference_date)
                if item.code == code
            ),
            None,
        )
    except Exception:
        choice = None
    # Si la grille ne sait pas résoudre le libellé, conserver le code réellement
    # stocké dans le contrat est plus sûr que fabriquer une classification.
    return _as_text(choice.label if choice is not None else code)


def classification_for_contract(data, has_legacy_classification=False):
    """Résout la balise historique depuis les données réellement sélectionnées.

    Une classification historique enregistrée reste prioritaire. Pour un contrat
    CCNS moderne sans ``IDclassification``, la source métier est ``ccns_group``.
    La qualification CEE reste distincte et n'est jamais transformée en
    classification.
    """
    data = data or {}
    current = _as_text(data.get("CLASSIFICATION", ""))
    if has_legacy_classification:
        return current
    convention = _as_text(data.get("CONVENTION", "")).strip().upper()
    group = _as_text(data.get("GROUPECCNS", "")).strip().upper()
    if convention == "CCNS" and group:
        return _ccns_group_label(group, data.get("DATEDEBUT"))
    return ""


def _has_legacy_classification(module, contract_id):
    if contract_id in (None, ""):
        return False
    DB = module.GestionDB.DB()
    try:
        DB.ExecuterReq(
            "SELECT IDclassification FROM contrats WHERE IDcontrat=%d;" % int(contract_id)
        )
        rows = DB.ResultatReq()
    finally:
        DB.Close()
    return bool(rows and rows[0][0] not in (None, ""))


def install(module):
    """Installe le mapping RC2 sans modifier le contrat public du module."""
    if getattr(module, "_RC2_PUBLIPOSTAGE_MAPPING", False):
        return module
    module._RC2_PUBLIPOSTAGE_MAPPING = True

    original_import_contract = module.Importation_contrat
    original_get_document = module.GetDonneesDocument

    def import_contract(IDcontrat=None):
        keywords, data = original_import_contract(IDcontrat=IDcontrat)
        if not data:
            return keywords, data
        data["CLASSIFICATION"] = classification_for_contract(
            data,
            has_legacy_classification=_has_legacy_classification(module, IDcontrat),
        )
        return keywords, data

    module.Importation_contrat = import_contract

    def get_document(categorie=None, ID=None):
        keywords, data = original_get_document(categorie=categorie, ID=ID)
        if not data:
            return keywords, data
        public_keywords, normalized = normalize_public_document(keywords, data)
        return public_keywords, normalized

    module.GetDonneesDocument = get_document
    return module
