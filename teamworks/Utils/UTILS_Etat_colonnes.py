#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""État de présentation robuste pour les listes configurables."""

import copy


VERSION = 1
_LARGEUR_MIN = 20
_LARGEUR_MAX = 4000


def _entier_borne(valeur, minimum, maximum):
    if isinstance(valeur, bool):
        return None
    try:
        entier = int(valeur)
    except (TypeError, ValueError):
        return None
    if entier < minimum or entier > maximum:
        return None
    return entier


def fusionner_colonnes(liste_defaut, etat):
    """Fusionne un état utilisateur avec les colonnes de la version courante.

    Les colonnes sont identifiées par leur ``nomChamp``. Les entrées inconnues
    d'un ancien Config.json sont ignorées et toute donnée invalide retombe sur
    la valeur par défaut de la version courante.
    """
    colonnes = copy.deepcopy(list(liste_defaut or []))
    if not isinstance(etat, dict) or etat.get("version") != VERSION:
        return colonnes

    etat_colonnes = etat.get("colonnes")
    if not isinstance(etat_colonnes, dict):
        return colonnes

    ordres = []
    for index, colonne in enumerate(colonnes):
        if not isinstance(colonne, list) or len(colonne) < 8:
            ordres.append((index + 1, index))
            continue
        champ = colonne[3]
        sauvegarde = etat_colonnes.get(champ)
        ordre_defaut = _entier_borne(colonne[7], 1, 10000) or (index + 1)
        ordre = ordre_defaut
        if isinstance(sauvegarde, dict):
            largeur = _entier_borne(
                sauvegarde.get("largeur"),
                _LARGEUR_MIN,
                _LARGEUR_MAX,
            )
            if largeur is not None:
                colonne[2] = largeur
            if isinstance(sauvegarde.get("visible"), bool):
                colonne[6] = sauvegarde["visible"]
            ordre_persistant = _entier_borne(sauvegarde.get("ordre"), 1, 10000)
            if ordre_persistant is not None:
                ordre = ordre_persistant
        ordres.append((ordre, index))

    # Les doublons / trous d'ordre d'un vieux fichier ne cassent jamais la vue.
    indices_tries = [index for _, index in sorted(ordres, key=lambda item: (item[0], item[1]))]
    for nouvel_ordre, index in enumerate(indices_tries, 1):
        colonnes[index][7] = nouvel_ordre
    return colonnes


def extraire_tri(etat, champs_connus, champ_defaut="nom", ascendant_defaut=True):
    if not isinstance(etat, dict) or etat.get("version") != VERSION:
        return champ_defaut, bool(ascendant_defaut)
    tri = etat.get("tri")
    if not isinstance(tri, dict):
        return champ_defaut, bool(ascendant_defaut)
    champ = tri.get("champ")
    if champ not in set(champs_connus or []):
        champ = champ_defaut
    ascendant = tri.get("ascendant")
    if not isinstance(ascendant, bool):
        ascendant = bool(ascendant_defaut)
    return champ, ascendant


def construire_etat(liste_colonnes, largeurs, champ_tri, tri_ascendant):
    """Construit un document JSON minimal à partir de l'état courant."""
    colonnes = {}
    for index, colonne in enumerate(list(liste_colonnes or []), 1):
        if not isinstance(colonne, (list, tuple)) or len(colonne) < 8:
            continue
        champ = colonne[3]
        if not isinstance(champ, str) or not champ or champ == "champ_recherche":
            continue
        largeur = _entier_borne((largeurs or {}).get(champ, colonne[2]), _LARGEUR_MIN, _LARGEUR_MAX)
        ordre = _entier_borne(colonne[7], 1, 10000) or index
        colonnes[champ] = {
            "largeur": largeur if largeur is not None else _LARGEUR_MIN,
            "ordre": ordre,
            "visible": bool(colonne[6]),
        }

    tri = {
        "champ": champ_tri if isinstance(champ_tri, str) else "nom",
        "ascendant": bool(tri_ascendant),
    }
    return {
        "version": VERSION,
        "colonnes": colonnes,
        "tri": tri,
    }
