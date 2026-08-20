#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Boîte noire technique de recette pour Teamworks CCNS.

Principes de confidentialité :
- aucune valeur de champ, aucun texte saisi, aucun identifiant métier ;
- aucun nom de fichier utilisateur, aucune requête SQL, aucun contenu BDD ;
- uniquement des événements techniques, classes Python/wx et identifiants wx numériques ;
- la chronologie reste en mémoire et n'est écrite qu'en cas de crash ou de freeze.
"""

from __future__ import annotations

from collections import deque
import atexit
import datetime
import os
import platform
import re
import sys
import threading
import time
import traceback
from typing import Callable, Optional


_MAX_EVENTS = 200
_MAX_REPORTS = 30
_EVENTS = deque(maxlen=_MAX_EVENTS)
_LOCK = threading.RLock()

_COMPONENT_RE = re.compile(r"^(?:app|menu|wx|system):[A-Za-z0-9_.:-]{1,160}$")
_ACTION_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,47}$")

_WATCHDOG_THREAD = None
_WATCHDOG_STOP = threading.Event()
_WATCHDOG_POSTER: Optional[Callable[[], None]] = None
_WATCHDOG_THRESHOLD = 8.0
_WATCHDOG_INTERVAL = 1.0
_WATCHDOG_VERSION = ""
_WATCHDOG_REPERTOIRE: Optional[str] = None
_LAST_HEARTBEAT = time.monotonic()
_HEARTBEAT_PENDING = False
_FREEZE_REPORTED = False
_FREEZE_PATH: Optional[str] = None
_FREEZE_STARTED = 0.0


def _date_iso() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="milliseconds")


def _horodatage_fichier() -> str:
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def _masquer_home(chemin: str) -> str:
    try:
        home = os.path.abspath(os.path.expanduser("~"))
        absolu = os.path.abspath(chemin)
        if os.path.normcase(absolu).startswith(os.path.normcase(home)):
            return "~" + absolu[len(home):]
        return absolu
    except Exception:
        return "<path>"


def _repertoire_logs_defaut() -> str:
    override = os.environ.get("TEAMWORKS_LOG_DIR", "").strip()
    if override:
        chemin = os.path.abspath(override)
    elif getattr(sys, "frozen", False):
        principal = os.path.dirname(os.path.abspath(sys.executable))
        portable = os.path.join(principal, "Portable")
        if os.path.isdir(portable):
            chemin = os.path.join(portable, "Logs")
        elif sys.platform == "win32":
            base = os.environ.get("APPDATA") or os.path.expanduser("~")
            chemin = os.path.join(base, "teamworks", "Logs")
        else:
            chemin = os.path.join(os.path.expanduser("~"), ".config", "teamworks", "Logs")
    elif sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        chemin = os.path.join(base, "teamworks", "Logs")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
        chemin = os.path.join(base, "teamworks", "Logs")
    os.makedirs(chemin, exist_ok=True)
    return chemin


def _action_sure(action: str) -> str:
    action = str(action or "").upper()
    if _ACTION_RE.fullmatch(action):
        return action
    return "TECH_EVENT"


def _composant_sur(component: str) -> str:
    component = str(component or "")
    if _COMPONENT_RE.fullmatch(component):
        return component
    return "system:redacted"


def Tracer(action: str, component: str, code: Optional[int] = None) -> None:
    """Ajoute un breadcrumb exclusivement technique à la mémoire circulaire."""
    evenement = {
        "date": _date_iso(),
        "mono": time.monotonic(),
        "action": _action_sure(action),
        "component": _composant_sur(component),
        "code": int(code) if isinstance(code, int) and not isinstance(code, bool) else None,
    }
    with _LOCK:
        _EVENTS.append(evenement)


def ViderChronologie() -> None:
    with _LOCK:
        _EVENTS.clear()


def SnapshotChronologie() -> list[dict]:
    with _LOCK:
        return [dict(item) for item in _EVENTS]


def FormaterChronologie() -> str:
    evenements = SnapshotChronologie()
    if not evenements:
        return "Chronologie technique : aucune étape enregistrée."
    lignes = [
        "Chronologie technique (mémoire circulaire, aucune donnée utilisateur) :",
        "-" * 78,
    ]
    origine = evenements[0]["mono"]
    for item in evenements:
        delta = max(0.0, item["mono"] - origine)
        suffixe = "" if item["code"] is None else " | code=%d" % item["code"]
        lignes.append(
            "%s | +%07.3fs | %s | %s%s"
            % (item["date"], delta, item["action"], item["component"], suffixe)
        )
    return "\n".join(lignes)


def _formater_stacks_threads() -> str:
    """Retourne les piles sans variables locales ni lignes de code source."""
    frames = sys._current_frames()
    main_ident = threading.main_thread().ident
    lignes = ["Piles des threads (sans variables locales ni contenu des lignes) :", "-" * 78]
    for ident in sorted(frames):
        role = "main" if ident == main_ident else "worker"
        lignes.append("Thread id=%s role=%s" % (ident, role))
        try:
            pile = traceback.extract_stack(frames[ident])
            for entree in pile[-80:]:
                lignes.append(
                    "  %s:%s in %s"
                    % (_masquer_home(entree.filename), entree.lineno, entree.name)
                )
        except Exception:
            lignes.append("  <pile indisponible>")
        lignes.append("")
    return "\n".join(lignes)


def _nettoyer_anciens_rapports(repertoire: str) -> None:
    try:
        candidats = []
        for nom in os.listdir(repertoire):
            if not nom.startswith("freeze-"):
                continue
            chemin = os.path.join(repertoire, nom)
            if os.path.isfile(chemin):
                candidats.append((os.path.getmtime(chemin), chemin))
        candidats.sort(reverse=True)
        for _, chemin in candidats[_MAX_REPORTS:]:
            try:
                os.remove(chemin)
            except OSError:
                pass
    except OSError:
        pass


def EcrireRapportFreeze(
    duree_secondes: float,
    *,
    version: str = "",
    repertoire: Optional[str] = None,
) -> str:
    """Écrit un état technique des threads lorsqu'une boucle UI ne répond plus."""
    repertoire = repertoire or _repertoire_logs_defaut()
    os.makedirs(repertoire, exist_ok=True)
    chemin = os.path.join(
        repertoire,
        "freeze-%s-%s.txt" % (_horodatage_fichier(), os.getpid()),
    )
    lignes = [
        "=" * 78,
        "Teamworks CCNS — rapport de gel de l'interface",
        "=" * 78,
        "Date: %s" % _date_iso(),
        "Durée sans heartbeat au diagnostic: %.2f s" % float(duree_secondes),
        "Version application: %s" % (version or "inconnue"),
        "PID: %s" % os.getpid(),
        "Python: %s" % platform.python_version(),
        "Système: %s" % platform.platform(),
        "Architecture: %s" % platform.machine(),
        "",
        FormaterChronologie(),
        "",
        _formater_stacks_threads(),
        "",
        "Confidentialité : aucune valeur de champ, aucun texte saisi, aucun identifiant",
        "métier, aucun montant, aucune requête SQL et aucun contenu de base de données",
        "ne sont collectés par la boîte noire.",
        "",
    ]
    with open(chemin, "w", encoding="utf-8", errors="replace") as fichier:
        fichier.write("\n".join(lignes))
        fichier.flush()
    _nettoyer_anciens_rapports(repertoire)
    return chemin


def _append_recovery(chemin: str, duree_secondes: float) -> None:
    try:
        with open(chemin, "a", encoding="utf-8", errors="replace") as fichier:
            fichier.write(
                "\nInterface réactive à nouveau après %.2f s sans heartbeat.\n"
                % float(duree_secondes)
            )
    except Exception:
        pass


def MarquerHeartbeat() -> None:
    """Doit être appelée dans le thread UI lorsque la boucle wx peut traiter une tâche."""
    global _LAST_HEARTBEAT, _HEARTBEAT_PENDING, _FREEZE_REPORTED, _FREEZE_PATH, _FREEZE_STARTED
    maintenant = time.monotonic()
    chemin_recovery = None
    duree = 0.0
    with _LOCK:
        if _FREEZE_REPORTED:
            chemin_recovery = _FREEZE_PATH
            duree = max(0.0, maintenant - _FREEZE_STARTED)
        _LAST_HEARTBEAT = maintenant
        _HEARTBEAT_PENDING = False
        _FREEZE_REPORTED = False
        _FREEZE_PATH = None
        _FREEZE_STARTED = 0.0
    if chemin_recovery:
        _append_recovery(chemin_recovery, duree)
        Tracer("FREEZE_RECOVERED", "app:wx_main_loop")


def _watchdog_loop() -> None:
    global _HEARTBEAT_PENDING, _FREEZE_REPORTED, _FREEZE_PATH, _FREEZE_STARTED
    while not _WATCHDOG_STOP.wait(_WATCHDOG_INTERVAL):
        poster = None
        maintenant = time.monotonic()
        with _LOCK:
            if not _HEARTBEAT_PENDING:
                _HEARTBEAT_PENDING = True
                poster = _WATCHDOG_POSTER
            age = max(0.0, maintenant - _LAST_HEARTBEAT)
            deja_signale = _FREEZE_REPORTED

        if poster is not None:
            try:
                poster()
            except Exception:
                with _LOCK:
                    _HEARTBEAT_PENDING = False

        if age >= _WATCHDOG_THRESHOLD and not deja_signale:
            try:
                Tracer("FREEZE_DETECTED", "app:wx_main_loop")
                chemin = EcrireRapportFreeze(
                    age,
                    version=_WATCHDOG_VERSION,
                    repertoire=_WATCHDOG_REPERTOIRE,
                )
            except Exception:
                chemin = None
            with _LOCK:
                _FREEZE_REPORTED = True
                _FREEZE_PATH = chemin
                _FREEZE_STARTED = _LAST_HEARTBEAT


def DemarrerWatchdog(
    poster_heartbeat: Callable[[], None],
    *,
    version: str = "",
    seuil_secondes: float = 8.0,
    intervalle_secondes: float = 1.0,
    repertoire: Optional[str] = None,
) -> None:
    """Démarre le watchdog de la boucle UI dans un thread daemon."""
    global _WATCHDOG_THREAD, _WATCHDOG_POSTER, _WATCHDOG_THRESHOLD, _WATCHDOG_INTERVAL
    global _WATCHDOG_VERSION, _WATCHDOG_REPERTOIRE, _LAST_HEARTBEAT, _HEARTBEAT_PENDING

    if _WATCHDOG_THREAD is not None and _WATCHDOG_THREAD.is_alive():
        return
    if not callable(poster_heartbeat):
        raise TypeError("poster_heartbeat doit être appelable")

    _WATCHDOG_POSTER = poster_heartbeat
    _WATCHDOG_THRESHOLD = max(0.05, float(seuil_secondes))
    _WATCHDOG_INTERVAL = max(0.01, min(float(intervalle_secondes), _WATCHDOG_THRESHOLD / 2.0))
    _WATCHDOG_VERSION = str(version or "")
    _WATCHDOG_REPERTOIRE = repertoire
    _LAST_HEARTBEAT = time.monotonic()
    _HEARTBEAT_PENDING = False
    _WATCHDOG_STOP.clear()
    Tracer("WATCHDOG_START", "app:wx_main_loop")
    _WATCHDOG_THREAD = threading.Thread(
        target=_watchdog_loop,
        name="teamworks-freeze-watchdog",
        daemon=True,
    )
    _WATCHDOG_THREAD.start()


def ArreterWatchdog() -> None:
    _WATCHDOG_STOP.set()


atexit.register(ArreterWatchdog)
