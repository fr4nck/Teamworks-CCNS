#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import tempfile


def ExtraireFichierAtomiquement(fichier_zip, nom_fichier, repertoire_destination):
    """Extrait un membre ZIP sans altérer la cible avant lecture complète."""
    destination = os.path.join(repertoire_destination, nom_fichier)
    repertoire_parent = os.path.dirname(destination)
    if repertoire_parent and not os.path.isdir(repertoire_parent):
        os.makedirs(repertoire_parent)

    descripteur, fichier_temporaire = tempfile.mkstemp(
        prefix=".teamworks-restore-",
        suffix=".tmp",
        dir=repertoire_parent or repertoire_destination,
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
