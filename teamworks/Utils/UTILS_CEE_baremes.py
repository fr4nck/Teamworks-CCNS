#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Stockage des barèmes employeur CEE par qualification et date d'effet."""

import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext


TABLE = "contrats_cee_baremes"
_CENT = Decimal("0.01")
QUALIFICATIONS = (
    "BAFA_HOLDER",
    "BAFA_TRAINEE",
    "UNQUALIFIED",
    "EQUIVALENT",
    "BAFD_HOLDER",
    "BAFD_TRAINEE",
)

_SCHEMA = {
    TABLE: [
        ("IDbareme", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID", u"ID du barème"),
        ("qualification", "VARCHAR(32)", u"Qualification", u"Qualification/statut CEE"),
        ("montant_journalier", "REAL", u"Montant journalier", u"Barème brut journalier employeur"),
        ("date_debut", "DATE", u"Début validité", u"Date de début d'application du barème"),
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


def _qualification(value):
    if value not in QUALIFICATIONS:
        raise ValueError("qualification CEE inconnue")
    return value


def _date_iso(value):
    if type(value) is datetime.date:
        return value.isoformat()
    if isinstance(value, str):
        datetime.datetime.strptime(value, "%Y-%m-%d")
        return value
    raise TypeError("date_debut doit être une date ou une chaîne ISO")


def _amount(value):
    try:
        montant = value if type(value) is Decimal else Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("montant_journalier invalide")
    if montant <= Decimal("0"):
        raise ValueError("montant_journalier doit être strictement positif")
    with localcontext() as context:
        context.prec = max(28, len(montant.as_tuple().digits) + 4)
        return montant.quantize(_CENT, rounding=ROUND_HALF_UP)


def SaveRate(DB, qualification, montant_journalier, date_debut):
    """Crée ou remplace le barème d'une qualification à une date d'effet."""
    EnsureTable(DB)
    qualification = _qualification(qualification)
    montant = _amount(montant_journalier)
    date_iso = _date_iso(date_debut)

    req = (
        "SELECT IDbareme FROM %s WHERE qualification='%s' AND date_debut='%s';"
        % (TABLE, qualification, date_iso)
    )
    DB.ExecuterReq(req)
    rows = DB.ResultatReq()
    donnees = [
        ("qualification", qualification),
        ("montant_journalier", float(montant)),
        ("date_debut", date_iso),
    ]
    if rows:
        DB.ReqMAJ(TABLE, donnees, "IDbareme", rows[0][0])
        return rows[0][0]
    return DB.ReqInsert(TABLE, donnees)


def GetApplicableRate(DB, qualification, reference_date):
    """Retourne le dernier barème applicable, ou None si aucun n'est défini."""
    EnsureTable(DB)
    qualification = _qualification(qualification)
    date_iso = _date_iso(reference_date)
    req = (
        "SELECT IDbareme, montant_journalier, date_debut FROM %s "
        "WHERE qualification='%s' AND date_debut<='%s' "
        "ORDER BY date_debut DESC, IDbareme DESC;"
        % (TABLE, qualification, date_iso)
    )
    DB.ExecuterReq(req)
    rows = DB.ResultatReq()
    if not rows:
        return None
    IDbareme, montant, date_debut = rows[0]
    return {
        "IDbareme": IDbareme,
        "qualification": qualification,
        "montant_journalier": _amount(montant),
        "date_debut": date_debut,
    }


def ListRates(DB, qualification=None):
    EnsureTable(DB)
    if qualification is None:
        req = "SELECT IDbareme, qualification, montant_journalier, date_debut FROM %s ORDER BY qualification, date_debut;" % TABLE
    else:
        qualification = _qualification(qualification)
        req = (
            "SELECT IDbareme, qualification, montant_journalier, date_debut FROM %s "
            "WHERE qualification='%s' ORDER BY date_debut;" % (TABLE, qualification)
        )
    DB.ExecuterReq(req)
    return DB.ResultatReq()
