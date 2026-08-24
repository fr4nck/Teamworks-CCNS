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
from Utils import UTILS_Adaptations
from Utils import UTILS_Customize
from Utils import UTILS_Interface
import six


def DateEngFr(textDate):
    return str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])


def DateFrEng(textDate):
    return str(textDate[6:10]) + "/" + str(textDate[3:5]) + "/" + str(textDate[:2])


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


def _bouton_action(parent, nom_image):
    taille = max(24, min(32, int(round(24 * _echelle_interface() / 100.0))))
    bitmap = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/%s" % nom_image), wx.BITMAP_TYPE_PNG)
    if bitmap.IsOk() and (bitmap.GetWidth() != taille or bitmap.GetHeight() != taille):
        bitmap = wx.Bitmap(bitmap.ConvertToImage().Scale(taille, taille, wx.IMAGE_QUALITY_HIGH))
    bouton = wx.BitmapButton(parent, -1, bitmap)
    cote = max(36, taille + 12)
    bouton.SetMinSize((cote, cote))
    return bouton


class Panel_Contrats(wx.Panel):
    def __init__(self, parent, id, IDpersonne=0):
        wx.Panel.__init__(self, parent, id, name="page_contrats", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDpersonne = IDpersonne

        self.titre = wx.StaticText(self, -1, _(u"Contrats"))
        police = self.titre.GetFont()
        police.SetWeight(wx.FONTWEIGHT_BOLD)
        police.SetPointSize(max(11, police.GetPointSize() + 2))
        self.titre.SetFont(police)

        self.list_ctrl_contrats = ListCtrl_contrats(self, -1)
        self.list_ctrl_contrats.SetMinSize((320, 180))

        self.bouton_contrats_ajouter = _bouton_action(self, "Ajouter.png")
        self.bouton_contrats_modifier = _bouton_action(self, "Modifier.png")
        self.bouton_contrats_supprimer = _bouton_action(self, "Supprimer.png")
        self.bouton_signature = _bouton_action(self, "Signature.png")
        self.bouton_due = _bouton_action(self, "Due.png")
        self.bouton_imprimer = _bouton_action(self, "Imprimante.png")

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.bouton_contrats_ajouter.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour saisir un nouveau contrat")))
        self.bouton_contrats_modifier.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour modifier le contrat sélectionné dans la liste")))
        self.bouton_contrats_supprimer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour supprimer le contrat sélectionné dans la liste")))
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
        actions = wx.WrapSizer(wx.HORIZONTAL)
        for numero, groupe in enumerate((
            (self.bouton_contrats_ajouter, self.bouton_contrats_modifier, self.bouton_contrats_supprimer),
            (self.bouton_signature, self.bouton_due),
            (self.bouton_imprimer,),
        )):
            if numero:
                actions.AddSpacer(10)
            for bouton in groupe:
                actions.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, 4)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
        sizer.Add(actions, 0, wx.EXPAND | wx.ALL, 8)
        sizer.Add(self.list_ctrl_contrats, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.SetSizer(sizer)

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
        dlgConfirm = wx.MessageDialog(self, txtMessage, _(u"Confirmation de suppression"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
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
        wx.ListCtrl.__init__(
            self,
            parent,
            id,
            style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES | wx.LC_SINGLE_SEL,
        )
        self.parent = parent
        self.IDpersonne = self.GetParent().IDpersonne
        self._ajustement_en_cours = False

        self.InsertColumn(0, _(u"ID"))
        self.InsertColumn(1, _(u"Date de début"))
        self.InsertColumn(2, _(u"Date de fin"))
        self.InsertColumn(3, _(u"Classification"))
        self.InsertColumn(4, _(u"Signé"))
        self.InsertColumn(5, _(u"DUE"))

        self.Remplissage()

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        wx.CallAfter(self.AjusterColonnes)

    def OnSize(self, event):
        wx.CallAfter(self.AjusterColonnes)
        event.Skip()

    def AjusterColonnes(self):
        if self._ajustement_en_cours:
            return
        largeur = self.GetClientSize().GetWidth()
        if largeur <= 120:
            return

        facteur = _echelle_interface() / 100.0
        minimums = [
            0,
            max(100, int(100 * facteur)),
            max(100, int(100 * facteur)),
            max(220, int(220 * facteur)),
            max(58, int(58 * facteur)),
            max(58, int(58 * facteur)),
        ]
        disponible = max(220, largeur - 24)
        fixes = sum(minimums[i] for i in (0, 1, 2, 4, 5))
        minimums[3] = max(minimums[3], disponible - fixes)

        self._ajustement_en_cours = True
        try:
            for index, taille in enumerate(minimums):
                self.SetColumnWidth(index, taille)
        finally:
            self._ajustement_en_cours = False

    def Remplissage(self):
        self.Importation_Classifications()
        self.Importation()

        if self.GetItemCount() != 0:
            self.DeleteAllItems()

        index = 0
        for IDcontrat, valeurs in self.DictContrats.items():
            etat = valeurs[0]
            classification = valeurs[1]
            date_debut = valeurs[2]
            date_fin = valeurs[3]
            date_rupture = valeurs[4]
            signature = valeurs[5]
            due = valeurs[6]

            self.InsertItem(index, str(IDcontrat))
            if etat == "Perim":
                item = self.GetItem(index)
                item.SetTextColour(UTILS_Interface.GetToken("disabled"))
                self.SetItem(item)

            self.SetItem(index, 1, DateEngFr(date_debut))
            if date_fin == "2999-01-01":
                date_fin = _(u"Indétermin.")
            else:
                date_fin = DateEngFr(date_fin)
            if date_rupture != "":
                date_fin = DateEngFr(date_rupture) + "-R"
            self.SetItem(index, 2, date_fin)
            self.SetItem(index, 3, classification)
            self.SetItem(index, 4, signature)
            self.SetItem(index, 5, "" if due is None else due)
            self.SetItemData(index, IDcontrat)
            index += 1

        self.SortItems(self.ColumnSorter)
        nbreItems = self.GetItemCount()
        if nbreItems > 0:
            self.EnsureVisible(nbreItems - 1)
        wx.CallAfter(self.AjusterColonnes)

    def ColumnSorter(self, key1, key2):
        item1 = self.GetItem(self.FindItem(-1, key1), 1).GetText()
        item2 = self.GetItem(self.FindItem(-1, key2), 1).GetText()
        item1 = DateFrEng(item1)
        item2 = DateFrEng(item2)
        return -1 if item1 < item2 else 1

    def Importation(self):
        self.parent.GetGrandParent().GetParent().contratEnCours = None
        self.parent.GetGrandParent().GetParent().MaJ_header()

        date_jour = datetime.date.today()
        DB = GestionDB.DB()
        self.DictContrats = {}
        req = """
        SELECT IDcontrat, IDclassification, date_debut, date_fin, date_rupture, signature, due
        FROM contrats
        WHERE IDpersonne=%d ORDER BY date_debut;
        """ % self.IDpersonne
        DB.ExecuterReq(req)
        listeContrats = DB.ResultatReq()

        for contrat in listeContrats:
            IDcontrat = contrat[0]
            classification = self.DictClass[contrat[1]]
            date_debut = contrat[2]
            date_fin = contrat[3]
            date_rupture = contrat[4]
            signature = contrat[5]
            due = contrat[6]
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
        req = """
        SELECT IDclassification, nom
        FROM contrats_class
        """
        DB.ExecuterReq(req)
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
