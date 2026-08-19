#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Ciblage des fichiers de publipostage selon le régime du contrat.

Les anciens fichiers restent utilisables : l'absence de métadonnées signifie
"modèle historique / secours" et ne bloque jamais une migration progressive.
"""

TABLE = "contrats_documents_modeles"

CEE_LABELS = {
    "BAFA_HOLDER": u"BAFA titulaire",
    "BAFA_TRAINEE": u"BAFA stagiaire",
    "UNQUALIFIED": u"Non diplômé",
    "EQUIVALENT": u"Qualification équivalente",
    "BAFD_HOLDER": u"BAFD titulaire",
    "BAFD_TRAINEE": u"BAFD stagiaire",
}

_SCHEMA = {
    TABLE: [
        ("IDdocument_modele", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID", u"ID du modèle documentaire"),
        ("nom_fichier", "VARCHAR(255)", u"Fichier", u"Nom du fichier de publipostage"),
        ("convention_code", "VARCHAR(32)", u"Convention", u"Convention ciblée"),
        ("ccns_group", "VARCHAR(8)", u"Groupe CCNS", u"Groupe CCNS ciblé, vide = générique"),
        ("cee_qualification", "VARCHAR(32)", u"Qualification CEE", u"Qualification CEE ciblée, vide = générique"),
    ]
}


def EnsureTable(DB):
    if DB is None:
        raise ValueError("DB est requis")
    if DB.IsTableExists(TABLE):
        return False
    DB.CreationTable(TABLE, _SCHEMA)
    DB.Commit()
    return True


def _clean(value):
    if value in (None, ""):
        return None
    return str(value)


def _normalize_cee(value):
    value = _clean(value)
    if value is None:
        return None
    if value in CEE_LABELS:
        return value
    lowered = value.strip().lower()
    for code, label in CEE_LABELS.items():
        if lowered == label.lower():
            return code
    return value


def SaveMetadata(DB, nom_fichier, convention_code=None, ccns_group=None, cee_qualification=None):
    """Crée ou remplace le ciblage d'un fichier de publipostage."""
    EnsureTable(DB)
    if not nom_fichier:
        raise ValueError("nom_fichier est requis")
    convention_code = _clean(convention_code)
    ccns_group = _clean(ccns_group)
    cee_qualification = _normalize_cee(cee_qualification)
    if convention_code == "CCNS" and cee_qualification:
        raise ValueError("un modèle CCNS ne peut pas cibler une qualification CEE")
    if convention_code != "CCNS" and ccns_group:
        raise ValueError("un groupe CCNS nécessite convention_code=CCNS")
    if cee_qualification and convention_code not in (None, "CEE"):
        raise ValueError("une qualification CEE est incompatible avec cette convention")
    req = "SELECT IDdocument_modele FROM %s WHERE nom_fichier='%s';" % (TABLE, nom_fichier.replace("'", "''"))
    DB.ExecuterReq(req)
    rows = DB.ResultatReq()
    donnees = [
        ("nom_fichier", nom_fichier),
        ("convention_code", convention_code),
        ("ccns_group", ccns_group),
        ("cee_qualification", cee_qualification),
    ]
    if rows:
        DB.ReqMAJ(TABLE, donnees, "IDdocument_modele", rows[0][0])
        return rows[0][0]
    return DB.ReqInsert(TABLE, donnees)


def GetMetadata(DB, nom_fichier):
    EnsureTable(DB)
    req = (
        "SELECT convention_code, ccns_group, cee_qualification FROM %s "
        "WHERE nom_fichier='%s';" % (TABLE, nom_fichier.replace("'", "''"))
    )
    DB.ExecuterReq(req)
    rows = DB.ResultatReq()
    if not rows:
        return None
    convention_code, ccns_group, cee_qualification = rows[0]
    return {
        "convention_code": _clean(convention_code),
        "ccns_group": _clean(ccns_group),
        "cee_qualification": _normalize_cee(cee_qualification),
    }


def IsCompatible(contract_data, metadata):
    """Teste la compatibilité sans accès DB.

    ``metadata is None`` correspond à un fichier historique : il reste visible
    comme solution de secours pour garantir la rétrocompatibilité.
    """
    if metadata is None:
        return True
    contract_data = contract_data or {}
    c_convention = _clean(contract_data.get("CONVENTION_CODE") or contract_data.get("CONVENTION"))
    c_group = _clean(contract_data.get("GROUPECCNS"))
    c_cee = _normalize_cee(contract_data.get("QUALIFICATIONCEE_CODE") or contract_data.get("QUALIFICATIONCEE"))
    m_convention = _clean(metadata.get("convention_code"))
    m_group = _clean(metadata.get("ccns_group"))
    m_cee = _normalize_cee(metadata.get("cee_qualification"))

    if m_convention == "CCNS":
        return c_convention == "CCNS" and (m_group is None or m_group == c_group)
    if m_convention == "CEE" or m_cee:
        return (c_convention == "CEE" or c_cee is not None) and (m_cee is None or m_cee == c_cee)
    return m_convention is None and m_group is None and m_cee is None


def FilterFilenames(DB, filenames, contract_data):
    """Retourne les fichiers compatibles, sans masquer les legacy non étiquetés."""
    EnsureTable(DB)
    result = []
    for filename in filenames:
        if IsCompatible(contract_data, GetMetadata(DB, filename)):
            result.append(filename)
    return result
