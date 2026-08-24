#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ObjectListView Candidats harmonisé avec la charte Teamworks."""

import wx

from Ol import OL_candidats_core as CORE
from ObjectListView import ColumnDefn
from Utils import UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _


Track = CORE.Track
DICT_COORDONNEES = CORE.DICT_COORDONNEES
DICT_QUALIFICATIONS = CORE.DICT_QUALIFICATIONS
DICT_TYPES_DIPLOMES = CORE.DICT_TYPES_DIPLOMES
LISTE_COLONNES = CORE.LISTE_COLONNES


class ListView(CORE.ListView):
    def InitObjectListView(self):
        self.oddRowsBackColor = UTILS_Interface.GetToken("surface_container_lowest")
        self.evenRowsBackColor = UTILS_Interface.GetToken("surface_container_low")
        self.useExpansionColumn = True

        colonnes = []
        for labelCol, alignement, largeur, nomChamp, args, description, affiche, ordre in sorted(
            self.listeColonnes, key=lambda item: item[7]
        ):
            if not affiche:
                continue
            # L'ancien pictogramme de civilité était redondant avec la colonne texte.
            # En mode cases à cocher on garde cependant cette colonne support.
            if args == "image_civilite" and not self.activeCheckBoxes:
                continue
            colonnes.append(ColumnDefn(labelCol, alignement, largeur, nomChamp))

        self.SetColumns(colonnes)
        self.SetEmptyListMsg(_(u"Aucun candidat"))
        self.SetEmptyListMsgFont(UTILS_Styles.GetFont("body-secondary"))
        if self.activeCheckBoxes:
            self.CreateCheckStateColumn(0)
            if len(self.columns) > 3:
                self.SetSortColumn(self.columns[3])
        elif len(self.columns) > 1:
            self.SetSortColumn(self.columns[1])
        self.SetObjects(self.donnees)

    def OnContextMenu(self, event):
        self.DestroyPopup()
        selection = bool(self.Selection())
        self.adresseMail = ""
        if selection:
            ID = self.Selection()[0].IDcandidat
            DB = CORE.GestionDB.DB()
            DB.ExecuterReq(
                "SELECT texte FROM coords_candidats WHERE IDcandidat=%d AND categorie='Email'" % ID
            )
            rows = DB.ResultatReq()
            DB.Close()
            if rows:
                self.adresseMail = rows[0][0]

        menu = wx.Menu()

        def ajouter(label, handler, enabled=True):
            identifiant = wx.NewIdRef()
            item = menu.Append(identifiant, label)
            item.Enable(enabled)
            self.Bind(wx.EVT_MENU, handler, id=identifiant)

        ajouter(_(u"Ajouter"), self.Menu_Ajouter)
        menu.AppendSeparator()
        ajouter(_(u"Modifier"), self.Menu_Modifier, selection)
        ajouter(_(u"Supprimer"), self.Menu_Supprimer, selection)

        if selection and self.adresseMail:
            menu.AppendSeparator()
            ajouter(_(u"Envoyer un email avec l'éditeur intégré"), self._mail_interne)
            ajouter(_(u"Ouvrir le client de messagerie"), self._mail_systeme)

        menu.AppendSeparator()
        ajouter(_(u"Créer un courrier ou un email"), self.Menu_Courrier, selection)
        menu.AppendSeparator()
        ajouter(_(u"Rechercher / filtrer"), self.Menu_Rechercher)
        ajouter(_(u"Afficher tout"), self.Menu_AfficherTout)
        ajouter(_(u"Colonnes et options"), self.Menu_Options)
        menu.AppendSeparator()
        ajouter(_(u"Imprimer"), self.MenuImprimer)
        ajouter(_(u"Exporter en texte"), self.MenuExportTexte)
        ajouter(_(u"Exporter vers Excel"), self.MenuExportExcel)
        menu.AppendSeparator()
        ajouter(_(u"Aide"), self.Menu_Aide)
        self.PopupMenu(menu)
        menu.Destroy()

    def _mail_interne(self, event):
        from Dlg import DLG_Mailer
        dlg = DLG_Mailer.Dialog(self)
        dlg.SetDonnees(
            [{"adresse": self.adresseMail, "pieces": [], "champs": {}}],
            modificationAutorisee=False,
        )
        dlg.ShowModal()
        dlg.Destroy()

    def _mail_systeme(self, event):
        CORE.FonctionsPerso.EnvoyerMail(adresses=[self.adresseMail], sujet="", message="")


if __name__ == "__main__":
    app = wx.App(0)
    frame = wx.Frame(None, title=_(u"Candidats"))
    panel = wx.Panel(frame)
    ctrl = ListView(panel, id=-1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
    ctrl.MAJ()
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(ctrl, 1, wx.EXPAND)
    panel.SetSizer(sizer)
    frame.SetSize((1100, 700))
    frame.Show()
    app.MainLoop()
