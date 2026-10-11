#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

from Utils.UTILS_Traduction import _
import wx

from Ctrl import CTRL_Texte
from Utils import UTILS_Styles


class Page(wx.Panel):
    """Page d'accueil de l'assistant contrat.

    Cette première étape doit rassurer et orienter. Elle ne contient donc plus
    de bandeau décoratif massif ni de HTML typographié en dur : la hiérarchie,
    les espacements et les textes suivent le design system Teamworks.
    """

    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.parent = self.GetGrandParent()

        self.label_titre = CTRL_Texte.H1(
            self,
            _(u"Créer un contrat"),
        )
        self.label_intro = CTRL_Texte.Lead(
            self,
            _(u"Teamworks vous guide étape par étape jusqu'au contrat prêt à relire et à imprimer."),
        )
        self.label_reassurance = CTRL_Texte.BodySecondary(
            self,
            _(u"Vous pouvez revenir à l'étape précédente à tout moment. Les contrôles CCNS et SMIC sont effectués pendant la saisie."),
        )

        self.label_avant = CTRL_Texte.H3(self, _(u"Ce parcours va vérifier"))
        self.label_point_identite = CTRL_Texte.BodyLarge(
            self,
            _(u"• les informations du salarié et le type de contrat"),
        )
        self.label_point_regles = CTRL_Texte.BodyLarge(
            self,
            _(u"• la durée du travail, la rémunération et les règles conventionnelles"),
        )
        self.label_point_document = CTRL_Texte.BodyLarge(
            self,
            _(u"• les éléments nécessaires à la génération du document final"),
        )

        self.label_conseil = CTRL_Texte.BodySecondary(
            self,
            _(u"Si vous créez souvent des contrats similaires, vous pourrez partir d'un modèle à l'étape suivante."),
        )

        self.__do_layout()

    def __do_layout(self):
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        section_gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        field_gap = UTILS_Styles.GetLayoutSpacing("field_gap")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_titre, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        sizer.Add(self.label_intro, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        sizer.Add(self.label_reassurance, 0, wx.EXPAND | wx.BOTTOM, section_gap)

        sizer.Add(self.label_avant, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        sizer.Add(self.label_point_identite, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        sizer.Add(self.label_point_regles, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        sizer.Add(self.label_point_document, 0, wx.EXPAND | wx.BOTTOM, section_gap)
        sizer.Add(self.label_conseil, 0, wx.EXPAND)
        sizer.AddStretchSpacer(1)

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(sizer, 1, wx.EXPAND | wx.ALL, page_gap)
        self.SetSizer(outer)

    def Validation(self):
        return True
