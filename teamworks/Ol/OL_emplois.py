#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ObjectListView Offres d'emploi harmonisé avec la charte Teamworks."""

import wx

from Ol import OL_emplois_core as CORE
from ObjectListView import ColumnDefn
from Utils import UTILS_Dates, UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _


Track = CORE.Track
LISTE_COLONNES_1 = CORE.LISTE_COLONNES_1
Importation_disponibilites = CORE.Importation_disponibilites
Importation_emplois_fonctions = CORE.Importation_emplois_fonctions
Importation_emplois_affectations = CORE.Importation_emplois_affectations
Importation_diffuseurs = CORE.Importation_diffuseurs


class ListView(CORE.ListView):
    def Importation_candidatures(self):
        DB = CORE.GestionDB.DB()
        req = """SELECT IDemploi, COUNT(IDcandidature)
        FROM candidatures
        WHERE IDemploi IS NOT NULL
        GROUP BY IDemploi;"""
        DB.ExecuterReq(req)
        rows = DB.ResultatReq()
        DB.Close()
        CORE.DICT_CANDIDATURES = {IDemploi: nombre for IDemploi, nombre in rows}
        return CORE.DICT_CANDIDATURES

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
            if args == "date":
                colonne = ColumnDefn(labelCol, alignement, largeur, nomChamp, stringConverter=UTILS_Dates.DateEngFr)
            else:
                colonne = ColumnDefn(labelCol, alignement, largeur, nomChamp)
            colonnes.append(colonne)
        self.SetColumns(colonnes)
        if len(self.columns) > 1:
            self.SetSortColumn(self.columns[1])
        self.SetEmptyListMsg(_(u"Aucune offre d'emploi"))
        self.SetEmptyListMsgFont(UTILS_Styles.GetFont("body-secondary"))
        self.SetObjects(self.donnees)

    def Supprimer(self):
        if len(self.Selection()) == 0:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord sélectionner une offre d'emploi à supprimer dans la liste."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False

        try:
            if self.GetGrandParent().GetParent().GetName() == "Recrutement":
                self.GetGrandParent().GetParent().AffichePanelResume(False)
        except Exception:
            pass

        track = self.Selection()[0]
        IDemploi = track.IDemploi
        nom = track.intitule

        # Conserve le garde-fou historique : une offre déjà rattachée à une
        # candidature doit d'abord être détachée explicitement par l'utilisateur.
        DB = CORE.GestionDB.DB()
        DB.ExecuterReq("SELECT IDcandidature FROM candidatures WHERE IDemploi=%d;" % IDemploi)
        candidatures = DB.ResultatReq()
        DB.Close()
        if candidatures:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous avez déjà enregistré %s candidature(s) rattachée(s) à cette offre d'emploi. "
                  u"Vous ne pouvez donc pas la supprimer.") % len(candidatures),
                "Information",
                wx.OK | wx.ICON_ERROR,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False

        dlgConfirm = wx.MessageDialog(
            self,
            _(u"Voulez-vous vraiment supprimer l'offre d'emploi : %s ?") % nom,
            _(u"Confirmation de suppression"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        reponse = dlgConfirm.ShowModal()
        dlgConfirm.Destroy()
        if reponse != wx.ID_YES:
            return False

        DB = CORE.GestionDB.DB()
        placeholder = "%s" if DB.isNetwork else "?"
        try:
            # Les tables dépendantes sont vidées avant l'offre principale et
            # l'ensemble n'est validé qu'une fois toutes les requêtes réussies.
            for table in (
                "emplois_dispo",
                "emplois_fonctions",
                "emplois_affectations",
                "emplois_diffuseurs",
                "emplois",
            ):
                DB.cursor.execute(
                    "DELETE FROM %s WHERE IDemploi=%s" % (table, placeholder),
                    (IDemploi,),
                )
            DB.Commit()
        except Exception as err:
            try:
                DB.connexion.rollback()
            except Exception:
                pass
            DB.Close()
            wx.MessageBox(
                _(u"L'offre d'emploi n'a pas pu être supprimée. Aucune suppression n'a été validée.\n\nDétail technique : %s") % err,
                _(u"Suppression annulée"),
                wx.OK | wx.ICON_ERROR,
            )
            return False
        DB.Close()

        self.MAJ()
        return True

    def OnContextMenu(self, event):
        selection = bool(self.Selection())
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


if __name__ == "__main__":
    app = wx.App(0)
    frame = wx.Frame(None, title=_(u"Offres d'emploi"))
    panel = wx.Panel(frame)
    ctrl = ListView(panel, id=-1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
    ctrl.MAJ()
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(ctrl, 1, wx.EXPAND)
    panel.SetSizer(sizer)
    frame.SetSize((1100, 700))
    frame.Show()
    app.MainLoop()
