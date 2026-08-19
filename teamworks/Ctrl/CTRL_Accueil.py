#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

from Utils.UTILS_Traduction import _
import wx

import wx.html as html
import wx.lib.wxpTag
import GestionDB
from Utils import UTILS_Branding
from Utils import UTILS_Config
from Utils import UTILS_Fichiers


# Liste des gadgets par défaut
LISTEGADGETSDEFAUT = [
    ["dossiers_incomplets", {"label": _(u"Dossiers incomplets"), "taille": (200, 200), "affichage": True, "config": False}],
    ["horloge", {"label": _(u"Horloge"), "taille": (200, 200), "affichage": True, "config": True, "couleur_face": (214, 223, 247)}],
    ["calendrier", {"label": _(u"Calendrier"), "taille": (200, 200), "affichage": True, "config": True}],
    ["updater", {"label": _(u"Mises à jour internet"), "taille": (200, 200), "affichage": True, "config": False}],
    ["notes", {"label": _(u"Bloc-notes"), "taille": (200, 200), "affichage": True, "config": True, "texte": _(u"Hello !"), "taillePolice": 10, "familyPolice": 74, "stylePolice": 90, "weightPolice": 90, "nomPolice": "Segoe Print"}],
]


def ImportListeGadgets():
    """Récupération des données de la table GADGETS."""
    DB = GestionDB.DB()
    req = "SELECT * FROM gadgets ORDER BY ordre;"
    DB.ExecuterReq(req)
    listeGadgetsTmp = DB.ResultatReq()
    DB.Close()

    listeGadgets = []
    for IDgadget, nom, label, description, taille, affichage, ordre, config, parametres in listeGadgetsTmp:
        dictTmp = {
            "nom": nom,
            "label": label,
            "taille": eval(taille),
            "affichage": eval(affichage),
            "ordre": ordre,
            "config": eval(config),
        }
        if parametres is not None and parametres != "":
            dictTmpParam = eval(parametres)
            for key, valeur in dictTmpParam.items():
                dictTmp[key] = valeur
        listeGadgets.append([nom, dictTmp])
    return listeGadgets


def MajTableGadgets(nomGadget="", parametres={}):
    """Enregistre les modifications de paramètres d'un gadget."""
    listeDonnees = []
    dictParametres = {}

    for key, valeur in parametres.items():
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
        listeDonnees.append(("parametres", str(list(dictParametres.values())[0])))

    DB = GestionDB.DB()
    DB.ReqMAJ("gadgets", listeDonnees, "nom", nomGadget, IDestChaine=True)
    DB.Close()


class MyHtmlWindow(html.HtmlWindow):
    def __init__(self, parent, id, listeGadgets):
        html.HtmlWindow.__init__(self, parent, id, style=wx.NO_FULL_REPAINT_ON_RESIZE)
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()

        self.couleur_fond = self.GetParent().couleur_fond
        self.listeGadgets = listeGadgets

    def OnLinkClicked(self, linkinfo):
        super(MyHtmlWindow, self).OnLinkClicked(linkinfo)

    def OnCellMouseHover(self, cell, x, y):
        super(MyHtmlWindow, self).OnCellMouseHover(cell, x, y)

    def OnCellClicked(self, cell, x, y, evt):
        if isinstance(cell, html.HtmlWordCell):
            html.HtmlSelection()
        super(MyHtmlWindow, self).OnCellClicked(cell, x, y, evt)
        return True

    def Alignement(self, c):
        """Aligne tous les gadgets en haut."""
        while c:
            if isinstance(c, html.HtmlContainerCell):
                c.SetAlignVer(0)
                self.Alignement(c.GetFirstChild())
            c = c.GetNext()

    def MAJ(self):
        source = self.Source()
        self.SetPage(source)
        self.Alignement(c=self.GetInternalRepresentation())
        self.SendSizeEvent()

    def Efface(self):
        txt = "<html><head><title>Page accueil</title></head><body bgcolor='%s'></body></html>" % self.ConvertitCouleur(self.couleur_fond)
        self.SetPage(txt)

    def Source(self):
        txtGadgets = ""
        index = 0
        for nomGadget, parametres in self.listeGadgets:
            if parametres["affichage"] is True:
                txtGadgets += """
                <wxp module="Gadget" class="PanelGadget" width=%d height=%d >
                    <param name="couleurFondPanel" value="%s">
                    <param name="index" value="%d">
                </wxp> """ % (
                    parametres["taille"][0],
                    parametres["taille"][1],
                    str(self.couleur_fond),
                    index,
                )
            index += 1

        return """
        <html>
        <head><title>Page accueil</title></head>
        <body bgcolor="%s">%s</body>
        </html>
        """ % (self.ConvertitCouleur(self.couleur_fond), txtGadgets)

    def ConvertitCouleur(self, couleur):
        return "#%02X%02X%02X" % couleur

    def Fermer_Gadget(self, nomGadgetAFermer):
        index = 0
        for nomGadget, parametres in self.listeGadgets:
            if nomGadget == nomGadgetAFermer:
                self.listeGadgets[index][1]["affichage"] = False
            index += 1
        self.MAJ()

    def Ouvre_Gadget(self, nomGadgetAOuvrir):
        index = 0
        for nomGadget, parametres in self.listeGadgets:
            if nomGadget == nomGadgetAOuvrir:
                self.listeGadgets[index][1]["affichage"] = True
            index += 1
        self.MAJ()


class BrandingFooter(wx.Panel):
    """Identité discrète de l'application et de l'organisation utilisatrice."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        palette = UTILS_Branding.GetHomeColours()
        self.SetBackgroundColour(palette["background"])

        row = wx.BoxSizer(wx.HORIZONTAL)
        row.AddStretchSpacer()

        wordmark = UTILS_Branding.BuildWordmark(self)
        row.Add(wordmark, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 18)

        logo_path = UTILS_Branding.GetAssociationLogoPath()
        logo_bitmap = UTILS_Branding.LoadScaledBitmap(logo_path, 180, 58)
        if logo_bitmap.IsOk():
            association = wx.StaticBitmap(self, bitmap=logo_bitmap)
            association.SetToolTip("Logo de l'organisation utilisatrice")
            row.Add(association, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 18)

        credit = wx.StaticText(self, label=UTILS_Branding.APPLICATION_CREDIT)
        credit.SetForegroundColour(palette["muted"])
        row.Add(credit, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)

        self.SetSizer(row)


class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, name="panel_accueil", style=wx.NO_FULL_REPAINT_ON_RESIZE)
        palette = UTILS_Branding.GetHomeColours()
        self.couleur_fond = palette["background"]
        self.SetBackgroundColour(self.couleur_fond)

        self.listeGadgets = self.GetListeGadgets()

        self.html = MyHtmlWindow(self, -1, self.listeGadgets)
        self.footer = BrandingFooter(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.html, 1, wx.EXPAND)
        sizer.Add(self.footer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 8)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)

        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnSize(self, event):
        event.Skip()

    def MAJ_Gadgets(self):
        self.Freeze()
        self.listeGadgets = self.GetListeGadgets()
        self.html.listeGadgets = self.listeGadgets
        self.html.MAJ()
        self.Thaw()

    def MAJpanel(self, listeElements=[]):
        if "exemple" in listeElements or listeElements == []:
            self.MAJ_Gadgets()

    def GetListeGadgets(self):
        listeGadgets = ImportListeGadgets()

        if self.GetGrandParent().MAJexiste is True:
            affichage = True
        else:
            affichage = False
        index = 0
        for gadget in listeGadgets:
            if gadget[0] == "updater":
                listeGadgets[index][1]["affichage"] = affichage
            index += 1

        return listeGadgets


class AffichageGadgets():
    """Boîte de dialogue d'affichage des gadgets pour barre de menus."""

    def __init__(self, parent):
        self.listeGadgets = ImportListeGadgets()

    def dialogue(self):
        listeNoms = []
        preSelection = []
        index = 0
        for nomGadget, parametres in self.listeGadgets:
            listeNoms.append(parametres["label"])
            if parametres["affichage"] is True:
                preSelection.append(index)
            index += 1

        message = _(u"Sélectionnez les gadgets que vous souhaitez afficher sur votre page d'accueil")
        dlg = wx.MultiChoiceDialog(None, message, _(u"Affichage des gadgets"), listeNoms, wx.CHOICEDLG_STYLE)
        dlg.SetSelections(preSelection)

        if dlg.ShowModal() == wx.ID_OK:
            resultats = dlg.GetSelections()
            for index in range(len(self.listeGadgets)):
                self.listeGadgets[index][1]["affichage"] = index in resultats

            try:
                topWindow = wx.GetApp().GetTopWindow()
                nomWindow = topWindow.GetName()
            except Exception:
                nomWindow = None
            if nomWindow == "general":
                cfg = topWindow.userConfig
                cfg["listeGadgets"] = self.listeGadgets
            else:
                cfg = UTILS_Config.FichierConfig(nomFichier=UTILS_Fichiers.GetRepUtilisateur("Config.dat"))
                cfg.SetItemConfig("listeGadgets", self.listeGadgets)

            dlg.Destroy()
            return True

        dlg.Destroy()
        return False


class MyFrame(wx.Frame):
    """Frame de test."""

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, title="", name="frm_accueil", style=wx.DEFAULT_FRAME_STYLE)
        self.parent = parent
        self.panel = Panel(self)


if __name__ == "__main__":
    app = wx.App(0)
    frame_1 = MyFrame(None)
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
