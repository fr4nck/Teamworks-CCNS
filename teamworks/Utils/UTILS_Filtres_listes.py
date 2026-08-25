# -*- coding: utf-8 -*-
"""Prédicats sûrs pour les filtres de colonnes des ObjectListView."""
from __future__ import annotations

import ast


def _numeric_literal(value):
    if isinstance(value, bool):
        raise ValueError("Un booléen n'est pas un critère numérique")
    if isinstance(value, (int, float)):
        return value
    parsed = ast.literal_eval(str(value))
    if isinstance(parsed, bool) or not isinstance(parsed, (int, float)):
        raise ValueError("Critère numérique invalide : %r" % (value,))
    return parsed


def ConstruirePredicat(dictFiltre, get_inscrits=None):
    """Construit un prédicat sans générer ni exécuter de code Python."""
    code = dictFiltre["code"]
    choix = dictFiltre["choix"]
    criteres = dictFiltre["criteres"]
    type_donnee = dictFiltre["typeDonnee"]

    def valeur(track):
        return getattr(track, code, None)

    if type_donnee == "texte":
        critere = str(criteres).lower()
        if choix == "EGAL":
            return lambda track: valeur(track) is not None and valeur(track).lower() == critere
        if choix == "DIFFERENT":
            return lambda track: valeur(track) is not None and valeur(track).lower() != critere
        if choix == "CONTIENT":
            return lambda track: valeur(track) is not None and critere in valeur(track).lower()
        if choix == "CONTIENTPAS":
            return lambda track: valeur(track) is not None and critere not in valeur(track).lower()
        if choix == "VIDE":
            return lambda track: valeur(track) in ("", None)
        if choix == "PASVIDE":
            return lambda track: valeur(track) not in ("", None)

    if type_donnee == "bool":
        if choix == "TRUE":
            return lambda track: valeur(track) in (True, "True", 1, "1")
        if choix == "FALSE":
            return lambda track: valeur(track) in (False, "False", 0, "0", None, "")

    if type_donnee in ("entier", "montant"):
        if choix == "COMPRIS":
            minimum_texte, maximum_texte = str(criteres).split(";", 1)
            minimum = _numeric_literal(minimum_texte)
            maximum = _numeric_literal(maximum_texte)
            return lambda track: valeur(track) >= minimum and valeur(track) <= maximum
        critere = _numeric_literal(criteres)
        operations = {
            "EGAL": lambda current: current == critere,
            "DIFFERENT": lambda current: current != critere,
            "SUP": lambda current: current > critere,
            "SUPEGAL": lambda current: current >= critere,
            "INF": lambda current: current < critere,
            "INFEGAL": lambda current: current <= critere,
        }
        if choix in operations:
            operation = operations[choix]
            return lambda track: operation(valeur(track))

    if type_donnee in ("date", "dateheure"):
        if choix == "COMPRIS":
            minimum, maximum = str(criteres).split(";", 1)
            return lambda track: (
                valeur(track) is not None
                and str(valeur(track)) >= minimum
                and str(valeur(track)) <= maximum
            )
        critere = str(criteres)
        operations = {
            "EGAL": lambda current: current == critere,
            "DIFFERENT": lambda current: current != critere,
            "SUP": lambda current: current > critere,
            "SUPEGAL": lambda current: current >= critere,
            "INF": lambda current: current < critere,
            "INFEGAL": lambda current: current <= critere,
        }
        if choix in operations:
            operation = operations[choix]
            return lambda track: valeur(track) is not None and operation(str(valeur(track)))

    if type_donnee == "inscrits" and choix in ("INSCRITS", "PRESENTS"):
        if get_inscrits is None:
            raise ValueError("Le résolveur des inscrits est obligatoire")
        identifiants = frozenset(get_inscrits(mode=code, choix=choix, criteres=criteres))
        attribut = "ID%s" % code
        return lambda track: getattr(track, attribut, None) in identifiants

    raise ValueError(
        "Filtre de colonne non supporté : type=%r choix=%r code=%r"
        % (type_donnee, choix, code)
    )
