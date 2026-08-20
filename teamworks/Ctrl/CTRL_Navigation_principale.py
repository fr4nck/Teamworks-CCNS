#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Navigation principale flexible de Teamworks.

Ce composant remplace le ``wx.Toolbook`` historique : les libellés ne sont plus
contraints par la largeur d'une toolbar native et peuvent passer sur plusieurs
lignes lorsque l'échelle de l'interface ou la largeur de fenêtre l'impose.
"""

import wx

from Utils import UTILS_Customize
from Utils import UTILS_Interface


def _echelle_interface():
    try:
        valeur = UTILS_Customize.GetValeur(
            "interface", "echelle_interface", "", ajouter_si_manquant=False
        )
        if valeur in (None, ""):
            valeur = UTILS_Customize.GetValeur(
                "interface", "echelle_police", "100", type_valeur=int
            )
        return max(80, min(200, int(valeur)))
    except Exception:
        return 100


def _dimension(valeur, minimum=1, maximum=None):
    resultat = max(minimum, int(round(valeur * _echelle_interface() / 100.0)))
    if maximum is not None:
        resultat = min(maximum, resultat)
    return resultat


def _bitmap_adapte(chemin, taille_base=24):
    taille = _dimension(taille_base, minimum=20, maximum=36)
    bitmap = wx.Bitmap(chemin, wx.BITMAP_TYPE_ANY)
    if bitmap.IsOk() and (bitmap.GetWidth() != taille or bitmap.GetHeight() != taille):
        bitmap = wx.Bitmap(
            bitmap.ConvertToImage().Scale(taille, taille, wx.IMAGE_QUALITY_HIGH)
        )
    return bitmap


class BoutonNavigation(wx.ToggleButton):
    """Bouton de section avec cible confortable et libellé jamais ellipsé."""

    def __init__(self, parent, label, bitmap=wx.NullBitmap):
        wx.ToggleButton.__init__(self, parent, -1, label=label)
        self._bitmap = bitmap
        self.SetBitmap(bitmap)
        self.SetBitmapPosition(wx.LEFT)
        self.SetBitmapMargins((_dimension(6), 0))
        self.AppliquerTheme(False)
        self._AjusterTaille()

    def _AjusterTaille(self):
        # GetBestSize tient compte du texte complet. On conserve donc toute la
        # place dont le libellé a besoin, même à 120/150 %.
        best = self.GetBestSize()
        hauteur = max(best.GetHeight(), _dimension(40, minimum=40))
        largeur = max(best.GetWidth(), _dimension(92, minimum=80))
        self.SetMinSize((largeur, hauteur))

    def AppliquerTheme(self, actif=False):
        if actif:
            fond = UTILS_Interface.GetToken("primary_container")
            texte = UTILS_Interface.GetToken("on_primary_container")
        else:
            fond = UTILS_Interface.GetToken("surface")
            texte = UTILS_Interface.GetToken("on_surface")
        self.SetBackgroundColour(fond)
        self.SetForegroundColour(texte)
        self.SetValue(bool(actif))


class NavigationPrincipale(wx.Panel):
    """Livre de pages piloté par une barre d'actions flexible."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, name="navigation_principale")
        self._pages = []
        self._boutons = []
        self._selection = -1
        self._active = True

        self.barre = wx.Panel(self, -1, name="barre_navigation_principale")
        self.sizer_barre = wx.WrapSizer(wx.HORIZONTAL)
        self.barre.SetSizer(self.sizer_barre)

        self.livre = wx.Simplebook(self, -1)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.barre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 6)
        sizer.Add(self.livre, 1, wx.EXPAND | wx.ALL, 6)
        self.SetSizer(sizer)

        self.AppliquerTheme()
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def AppliquerTheme(self):
        surface = UTILS_Interface.GetToken("surface")
        barre = UTILS_Interface.GetToken("surface_container_low")
        self.SetBackgroundColour(surface)
        self.barre.SetBackgroundColour(barre)
        self.livre.SetBackgroundColour(surface)
        for index, bouton in enumerate(self._boutons):
            bouton.AppliquerTheme(index == self._selection)

    def AddPage(self, page, label, bitmap=wx.NullBitmap, select=False):
        index = len(self._pages)
        self._pages.append(page)
        self.livre.AddPage(page, label, select=False)

        bouton = BoutonNavigation(self.barre, label, bitmap)
        bouton.Bind(wx.EVT_TOGGLEBUTTON, lambda event, i=index: self.SetSelection(i))
        self._boutons.append(bouton)
        self.sizer_barre.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, 6)

        if self._selection == -1 or select:
            self.SetSelection(index, rafraichir=False)
        else:
            bouton.AppliquerTheme(False)

        self.barre.Layout()
        self.Layout()
        return True

    def GetPage(self, index):
        return self._pages[index]

    def GetPageCount(self):
        return len(self._pages)

    def GetSelection(self):
        return self._selection

    def SetSelection(self, index, rafraichir=True):
        if index < 0 or index >= len(self._pages):
            return self._selection
        ancienne = self._selection
        if index == ancienne:
            self._boutons[index].SetValue(True)
            return ancienne

        if rafraichir:
            self.MAJ_panel(index)

        self._selection = index
        self.livre.SetSelection(index)
        for numero, bouton in enumerate(self._boutons):
            bouton.AppliquerTheme(numero == index)
        return ancienne

    def ChangeSelection(self, index):
        """Compatibilité wx.BookCtrl : change de page sans MAJ métier."""
        return self.SetSelection(index, rafraichir=False)

    def MAJ_page_si_affichee(self, code=""):
        index = self.dict_pages_by_index[code]
        if index == self.GetSelection():
            self.MAJ_panel(index)

    def MAJ_panel(self, numPage=0):
        page = self.GetPage(numPage)
        maj = getattr(page, "MAJpanel", None)
        if maj is not None:
            maj()

    def ActiveToolBook(self, etat=True):
        """API historique conservée pour le reste de Teamworks."""
        self._active = bool(etat)
        if self.GetPageCount():
            self.SetSelection(0, rafraichir=False)
            if not etat:
                accueil = self.GetPage(0)
                html = getattr(accueil, "html", None)
                if html is not None and hasattr(html, "Efface"):
                    html.Efface()

        # Accueil reste toujours accessible ; les autres sections suivent
        # l'état d'ouverture du fichier métier.
        for index, bouton in enumerate(self._boutons):
            bouton.Enable(True if index == 0 else bool(etat))

    def OnSize(self, event):
        # WrapSizer recalculera les lignes suivant la largeur disponible.
        self.barre.Layout()
        self.Layout()
        event.Skip()
