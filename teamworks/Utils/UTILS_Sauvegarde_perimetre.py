# -*- coding: utf-8 -*-
"""Périmètre strict des sauvegardes Teamworks : dossier actuellement ouvert.

Les mêmes chemins Data et les mêmes suffixes historiques peuvent être
partagés par plusieurs applications. Une sauvegarde Teamworks ne doit donc
JAMAIS découvrir automatiquement tous les fichiers *_{TDATA,TPHOTOS,
TDOCUMENTS}.dat du répertoire, ni toutes les bases d'un serveur MySQL.
"""
import os


_CATEGORIES = ("TDATA", "TPHOTOS", "TDOCUMENTS")


def fichier_actif():
    """Utilise exactement la notion de dossier actif de GestionDB.

    Aucune ouverture de base, aucun changement de configuration.
    """
    import GestionDB
    return GestionDB.DB.GetNomFichierDefaut(None)


def analyser_fichier_actif(nom_fichier):
    """Renvoie le mode et la racine du seul dossier Teamworks ouvert."""
    if not isinstance(nom_fichier, str) or not nom_fichier.strip():
        return None
    nom_fichier = nom_fichier.strip()
    if "[RESEAU]" in nom_fichier:
        login, sep, nom = nom_fichier.partition("[RESEAU]")
        if not sep or len(login.split(";")) != 4:
            return None
        mode = "reseau"
        nom = nom.strip()
        connexions = login.split(";")
        try:
            port = int(connexions[0])
        except (ValueError, TypeError):
            return None
        identity = (str(port), connexions[1].casefold(), connexions[2])
    else:
        mode = "local"
        nom = nom_fichier
        identity = None

    if (not nom or nom in (".", "..") or
            any(c in nom for c in "/\\:\0\r\n") or
            "[RESEAU]" in nom or nom.endswith(".dat")):
        return None

    # Les fichiers logiques Teamworks possèdent trois familles de données.
    # Ne pas énumérer les autres dossiers Noethys du même répertoire/serveur.
    return {"mode": mode, "nom": nom, "connexion": identity}


def composants_du_dossier(nom_fichier):
    """Liste blanche exacte : fichiers ou bases SQL du dossier actif."""
    scope = analyser_fichier_actif(nom_fichier)
    if not scope:
        return {"locaux": (), "reseau": ()}
    nom = scope["nom"]
    if scope["mode"] == "local":
        return {
            "locaux": tuple("%s_%s.dat" % (nom, code) for code in _CATEGORIES),
            "reseau": (),
        }
    return {
        "locaux": (),
        "reseau": tuple(
            "%s_%s" % (nom.lower(), code.lower()) for code in _CATEGORIES
        ),
    }


def connexion_correspond(nom_fichier, dict_connexion):
    scope = analyser_fichier_actif(nom_fichier)
    if not scope or scope["mode"] != "reseau" or not dict_connexion:
        return False
    port, host, user = scope["connexion"]
    try:
        current = (
            str(int(dict_connexion.get("port"))),
            str(dict_connexion.get("host") or
                dict_connexion.get("hote") or "").casefold(),
            str(dict_connexion.get("user") or
                dict_connexion.get("utilisateur") or ""),
        )
    except (TypeError, ValueError):
        return False
    return current == (port, host, user)


def valider_selection(nom_fichier, locaux=(), reseau=(), connexion=None):
    """Retourne (bool, motif) ; refuse aussi les profils automatiques anciens.

    L'absence de contexte ne déclenche jamais une découverte globale.
    """
    scope = analyser_fichier_actif(nom_fichier)
    if not scope:
        return False, "Aucun dossier Teamworks actuellement ouvert."
    composants = composants_du_dossier(nom_fichier)
    for kind, items in (("locaux", locaux or ()), ("reseau", reseau or ())):
        acceptes = set(composants[kind])
        if any(item not in acceptes for item in items):
            return False, (
                "La sélection contient des données extérieures au dossier "
                "Teamworks actuellement ouvert."
            )
    if reseau and not connexion_correspond(nom_fichier, connexion):
        return False, (
            "La connexion MySQL n'est pas celle du dossier Teamworks "
            "actuellement ouvert."
        )
    return True, ""
