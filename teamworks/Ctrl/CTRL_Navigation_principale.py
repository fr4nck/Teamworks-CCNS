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


class BoutonNavigation(wx.Control):
    """Bouton de section compact, dessiné avec la palette Teamworks.

    Les ``ToggleButton`` natifs ne respectent pas toujours leur couleur sous
    Windows et peuvent absorber la largeur restante dans un ``WrapSizer``.
    Ce contrôle garde donc une géométrie déterministe et un rendu identique
    pour les apparences claire et sombre.
    """

    def __init__(self, parent, label, bitmap=wx.NullBitmap):
        wx.Control.__init__(
            self, parent, -1, name="bouton_navigation_%s" % label.lower(),
            style=wx.BORDER_NONE | wx.WANTS_CHARS,
        )
        self.label = label
        self.bitmap = bitmap if bitmap is not None else wx.NullBitmap
        self._actif = False
        self._survol = False
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self._AjusterTaille()
        self.AppliquerTheme(False)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
        self.Bind(wx.EVT_LEFT_UP, self.OnClick)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def _AjusterTaille(self):
        dc = wx.ClientDC(self)
        dc.SetFont(self.GetFont())
        largeur_texte, hauteur_texte = dc.GetTextExtent(self.label)
        largeur_icone = self.bitmap.GetWidth() if self.bitmap.IsOk() else 0
        hauteur_icone = self.bitmap.GetHeight() if self.bitmap.IsOk() else 0
        espace_icone = _dimension(8) if largeur_icone else 0
        largeur = max(
            largeur_texte + largeur_icone + espace_icone + 2 * _dimension(14),
            _dimension(92, minimum=80),
        )
        hauteur = max(
            hauteur_texte + 2 * _dimension(8),
            hauteur_icone + 2 * _dimension(6),
            _dimension(40, minimum=40),
        )
        self.SetMinSize((largeur, hauteur))
        self.SetMaxSize((largeur, hauteur))

    def SetValue(self, actif):
        self._actif = bool(actif)
        self.Refresh()

    def GetValue(self):
        return self._actif

    def AppliquerTheme(self, actif=False):
        self.SetValue(bool(actif))

    def _Couleurs(self):
        if not self.IsEnabled():
            return (
                UTILS_Interface.GetToken("surface_container_low"),
                UTILS_Interface.GetToken("disabled"),
                UTILS_Interface.GetToken("outline_variant"),
            )
        if self._actif:
            return (
                UTILS_Interface.GetToken("primary_container"),
                UTILS_Interface.GetToken("on_primary_container"),
                UTILS_Interface.GetToken("primary"),
            )
        fond = "surface_container_high" if self._survol else "surface_container_low"
        return (
            UTILS_Interface.GetToken(fond),
            UTILS_Interface.GetToken("on_surface"),
            UTILS_Interface.GetToken("outline_variant"),
        )

    def OnPaint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        fond, texte, contour = self._Couleurs()
        dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour()))
        dc.Clear()
        largeur, hauteur = self.GetClientSize()
        dc.SetPen(wx.Pen(contour, 1))
        dc.SetBrush(wx.Brush(fond))
        dc.DrawRoundedRectangle(0, 0, max(1, largeur), max(1, hauteur), _dimension(5))

        dc.SetFont(self.GetFont())
        dc.SetTextForeground(texte)
        largeur_texte, hauteur_texte = dc.GetTextExtent(self.label)
        largeur_icone = self.bitmap.GetWidth() if self.bitmap.IsOk() else 0
        espace = _dimension(8) if largeur_icone else 0
        largeur_contenu = largeur_icone + espace + largeur_texte
        x = max(_dimension(10), (largeur - largeur_contenu) // 2)
        if self.bitmap.IsOk():
            dc.DrawBitmap(self.bitmap, x, (hauteur - self.bitmap.GetHeight()) // 2, True)
            x += largeur_icone + espace
        dc.DrawText(self.label, x, (hauteur - hauteur_texte) // 2)

    def OnEnter(self, event):
        self._survol = True
        self.Refresh()

    def OnLeave(self, event):
        self._survol = False
        self.Refresh()

    def OnClick(self, event):
        if self.IsEnabled():
            commande = wx.CommandEvent(wx.wxEVT_BUTTON, self.GetId())
            commande.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(commande)

    def OnKeyDown(self, event):
        if event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_SPACE):
            self.OnClick(event)
            return
        event.Skip()


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
        bouton.Bind(wx.EVT_BUTTON, lambda event, i=index: self.SetSelection(i))
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
