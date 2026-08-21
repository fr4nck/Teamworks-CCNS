#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
from Utils import UTILS_Adaptations
from Utils import UTILS_Interface
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau
from Ol import OL_Feries


def _dip(window, width, height):
    """Convertit une taille logique en pixels en respectant le DPI natif."""
    try:
        return window.FromDIP(wx.Size(width, height))
    except Exception:
        return wx.Size(width, height)


def _section_title(parent, label):
    ctrl = wx.StaticText(parent, -1, label)
    font = ctrl.GetFont()
    font.SetWeight(wx.FONTWEIGHT_BOLD)
    font.SetPointSize(max(10, font.GetPointSize() + 1))
    ctrl.SetFont(font)
    ctrl.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))
    return ctrl


class Panel(wx.Panel):
    def __init__(self, parent, type="fixe"):
        wx.Panel.__init__(self, parent, id=-1, name="panel_feries", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.type = type
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))

        self.label_titre = _section_title(self, _(u"Jours %ss") % self.type)
        self.ctrl_listview = OL_Feries.ListView(
            self,
            type=self.type,
            id=-1,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES,
        )
        self.ctrl_listview.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        self.ctrl_listview.MAJ()
        self.ctrl_recherche = OL_Feries.CTRL_Outils(self, listview=self.ctrl_listview)

        self.bouton_ajouter = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Ajouter"), cheminImage="Images/32x32/Ajouter.png"
        )
        self.bouton_modifier = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Modifier"), cheminImage="Images/32x32/Modifier.png"
        )
        self.bouton_supprimer = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Supprimer"), cheminImage="Images/32x32/Supprimer.png"
        )

        self.bouton_ajouter.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour ajouter un jour férié %s") % self.type))
        self.bouton_modifier.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour modifier le jour férié %s sélectionné dans la liste") % self.type))
        self.bouton_supprimer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour supprimer le jour férié %s sélectionné dans la liste") % self.type))

        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.Ajouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.Modifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.Supprimer, self.bouton_supprimer)

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.label_titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer_base.Add(self.ctrl_listview, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer_base.Add(self.ctrl_recherche, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        sizer_actions = wx.WrapSizer(wx.HORIZONTAL)
        sizer_actions.Add(self.bouton_ajouter, 0, wx.RIGHT | wx.BOTTOM, 6)
        sizer_actions.Add(self.bouton_modifier, 0, wx.RIGHT | wx.BOTTOM, 6)
        sizer_actions.Add(self.bouton_supprimer, 0, wx.RIGHT | wx.BOTTOM, 6)
        sizer_base.Add(sizer_actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        self.SetSizer(sizer_base)

    def Ajouter(self, event):
        self.ctrl_listview.Ajouter(None)

    def Modifier(self, event):
        self.ctrl_listview.Modifier(None)

    def Supprimer(self, event):
        self.ctrl_listview.Supprimer(None)


class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        )
        self.parent = parent
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        intro = _(u"Vous pouvez ici saisir, modifier ou supprimer des jours fériés. Ces informations sont utilisées dans le calendrier de saisie des consommations et dans le paramétrage des unités des activités.")
        titre = _(u"Gestion des jours fériés")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(
            self,
            titre=titre,
            texte=intro,
            hauteurHtml=30,
            nomImage=Chemins.GetStaticPath("Images/32x32/Jour.png"),
        )
        self.panel_variables = Panel(self, type="variable")
        self.panel_fixes = Panel(self, type="fixe")

        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Aide"), cheminImage="Images/32x32/Aide.png"
        )
        self.bouton_saisie_auto = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Génération auto. des jours variables"),
            cheminImage="Images/32x32/Magique.png",
        )
        self.bouton_fermer = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_CANCEL,
            texte=_(u"Fermer"),
            cheminImage="Images/32x32/Fermer.png",
        )

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSaisieAuto, self.bouton_saisie_auto)

    def __set_properties(self):
        self.SetTitle(_(u"Gestion des jours fériés"))
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour obtenir de l'aide")))
        self.bouton_saisie_auto.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour saisir automatiquement les jours fériés variables")))
        self.bouton_fermer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour fermer")))
        self.SetMinSize(_dip(self, 680, 620))
        self.SetSize(_dip(self, 860, 760))

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND)

        sizer_contenu = wx.BoxSizer(wx.HORIZONTAL)
        sizer_contenu.Add(self.panel_variables, 1, wx.EXPAND | wx.RIGHT, 6)
        sizer_contenu.Add(self.panel_fixes, 1, wx.EXPAND | wx.LEFT, 6)
        sizer_base.Add(sizer_contenu, 1, wx.EXPAND | wx.ALL, 12)

        sizer_boutons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_boutons.Add(self.bouton_aide, 0, wx.RIGHT, 8)
        sizer_boutons.Add(self.bouton_saisie_auto, 0, wx.RIGHT, 8)
        sizer_boutons.AddStretchSpacer(1)
        sizer_boutons.Add(self.bouton_fermer, 0)
        sizer_base.Add(sizer_boutons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        self.SetSizer(sizer_base)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Joursfris")

    def OnBoutonSaisieAuto(self, event):
        from Dlg import DLG_Saisie_feries_auto
        dlg = DLG_Saisie_feries_auto.MyDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            self.panel_variables.ctrl_listview.MAJ()
        dlg.Destroy()


if __name__ == "__main__":
    app = wx.App(0)
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
