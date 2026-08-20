#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
import wx
import GestionDB
from Ctrl import CTRL_Calendrier_tw
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


def _bitmap_titre(nom_image):
    taille = max(18, min(24, int(round(18 * _echelle_interface() / 100.0))))
    bitmap = wx.Bitmap(
        Chemins.GetStaticPath("Images/16x16/%s" % nom_image),
        wx.BITMAP_TYPE_ANY,
    )
    if bitmap.IsOk() and (bitmap.GetWidth() != taille or bitmap.GetHeight() != taille):
        bitmap = wx.Bitmap(
            bitmap.ConvertToImage().Scale(taille, taille, wx.IMAGE_QUALITY_HIGH)
        )
    return bitmap


def _bouton_titre(parent, nom_image, aide):
    bitmap = _bitmap_titre(nom_image)
    bouton = wx.BitmapButton(parent, -1, bitmap, style=wx.BORDER_NONE)
    cote = max(30, bitmap.GetWidth() + 10)
    bouton.SetMinSize((cote, cote))
    bouton.SetToolTip(wx.ToolTip(aide))
    return bouton


class PanelGadget(wx.Panel):
    """Conteneur moderne d'un gadget historique.

    Le contenu métier des gadgets reste inchangé. Seul le chrome est désormais
    un layout wx natif extensible, sans peinture ni sizer à dimensions figées.
    """

    def __init__(self, parent, couleurFondPanel, index, size=wx.DefaultSize):
        wx.Panel.__init__(self, parent, -1, size=size, name="panel_gadget")
        self.index = int(index)
        self.couleurFondPanel = couleurFondPanel

        self.nomGadget = parent.listeGadgets[self.index][0]
        self.paramGadget = parent.listeGadgets[self.index][1]
        self.texteTitre = self.paramGadget["label"]

        # Attributs conservés pour les contenus/configurations historiques.
        self.espaceBord = 0
        self.coinArrondi = 0
        self.hauteurTitre = max(32, int(round(32 * _echelle_interface() / 100.0)))
        self.couleurFondDC = self.couleurFondPanel
        self.couleurFondCadre = (214, 223, 247)
        self.couleurFondTitre = (70, 70, 70)
        self.couleurBord = (70, 70, 70)
        self.couleurDegrade = (130, 190, 235)
        self.couleurTexteTitre = (255, 255, 255)

        self.GetContenu(self.nomGadget)

        self.barre_titre = wx.Panel(self, -1, name="barre_titre_gadget")
        self.titre = wx.StaticText(self.barre_titre, -1, self.texteTitre)
        police = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        police.SetWeight(wx.FONTWEIGHT_BOLD)
        self.titre.SetFont(police)

        self.img_config = _bouton_titre(
            self.barre_titre,
            "Gadget_config.png",
            _(u"Cliquez ici pour accéder aux options de ce gadget"),
        )
        self.img_fermer = _bouton_titre(
            self.barre_titre,
            "Gadget_fermer.png",
            _(u"Cliquez ici pour fermer ce gadget"),
        )
        if self.paramGadget["config"] is False:
            self.img_config.Hide()

        sizer_titre = wx.BoxSizer(wx.HORIZONTAL)
        sizer_titre.Add(self.titre, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
        sizer_titre.Add(self.img_config, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 2)
        sizer_titre.Add(self.img_fermer, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        self.barre_titre.SetSizer(sizer_titre)
        self.barre_titre.SetMinSize((-1, self.hauteurTitre))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.barre_titre, 0, wx.EXPAND)
        sizer.Add(self.contenu, 1, wx.EXPAND | wx.ALL, 6)
        self.SetSizer(sizer)

        self.AppliquerTheme()

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.img_config.Bind(wx.EVT_BUTTON, self.OnConfigGadget)
        self.img_fermer.Bind(wx.EVT_BUTTON, self.OnFermerGadget)

    def AppliquerTheme(self):
        surface = UTILS_Interface.GetToken("surface")
        titre = UTILS_Interface.GetToken("surface_container_high")
        texte = UTILS_Interface.GetToken("on_surface")
        contour = UTILS_Interface.GetToken("outline_variant")

        self.couleurFondDC = (surface.Red(), surface.Green(), surface.Blue())
        self.couleurFondTitre = (titre.Red(), titre.Green(), titre.Blue())
        self.couleurTexteTitre = (texte.Red(), texte.Green(), texte.Blue())
        self.couleurBord = (contour.Red(), contour.Green(), contour.Blue())
        self.couleurDegrade = self.couleurFondTitre

        self.SetBackgroundColour(surface)
        self.barre_titre.SetBackgroundColour(titre)
        self.titre.SetForegroundColour(texte)
        self.img_config.SetBackgroundColour(titre)
        self.img_fermer.SetBackgroundColour(titre)
        self.Refresh()

    def OnSize(self, event):
        self.Layout()
        event.Skip()

    def OnFermerGadget(self, event):
        # Le host AUI masque immédiatement le pane puis persiste l'état hors de
        # l'événement souris afin qu'une écriture SQLite ne fige pas l'interface.
        self.GetParent().Fermer_Gadget(self.nomGadget)

    def OnConfigGadget(self, event):
        self.contenu.Config()

    def SaveConfig(self, parametres=None):
        """Sauvegarde les paramètres du gadget dans la table ``gadgets``."""
        if parametres is None:
            parametres = {}

        for key, valeur in parametres.items():
            self.GetParent().listeGadgets[self.index][1][key] = valeur
            self.paramGadget[key] = valeur

        listeDonnees = []
        dictParametres = {}

        nomGadget = self.GetParent().listeGadgets[self.index][0]
        dictGadget = self.GetParent().listeGadgets[self.index][1]

        for key, valeur in dictGadget.items():
            if key == "label":
                listeDonnees.append(("label", valeur))
            elif key == "taille":
                listeDonnees.append(("taille", str(valeur)))
            elif key == "affichage":
                listeDonnees.append(("affichage", str(valeur)))
            elif key == "ordre":
                listeDonnees.append(("ordre", valeur))
            elif key == "config":
                listeDonnees.append(("config", str(valeur)))
            else:
                dictParametres[key] = valeur

        if dictParametres:
            listeDonnees.append(("parametres", str(dictParametres)))

        DB = GestionDB.DB()
        DB.ReqMAJ("gadgets", listeDonnees, "nom", nomGadget, IDestChaine=True)
        DB.Close()

    def GetContenu(self, nomGadget):
        """Construit le contenu métier correspondant au gadget."""
        if nomGadget == "dossiers_incomplets":
            self.contenu = Gadget_DossiersIncomplets(self)
        elif nomGadget == "horloge":
            self.contenu = Gadget_Horloge(self)
        elif nomGadget == "notes":
            self.contenu = Gadget_BlocNotes(self)
        elif nomGadget == "updater":
            self.contenu = Gadget_Updater(self)
        elif nomGadget == "calendrier":
            self.contenu = Gadget_Calendrier(self)
        else:
            self.contenu = wx.Panel(self)


# --------------------------------------------------------------------------------------------------------------

class Gadget_BlocNotes(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, name="panel_gadget_blocnotes")
        self.parent = parent
        dictParam = self.parent.paramGadget
        if dictParam["multipages"] is True:
            style = wx.TE_MULTILINE | wx.NO_BORDER
        else:
            style = wx.TE_MULTILINE | wx.NO_BORDER | wx.TE_NO_VSCROLL
        self.texte = wx.TextCtrl(self, -1, dictParam["texte"], style=style)
        couleurFond = dictParam["couleur_fond"]
        self.texte.SetBackgroundColour(couleurFond)
        self.parent.couleurFondCadre = couleurFond
        couleurPolice = dictParam["couleur_police"]
        self.texte.SetForegroundColour(couleurPolice)
        font = wx.Font(
            dictParam["taillePolice"],
            dictParam["familyPolice"],
            dictParam["stylePolice"],
            dictParam["weightPolice"],
            False,
            dictParam["nomPolice"],
        )
        self.texte.SetFont(font)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.texte, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

        self.texte.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def OnKillFocus(self, event):
        self.parent.SaveConfig({"texte": self.texte.GetValue()})
        event.Skip()

    def Config(self):
        from Dlg import DLG_Parametres_blocnotes
        dlg = DLG_Parametres_blocnotes.Dialog(None)
        dlg.ShowModal()
        dlg.Destroy()


# ----------------------------------------------------------------------------------------------------------------

class Gadget_DossiersIncomplets(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, name="panel_gadget_dossiersincomplets")
        self.parent = parent
        dictParam = self.parent.paramGadget

        from Ctrl import CTRL_Gadget_pb_personnes as pbPersonnes
        self.tree = pbPersonnes.TreeCtrl(self)

        self.tree.couleurFond = dictParam["couleur_fond"]
        self.tree.couleurPersonne = dictParam["couleurPersonne"]
        self.tree.couleurType = dictParam["couleurType"]
        self.tree.couleurProbleme = dictParam["couleurProbleme"]
        self.tree.couleurTraits = dictParam["couleurTraits"]
        self.tree.expandPersonnes = dictParam["expandPersonnes"]
        self.tree.expandTypes = dictParam["expandTypes"]
        self.parent.couleurFondCadre = dictParam["couleur_fond"]

        self.tree.MAJ_treeCtrl()

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.tree, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

    def Config(self):
        from Dlg import DLG_Parametres_dossiers
        dlg = DLG_Parametres_dossiers.Dialog(None)
        dlg.ShowModal()
        dlg.Destroy()


# ----------------------------------------------------------------------------------------------------------------

class Gadget_Horloge(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, name="panel_gadget_horloge")
        self.parent = parent
        dictParam = self.parent.paramGadget

        import wx.lib.analogclock as clock

        couleurFace = dictParam["couleur_face"]
        couleurFond = dictParam["couleur_fond"]

        self.horloge = clock.AnalogClock(self, size=(160, 160))
        self.horloge.SetBackgroundColour(couleurFond)
        self.parent.couleurFondCadre = couleurFond
        self.horloge.SetFaceFillColour(couleurFace)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.horloge, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

    def Config(self):
        from Dlg import DLG_Parametres_horloge
        dlg = DLG_Parametres_horloge.Dialog(None)
        dlg.ShowModal()
        dlg.Destroy()


# ----------------------------------------------------------------------------------------------------------------

class Gadget_Updater(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, name="panel_gadget_updater")
        self.parent = parent
        couleurFondUpdater = (128, 221, 128)
        self.parent.couleurFondCadre = couleurFondUpdater

        self.texte = wx.StaticText(
            self,
            -1,
            _(u"Une nouvelle version du logiciel est disponible !\n\nCliquez ci-dessous pour la télécharger et l'installer dès maintenant."),
        )
        self.SetBackgroundColour(couleurFondUpdater)

        self.bouton_telecharger = wx.BitmapButton(
            self,
            -1,
            wx.Bitmap(
                Chemins.GetStaticPath("Images/BoutonsImages/Telecharger_L140.png"),
                wx.BITMAP_TYPE_ANY,
            ),
        )
        self.bouton_telecharger.SetMinSize((-1, max(48, int(round(48 * _echelle_interface() / 100.0)))))
        self.bouton_telecharger.SetToolTip(
            wx.ToolTip(_(u"Cliquez ici pour télécharger et installer\nla nouvelle version de TeamWorks"))
        )

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.texte, 1, wx.EXPAND | wx.BOTTOM, 8)
        self.sizer.Add(self.bouton_telecharger, 0, wx.EXPAND)
        self.SetSizer(self.sizer)

        self.Bind(wx.EVT_BUTTON, self.OnBoutonTelecharger, self.bouton_telecharger)

    def Config(self):
        pass

    def OnBoutonTelecharger(self, event):
        topWindow = wx.GetApp().GetTopWindow()
        topWindow.On_outils_updater(None)


# ----------------------------------------------------------------------------------------------------------------------------

class Gadget_Calendrier(CTRL_Calendrier_tw.Panel):
    def __init__(self, parent, ID=-1):
        CTRL_Calendrier_tw.Panel.__init__(
            self,
            parent,
            ID,
            afficheBoutonAnnuel=False,
            afficheAujourdhui=False,
        )
        self.parent = parent
        dictParam = self.GetParent().paramGadget

        self.calendrier.SetBackgroundColour(dictParam["colFond"])
        self.SetBackgroundColour(dictParam["colFond"])
        self.parent.couleurFondCadre = dictParam["colFond"]
        self.calendrier.couleurFond = dictParam["colFond"]
        self.calendrier.couleurNormal = dictParam["colNormal"]
        self.calendrier.couleurWE = dictParam["colWE"]
        self.calendrier.couleurSelect = dictParam["colSelect"]
        self.calendrier.couleurSurvol = dictParam["colSurvol"]
        self.calendrier.couleurFontJours = dictParam["colFontJours"]
        self.calendrier.couleurVacances = dictParam["colVacs"]
        self.calendrier.couleurFontJoursAvecPresents = dictParam["colFontPresents"]
        self.calendrier.couleurFerie = dictParam["colFeries"]

    def Config(self):
        from Dlg import DLG_Parametres_calendrier
        dlg = DLG_Parametres_calendrier.Dialog(None)
        dlg.ShowModal()
        dlg.Destroy()


# --------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, title="", name="frm_gadgets", style=wx.DEFAULT_FRAME_STYLE)
        self.parent = parent
        self.panel = wx.Panel(self, -1)

        couleurFondPanel = UTILS_Interface.GetToken("surface")
        self.panel.SetBackgroundColour(couleurFondPanel)

        # Ce bloc n'est qu'un harnais manuel de développement. PanelGadget
        # attend normalement l'hôte AUI de CTRL_Gadgets_flottants.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddStretchSpacer()
        self.panel.SetSizer(sizer)


if __name__ == "__main__":
    app = wx.App(0)
    frame_1 = MyFrame(None)
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
