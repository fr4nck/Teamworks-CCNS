#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Instrumentation légère des lenteurs Teamworks.

Le diagnostic est désactivé par défaut. Il s'active avec la variable
``TEAMWORKS_PERF_DIAG=1`` et n'ajoute alors que des mesures en mémoire,
récupérables par les tests ou par une console de développement.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager

_VARIABLE_ENV = "TEAMWORKS_PERF_DIAG"
_VALEURS_ACTIVES = ("1", "true", "oui", "yes", "on")
_MESURES = []


def diagnostic_actif():
    """Indique si la collecte des mesures est activée."""
    return os.environ.get(_VARIABLE_ENV, "").strip().lower() in _VALEURS_ACTIVES


def reinitialiser_mesures():
    """Vide les mesures collectées pendant la session courante."""
    del _MESURES[:]


def obtenir_mesures():
    """Retourne une copie des mesures collectées."""
    return list(_MESURES)


def enregistrer_mesure(categorie, nom, duree, details=None):
    """Ajoute une mesure si le diagnostic est actif."""
    if not diagnostic_actif():
        return
    _MESURES.append({
        "categorie": categorie,
        "nom": nom,
        "duree": float(duree),
        "details": details or {},
    })


@contextmanager
def mesurer(categorie, nom, details=None):
    """Mesure un bloc avec ``time.perf_counter()`` si le diagnostic est actif."""
    if not diagnostic_actif():
        yield
        return
    debut = time.perf_counter()
    try:
        yield
    finally:
        enregistrer_mesure(categorie, nom, time.perf_counter() - debut, details)
