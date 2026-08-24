#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Navigation principale flexible de Teamworks.

Les pages métier restent directement enfants de ce composant, comme elles
l'étaient du ``wx.Toolbook`` historique. On conserve ainsi les chaînes
``GetParent()/GetGrandParent()`` existantes tout en supprimant la toolbar à
largeur figée qui tronquait les libellés lorsque l'interface était agrandie.
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


def BitmapNavigation(chemin, taille_base=24):
    """Charge une icône de navigation à l'échelle de l'interface."""
    taille = _dimension(taille_base, minimum=20, maximum=36)
    bitmap = wx.Bitmap(chemin, wx.BITMAP_TYPE_ANY)
    if bitmap.IsOk() and (bitmap.GetWidth() != taille or bitmap.GetHeight() != taille):
        bitmap = wx.Bitmap(
            bitmap.ConvertToImage().Scale(taille, taille, wx.IMAGE_QUALITY_HIGH)
        )
    return bitmap


class BoutonNavigation(wx.ToggleButton):
    """Bouton de section dont la taille suit réellement son contenu."""

    def __init__(self, parent, label, bitmap=wx.NullBitmap):
        wx.ToggleButton.__init__(self, parent, -1, label=label)
        if bitmap is not None and bitmap.IsOk():
            self.SetBitmap(bitmap)
            self.SetBitmapPosition(wx.LEFT)
            self.SetBitmapMargins((_dimension(6), 0))
        self._AjusterTaille()
        self.AppliquerTheme(False)

    def _AjusterTaille(self):
        # GetBestSize mesure le libellé complet avec la police courante : aucun
        # texte n'est volontairement rogné lorsque l'utilisateur passe à 120 %.
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
    """Livre de pages léger piloté par une barre de navigation flexible."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, name="navigation_principale")
        self._pages = []
        self._boutons = []
        self._selection = -1
        self._active = True

        self.barre = wx.Panel(self, -1, name="barre_navigation_principale")
        self.sizer_barre = wx.WrapSizer(wx.HORIZONTAL)
        self.barre.SetSizer(self.sizer_barre)

        # Les pages restent directement enfants de NavigationPrincipale afin de
        # préserver la hiérarchie historique attendue par les contrôles métier.
        self.sizer_pages = wx.BoxSizer(wx.VERTICAL)

        self.sizer_principal = wx.BoxSizer(wx.VERTICAL)
        self.sizer_principal.Add(
            self.barre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, _dimension(6)
        )
        self.sizer_principal.Add(self.sizer_pages, 1, wx.EXPAND | wx.ALL, _dimension(6))
        self.SetSizer(self.sizer_principal)

        self.AppliquerTheme()
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def AppliquerTheme(self):
        surface = UTILS_Interface.GetToken("surface")
        barre = UTILS_Interface.GetToken("surface_container_low")
        self.SetBackgroundColour(surface)
        self.barre.SetBackgroundColour(barre)
        for index, bouton in enumerate(self._boutons):
            bouton.AppliquerTheme(index == self._selection)

    def AddPage(self, page, label, bitmap=wx.NullBitmap, select=False):
        if page.GetParent() is not self:
            page.Reparent(self)

        index = len(self._pages)
        self._pages.append(page)
        self.sizer_pages.Add(page, 1, wx.EXPAND)
        page.Hide()

        bouton = BoutonNavigation(self.barre, label, bitmap)
        bouton.Bind(wx.EVT_TOGGLEBUTTON, lambda event, i=index: self.SetSelection(i))
        self._boutons.append(bouton)
        self.sizer_barre.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, _dimension(6))

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

        if rafraichir and ancienne != -1:
            self.MAJ_panel(index)

        if ancienne != -1:
            self._pages[ancienne].Hide()
        self._selection = index
        self._pages[index].Show()

        for numero, bouton in enumerate(self._boutons):
            bouton.AppliquerTheme(numero == index)

        self.Layout()
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

        # Accueil reste toujours accessible ; les autres sections dépendent de
        # l'ouverture d'un fichier métier.
        for index, bouton in enumerate(self._boutons):
            bouton.Enable(True if index == 0 else bool(etat))

    def OnSize(self, event):
        # WrapSizer recalcule le nombre de lignes selon la largeur réelle.
        self.barre.Layout()
        self.Layout()
        event.Skip()
