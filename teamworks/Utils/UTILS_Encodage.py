#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Décodage des anciens contenus externes à leur frontière d'import."""

ENCODAGES_EXTERNES_HISTORIQUES = (
    "utf-8-sig",
    "utf-8",
    "iso-8859-15",
    "cp1252",
)


def DecodeTexteExterne(value, encodings=ENCODAGES_EXTERNES_HISTORIQUES):
    """Retourne du texte Unicode à partir d'une valeur externe éventuelle.

    Les appels à cette fonction doivent rester placés au point de lecture d'un
    fichier, d'une réponse réseau ou d'une ressource historique. Le code
    interne ne doit pas s'en servir pour masquer un mélange d'encodages.
    """
    if not isinstance(value, bytes):
        return value

    for encoding in encodings:
        try:
            return value.decode(encoding)
        except UnicodeDecodeError:
            continue
    return value.decode("utf-8", errors="replace")
