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


def PrepareDocument(document_code, IDpersonne=None, IDcontrat=None):
    """Prépare un document RH en conservant tous les mots-clés historiques.

    Les nouveaux modèles disposent en plus de STRUCTURE_*, SALARIE_* et CONTRAT_*.
    """
    document_type = get_document_type(document_code)
    legacy_values = _load_legacy_values(IDpersonne=IDpersonne, IDcontrat=IDcontrat)

    contract_values = _contract_values(legacy_values)
    if document_type.scope is DocumentScope.EMPLOYEE and IDcontrat in (None, 0, ""):
        contract_values = None

    return prepare_hr_document(
        document_type.code,
        structure=UTILS_Organisation.GetProfilPublipostage(),
        employee=_employee_values(legacy_values),
        contract=contract_values,
        extra=legacy_values,
    )


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
