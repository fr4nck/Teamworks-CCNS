#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Contrôles texte sémantiques de Teamworks.

Usage proche du Web : Display, H1 à H6, Lead, Body, Label, Caption, etc.
Les propriétés visuelles sont centralisées dans Utils.UTILS_Styles.
"""

import wx

from Utils import UTILS_Styles


class Texte(wx.StaticText):
    def __init__(self, parent, texte=u"", style="body", id=-1, **kwargs):
        wx.StaticText.__init__(self, parent, id, texte, **kwargs)
        self.style_semantique = style
        # Le rôle reste attaché au contrôle : UTILS_Theme peut ainsi
        # recalculer la police depuis sa définition sémantique lors d'un
        # changement d'échelle, sans multiplier une taille déjà agrandie.
        self._teamworks_semantic_text_style = style
        self.AppliquerStyle()

    def AppliquerStyle(self, style=None):
        if style is not None:
            self.style_semantique = style
        self._teamworks_semantic_text_style = self.style_semantique
        UTILS_Styles.AppliquerTexte(self, self.style_semantique)
        return self

    def GetEspacement(self):
        return UTILS_Styles.GetTextSpacing(self.style_semantique)


def Display(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="display", **kwargs)


def H1(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="h1", **kwargs)


def H2(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="h2", **kwargs)


def H3(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="h3", **kwargs)


def H4(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="h4", **kwargs)


def H5(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="h5", **kwargs)


def H6(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="h6", **kwargs)


def Lead(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="lead", **kwargs)


def BodyLarge(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="body-large", **kwargs)


def Body(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="body", **kwargs)


def BodySecondary(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="body-secondary", **kwargs)


def BodySmall(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="body-small", **kwargs)


def Label(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="label", **kwargs)


def Caption(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="caption", **kwargs)


def Micro(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="micro", **kwargs)


def DataLarge(parent, texte=u"", **kwargs):
    return Texte(parent, texte, style="data-large", **kwargs)
