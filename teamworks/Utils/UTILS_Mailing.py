#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fonctions pures de préparation des mailings Teamworks.

Ce module ne se connecte à aucun serveur et ne dépend pas de wxPython. Il
centralise les opérations qui doivent être déterministes avant l'envoi :
validation des adresses, fusion des champs et composition des pièces jointes.
"""

from __future__ import annotations

import datetime
import re


_EMAIL_RE = re.compile(
    r"^[^\s@<>]+@(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
)
_KEYWORD_RE = re.compile(r"\{[A-Za-z0-9_]+\}")


def NormalizeEmail(value):
    """Retourne une adresse normalisée ou ``None`` si elle est invalide."""
    if value is None:
        return None
    address = str(value).strip()
    if not address or len(address) > 254:
        return None
    if not _EMAIL_RE.match(address):
        return None
    local, domain = address.rsplit("@", 1)
    if len(local) > 64:
        return None
    return "%s@%s" % (local, domain.lower())


def IsValidEmail(value):
    return NormalizeEmail(value) is not None


def SplitEmailAddresses(value):
    """Découpe une saisie manuelle et élimine invalides et doublons.

    Les séparateurs acceptés sont point-virgule, virgule et retours à la ligne.
    L'ordre de première apparition est conservé.
    """
    if value is None:
        return []
    candidates = re.split(r"[;,\r\n]+", str(value))
    result = []
    seen = set()
    for candidate in candidates:
        address = NormalizeEmail(candidate)
        if address is None:
            continue
        key = address.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(address)
    return result


def _field_text(value):
    if value is None:
        return ""
    if isinstance(value, datetime.datetime):
        value = value.date()
    if isinstance(value, datetime.date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, bool):
        return str(value)
    return str(value)


def MergeFields(template, fields=None, standard_fields=None):
    """Fusionne les mots-clés sans modifier les dictionnaires fournis."""
    text = "" if template is None else str(template)
    for mapping in (standard_fields or {}, fields or {}):
        for keyword, value in mapping.items():
            text = text.replace(str(keyword), _field_text(value))
    return text


def FindUnresolvedKeywords(text):
    """Retourne les mots-clés encore présents, sans doublon et dans l'ordre."""
    found = []
    seen = set()
    for keyword in _KEYWORD_RE.findall("" if text is None else str(text)):
        if keyword not in seen:
            seen.add(keyword)
            found.append(keyword)
    return found


def CombineAttachments(personal=None, common=None):
    """Compose les pièces jointes sans muter les listes d'origine.

    Un même chemin n'est conservé qu'une fois, ce qui rend une seconde
    préparation idempotente et évite les doublons historiques du mailer.
    """
    result = []
    seen = set()
    for source in (personal or (), common or ()):
        for item in source:
            if item in (None, ""):
                continue
            path = str(item)
            if path in seen:
                continue
            seen.add(path)
            result.append(path)
    return result


def PreparePayload(address, subject, html, fields=None, standard_fields=None,
                   personal_attachments=None, common_attachments=None, images=None):
    """Prépare un message sérialisable avant création du backend d'envoi."""
    normalized = NormalizeEmail(address)
    if normalized is None:
        raise ValueError("Adresse email invalide : %r" % (address,))
    merged_html = MergeFields(html, fields=fields, standard_fields=standard_fields)
    return {
        "destinataires": [normalized],
        "sujet": "" if subject is None else str(subject),
        "texte_html": merged_html,
        "fichiers": CombineAttachments(personal_attachments, common_attachments),
        "images": list(images or ()),
        "champs": dict(fields or {}),
        "motscles_non_resolus": FindUnresolvedKeywords(merged_html),
    }
