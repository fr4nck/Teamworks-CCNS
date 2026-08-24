#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import Chemins
from Utils import UTILS_Interface
from Utils import UTILS_Styles
from Ctrl import CTRL_Texte
import wx
import wx.html as html


def _html_colour(colour):
    return "#%02X%02X%02X" % (colour.Red(), colour.Green(), colour.Blue())


class MyHtml(html.HtmlWindow):
    """Texte enrichi de bandeau dont la hauteur suit l'échelle de l'UI."""

    def __init__(self, parent, texte="", hauteur=25):
        html.HtmlWindow.__init__(
            self,
            parent,
            -1,
            style=wx.html.HW_NO_SELECTION | wx.html.HW_SCROLLBAR_NEVER | wx.NO_FULL_REPAINT_ON_RESIZE,
        )
        self.SetBorders(0)
        self.hauteur_base = hauteur
        self.SetMinSize((-1, UTILS_Styles.Scale(hauteur, 25)))
        self.SetTexte(texte)

    def SetTexte(self, texte=""):
        fond = UTILS_Interface.GetToken("surface_container_high")
        texte_secondaire = UTILS_Interface.GetToken("on_surface_variant")
        self.SetBackgroundColour(fond)
        self.SetPage(
            u'<BODY BGCOLOR="%s" TEXT="%s"><FONT SIZE=-1>%s</FONT></BODY>'
            % (_html_colour(fond), _html_colour(texte_secondaire), texte)
        )


class Bandeau(wx.Panel):
    """Bandeau métier compact, extensible horizontalement et sans hauteur figée."""

    def __init__(self, parent, titre="", texte="", hauteurHtml=25, nomImage=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)

        if nomImage and "Static" not in nomImage:
            nomImage = Chemins.GetStaticPath(nomImage)

        img = wx.Bitmap(nomImage, wx.BITMAP_TYPE_ANY) if nomImage else wx.NullBitmap
        self.image = wx.StaticBitmap(self, -1, img)
        self.ctrl_titre = CTRL_Texte.H1(self, titre)
        self.ctrl_intro = MyHtml(self, texte, hauteurHtml)
        self.ligne = wx.StaticLine(self, -1)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.AppliquerTheme()

    def AppliquerTheme(self):
        fond = UTILS_Interface.GetToken("surface_container_high")
        bordure = UTILS_Interface.GetToken("outline_variant")

        self.SetBackgroundColour(fond)
        self.ctrl_titre.AppliquerStyle("h1")
        self.ctrl_intro.SetBackgroundColour(fond)
        self.ligne.SetForegroundColour(bordure)

    def __do_layout(self):
        field_gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        content_padding = UTILS_Styles.GetLayoutSpacing("content_padding")

        textes = wx.BoxSizer(wx.VERTICAL)
        textes.Add(self.ctrl_titre, 0, wx.EXPAND | wx.TOP | wx.RIGHT, field_gap)
        textes.Add(self.ctrl_intro, 0, wx.EXPAND | wx.RIGHT | wx.BOTTOM, field_gap)

        contenu = wx.BoxSizer(wx.HORIZONTAL)
        if self.image.GetBitmap().IsOk():
            contenu.Add(self.image, 0, wx.ALL | wx.ALIGN_TOP, content_padding)
        contenu.Add(textes, 1, wx.EXPAND)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(contenu, 0, wx.EXPAND)
        sizer.Add(self.ligne, 0, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()
