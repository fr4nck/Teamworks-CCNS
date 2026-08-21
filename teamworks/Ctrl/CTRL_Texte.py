#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Contrôles texte sémantiques de Teamworks.

Usage proche des balises HTML : H1, H2, H3, Body, Label et Caption.
Les propriétés visuelles sont centralisées dans Utils.UTILS_Styles.
"""

import wx

from Utils import UTILS_Styles


class Texte(wx.StaticText):
    def __init__(self, parent, texte=u"", style="body", id=-1, **kwargs):
        wx.StaticText.__init__(self, parent, id, texte, **kwargs)
        self.style_semantique = style
        self.AppliquerStyle()

    def AppliquerStyle(self, style=None):
        if style is not None:
            self.style_semantique = style
        UTILS_Styles.AppliquerTexte(self, self.style_semantique)
        return self

    def GetEspacement(self):
        return UTILS_Styles.GetTextSpacing(self.style_semantique)


def H1(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="h1", **kwargs)


def H2(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="h2", **kwargs)


def H3(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="h3", **kwargs)


def Body(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="body", **kwargs)


def BodySecondary(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="body-secondary", **kwargs)


def Label(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="label", **kwargs)


def Caption(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="caption", **kwargs)
