#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fonctions pures de préparation des mailings Teamworks.

Ce module ne se connecte à aucun serveur et ne dépend pas de wxPython. Il
centralise les opérations qui doivent être déterministes avant l'envoi :
validation des adresses, fusion des champs, composition des pièces jointes et
validation de la configuration des backends de messagerie.
"""

from __future__ import annotations

import datetime
import re


_EMAIL_RE = re.compile(
    r"^[^\s@<>]+@(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
)
_KEYWORD_RE = re.compile(r"\{[A-Za-z0-9_]+\}")
_SUPPORTED_BACKENDS = ("smtp", "smtp_obsolete", "mailjet")


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


def ParseBackendParameters(value, strict=True):
    """Décode le format historique ``cle==valeur##cle==valeur``.

    ``split('==', 1)`` est volontaire : certaines valeurs externes peuvent
    contenir le caractère ``=``. En mode non strict, les fragments corrompus
    sont ignorés afin qu'un écran de configuration puisse rester ouvrable.
    """
    if value in (None, ""):
        return {}

    result = {}
    for raw_item in str(value).split("##"):
        item = raw_item.strip()
        if not item:
            continue
        if "==" not in item:
            if strict:
                raise ValueError("Paramètre de messagerie invalide : %s" % item)
            continue
        name, parameter_value = item.split("==", 1)
        name = name.strip()
        if not name:
            if strict:
                raise ValueError("Nom de paramètre de messagerie vide")
            continue
        result[name] = parameter_value
    return result


def SerializeBackendParameters(values, ordered_names=None):
    """Encode un dictionnaire dans le format historique de Teamworks."""
    mapping = dict(values or {})
    names = list(ordered_names or mapping.keys())
    for name in mapping:
        if name not in names:
            names.append(name)
    return "##".join(
        "%s==%s" % (name, "" if mapping[name] is None else mapping[name])
        for name in names
        if name in mapping
    )


def NormalizeBackendName(value):
    backend = "" if value is None else str(value).strip().lower()
    if backend not in _SUPPORTED_BACKENDS:
        raise ValueError(
            "Backend de messagerie inconnu : %r (attendus : %s)"
            % (value, ", ".join(_SUPPORTED_BACKENDS))
        )
    return backend


def ValidateBackendConfig(
    backend,
    email_exp,
    host=None,
    port=None,
    username=None,
    password=None,
    use_tls=False,
    parameters=None,
):
    """Valide et normalise une configuration avant toute connexion réseau."""
    backend = NormalizeBackendName(backend)
    sender = NormalizeEmail(email_exp)
    if sender is None:
        raise ValueError("Adresse d'expédition invalide : %r" % (email_exp,))

    parsed_parameters = ParseBackendParameters(parameters, strict=True)

    normalized_port = None
    if port not in (None, ""):
        try:
            normalized_port = int(port)
        except (TypeError, ValueError):
            raise ValueError("Port SMTP invalide : %r" % (port,))
        if not 1 <= normalized_port <= 65535:
            raise ValueError("Port SMTP hors plage : %r" % (port,))

    normalized_host = None if host in (None, "") else str(host).strip()
    normalized_username = None if username in (None, "") else str(username)
    normalized_password = None if password in (None, "") else str(password)

    if backend in ("smtp", "smtp_obsolete"):
        if not normalized_host:
            raise ValueError("Serveur SMTP manquant")
        if (normalized_username is None) != (normalized_password is None):
            raise ValueError(
                "Utilisateur et mot de passe SMTP doivent être renseignés ensemble"
            )

    if backend == "mailjet":
        api_key = parsed_parameters.get("api_key", "").strip()
        api_secret = parsed_parameters.get("api_secret", "").strip()
        if not api_key or not api_secret:
            raise ValueError("Les clés API Mailjet sont incomplètes")

    return {
        "backend": backend,
        "email_exp": sender,
        "host": normalized_host,
        "port": normalized_port,
        "username": normalized_username,
        "password": normalized_password,
        "use_tls": bool(use_tls),
        "parameters": parsed_parameters,
    }


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
