#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Diagnostics de crash persistants pour Teamworks CCNS.

Ce module reste volontairement limité à la bibliothèque standard afin de pouvoir
être importé avant wxPython et avant le reste du runtime historique.

Les rapports sont conçus pour le débogage à distance sans collecter de données
métier : aucune variable locale ni message d'exception arbitraire n'est sérialisé.
"""

from __future__ import annotations

import atexit
import datetime
import faulthandler
import os
import platform
import re
import sys
import traceback
from typing import Optional


_NOM_APPLICATION = "Teamworks CCNS"
_MAX_RAPPORTS = 30
_NATIVE_HANDLE = None
_NATIVE_PATH: Optional[str] = None
_NATIVE_INITIAL_SIZE = 0
_LAST_EXCEPTION_OBJECT = None
_LAST_REPORT_PATH: Optional[str] = None
_EARLY_HOOK_INSTALLED = False
_TECHNICAL_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]{0,160}$")


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
        return "<path>"


def _version_python() -> str:
    return platform.python_version()


def GetVersionApplication(fallback: str = "") -> str:
    """Lit la version moderne du dépôt/portable avant la version historique."""
    # Les versions explicites de test ou de diagnostic restent prioritaires.
    # Seule la version Vanilla connue (ou l'absence de version) est remplacée
    # par la version moderne distribuée dans VERSION.
    if fallback and fallback != "2.1.3.1":
        return fallback
    principal = _repertoire_principal()
    for chemin in (
        os.path.join(principal, "VERSION"),
        os.path.join(os.path.dirname(principal), "VERSION"),
    ):
        try:
            with open(chemin, "r", encoding="utf-8", errors="replace") as fichier:
                version = fichier.read().strip()
            if version:
                return version
        except OSError:
            pass
    return fallback or ""


def _informations_build() -> list[str]:
    principal = _repertoire_principal()
    lignes: list[str] = []
    for nom in ("BUILD.txt", "VERSION"):
        chemin = os.path.join(principal, nom)
        try:
            if os.path.isfile(chemin):
                with open(chemin, "r", encoding="utf-8", errors="replace") as fichier:
                    contenu = fichier.read().strip()
                if contenu:
                    lignes.append(f"{nom}: {contenu.replace(chr(10), ' | ')}")
        except Exception:
            pass
    return lignes


def _nom_technique(value) -> str:
    if isinstance(value, str) and _TECHNICAL_NAME_RE.fullmatch(value):
        return value
    return ""


def _detail_exception_sur(exctype, value) -> str:
    """Retourne un détail utile sans sérialiser le message libre de l'exception."""
    nom = getattr(exctype, "__name__", "Exception")

    if isinstance(value, ModuleNotFoundError):
        module = _nom_technique(getattr(value, "name", None))
        return "%s | module=%s" % (nom, module) if module else nom

    if isinstance(value, ImportError):
        module = _nom_technique(getattr(value, "name", None))
        return "%s | module=%s" % (nom, module) if module else nom

    if isinstance(value, AttributeError):
        attribut = _nom_technique(getattr(value, "name", None))
        return "%s | attribut=%s" % (nom, attribut) if attribut else nom

    if isinstance(value, OSError):
        errno = getattr(value, "errno", None)
        return "%s | errno=%s" % (nom, errno) if isinstance(errno, int) else nom

    return nom


def _formater_pile(tb) -> list[str]:
    lignes = []
    if tb is None:
        return ["  <pile indisponible>"]
    try:
        for entree in traceback.extract_tb(tb):
            lignes.append(
                "  %s:%s in %s"
                % (_masquer_home(entree.filename), entree.lineno, entree.name)
            )
    except Exception:
        lignes.append("  <pile indisponible>")
    return lignes


def _formater_exception_sans_donnees(exctype, value, tb) -> str:
    """Formate la chaîne d'exceptions sans message, locals ni ligne source."""
    lignes = []
    courant = value
    courant_type = exctype
    courant_tb = tb
    vus = set()
    index = 0

    while courant is not None and id(courant) not in vus and index < 8:
        vus.add(id(courant))
        if index:
            lignes.append("Causé par :")
        lignes.append("Exception: %s" % _detail_exception_sur(courant_type, courant))
        lignes.extend(_formater_pile(courant_tb))

        suivant = getattr(courant, "__cause__", None)
        if suivant is None and not getattr(courant, "__suppress_context__", False):
            suivant = getattr(courant, "__context__", None)
        if suivant is None:
            break
        courant = suivant
        courant_type = type(suivant)
        courant_tb = getattr(suivant, "__traceback__", None)
        index += 1

    return "\n".join(lignes)


def _chronologie_technique() -> str:
    try:
        from Utils import UTILS_Blackbox
        return UTILS_Blackbox.FormaterChronologie()
    except Exception:
        return "Chronologie technique : indisponible."


def ConstruireRapport(
    exctype,
    value,
    tb,
    *,
    version: str = "",
    contexte: str = "Exception Python",
    version_wx: str = "",
) -> str:
    pile = _formater_exception_sans_donnees(exctype, value, tb)
    version = GetVersionApplication(version)
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
        _chronologie_technique(),
        "",
        "Pile Python sécurisée :",
        "-" * 78,
        pile,
        "",
        "Confidentialité : aucune variable locale, valeur de champ, texte saisi,",
        "identifiant métier, montant, requête SQL ou contenu de base de données n'est",
        "collecté. Les messages d'exception libres ne sont pas sérialisés.",
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

    La même instance d'exception n'est écrite qu'une fois lorsque plusieurs
    hooks la voient successivement (wx puis sys, par exemple).
    """
    global _LAST_EXCEPTION_OBJECT, _LAST_REPORT_PATH

    if _LAST_EXCEPTION_OBJECT is value and _LAST_REPORT_PATH and os.path.isfile(_LAST_REPORT_PATH):
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

    _LAST_EXCEPTION_OBJECT = value
    _LAST_REPORT_PATH = chemin
    _nettoyer_anciens_rapports(repertoire)
    return chemin


def InstallerHookMinimal(*, version: str = "") -> None:
    """Installe un hook sans wxPython pour les erreurs de démarrage/import."""
    global _EARLY_HOOK_INSTALLED
    if _EARLY_HOOK_INSTALLED:
        return

    def early_excepthook(exctype, value, tb):
        try:
            EcrireRapportException(
                exctype,
                value,
                tb,
                version=version,
                contexte="Démarrage / import",
            )
        except Exception:
            pass
        try:
            sortie = getattr(sys, "__stderr__", None)
            if sortie is not None:
                sortie.write("Teamworks CCNS : rapport de crash créé.\n")
        except Exception:
            pass

    sys.excepthook = early_excepthook
    _EARLY_HOOK_INSTALLED = True


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
    """Capture les erreurs fatales Python/C dans un fichier dédié."""
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
