#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Teamworks-CCNS
# Origine :         updater historique Teamworks/Noethys
# Licence:          Licence GNU GPL
#------------------------------------------------------------------------

"""Interface de mise à jour de Teamworks-CCNS.

L'updater hérité de Teamworks pointait vers l'ancienne infrastructure
Teamworks/Noethys et supposait des versions strictement numériques. Teamworks-
CCNS ne dispose pas encore d'un protocole d'auto-mise-à-jour validé (canal,
intégrité, téléchargement et relance). Le parcours est donc volontairement
neutralisé : il affiche la version locale canonique et n'effectue aucun accès
réseau ni téléchargement.
"""

import os

import Chemins
from Utils import UTILS_Adaptations  # noqa: F401 - initialise les adaptations wx historiques
from Utils import UTILS_Versions
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Bouton_image


MESSAGE_UPDATER_INDISPONIBLE = (
    "La mise à jour automatique n’est pas encore disponible pour Teamworks-CCNS."
)


def _local_version_paths():
    """Return VERSION locations for frozen installs and source checkouts."""
    packaged_path = Chemins.GetMainPath("VERSION")
    source_root_path = os.path.normpath(
        os.path.join(os.path.dirname(packaged_path), os.pardir, "VERSION")
    )
    if source_root_path == packaged_path:
        return (packaged_path,)
    return packaged_path, source_root_path


class Page_recherche(wx.Panel):
    """Disabled update-search page kept for compatibility with the existing UI."""

    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(
            self,
            parent,
            ID,
            name="page_recherche",
            style=wx.TAB_TRAVERSAL,
        )
        self.parent = parent

        self.label_introduction = wx.StaticText(
            self,
            -1,
            _(u"Cliquez sur le bouton 'Rechercher' pour afficher l'état des mises à jour."),
        )

        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Aide"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"),
        )
        self.bouton_ok = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Rechercher"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Loupe.png"),
        )
        self.bouton_annuler = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Fermer"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"),
        )

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.Onbouton_aide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_ok, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_annuler, self.bouton_annuler)

    def __set_properties(self):
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour vérifier l'état des mises à jour")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour fermer")))

    def __do_layout(self):
        sizer_boutons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        sizer_boutons.AddStretchSpacer(1)
        sizer_boutons.Add(self.bouton_ok, 0, wx.RIGHT, 10)
        sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)

        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.label_introduction, 1, wx.ALL | wx.EXPAND, 10)
        sizer_base.Add(sizer_boutons, 0, wx.ALL | wx.EXPAND, 10)
        self.SetSizer(sizer_base)
        self.Layout()

    def Onbouton_aide(self, event):
        self.parent.Aide()

    def Onbouton_annuler(self, event):
        self.parent.Fermer()

    def Onbouton_ok(self, event):
        self.Recherche()

    def Activation(self):
        pass

    def GetVersionLogiciel(self):
        """Return the local canonical VERSION, or None if it cannot be trusted."""
        return UTILS_Versions.read_first_valid_version(_local_version_paths())

    def ConvertVersionTuple(self, texteVersion=""):
        """Backward-compatible entry point using the CCNS prerelease parser."""
        return UTILS_Versions.parse_version(texteVersion)

    def Recherche(self):
        """Report updater state without contacting the historical services."""
        version_locale = self.GetVersionLogiciel()
        if version_locale is None:
            texte_version = _(u"Version locale : inconnue.")
        else:
            # Parsing here also documents the comparison semantics used by any
            # future CCNS updater implementation.
            self.ConvertVersionTuple(version_locale)
            texte_version = _(u"Version locale : %s.") % version_locale

        self.label_introduction.SetLabel(
            "%s\n\n%s" % (texte_version, _(MESSAGE_UPDATER_INDISPONIBLE))
        )
        self.Layout()


class Dialog(wx.Dialog):
    """Compatibility dialog for the deliberately disabled automatic updater."""

    def __init__(self, parent):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            name="DLG_Updater",
            style=(
                wx.DEFAULT_DIALOG_STYLE
                | wx.RESIZE_BORDER
                | wx.MAXIMIZE_BOX
                | wx.MINIMIZE_BOX
            ),
        )
        self.parent = parent
        self.installation = False
        self.afficher_page_recherche = True

        intro = _(
            u"Teamworks-CCNS n'utilise plus le mécanisme historique de mise à jour Teamworks/Noethys."
        )
        titre = _(u"Mise à jour du logiciel")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(
            self,
            titre=titre,
            texte=intro,
            hauteurHtml=30,
            nomImage=Chemins.GetStaticPath("Images/32x32/Telecharger.png"),
        )

        self.page_active = ""
        self.dictPages = {}

        self.sizer_base = wx.BoxSizer(wx.VERTICAL)
        self.sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        self.Creation_page("page_recherche", Page_recherche)
        self.Active_page("page_recherche")

        self.SetSizer(self.sizer_base)
        self.SetMinSize((600, 360))
        self.SetSize((600, 360))
        self.CentreOnScreen()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def GetEtat(self):
        """No installation can be launched while the updater is disabled."""
        return False

    def Creation_page(self, nomPage="", classe=None):
        page = classe(self)
        self.sizer_base.Add(page, 1, wx.EXPAND, 0)
        page.Show(False)
        self.dictPages[nomPage] = page

    def GetPage(self, nomPage=""):
        return self.dictPages[nomPage]

    def Active_page(self, choixPage=""):
        if self.page_active:
            self.dictPages[self.page_active].Show(False)
        if choixPage:
            self.page_active = choixPage
            self.dictPages[self.page_active].Show(True)
            self.dictPages[self.page_active].Activation()
            self.Layout()

    def Aide(self):
        from Utils import UTILS_Aide

        UTILS_Aide.Aide("Rechercherunemisejourdulogiciel")

    def Fermer(self):
        if self.IsModal():
            self.EndModal(wx.ID_CANCEL)
        else:
            self.Destroy()

    def OnClose(self, event):
        self.Fermer()


if __name__ == "__main__":
    app = wx.App(0)
    frame_1 = Dialog(None)
    app.SetTopWindow(frame_1)
    frame_1.ShowModal()
    frame_1.Destroy()
    app.MainLoop()
