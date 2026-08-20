#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
from Utils import UTILS_Colonnes
from Utils import UTILS_Interface
import wx
from Ctrl import CTRL_Bouton_image
from Ol import OL_candidatures
from Ol import OL_entretiens


class Panel(wx.Panel):
    def __init__(self, parent, id=-1, IDpersonne=0):
        wx.Panel.__init__(self, parent, id, name="page_candidatures", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDpersonne = IDpersonne
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.titre_candidatures = self._titre(_(u"Candidatures"))
        self.ctrl_candidatures = OL_candidatures.ListView(
            self,
            id=-1,
            name="OL_candidatures",
            IDpersonne=IDpersonne,
            colorerSalaries=False,
            modeAffichage="sans_nom",
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES,
        )
        self.ctrl_candidatures.SetMinSize((300, 140))
        self.ctrl_candidatures.MAJ()
        self.colonnes_candidatures = UTILS_Colonnes.ColonnesFlexibles(
            self.ctrl_candidatures,
            extensibles=(2, 3, 4, 5, 7),
        )

        self.bouton_candidatures_ajouter = self._bouton(_(u"Ajouter"), "Ajouter.png")
        self.bouton_candidatures_modifier = self._bouton(_(u"Modifier"), "Modifier.png")
        self.bouton_candidatures_supprimer = self._bouton(_(u"Supprimer"), "Supprimer.png")

        self.titre_entretiens = self._titre(_(u"Entretiens"))
        self.ctrl_entretiens = OL_entretiens.ListView(
            self,
            id=-1,
            name="OL_entretiens",
            IDpersonne=IDpersonne,
            colorerSalaries=False,
            modeAffichage="sans_nom",
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES,
        )
        self.ctrl_entretiens.SetMinSize((300, 140))
        self.ctrl_entretiens.MAJ()
        self.colonnes_entretiens = UTILS_Colonnes.ColonnesFlexibles(
            self.ctrl_entretiens,
            extensibles=(3, 4),
        )

        self.bouton_entretiens_ajouter = self._bouton(_(u"Ajouter"), "Ajouter.png")
        self.bouton_entretiens_modifier = self._bouton(_(u"Modifier"), "Modifier.png")
        self.bouton_entretiens_supprimer = self._bouton(_(u"Supprimer"), "Supprimer.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjoutCandidature, self.bouton_candidatures_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifCandidature, self.bouton_candidatures_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprCandidature, self.bouton_candidatures_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjoutEntretien, self.bouton_entretiens_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifEntretien, self.bouton_entretiens_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprEntretien, self.bouton_entretiens_supprimer)

    def _titre(self, label):
        ctrl = wx.StaticText(self, -1, label)
        font = ctrl.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        font.SetPointSize(max(11, font.GetPointSize() + 2))
        ctrl.SetFont(font)
        return ctrl

    def _bouton(self, label, image):
        return CTRL_Bouton_image.CTRL(
            self,
            texte=label,
            cheminImage=Chemins.GetStaticPath("Images/16x16/%s" % image),
            tailleImage=(20, 20),
        )

    def __set_properties(self):
        self.bouton_candidatures_ajouter.SetToolTip(wx.ToolTip(_(u"Saisir une nouvelle candidature")))
        self.bouton_candidatures_modifier.SetToolTip(wx.ToolTip(_(u"Modifier la candidature sélectionnée")))
        self.bouton_candidatures_supprimer.SetToolTip(wx.ToolTip(_(u"Supprimer la candidature sélectionnée")))
        self.bouton_entretiens_ajouter.SetToolTip(wx.ToolTip(_(u"Saisir un nouvel entretien")))
        self.bouton_entretiens_modifier.SetToolTip(wx.ToolTip(_(u"Modifier l'entretien sélectionné")))
        self.bouton_entretiens_supprimer.SetToolTip(wx.ToolTip(_(u"Supprimer l'entretien sélectionné")))

    @staticmethod
    def _barre_actions(*boutons):
        sizer = wx.WrapSizer(wx.HORIZONTAL)
        for bouton in boutons:
            sizer.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, 6)
        return sizer

    def __do_layout(self):
        candidatures = wx.BoxSizer(wx.VERTICAL)
        candidatures.Add(self.titre_candidatures, 0, wx.EXPAND | wx.BOTTOM, 6)
        candidatures.Add(
            self._barre_actions(
                self.bouton_candidatures_ajouter,
                self.bouton_candidatures_modifier,
                self.bouton_candidatures_supprimer,
            ),
            0,
            wx.EXPAND | wx.BOTTOM,
            4,
        )
        candidatures.Add(self.ctrl_candidatures, 1, wx.EXPAND)

        entretiens = wx.BoxSizer(wx.VERTICAL)
        entretiens.Add(self.titre_entretiens, 0, wx.EXPAND | wx.BOTTOM, 6)
        entretiens.Add(
            self._barre_actions(
                self.bouton_entretiens_ajouter,
                self.bouton_entretiens_modifier,
                self.bouton_entretiens_supprimer,
            ),
            0,
            wx.EXPAND | wx.BOTTOM,
            4,
        )
        entretiens.Add(self.ctrl_entretiens, 1, wx.EXPAND)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(candidatures, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(entretiens, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.SetSizer(sizer)

    def OnBoutonAjoutCandidature(self, event):
        self.ctrl_candidatures.Ajouter()

    def OnBoutonModifCandidature(self, event):
        self.ctrl_candidatures.Modifier()

    def OnBoutonSupprCandidature(self, event):
        self.ctrl_candidatures.Supprimer()

    def OnBoutonAjoutEntretien(self, event):
        self.ctrl_entretiens.Ajouter()

    def OnBoutonModifEntretien(self, event):
        self.ctrl_entretiens.Modifier()

    def OnBoutonSupprEntretien(self, event):
        self.ctrl_entretiens.Supprimer()
