#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Instrumentation légère des lenteurs Teamworks.

Le diagnostic est désactivé par défaut. Il s'active avec la variable
``TEAMWORKS_PERF_DIAG=1`` et n'ajoute alors que des mesures en mémoire,
récupérables par les tests ou par une console de développement.

Les actions agrègent les temps SQL/connexion et le nombre de requêtes afin de
séparer la latence base distante du temps Python/wx. L'instrumentation SQL est
installée à la demande par les écrans diagnostiqués et ne modifie rien lorsque
le diagnostic est désactivé.
"""

from __future__ import annotations

import os
import threading
import time
from contextlib import contextmanager

_VARIABLE_ENV = "TEAMWORKS_PERF_DIAG"
_VALEURS_ACTIVES = ("1", "true", "oui", "yes", "on")
_MESURES = []
_ETAT = threading.local()


def diagnostic_actif():
    """Indique si la collecte des mesures est activée."""
    return os.environ.get(_VARIABLE_ENV, "").strip().lower() in _VALEURS_ACTIVES


def reinitialiser_mesures():
    """Vide les mesures collectées pendant la session courante."""
    del _MESURES[:]
    _ETAT.actions = []


def obtenir_mesures():
    """Retourne une copie des mesures collectées."""
    return list(_MESURES)


def _actions():
    if not hasattr(_ETAT, "actions"):
        _ETAT.actions = []
    return _ETAT.actions


def enregistrer_mesure(categorie, nom, duree, details=None):
    """Ajoute une mesure et l'agrège dans les actions actives."""
    if not diagnostic_actif():
        return

    details = details or {}
    duree = float(duree)
    _MESURES.append({
        "categorie": categorie,
        "nom": nom,
        "duree": duree,
        "details": details,
    })

    for action in list(_actions()):
        action["temps_par_categorie"][categorie] = (
            action["temps_par_categorie"].get(categorie, 0.0) + duree
        )
        if categorie == "sql" and details.get("phase") == "execute":
            action["nb_requetes"] += 1


def demarrer_action(nom, details=None):
    """Démarre une mesure agrégée, utilisable aussi à travers ``wx.CallAfter``."""
    if not diagnostic_actif():
        return None
    action = {
        "nom": nom,
        "details": dict(details or {}),
        "debut": time.perf_counter(),
        "temps_par_categorie": {},
        "nb_requetes": 0,
    }
    _actions().append(action)
    return action


def terminer_action(action):
    """Termine une action et enregistre son résumé SQL / Python-wx."""
    if action is None or not diagnostic_actif():
        return None

    actions = _actions()
    if action not in actions:
        return None
    actions.remove(action)

    duree = time.perf_counter() - action["debut"]
    temps = action["temps_par_categorie"]
    sql = temps.get("sql", 0.0)
    connexion = temps.get("connexion", 0.0)
    io = temps.get("io", 0.0)
    temps_db = sql + connexion
    details = dict(action["details"])
    details.update({
        "nb_requetes": action["nb_requetes"],
        "sql_ms": round(sql * 1000.0, 2),
        "connexion_ms": round(connexion * 1000.0, 2),
        "io_ms": round(io * 1000.0, 2),
        "python_wx_ms": round(max(0.0, duree - temps_db - io) * 1000.0, 2),
        "total_ms": round(duree * 1000.0, 2),
    })
    mesure = {
        "categorie": "action",
        "nom": action["nom"],
        "duree": duree,
        "details": details,
    }
    _MESURES.append(mesure)
    return mesure


@contextmanager
def mesurer_action(nom, details=None):
    """Mesure une action UI complète et agrège ses accès base."""
    action = demarrer_action(nom, details)
    try:
        yield action
    finally:
        terminer_action(action)


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


def _apercu_requete(req, limite=220):
    texte = " ".join(str(req).split())
    if len(texte) > limite:
        return texte[: limite - 3] + "..."
    return texte


def installer_instrumentation_sql(gestion_db_module=None):
    """Instrumente ``GestionDB.DB`` une seule fois quand le diagnostic est actif.

    L'installation est volontairement déclenchée par les écrans wx étudiés :
    en production, sans ``TEAMWORKS_PERF_DIAG``, aucun monkey-patch n'est posé.
    """
    if not diagnostic_actif():
        return False

    if gestion_db_module is None:
        import GestionDB as gestion_db_module

    classe_db = gestion_db_module.DB
    if getattr(classe_db, "_teamworks_perf_sql_installe", False):
        return True

    executer_original = classe_db.ExecuterReq
    resultat_original = classe_db.ResultatReq

    def executer_instrumente(self, req, *args, **kwargs):
        details = {
            "phase": "execute",
            "reseau": bool(getattr(self, "isNetwork", False)),
            "requete": _apercu_requete(req),
        }
        with mesurer("sql", "GestionDB.ExecuterReq", details):
            return executer_original(self, req, *args, **kwargs)

    def resultat_instrumente(self, *args, **kwargs):
        details = {
            "phase": "fetch",
            "reseau": bool(getattr(self, "isNetwork", False)),
        }
        with mesurer("sql", "GestionDB.ResultatReq", details):
            return resultat_original(self, *args, **kwargs)

    classe_db.ExecuterReq = executer_instrumente
    classe_db.ResultatReq = resultat_instrumente
    classe_db._teamworks_perf_sql_installe = True
    return True
