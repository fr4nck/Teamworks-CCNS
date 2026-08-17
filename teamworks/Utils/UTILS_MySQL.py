#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Options et diagnostic de connexion MySQL, sans dépendance graphique."""


def ConstruireOptionsConnexion(host, user, password, port, certificats=None):
    """Construit une connexion tolérante aux anciens serveurs MySQL/MariaDB.

    Le chemin Python pur évite les défauts de l'extension C du connecteur dans
    les exécutables PyInstaller et reste compatible avec le serveur 5.5 en
    production. Le chiffrement n'est désactivé que si aucun CA n'est configuré.
    """
    certificats = certificats or {}
    options = {
        "host": host,
        "user": user,
        "passwd": password,
        "port": int(port),
        "use_unicode": True,
        "charset": "utf8",
        "connection_timeout": 10,
        "use_pure": True,
    }
    if certificats.get("ca"):
        options["ssl_ca"] = certificats["ca"]
        if certificats.get("key"):
            options["ssl_key"] = certificats["key"]
        if certificats.get("cert"):
            options["ssl_cert"] = certificats["cert"]
    else:
        options["ssl_disabled"] = True
    return options


def _ValeurErreur(erreur, attribut):
    valeur = getattr(erreur, attribut, None)
    if valeur in (None, ""):
        return None
    return str(valeur).replace("\r", " ").replace("\n", " ")


def FormaterDiagnosticConnexion(erreur, host, port, interface, version_connecteur):
    """Retourne un diagnostic copiable ne contenant jamais les identifiants."""
    details = [
        "Connexion MySQL impossible.",
        "Pilote : %s %s (mode Python pur)" % (interface, version_connecteur),
        "Serveur : %s:%s" % (host or "<non renseigné>", port),
        "Erreur : %s: %s" % (type(erreur).__name__, str(erreur) or "<sans message>"),
    ]
    errno = _ValeurErreur(erreur, "errno")
    sqlstate = _ValeurErreur(erreur, "sqlstate")
    if errno:
        details.append("Code MySQL : %s" % errno)
    if sqlstate:
        details.append("SQLSTATE : %s" % sqlstate)
    if "failed raising error" in str(erreur).lower():
        details.append(
            "Indice : le connecteur embarqué n'a pas réussi à restituer "
            "l'erreur du serveur ; vérifier l'artefact Windows et son manifeste."
        )
    return "\n".join(details)
