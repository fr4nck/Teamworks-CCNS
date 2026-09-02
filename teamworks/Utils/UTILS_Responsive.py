#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Règles responsive communes aux formulaires Teamworks-CCNS.

Les décisions de mise en page sont prises à partir de la largeur réellement
allouée à la fenêtre et de l'échelle d'interface. Elles ne dépendent donc pas de
la résolution totale de l'écran et restent cohérentes avec les Snap Layouts de
Windows 11.
"""

from __future__ import annotations


DEFAULT_TWO_COLUMN_MIN_LOGICAL_WIDTH = 1120


def logical_width(pixel_width, scale_percent=100):
    """Retourne la largeur utile en pixels logiques.

    Exemple : 1720 px physiques à 200 % correspondent à 860 px logiques pour
    décider si un formulaire peut raisonnablement rester en deux colonnes.
    """
    try:
        width = max(0.0, float(pixel_width))
    except (TypeError, ValueError):
        width = 0.0
    try:
        scale = max(1.0, float(scale_percent))
    except (TypeError, ValueError):
        scale = 100.0
    return width * 100.0 / scale


def form_column_count(
    pixel_width,
    scale_percent=100,
    two_column_min_logical_width=DEFAULT_TWO_COLUMN_MIN_LOGICAL_WIDTH,
):
    """Retourne 1 ou 2 colonnes pour une fiche métier.

    Le seuil est centralisé et exprimé en largeur logique afin qu'un même écran
    puisse basculer en une colonne lorsque l'utilisateur augmente fortement le
    zoom d'interface.
    """
    return 2 if logical_width(pixel_width, scale_percent) >= float(
        two_column_min_logical_width
    ) else 1


def should_stack_form(pixel_width, scale_percent=100):
    return form_column_count(pixel_width, scale_percent) == 1
