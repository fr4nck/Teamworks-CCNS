#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Diagnostics de crash persistants pour Teamworks CCNS.

Ce module reste volontairement limité à la bibliothèque standard afin de pouvoir
être importé avant wxPython et avant le reste de Teamworks par le bootstrap du
portable PyInstaller.
"""

from __future__ import annotations

import atexit
import datetime
import faulthandler
import os
import platform
import sys
import traceback
from typing import Optional


_NOM_APPLICATION = "Teamworks CCNS"
_MAX_RAPPORTS = 30
_NATIVE_HANDLE = None
_NATIVE_PATH: Optional[str] = None
_NATIVE_INITIAL_SIZE = 0
_LAST_EXCEPTION_ID: Optional[int] = None
_LAST_REPORT_PATH: Optional[str] = None


def _repertoire_principal() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def GetRepertoireLogs() -> str:
    """Retourne le dossier de diagnostics sans dépendre du reste de Teamworks."""
    override = os.environ.get("TEAMWORKS_LOG_DIR", "").strip()
    if override:
        chemin = os.path.abspath(override)
    else:
        principal = _repertoire_principal()
        portable = os.path.join(principal, "Portable")
        if os.path.isdir(portable):
            chemin = os.path.join(portable, "Logs")
        elif sys.platform == "win32":
            base = os.environ.get("APPDATA") or os.path.expanduser("~")
            chemin = os.path.join(base, "teamworks", "Logs")
        else:
            base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
            chemin = os.path.join(base, "teamworks", "Logs")

    os.makedirs(chemin, exist_ok=True)
    return chemin


def _horodatage_fichier() -> str:
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def _date_iso() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _masquer_home(chemin: str) -> str:
    if not chemin:
        return ""
    try:
        home = os.path.abspath(os.path.expanduser("~"))
        absolu = os.path.abspath(chemin)
        if os.path.normcase(absolu).startswith(os.path.normcase(home)):
            return "~" + absolu[len(home):]
        return absolu
    except Exception:
        return str(chemin)


def _version_python() -> str:
    return platform.python_version()


def _informations_build() -> list[str]:
    principal = _repertoire_principal()
    lignes: list[str] = []
    for nom in ("BUILD.txt", "VERSION"):
        chemin = os.path.join(principal, nom)
        try:
            if os.path.isfile(chemin):
                contenu = open(chemin, "r", encoding="utf-8", errors="replace").read().strip()
                if contenu:
                    lignes.append(f"{nom}: {contenu.replace(chr(10), ' | ')}")
        except Exception:
            pass
    return lignes


def ConstruireRapport(
    exctype,
    value,
    tb,
    *,
    version: str = "",
    contexte: str = "Exception Python",
    version_wx: str = "",
) -> str:
    trace = "".join(traceback.format_exception(exctype, value, tb))
    lignes = [
        "=" * 78,
        f"{_NOM_APPLICATION} — rapport de crash",
        "=" * 78,
        f"Date: {_date_iso()}",
        f"Contexte: {contexte or 'Exception Python'}",
        f"Version application: {version or 'inconnue'}",
        f"PID: {os.getpid()}",
        f"Portable/PyInstaller: {'oui' if getattr(sys, 'frozen', False) else 'non'}",
        f"Python: {_version_python()}",
        f"wxPython: {version_wx or 'non disponible au moment du crash'}",
        f"Système: {platform.platform()}",
        f"Architecture: {platform.machine()}",
        f"Exécutable: {_masquer_home(sys.executable)}",
        f"Répertoire courant: {_masquer_home(os.getcwd())}",
    ]
    lignes.extend(_informations_build())
    lignes.extend([
        "",
        "Traceback:",
        "-" * 78,
        trace.rstrip(),
        "",
        "Note: ce fichier ne contient volontairement ni mot de passe, ni variables",
        "d'environnement, ni contenu de base de données.",
        "",
    ])
    return "\n".join(lignes)


def _nettoyer_anciens_rapports(repertoire: str, conserver: int = _MAX_RAPPORTS) -> None:
    try:
        fichiers = []
        for nom in os.listdir(repertoire):
            if not (nom.startswith("crash-") or nom.startswith("native-crash-")):
                continue
            chemin = os.path.join(repertoire, nom)
            if os.path.isfile(chemin):
                fichiers.append((os.path.getmtime(chemin), chemin))
        fichiers.sort(reverse=True)
        for _, chemin in fichiers[conserver:]:
            try:
                os.remove(chemin)
            except OSError:
                pass
    except OSError:
        pass


def EcrireRapportException(
    exctype,
    value,
    tb,
    *,
    version: str = "",
    contexte: str = "Exception Python",
    version_wx: str = "",
    repertoire: Optional[str] = None,
) -> str:
    """Écrit un rapport persistant et retourne son chemin.

    Une même instance d'exception n'est écrite qu'une fois afin d'éviter le
    doublon hook wx -> bootstrap.
    """
    global _LAST_EXCEPTION_ID, _LAST_REPORT_PATH

    exception_id = id(value)
    if _LAST_EXCEPTION_ID == exception_id and _LAST_REPORT_PATH and os.path.isfile(_LAST_REPORT_PATH):
        return _LAST_REPORT_PATH

    repertoire = repertoire or GetRepertoireLogs()
    os.makedirs(repertoire, exist_ok=True)
    chemin = os.path.join(repertoire, f"crash-{_horodatage_fichier()}-{os.getpid()}.txt")
    rapport = ConstruireRapport(
        exctype,
        value,
        tb,
        version=version,
        contexte=contexte,
        version_wx=version_wx,
    )
    with open(chemin, "w", encoding="utf-8", errors="replace") as fichier:
        fichier.write(rapport)
        fichier.flush()

    _LAST_EXCEPTION_ID = exception_id
    _LAST_REPORT_PATH = chemin
    _nettoyer_anciens_rapports(repertoire)
    return chemin


def _fermer_native(clean: bool = True) -> None:
    global _NATIVE_HANDLE, _NATIVE_PATH, _NATIVE_INITIAL_SIZE
    if _NATIVE_HANDLE is None:
        return
    try:
        if faulthandler.is_enabled():
            faulthandler.disable()
    except Exception:
        pass
    try:
        _NATIVE_HANDLE.flush()
        _NATIVE_HANDLE.close()
    except Exception:
        pass

    if clean and _NATIVE_PATH:
        try:
            if os.path.getsize(_NATIVE_PATH) <= _NATIVE_INITIAL_SIZE:
                os.remove(_NATIVE_PATH)
        except OSError:
            pass

    _NATIVE_HANDLE = None
    _NATIVE_PATH = None
    _NATIVE_INITIAL_SIZE = 0


def ActiverFaulthandler(*, version: str = "", repertoire: Optional[str] = None) -> Optional[str]:
    """Capture les erreurs fatales Python/C dans un fichier dédié.

    Le fichier vide est supprimé lors d'une fermeture normale. En cas de crash
    fatal, le processus ne passe pas par atexit et le fichier reste disponible.
    """
    global _NATIVE_HANDLE, _NATIVE_PATH, _NATIVE_INITIAL_SIZE

    if _NATIVE_HANDLE is not None:
        return _NATIVE_PATH
    if faulthandler.is_enabled():
        return None

    try:
        repertoire = repertoire or GetRepertoireLogs()
        os.makedirs(repertoire, exist_ok=True)
        chemin = os.path.join(repertoire, f"native-crash-{_horodatage_fichier()}-{os.getpid()}.log")
        handle = open(chemin, "w", encoding="utf-8", errors="replace")
        handle.write(
            f"{_NOM_APPLICATION} | {version or 'version inconnue'} | {_date_iso()} | PID {os.getpid()}\n"
        )
        handle.flush()
        initial_size = handle.tell()
        faulthandler.enable(file=handle, all_threads=True)

        _NATIVE_HANDLE = handle
        _NATIVE_PATH = chemin
        _NATIVE_INITIAL_SIZE = initial_size
        atexit.register(_fermer_native, True)
        return chemin
    except Exception:
        try:
            if _NATIVE_HANDLE is not None:
                _NATIVE_HANDLE.close()
        except Exception:
            pass
        _NATIVE_HANDLE = None
        _NATIVE_PATH = None
        _NATIVE_INITIAL_SIZE = 0
        return None


def DesactiverFaulthandler(clean: bool = True) -> None:
    _fermer_native(clean)
