#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sauvegarde MySQL Windows/Unix : processus discret, borné et vérifiable.

Aucune requête de mutation ; aucune restauration ; aucune donnée sensible
dans le diagnostic. Le dump écrit directement dans un fichier temporaire.
"""
import base64
import os
import re
import subprocess
import tempfile
import time


def _creationflags(platform=None):
    """Pas de console noire devant l'application wx sous Windows."""
    if (platform or os.name) == "nt":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    return 0


def _diagnostic_sans_secrets(texte, secrets=()):
    texte = str(texte or "")
    valeurs = [str(secret) for secret in secrets if secret]
    for secret in tuple(valeurs):
        if secret.startswith("#64#"):
            try:
                valeurs.append(base64.b64decode(secret[4:]).decode("utf-8"))
            except (ValueError, UnicodeError):
                pass
    for secret in sorted(set(valeurs), key=len, reverse=True):
        if secret:
            texte = texte.replace(secret, "[masqué]")
    texte = re.sub(r"(?is)(?:INSERT\s+INTO|REPLACE\s+INTO).*", "[SQL masqué]", texte)
    return texte[-4096:]


def ExporterSQL(args, destination, progression=None, secrets=(),
                inactivite=600, duree_max=7200):
    """Retourne un bilan ; ne confond jamais un dump bloqué avec un succès.

    Attente bornée, contrôle de croissance du fichier, erreurs redirigées dans
    un fichier et non dans un PIPE qui risquerait de se remplir. Pas de shell.
    """
    debut = time.monotonic()
    dernier_octet = debut
    taille = 0
    erreur = None
    code = None
    details = ""
    proc = None

    try:
        with open(destination, "wb") as sortie, tempfile.TemporaryFile() as erreurs:
            proc = subprocess.Popen(
                list(args), stdout=sortie, stderr=erreurs,
                stdin=subprocess.DEVNULL, shell=False,
                creationflags=_creationflags(),
            )
            try:
                while True:
                    try:
                        proc.wait(timeout=2)
                        break
                    except subprocess.TimeoutExpired:
                        maintenant = time.monotonic()
                        nouvelle_taille = os.path.getsize(destination)
                        if nouvelle_taille > taille:
                            dernier_octet = maintenant
                        taille = nouvelle_taille
                        if progression is not None:
                            progression(taille)
                        if maintenant - dernier_octet >= inactivite:
                            erreur = "mysqldump est sans progression depuis 10 minutes."
                            break
                        if maintenant - debut >= duree_max:
                            erreur = "mysqldump a dépassé la durée limite de 2 heures."
                            break
            finally:
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=5)

            code = proc.returncode
            erreurs.seek(0, os.SEEK_END)
            erreurs.seek(max(0, erreurs.tell() - 4096))
            details = _diagnostic_sans_secrets(
                erreurs.read().decode("utf-8", "replace"), secrets
            )
            if erreur is None and code != 0:
                erreur = "mysqldump a échoué (code %s) : %s" % (code, details[-1800:])
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        erreur = "Export MySQL impossible : %s" % exc

    taille = os.path.getsize(destination) if os.path.isfile(destination) else 0
    if erreur is None and taille == 0:
        erreur = "mysqldump a produit un fichier SQL vide."
    return {
        "octets": taille, "code_retour": code,
        "secondes": round(time.monotonic() - debut, 1),
        "erreur": _diagnostic_sans_secrets(erreur, secrets) if erreur else None,
        "diagnostic": details,
    }
