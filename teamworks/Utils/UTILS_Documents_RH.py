#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Passerelle entre le catalogue documentaire RH et le publiposteur historique."""

from application.services.hr_documents import prepare_hr_document
from domain.documents import DocumentScope, get_document_type
from Utils import UTILS_Organisation
from Utils import UTILS_Publipostage_donnees


def _load_legacy_values(IDpersonne=None, IDcontrat=None):
    if IDcontrat not in (None, 0, ""):
        _keywords, values = UTILS_Publipostage_donnees.GetDonneesDocument(
            categorie="contrat",
            ID=IDcontrat,
        )
        return dict(values or {})
    if IDpersonne not in (None, 0, ""):
        _keywords, values = UTILS_Publipostage_donnees.GetDonneesDocument(
            categorie="personne",
            ID=IDpersonne,
        )
        return dict(values or {})
    return {}


def _employee_values(legacy_values):
    return {
        "nom": legacy_values.get("NOM", ""),
        "prenom": legacy_values.get("PRENOM", ""),
        "civilite": legacy_values.get("CIVILITE", ""),
        "date_naissance": legacy_values.get("DATENAISS", ""),
        "adresse": legacy_values.get("ADRESSERESID", ""),
        "code_postal": legacy_values.get("CPRESID", ""),
        "ville": legacy_values.get("VILLERESID", ""),
        "telephones": legacy_values.get("TELEPHONES", ""),
        "emails": legacy_values.get("EMAILS", ""),
    }


def _contract_values(legacy_values):
    return {
        "date_debut": legacy_values.get("DATEDEBUT", ""),
        "date_fin": legacy_values.get("DATEFIN", ""),
        "type": legacy_values.get("TYPECONTRAT", ""),
        "classification": legacy_values.get("CLASSIFICATION", ""),
        "convention": legacy_values.get("CONVENTION", ""),
        "groupe_ccns": legacy_values.get("GROUPECCNS", ""),
        "duree_hebdo": legacy_values.get("DUREEHEBDO", ""),
        "salaire_brut_mensuel": legacy_values.get("SALAIREBRUTMENSUEL", ""),
    }


def _prepare_from_values(document_code, legacy_values):
    document_type = get_document_type(document_code)
    contract_values = _contract_values(legacy_values)
    if document_type.scope is DocumentScope.EMPLOYEE and not contract_values["date_debut"]:
        contract_values = None
    return prepare_hr_document(
        document_type.code,
        structure=UTILS_Organisation.GetProfilPublipostage(),
        employee=_employee_values(legacy_values),
        contract=contract_values,
        extra=legacy_values,
    )


def PrepareDocument(document_code, IDpersonne=None, IDcontrat=None):
    """Prépare un document RH en conservant tous les mots-clés historiques."""
    document_type = get_document_type(document_code)
    if document_type.scope is DocumentScope.CONTRACT and IDcontrat in (None, 0, ""):
        raise ValueError("Un contrat est requis pour ce type de document RH.")
    if document_type.scope is DocumentScope.EMPLOYEE and IDpersonne in (None, 0, ""):
        raise ValueError("Un salarié est requis pour ce type de document RH.")
    legacy_values = _load_legacy_values(IDpersonne=IDpersonne, IDcontrat=IDcontrat)
    return _prepare_from_values(document_code, legacy_values)


def GetDonneesPublipostage(document_code, IDpersonne=None, IDcontrat=None):
    """Retourne les mots-clés prêts pour un modèle et l'état de préparation."""
    prepared = PrepareDocument(
        document_code,
        IDpersonne=IDpersonne,
        IDcontrat=IDcontrat,
    )
    values = prepared.merge_context.as_dict()
    keywords = tuple(sorted(values))
    return keywords, values, prepared


def _enrich_dict_donnees(dict_donnees, document_code, expected_category):
    if not dict_donnees or dict_donnees.get("CATEGORIE") != expected_category:
        return dict_donnees

    document_type = get_document_type(document_code)
    expected_scope = (
        DocumentScope.CONTRACT if expected_category == "contrat" else DocumentScope.EMPLOYEE
    )
    if document_type.scope is not expected_scope:
        raise ValueError(
            "Le document %s n'est pas compatible avec le contexte %s."
            % (document_type.code, expected_category)
        )

    motcles = list(dict_donnees.get("MOTSCLES", []))
    connus = {motcle for motcle, _type in motcles}
    nombre = int(dict_donnees.get("NBREDOCUMENTS", 0) or 0)

    for index in range(1, nombre + 1):
        legacy_values = dict(dict_donnees.get(index, {}) or {})
        prepared = _prepare_from_values(document_type.code, legacy_values)
        values = prepared.merge_context.as_dict()
        dict_donnees[index] = values
        for motcle in values:
            if motcle not in connus:
                motcles.append((motcle, "base"))
                connus.add(motcle)

    dict_donnees["MOTSCLES"] = motcles
    dict_donnees["DOCUMENT_KIND"] = document_type.code
    return dict_donnees


def EnrichirDictDonneesContrat(dict_donnees, document_code="contract"):
    """Ajoute les mots-clés RH à un dictionnaire vanilla de contrat."""
    return _enrich_dict_donnees(
        dict_donnees,
        document_code=document_code,
        expected_category="contrat",
    )


def EnrichirDictDonneesPersonne(dict_donnees, document_code):
    """Ajoute les mots-clés RH à un dictionnaire vanilla de salarié."""
    return _enrich_dict_donnees(
        dict_donnees,
        document_code=document_code,
        expected_category="personne",
    )


def GetDictDonneesDocument(document_code, IDpersonne=None, IDcontrat=None):
    """Construit le dictionnaire complet attendu par le publiposteur historique."""
    document_type = get_document_type(document_code)
    if document_type.scope is DocumentScope.CONTRACT:
        if IDcontrat in (None, 0, ""):
            raise ValueError("Un contrat est requis pour ce type de document RH.")
        dict_donnees = UTILS_Publipostage_donnees.GetDictDonnees(
            categorie="contrat",
            listeID=[IDcontrat],
        )
        return EnrichirDictDonneesContrat(
            dict_donnees,
            document_code=document_type.code,
        )

    if IDpersonne in (None, 0, ""):
        raise ValueError("Un salarié est requis pour ce type de document RH.")
    dict_donnees = UTILS_Publipostage_donnees.GetDictDonnees(
        categorie="personne",
        listeID=[IDpersonne],
    )
    return EnrichirDictDonneesPersonne(
        dict_donnees,
        document_code=document_type.code,
    )
