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
import datetime
import FonctionsPerso
from Dlg import DLG_Edition_DUE
from Dlg import DLG_Creation_contrat
from Utils import UTILS_Adaptations, UTILS_Contrats_schema
import six


CEE_QUALIFICATION_LABELS = {
    "BAFA_HOLDER": u"BAFA titulaire",
    "BAFA_TRAINEE": u"BAFA stagiaire",
    "UNQUALIFIED": u"Non diplômé",
    "EQUIVALENT": u"Qualification équivalente",
    "BAFD_HOLDER": u"BAFD titulaire",
    "BAFD_TRAINEE": u"BAFD stagiaire",
}


def BuildContractDisplayLabel(IDclassification=None, convention_code=None, ccns_group=None, cee_qualification=None, legacy_labels=None):
    """Libellé neutre pour contrats historiques, CCNS et CEE modernes."""
    legacy_labels = legacy_labels or {}
    if cee_qualification:
        return u"CEE — %s" % CEE_QUALIFICATION_LABELS.get(cee_qualification, cee_qualification)
    if convention_code == "CCNS" and ccns_group:
        return u"CCNS — %s" % ccns_group
    if IDclassification not in (None, ""):
        return legacy_labels.get(IDclassification, u"Classification #%s" % IDclassification)
    if convention_code:
        return six.text_type(convention_code)
    return _(u"Contrat")


def DateEngFr(textDate):
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateFrEng(textDate):
    text = str(textDate[6:10]) + "/" + str(textDate[3:5]) + "/" + str(textDate[:2])
    return text

class Panel_Contrats(wx.Panel):
    def __init__(self, parent, id, IDpersonne=0):
        wx.Panel.__init__(self, parent, id, name="page_contrats", style=wx.TAB_TRAVERSAL)

        self.parent = parent
        self.IDpersonne = IDpersonne

        self.staticBox_contrats_staticbox = wx.StaticBox(self, -1, _(u"Contrats"))
        self.list_ctrl_contrats = ListCtrl_contrats(self, -1)
        self.list_ctrl_contrats.SetMinSize((20, 20))

        self.bouton_contrats_ajouter = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG))
        self.bouton_contrats_modifier = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG))
        self.bouton_contrats_supprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG))
        self.bouton_signature = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Signature.png"), wx.BITMAP_TYPE_PNG))
        self.bouton_due = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Due.png"), wx.BITMAP_TYPE_PNG))
        self.bouton_imprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG))

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.bouton_contrats_ajouter.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour saisir un nouveau contrat")))
        self.bouton_contrats_ajouter.SetSize(self.bouton_contrats_ajouter.GetBestSize())
        self.bouton_contrats_modifier.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour modifier le contrat sélectionné dans la liste")))
        self.bouton_contrats_modifier.SetSize(self.bouton_contrats_modifier.GetBestSize())
        self.bouton_contrats_supprimer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour supprimer le contrat sélectionné dans la liste")))
        self.bouton_contrats_supprimer.SetSize(self.bouton_contrats_supprimer.GetBestSize())
        self.bouton_signature.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour signaler que le contrat est signé ou non")))
        self.bouton_due.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour signaler si la DUE a bien été faite")))
        self.bouton_imprimer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour imprimer un contrat, une DUE, une attestation de travail, etc...")))

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjoutContrat, self.bouton_contrats_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifContrat, self.bouton_contrats_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprContrat, self.bouton_contrats_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSignature, self.bouton_signature)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonDue, self.bouton_due)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimer, self.bouton_imprimer)

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=10)
        staticBox_contrats = wx.StaticBoxSizer(self.staticBox_contrats_staticbox, wx.VERTICAL)
        grid_sizer_contrats = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)

        grid_sizer_contrats.Add(self.list_ctrl_contrats, 1, wx.EXPAND, 0)

        grid_sizer_boutons_contrats = wx.FlexGridSizer(rows=8, cols=1, vgap=5, hgap=5)
        grid_sizer_boutons_contrats.Add(self.bouton_contrats_ajouter, 0, 0, 0)
        grid_sizer_boutons_contrats.Add(self.bouton_contrats_modifier, 0, 0, 0)
        grid_sizer_boutons_contrats.Add(self.bouton_contrats_supprimer, 0, 0, 0)
        grid_sizer_boutons_contrats.Add((10, 10), 0, 0, 0)
        grid_sizer_boutons_contrats.Add(self.bouton_signature, 0, 0, 0)
        grid_sizer_boutons_contrats.Add(self.bouton_due, 0, 0, 0)
        grid_sizer_boutons_contrats.Add((10, 10), 0, 0, 0)
        grid_sizer_boutons_contrats.Add(self.bouton_imprimer, 0, 0, 0)
        grid_sizer_contrats.Add(grid_sizer_boutons_contrats, 1, wx.EXPAND, 0)

        grid_sizer_contrats.AddGrowableRow(0)
        grid_sizer_contrats.AddGrowableCol(0)
        staticBox_contrats.Add(grid_sizer_contrats, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticBox_contrats, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.TOP|wx.EXPAND, 5)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)

    def MAJ_barre_problemes(self):
        if self.IDpersonne in FonctionsPerso.Recherche_ContratsEnCoursOuAVenir():
            self.parent.GetGrandParent().barre_problemes = True
        else:
            self.parent.GetGrandParent().barre_problemes = False
        self.parent.GetGrandParent().MAJ_barre_problemes()

    def OnBoutonAjoutContrat(self, event):
        self.AjouterContrat()
        event.Skip()

    def AjouterContrat(self):
        dlg = DLG_Creation_contrat.Dialog(self, IDcontrat=0, IDpersonne=self.IDpersonne)
        dlg.ShowModal()
        dlg.Destroy()

    def OnBoutonModifContrat(self, event):
        self.ModifierContrat()
        event.Skip()

    def ModifierContrat(self):
        index = self.list_ctrl_contrats.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(self, _(u"Vous devez d'abord sélectionner un contrat à modifier dans la liste."), "Information", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        varIDcontrat = self.list_ctrl_contrats.GetItemData(index)
        dlg = DLG_Creation_contrat.Dialog(self, IDcontrat=varIDcontrat, IDpersonne=self.IDpersonne)
        dlg.ShowModal()
        dlg.Destroy()

    def OnBoutonSupprContrat(self, event):
        self.SupprimerContrat()
        event.Skip()

    def SupprimerContrat(self):
        index = self.list_ctrl_contrats.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(self, _(u"Vous devez d'abord sélectionner un contrat à supprimer dans la liste."), "Information", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        texteContrat = self.list_ctrl_contrats.GetItem(index, 3).GetText()
        txtMessage = six.text_type((_(u"Voulez-vous vraiment supprimer ce contrat ? \n\n> ") + texteContrat))
        dlgConfirm = wx.MessageDialog(self, txtMessage, _(u"Confirmation de suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
        reponse = dlgConfirm.ShowModal()
        dlgConfirm.Destroy()
        if reponse == wx.ID_NO:
            return

        varIDcontrat = self.list_ctrl_contrats.GetItemData(index)
        DB = GestionDB.DB()
        DB.ReqDEL("contrats", "IDcontrat", varIDcontrat)
        DB.Close()
        self.list_ctrl_contrats.Remplissage()
        self.MAJ_barre_problemes()

    def OnBoutonSignature(self, event):
        index = self.list_ctrl_contrats.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(self, _(u"Vous devez d'abord sélectionner un contrat dans la liste."), "Information", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        IDcontrat = self.list_ctrl_contrats.GetItemData(index)
        etatSignature = self.list_ctrl_contrats.GetItem(index, 4).GetText()
        etatSignature = "" if etatSignature == "Oui" else "Oui"
        DB = GestionDB.DB()
        DB.ReqMAJ("contrats", [("signature", etatSignature)], "IDcontrat", IDcontrat)
        DB.Commit()
        DB.Close()
        self.list_ctrl_contrats.SetItem(index, 4, etatSignature)
        self.MAJ_barre_problemes()

    def OnBoutonDue(self, event):
        index = self.list_ctrl_contrats.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(self, _(u"Vous devez d'abord sélectionner un contrat dans la liste."), "Information", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        IDcontrat = self.list_ctrl_contrats.GetItemData(index)
        etatDue = self.list_ctrl_contrats.GetItem(index, 5).GetText()
        etatDue = "" if etatDue == "Oui" else "Oui"
        DB = GestionDB.DB()
        DB.ReqMAJ("contrats", [("due", etatDue)], "IDcontrat", IDcontrat)
        DB.Commit()
        DB.Close()
        self.list_ctrl_contrats.SetItem(index, 5, etatDue)
        self.MAJ_barre_problemes()

    def OnBoutonImprimer(self, event):
        index = self.list_ctrl_contrats.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(self, _(u"Vous devez d'abord sélectionner un contrat dans la liste proposée."), "Information", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        from Dlg import DLG_Selection_type_document
        listeBoutons = [
            (Chemins.GetStaticPath("Images/BoutonsImages/Imprimer_doc_DUE.png"), _(u"Cliquez ici pour imprimer une D.U.E.")),
            (Chemins.GetStaticPath("Images/BoutonsImages/Imprimer_doc_contrat.png"), _(u"Cliquez ici pour imprimer un autre document (Contrat, attestation, etc...)")),
        ]
        dlg = DLG_Selection_type_document.Dialog(self, size=(450, 335), listeBoutons=listeBoutons, type="contrats")
        if dlg.ShowModal() == wx.ID_OK:
            ChoixType = dlg.GetChoix()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return False
        if ChoixType == 1:
            self.ImprimerDUE()
        if ChoixType == 2:
            self.ImprimerContrat()

    def ImprimerContrat(self):
        index = self.list_ctrl_contrats.GetFirstSelected()
        IDcontrat = self.list_ctrl_contrats.GetItemData(index)
        from Utils import UTILS_Publipostage_donnees
        dictDonnees = UTILS_Publipostage_donnees.GetDictDonnees(categorie="contrat", listeID=[IDcontrat])
        from Dlg import DLG_Publiposteur
        dlg = DLG_Publiposteur.Dialog(self, "", dictDonnees=dictDonnees)
        dlg.ShowModal()
        dlg.Destroy()

    def ImprimerDUE(self):
        index = self.list_ctrl_contrats.GetFirstSelected()
        IDcontrat = self.list_ctrl_contrats.GetItemData(index)
        dlg = DLG_Edition_DUE.Dialog(self, IDcontrat=IDcontrat)
        dlg.ShowModal()
        dlg.Destroy()


class ListCtrl_contrats(wx.ListCtrl):
    def __init__(self, parent, id):
        wx.ListCtrl.__init__(self, parent, id, size=(250, -1), style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES|wx.LC_SINGLE_SEL|wx.SUNKEN_BORDER)
        self.parent = parent
        self.IDpersonne = self.GetParent().IDpersonne

        self.InsertColumn(0, _(u"ID"))
        self.SetColumnWidth(0, 0)
        self.InsertColumn(1, _(u"Date de début"))
        self.SetColumnWidth(1, 85)
        self.InsertColumn(2, _(u"Date de fin"))
        self.SetColumnWidth(2, 85)
        self.InsertColumn(3, _(u"Régime / classement"))
        self.SetColumnWidth(3, 220)
        self.InsertColumn(4, _(u"Signé"))
        self.SetColumnWidth(4, 43)
        self.InsertColumn(5, _(u"Due"))
        self.SetColumnWidth(5, 40)

        self.Remplissage()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def Remplissage(self):
        self.Importation_Classifications()
        self.Importation()

        if self.GetItemCount() != 0:
            self.DeleteAllItems()

        index = 0
        for IDcontrat, valeurs in self.DictContrats.items():
            etat, classification, date_debut, date_fin, date_rupture, signature, due = valeurs
            self.InsertItem(index, str(IDcontrat))
            if etat == "Perim":
                item = self.GetItem(index)
                item.SetTextColour("GREY")
                self.SetItem(item)

            self.SetItem(index, 1, DateEngFr(date_debut))
            if date_fin == "2999-01-01":
                date_fin_affichee = _(u"Indétermin.")
            else:
                date_fin_affichee = DateEngFr(date_fin)
            if date_rupture != "":
                date_fin_affichee = DateEngFr(date_rupture) + "-R"
            self.SetItem(index, 2, date_fin_affichee)
            self.SetItem(index, 3, classification)
            self.SetItem(index, 4, signature or "")
            self.SetItem(index, 5, due or "")
            self.SetItemData(index, IDcontrat)
            index += 1

        self.SortItems(self.ColumnSorter)
        nbreItems = self.GetItemCount()
        if nbreItems > 0:
            self.EnsureVisible(nbreItems-1)

    def ColumnSorter(self, key1, key2):
        item1 = self.GetItem(self.FindItem(-1, key1), 1).GetText()
        item2 = self.GetItem(self.FindItem(-1, key2), 1).GetText()
        item1 = DateFrEng(item1)
        item2 = DateFrEng(item2)
        if item1 < item2:
            return -1
        return 1

    def Importation(self):
        self.parent.GetGrandParent().GetParent().contratEnCours = None
        self.parent.GetGrandParent().GetParent().MaJ_header()
        date_jour = datetime.date.today()

        DB = GestionDB.DB()
        UTILS_Contrats_schema.EnsureContractEngineColumns(DB)
        self.DictContrats = {}
        req = """
        SELECT IDcontrat, IDclassification, cee_qualification, convention_code, ccns_group,
               date_debut, date_fin, date_rupture, signature, due
        FROM contrats
        WHERE IDpersonne=%d ORDER BY date_debut;
        """ % self.IDpersonne
        DB.ExecuterReq(req)
        listeContrats = DB.ResultatReq()

        for contrat in listeContrats:
            (IDcontrat, IDclassification, cee_qualification, convention_code, ccns_group,
             date_debut, date_fin, date_rupture, signature, due) = contrat
            classification = BuildContractDisplayLabel(
                IDclassification=IDclassification,
                convention_code=convention_code,
                ccns_group=ccns_group,
                cee_qualification=cee_qualification,
                legacy_labels=self.DictClass,
            )

            date_fin_2 = datetime.date(int(date_fin[:4]), int(date_fin[5:7]), int(date_fin[8:10]))
            reste = str(date_fin_2 - date_jour)
            if reste != "0:00:00":
                jours = int(reste[:reste.index("day")])
                if jours > 0:
                    etat = "Ok"
                    self.parent.GetGrandParent().GetParent().contratEnCours = (classification, date_debut, date_fin, date_rupture)
                    self.parent.GetGrandParent().GetParent().MaJ_header()
                else:
                    etat = "Perim"
            else:
                etat = "Ok"
                self.parent.GetGrandParent().GetParent().contratEnCours = (classification, date_debut, date_fin, date_rupture)
                self.parent.GetGrandParent().GetParent().MaJ_header()

            self.DictContrats[IDcontrat] = (etat, classification, date_debut, date_fin, date_rupture, signature, due)

        DB.Close()

    def Importation_Classifications(self):
        DB = GestionDB.DB()
        self.DictClass = {}
        DB.ExecuterReq("SELECT IDclassification, nom FROM contrats_class")
        listeClassifications = DB.ResultatReq()
        for classification in listeClassifications:
            self.DictClass[classification[0]] = classification[1]
        DB.Close()

    def OnItemActivated(self, event):
        self.parent.ModifierContrat()

    def OnContextMenu(self, event):
        if self.GetFirstSelected() == -1:
            return False
        index = self.GetFirstSelected()
        etatSignature = self.GetItem(index, 4).GetText()
        etatDue = self.GetItem(index, 5).GetText()

        menuPop = UTILS_Adaptations.Menu()
        item = wx.MenuItem(menuPop, 10, _(u"Ajouter"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Ajouter, id=10)

        menuPop.AppendSeparator()
        item = wx.MenuItem(menuPop, 20, _(u"Modifier"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Modifier, id=20)

        item = wx.MenuItem(menuPop, 30, _(u"Supprimer"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Supprimer, id=30)

        menuPop.AppendSeparator()
        txt = _(u"Contrat non signé !") if etatSignature == "Oui" else _(u"Contrat signé !")
        item = wx.MenuItem(menuPop, 40, txt)
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Signature.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Signature, id=40)

        txt = _(u"DUE non faite !") if etatDue == "Oui" else _(u"DUE faite !")
        item = wx.MenuItem(menuPop, 80, txt)
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Due.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Due, id=80)

        menuPop.AppendSeparator()
        item = wx.MenuItem(menuPop, 50, _(u"Imprimer un document"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Imprimer, id=50)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Menu_Ajouter(self, event):
        self.parent.AjouterContrat()

    def Menu_Modifier(self, event):
        self.parent.ModifierContrat()

    def Menu_Supprimer(self, event):
        self.parent.SupprimerContrat()

    def Menu_Signature(self, event):
        self.parent.OnBoutonSignature(None)

    def Menu_Due(self, event):
        self.parent.OnBoutonDue(None)

    def Menu_Imprimer(self, event):
        self.parent.OnBoutonImprimer(None)
