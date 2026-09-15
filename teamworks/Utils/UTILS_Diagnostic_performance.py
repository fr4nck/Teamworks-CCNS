#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Instrumentation légère des lenteurs Teamworks.

Le diagnostic est désactivé par défaut. Il s'active avec la variable
``TEAMWORKS_PERF_DIAG=1`` et collecte alors des mesures en mémoire.

Pour une recette partageable, ``TEAMWORKS_PERF_LOG`` peut pointer vers un
fichier JSONL. Seuls les résumés d'actions et leurs métriques agrégées y sont
écrits : aucune requête SQL, aucun identifiant métier et aucune valeur de champ.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import threading
import time
from contextlib import contextmanager

_VARIABLE_ENV = "TEAMWORKS_PERF_DIAG"
_VARIABLE_LOG = "TEAMWORKS_PERF_LOG"
_VALEURS_ACTIVES = ("1", "true", "oui", "yes", "on")
_MESURES = []
_ETAT = threading.local()
_LOG_LOCK = threading.RLock()
_RE_IDENTIFIANT_SQL = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")
_RE_TABLE_SQL = re.compile(
    r"\b(?:FROM|INTO|UPDATE|JOIN)\s+[`\"\[]?([A-Za-z_][A-Za-z0-9_$]*)",
    re.IGNORECASE,
)
_RE_COMPOSANT = re.compile(r"[^A-Za-z0-9_.:-]+")
_METRIQUES_PERSISTEES = (
    "nb_requetes",
    "sql_ms",
    "connexion_ms",
    "io_ms",
    "python_wx_ms",
    "total_ms",
    "connexions_physiques",
    "connexions_reutilisees",
)


def diagnostic_actif():
    return os.environ.get(_VARIABLE_ENV, "").strip().lower() in _VALEURS_ACTIVES


def reinitialiser_mesures():
    del _MESURES[:]
    _ETAT.actions = []


def obtenir_mesures():
    return list(_MESURES)


def _actions():
    if not hasattr(_ETAT, "actions"):
        _ETAT.actions = []
    return _ETAT.actions


def _tracer_blackbox(action, component):
    try:
        from Utils import UTILS_Blackbox
        UTILS_Blackbox.Tracer(action, component)
    except Exception:
        pass


def _composant_action(nom):
    texte = _RE_COMPOSANT.sub("_", str(nom or "action"))[:140]
    if texte.startswith("wx."):
        return "wx:%s" % texte[3:]
    return "app:perf.%s" % texte


def _signature_requete(req):
    texte = " ".join(str(req or "").split())
    if not texte:
        return "unknown"
    premier = texte.split(None, 1)[0].strip("`\"[]();,").lower()
    operation = premier if _RE_IDENTIFIANT_SQL.match(premier) else "unknown"
    table = None
    match = _RE_TABLE_SQL.search(texte)
    if match:
        candidate = match.group(1)
        if _RE_IDENTIFIANT_SQL.match(candidate):
            table = candidate.lower()
    return "%s:%s" % (operation, table) if table else operation


def _composant_sql(signature):
    texte = _RE_COMPOSANT.sub("_", str(signature or "unknown").replace(":", "."))[:140]
    return "app:sql.%s" % texte


def _ecrire_resume_action(mesure):
    chemin = os.environ.get(_VARIABLE_LOG, "").strip()
    if not chemin:
        return
    details = mesure.get("details") or {}
    details_persistes = {cle: details.get(cle, 0) for cle in _METRIQUES_PERSISTEES}
    resume = {
        "date": datetime.datetime.now().astimezone().isoformat(timespec="milliseconds"),
        "categorie": "action",
        "nom": mesure.get("nom", ""),
        "details": details_persistes,
    }
    try:
        chemin = os.path.abspath(os.path.expanduser(chemin))
        repertoire = os.path.dirname(chemin)
        if repertoire:
            os.makedirs(repertoire, exist_ok=True)
        ligne = json.dumps(resume, ensure_ascii=False, sort_keys=True)
        with _LOG_LOCK:
            with open(chemin, "a", encoding="utf-8") as fichier:
                fichier.write(ligne + "\n")
    except Exception:
        pass


def enregistrer_mesure(categorie, nom, duree, details=None):
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
        elif categorie == "connexion":
            action["connexions_physiques"] += 1
        elif categorie == "connexion_reutilisee":
            action["connexions_reutilisees"] += 1


def enregistrer_reutilisation_connexion(nom="GestionDB.DB"):
    """Compte une réutilisation explicite d'une connexion bornée déjà ouverte."""
    enregistrer_mesure("connexion_reutilisee", nom, 0.0, {"reutilisee": True})


def demarrer_action(nom, details=None):
    if not diagnostic_actif():
        return None
    action = {
        "nom": nom,
        "details": dict(details or {}),
        "debut": time.perf_counter(),
        "temps_par_categorie": {},
        "nb_requetes": 0,
        "connexions_physiques": 0,
        "connexions_reutilisees": 0,
    }
    _actions().append(action)
    _tracer_blackbox("PERF_ACTION_START", _composant_action(nom))
    return action


def terminer_action(action):
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
        "connexions_physiques": action["connexions_physiques"],
        "connexions_reutilisees": action["connexions_reutilisees"],
    })
    mesure = {
        "categorie": "action",
        "nom": action["nom"],
        "duree": duree,
        "details": details,
    }
    _MESURES.append(mesure)
    _ecrire_resume_action(mesure)
    _tracer_blackbox("PERF_ACTION_END", _composant_action(action["nom"]))
    return mesure


@contextmanager
def mesurer_action(nom, details=None):
    action = demarrer_action(nom, details)
    try:
        yield action
    finally:
        terminer_action(action)


@contextmanager
def mesurer(categorie, nom, details=None):
    if not diagnostic_actif():
        yield
        return
    debut = time.perf_counter()
    try:
        yield
    finally:
        enregistrer_mesure(categorie, nom, time.perf_counter() - debut, details)


def installer_instrumentation_sql(gestion_db_module=None):
    """Instrumente ``GestionDB.DB`` une seule fois quand le diagnostic est actif."""
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
        signature = _signature_requete(req)
        details = {
            "phase": "execute",
            "reseau": bool(getattr(self, "isNetwork", False)),
            "signature": signature,
        }
        composant = _composant_sql(signature)
        _tracer_blackbox("PERF_SQL_START", composant)
        try:
            with mesurer("sql", "GestionDB.ExecuterReq", details):
                return executer_original(self, req, *args, **kwargs)
        finally:
            _tracer_blackbox("PERF_SQL_END", composant)

    def resultat_instrumente(self, *args, **kwargs):
        details = {
            "phase": "fetch",
            "reseau": bool(getattr(self, "isNetwork", False)),
            "signature": "fetch",
        }
        composant = _composant_sql("fetch")
        _tracer_blackbox("PERF_SQL_START", composant)
        try:
            with mesurer("sql", "GestionDB.ResultatReq", details):
                return resultat_original(self, *args, **kwargs)
        finally:
            _tracer_blackbox("PERF_SQL_END", composant)

    classe_db.ExecuterReq = executer_instrumente
    classe_db.ResultatReq = resultat_instrumente
    classe_db._teamworks_perf_sql_installe = True
    return True
