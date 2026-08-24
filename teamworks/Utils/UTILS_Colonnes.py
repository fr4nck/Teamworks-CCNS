#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gestion explicite des colonnes flexibles des tableaux métier Teamworks.

Ce module n'intervient jamais globalement. Un écran choisit lui-même les colonnes
qui peuvent absorber l'espace libre. Les largeurs historiques restent des minima
et, si la fenêtre devient trop étroite, le listctrl conserve son scroll horizontal
plutôt que d'écraser les informations.
"""

import wx

from Utils import UTILS_Theme


class ColonnesFlexibles:
    """Distribue le surplus horizontal à un ensemble de colonnes choisies."""

    def __init__(self, listctrl, extensibles, marge=24):
        self.listctrl = listctrl
        self.extensibles = tuple(extensibles)
        self.marge = int(marge)
        self._largeurs_reference = None
        self._ajustement_en_cours = False

        self.listctrl.Bind(wx.EVT_SIZE, self.OnSize)
        wx.CallAfter(self.Ajuster)

    def _capturer_reference(self):
        try:
            nombre = self.listctrl.GetColumnCount()
        except Exception:
            return []
        if nombre <= 0:
            return []

        if self._largeurs_reference is None or len(self._largeurs_reference) != nombre:
            self._largeurs_reference = [
                max(0, self.listctrl.GetColumnWidth(index))
                for index in range(nombre)
            ]
        return list(self._largeurs_reference)

    def ReinitialiserReference(self):
        """À appeler après une reconstruction complète des colonnes."""
        self._largeurs_reference = None
        wx.CallAfter(self.Ajuster)

    def OnSize(self, event):
        wx.CallAfter(self.Ajuster)
        event.Skip()

    def Ajuster(self):
        if self._ajustement_en_cours:
            return

        references = self._capturer_reference()
        if not references:
            return

        try:
            largeur_disponible = self.listctrl.GetClientSize().GetWidth() - self.marge
        except Exception:
            return
        if largeur_disponible <= 0:
            return

        facteur = UTILS_Theme.interface_scale_percent() / 100.0
        minima = [
            0 if largeur == 0 else max(22, int(round(largeur * facteur)))
            for largeur in references
        ]
        cibles = list(minima)
        total_minimum = sum(minima)

        indices = [
            index for index in self.extensibles
            if 0 <= index < len(cibles) and minima[index] > 0
        ]
        if largeur_disponible > total_minimum and indices:
            surplus = largeur_disponible - total_minimum
            poids_total = sum(max(1, minima[index]) for index in indices)
            distribue = 0
            for position, index in enumerate(indices):
                if position == len(indices) - 1:
                    ajout = surplus - distribue
                else:
                    ajout = int(round(surplus * max(1, minima[index]) / float(poids_total)))
                    distribue += ajout
                cibles[index] += max(0, ajout)

        self._ajustement_en_cours = True
        try:
            for index, largeur in enumerate(cibles):
                if self.listctrl.GetColumnWidth(index) != largeur:
                    self.listctrl.SetColumnWidth(index, largeur)
        finally:
            self._ajustement_en_cours = False
