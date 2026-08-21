#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Utilitaires communs aux composants de l'écran Présences."""


def find_presences_panel(window):
    """Retrouve le conteneur Présences sans supposer une profondeur de parents."""
    current = window
    while current is not None:
        try:
            if current.GetName() == "panel_presences":
                return current
        except Exception:
            pass
        try:
            current = current.GetParent()
        except Exception:
            current = None
    return None
