#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import sqlite3
import tempfile


def _VerifierNomFichierLocal(nom_fichier):
    if not nom_fichier or nom_fichier in (".", ".."):
        raise ValueError("Nom de fichier de restauration invalide")
    if "/" in nom_fichier or "\\" in nom_fichier:
        raise ValueError("La restauration locale attend un nom de fichier simple")


def _SelectionnerMembreUnique(fichier_zip, nom_fichier):
    membres = [
        membre
        for membre in fichier_zip.infolist()
        if membre.filename == nom_fichier
    ]
    if not membres:
        raise ValueError("Le fichier demandé est absent de la sauvegarde")
    if len(membres) != 1:
        raise ValueError("La sauvegarde contient plusieurs entrées ambiguës pour ce fichier")
    return membres[0]


def _ValiderBaseSQLite(fichier_sqlite):
    connexion = None
    curseur = None
    try:
        connexion = sqlite3.connect(fichier_sqlite)
        curseur = connexion.cursor()
        curseur.execute("PRAGMA quick_check;")
        resultats = curseur.fetchall()
        if resultats != [("ok",)]:
            raise sqlite3.DatabaseError(
                "Base SQLite invalide : PRAGMA quick_check=%r" % (resultats,)
            )
    finally:
        if curseur is not None:
            curseur.close()
        if connexion is not None:
            connexion.close()


def ExtraireFichierAtomiquement(fichier_zip, nom_fichier, repertoire_destination):
    """Extrait et valide une base SQLite avant remplacement atomique."""
    _VerifierNomFichierLocal(nom_fichier)
    membre = _SelectionnerMembreUnique(fichier_zip, nom_fichier)
    destination = os.path.join(repertoire_destination, nom_fichier)

    descripteur, fichier_temporaire = tempfile.mkstemp(
        prefix=".teamworks-restore-",
        suffix=".tmp",
        dir=repertoire_destination,
    )

    try:
        with os.fdopen(descripteur, "wb") as destination_temporaire:
            with fichier_zip.open(membre, "r") as source:
                shutil.copyfileobj(source, destination_temporaire)
            destination_temporaire.flush()
            os.fsync(destination_temporaire.fileno())
        _ValiderBaseSQLite(fichier_temporaire)
        os.replace(fichier_temporaire, destination)
    except Exception:
        try:
            os.remove(fichier_temporaire)
        except OSError:
            pass
        raise

    return destination
