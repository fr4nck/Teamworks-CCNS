#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Normalisation des versions Teamworks pour les comparaisons historiques."""

import re


_VERSION_NUMERIQUE = re.compile(r"^\s*(\d+(?:\.\d+)*)")


def ConvertirTuple(texte_version=""):
    """Retourne le préfixe numérique d'une version sous forme de tuple.

    Le cœur historique compare uniquement des tuples d'entiers. Les suffixes
    d'édition ou de préversion ne participent donc pas à la migration du schéma
    de données : ``0.9.2-rc3`` et ``0.9.2`` désignent le même niveau de schéma.
    """
    if isinstance(texte_version, list):
        return tuple(texte_version)
    if isinstance(texte_version, tuple):
        return texte_version

    match = _VERSION_NUMERIQUE.match(str(texte_version))
    if match is None:
        raise ValueError("Version numérique invalide : %r" % (texte_version,))
    return tuple(int(element) for element in match.group(1).split("."))
