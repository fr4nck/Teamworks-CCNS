#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Prépare les valeurs DPAE/DUE à partir d'un contrat historique ou moderne."""

from __future__ import annotations

import datetime

import GestionDB
from Utils.UTILS_Traduction import _


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def _postal_code(value):
    text = _text(value)
    if not text:
        return ""
    try:
        return "%05d" % int(text)
    except (TypeError, ValueError):
        return text


def _compact_date(value):
    text = _text(value)
    if not text:
        return ""
    try:
        parsed = datetime.date.fromisoformat(text[:10])
    except (TypeError, ValueError):
        digits = "".join(char for char in text if char.isdigit())
        return digits
    return "%02d%02d%04d" % (parsed.day, parsed.month, parsed.year)


def _trial_days(legacy_value, modern_value, modern_unit):
    unit = _text(modern_unit).upper()
    raw = modern_value if modern_value not in (None, "") else legacy_value
    if raw in (None, ""):
        return ""
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return _text(raw)
    if modern_value not in (None, ""):
        if unit in ("DAY", "DAYS", "JOUR", "JOURS", ""):
            return str(value)
        if unit in ("WEEK", "WEEKS", "SEMAINE", "SEMAINES"):
            return str(value * 7)
        # Une période exprimée en mois n'est pas convertie artificiellement en
        # jours : la DPAE historique ne sait représenter que des jours.
        return ""
    return str(value)


def _load_saved_employer_values(DB):
    if not DB.IsTableExists("due_valeurs"):
        return {}
    DB.ExecuterReq("SELECT code, valeur FROM due_valeurs;")
    return {code: _text(value) for code, value in DB.ResultatReq()}


def BuildValues(IDcontrat):
    """Retourne les valeurs du formulaire DPAE pour ``IDcontrat``.

    Le chargeur n'impose ni classification historique ni valeur de point. Il
    accepte donc les contrats créés par le moteur moderne CCNS/CEE tout en
    conservant les champs employeur mémorisés dans ``due_valeurs``.
    """
    try:
        IDcontrat = int(IDcontrat)
    except (TypeError, ValueError):
        raise ValueError("IDcontrat invalide")
    if IDcontrat <= 0:
        raise ValueError("IDcontrat invalide")

    DB = GestionDB.DB()
    try:
        values = _load_saved_employer_values(DB)
        DB.ExecuterReq(
            """
            SELECT c.IDpersonne, c.date_debut, c.date_fin, c.essai,
                   c.convention_code, c.ccns_group, c.weekly_hours,
                   c.trial_period_value, c.trial_period_unit,
                   t.nom, t.nom_abrege, t.duree_indeterminee,
                   p.civilite, p.nom, p.nom_jfille, p.prenom, p.date_naiss,
                   p.cp_naiss, p.ville_naiss, p.num_secu,
                   p.adresse_resid, p.cp_resid, p.ville_resid,
                   nat.nationalite, naissance.nom
            FROM contrats c
            LEFT JOIN contrats_types t ON t.IDtype=c.IDtype
            LEFT JOIN personnes p ON p.IDpersonne=c.IDpersonne
            LEFT JOIN pays nat ON nat.IDpays=p.nationalite
            LEFT JOIN pays naissance ON naissance.IDpays=p.pays_naiss
            WHERE c.IDcontrat=%d;
            """ % IDcontrat
        )
        rows = DB.ResultatReq()
        if not rows:
            raise ValueError("Contrat introuvable : %d" % IDcontrat)

        (
            IDpersonne,
            date_debut,
            date_fin,
            essai,
            convention_code,
            ccns_group,
            weekly_hours,
            trial_period_value,
            trial_period_unit,
            type_nom,
            type_abrege,
            duree_indeterminee,
            civilite,
            nom,
            nom_jfille,
            prenom,
            date_naiss,
            cp_naiss,
            ville_naiss,
            num_secu,
            adresse_resid,
            cp_resid,
            ville_resid,
            nationalite,
            pays_naiss,
        ) = rows[0]

        if IDpersonne in (None, 0, ""):
            raise ValueError("Le contrat %d n'est rattaché à aucun salarié" % IDcontrat)

        civilite = _text(civilite)
        nom = _text(nom)
        nom_jfille = _text(nom_jfille)
        type_abrege = _text(type_abrege).upper()
        duree_indeterminee = _text(duree_indeterminee).lower()
        nationalite = _text(nationalite)

        if civilite == "Mr":
            due_civilite = _(u"M.")
            sexe = _(u"Masculin")
            nom_naissance = nom
            nom_marital = ""
        elif civilite in ("Mme", "Melle"):
            due_civilite = civilite
            sexe = _(u"Féminin")
            nom_naissance = nom_jfille or nom
            nom_marital = nom if nom_jfille else ""
        else:
            due_civilite = civilite
            sexe = ""
            nom_naissance = nom
            nom_marital = ""

        is_cdi = type_abrege == "CDI" or duree_indeterminee in ("oui", "yes", "true", "1")
        if is_cdi:
            contract_type = _(u"Contrat à durée indéterminée")
            due_end_date = ""
        else:
            contract_type = _(u"Contrat à durée déterminée")
            due_end_date = _compact_date(date_fin)

        cp_birth = _postal_code(cp_naiss)
        if nationalite.lower() in ("française", "francaise"):
            nationality_kind = _(u"Française")
            nationality_detail = ""
        elif nationalite:
            nationality_kind = _(u"Etrangère")
            nationality_detail = nationalite
        else:
            nationality_kind = ""
            nationality_detail = ""

        values.update(
            {
                "CIVILITE_SALARIE": due_civilite,
                "NOMNAISS_SALARIE": nom_naissance,
                "NOMMARITAL_SALARIE": nom_marital,
                "PRENOM_SALARIE": _text(prenom),
                "SEXE_SALARIE": sexe,
                "NUMSECU_SALARIE": _text(num_secu).replace(" ", ""),
                "DATENAISS_SALARIE": _compact_date(date_naiss),
                "NATIONALITE1_SALARIE": nationality_kind,
                "NATIONALITE2_SALARIE": nationality_detail,
                "DEPARTNAISS_SALARIE": cp_birth[:2],
                "VILLENAISS_SALARIE": _text(ville_naiss),
                "PAYSNAISS_SALARIE": _text(pays_naiss),
                "ADRESSE_SALARIE": _text(adresse_resid),
                "CP_SALARIE": _postal_code(cp_resid),
                "VILLE_SALARIE": _text(ville_resid),
                "DATE_EMBAUCHE": _compact_date(date_debut),
                "CONTRAT_TYPE": contract_type,
                "DATE_FIN_CONTRAT": due_end_date,
                "PERIODE_ESSAI": _trial_days(essai, trial_period_value, trial_period_unit),
                "DUREE_TRAVAIL_HEBDO": _text(weekly_hours),
                "NATURE_EMPLOI": _text(ccns_group) or _text(convention_code) or _text(type_nom),
            }
        )
        return values
    finally:
        DB.Close()


def ApplyToLegacyFields(IDcontrat, fields):
    """Applique les valeurs modernes à la structure de champs PDF historique."""
    values = BuildValues(IDcontrat)
    for field in fields:
        code = field[0]
        if code in values:
            field[4] = values[code]
    return values
