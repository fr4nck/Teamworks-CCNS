#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import tempfile


def _VerifierNomFichierLocal(nom_fichier):
    if not nom_fichier or nom_fichier in (".", ".."):
        raise ValueError("Nom de fichier de restauration invalide")
    if "/" in nom_fichier or "\\" in nom_fichier:
        raise ValueError("La restauration locale attend un nom de fichier simple")


def ExtraireFichierAtomiquement(fichier_zip, nom_fichier, repertoire_destination):
    """Extrait un fichier local sans altérer la cible avant lecture complète."""
    _VerifierNomFichierLocal(nom_fichier)
    destination = os.path.join(repertoire_destination, nom_fichier)

    descripteur, fichier_temporaire = tempfile.mkstemp(
        prefix=".teamworks-restore-",
        suffix=".tmp",
        dir=repertoire_destination,
    )

    try:
        with os.fdopen(descripteur, "wb") as destination_temporaire:
            with fichier_zip.open(nom_fichier, "r") as source:
                shutil.copyfileobj(source, destination_temporaire)
            destination_temporaire.flush()
            os.fsync(destination_temporaire.fileno())
        os.replace(fichier_temporaire, destination)
    except Exception:
        try:
            os.remove(fichier_temporaire)
        except OSError:
            pass
        raise

    return destination
