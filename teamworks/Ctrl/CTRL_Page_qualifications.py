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
from Utils import UTILS_Adaptations, UTILS_Interface
from Ctrl import CTRL_Bouton_image
from Dlg import DLG_Saisie_piece
import GestionDB
import datetime
import six


def DateEngFr(textDate):
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text


def DateFrEng(textDate):
    text = str(textDate[6:10]) + "/" + str(textDate[3:5]) + "/" + str(textDate[:2])
    return text


def _section_title(parent, label):
    ctrl = wx.StaticText(parent, -1, label)
    font = ctrl.GetFont()
    font.SetWeight(wx.FONTWEIGHT_BOLD)
    font.SetPointSize(max(10, font.GetPointSize() + 1))
    ctrl.SetFont(font)
    ctrl.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))
    return ctrl


class Panel_Statut(wx.Panel):
    def __init__(self, parent, id, IDpersonne=0):
        wx.Panel.__init__(self, parent, id, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDpersonne = IDpersonne
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.titre_pieces = _section_title(self, _(u"Pièces à fournir"))
        self.titre_diplomes = _section_title(self, _(u"Qualifications"))
        self.titre_dossier = _section_title(self, _(u"Pièces reçues"))

        self.list_ctrl_diplomes = ListCtrl_Diplomes(self, -1)
        self.list_ctrl_pieces = ListCtrl_Pieces(self, -1)
        self.list_ctrl_dossier = ListCtrl_Dossier(self, -1)

        for ctrl in (self.list_ctrl_diplomes, self.list_ctrl_pieces, self.list_ctrl_dossier):
            ctrl.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
            ctrl.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))

        self.bouton_diplomes_modifier = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Modifier les qualifications"), cheminImage="Images/32x32/Modifier.png"
        )
        self.bouton_dossier_ajouter = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Ajouter une pièce"), cheminImage="Images/32x32/Ajouter.png"
        )
        self.bouton_dossier_modifier = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Modifier"), cheminImage="Images/32x32/Modifier.png"
        )
        self.bouton_dossier_supprimer = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Supprimer"), cheminImage="Images/32x32/Supprimer.png"
        )

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.bouton_diplomes_modifier.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour modifier cette liste")))
        self.list_ctrl_pieces.SetToolTip(wx.ToolTip(_(u"Liste des pièces que la personne doit fournir. \n\nAstuce : Double-cliquez sur une ligne pour créer directement \nune pièce du type sélectionné dans la liste")))
        self.list_ctrl_diplomes.SetToolTip(wx.ToolTip(_(u"Cliquez sur le bouton 'Modifier les qualifications' pour modifier cette liste")))
        self.bouton_dossier_ajouter.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour saisir une nouvelle pièce")))
        self.bouton_dossier_modifier.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour modifier la pièce sélectionnée dans la liste")))
        self.bouton_dossier_supprimer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour supprimer la pièce sélectionnée")))

        self.Bind(wx.EVT_BUTTON, self.OnBouton_Diplomes, self.bouton_diplomes_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjoutPiece, self.bouton_dossier_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifPiece, self.bouton_dossier_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprPiece, self.bouton_dossier_supprimer)

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_haut = wx.BoxSizer(wx.HORIZONTAL)

        sizer_pieces = wx.BoxSizer(wx.VERTICAL)
        sizer_pieces.Add(self.titre_pieces, 0, wx.BOTTOM, 6)
        sizer_pieces.Add(self.list_ctrl_pieces, 1, wx.EXPAND)
        sizer_haut.Add(sizer_pieces, 1, wx.EXPAND | wx.RIGHT, 8)

        sizer_diplomes = wx.BoxSizer(wx.VERTICAL)
        sizer_diplomes.Add(self.titre_diplomes, 0, wx.BOTTOM, 6)
        sizer_diplomes.Add(self.list_ctrl_diplomes, 1, wx.EXPAND)
        sizer_diplomes.Add(self.bouton_diplomes_modifier, 0, wx.TOP, 8)
        sizer_haut.Add(sizer_diplomes, 1, wx.EXPAND | wx.LEFT, 8)

        sizer_base.Add(sizer_haut, 1, wx.EXPAND | wx.ALL, 12)

        sizer_dossier = wx.BoxSizer(wx.VERTICAL)
        sizer_dossier.Add(self.titre_dossier, 0, wx.BOTTOM, 6)
        sizer_dossier.Add(self.list_ctrl_dossier, 1, wx.EXPAND)
        sizer_actions = wx.WrapSizer(wx.HORIZONTAL)
        sizer_actions.Add(self.bouton_dossier_ajouter, 0, wx.RIGHT | wx.TOP, 6)
        sizer_actions.Add(self.bouton_dossier_modifier, 0, wx.RIGHT | wx.TOP, 6)
        sizer_actions.Add(self.bouton_dossier_supprimer, 0, wx.RIGHT | wx.TOP, 6)
        sizer_dossier.Add(sizer_actions, 0, wx.EXPAND | wx.TOP, 2)
        sizer_base.Add(sizer_dossier, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        self.SetSizer(sizer_base)

    def MAJ_barre_problemes(self):
        self.parent.GetGrandParent().MAJ_barre_problemes()

    def OnBouton_Diplomes(self, event):
        """ Boîte de dialogue pour choisir les diplômes """
        resultat = ""
        titre = _(u"Sélection des qualifications")

        DB = GestionDB.DB()
        req = "SELECT IDtype_diplome, nom_diplome FROM types_diplomes ORDER BY nom_diplome"
        DB.ExecuterReq(req)
        donnees = DB.ResultatReq()
        DB.Close()

        dictDiplomes = {}
        listeNoms = []
        preSelection = []
        TypesDiplomesPerso = []
        index = 0
        for diplome in donnees:
            ID = diplome[0]
            nom = diplome[1]
            dictDiplomes[index] = ID
            listeNoms.append(nom)
            if ID in self.list_ctrl_diplomes.listeDiplomes:
                preSelection.append(index)
                TypesDiplomesPerso.append(ID)
            index += 1
        message = _(u"Sélectionnez les qualifications que possède la personne dans la liste proposée :")
        dlg = wx.MultiChoiceDialog(self, message, titre, listeNoms, wx.CHOICEDLG_STYLE)
        dlg.SetSelections(preSelection)

        if dlg.ShowModal() == wx.ID_OK:
            resultat = dlg.GetSelections()
        else:
            return
        dlg.Destroy()

        listeAEnregistrer = []
        for diplome in resultat:
            IDtype_diplome = dictDiplomes[diplome]
            if IDtype_diplome in TypesDiplomesPerso:
                TypesDiplomesPerso.remove(IDtype_diplome)
            else:
                listeAEnregistrer.append(IDtype_diplome)

        if len(listeAEnregistrer) != 0:
            DB = GestionDB.DB()
            for IDtype in listeAEnregistrer:
                DB.ExecuterReq("INSERT INTO diplomes (IDpersonne, IDtype_diplome) VALUES (%d, %d)" % (self.IDpersonne, IDtype))
            DB.Commit()
            DB.Close()

        if len(TypesDiplomesPerso) != 0:
            DB = GestionDB.DB()
            for IDtype in TypesDiplomesPerso:
                DB.ExecuterReq("DELETE FROM diplomes WHERE IDpersonne=%d AND IDtype_diplome=%d" % (self.IDpersonne, IDtype))
            DB.Commit()
            DB.Close()

        self.list_ctrl_diplomes.Remplissage()
        self.list_ctrl_pieces.Remplissage()
        self.MAJ_barre_problemes()

    def OnBoutonAjoutPiece(self, event):
        self.AjouterPiece()
        event.Skip()

    def AjouterPiece(self, IDtypePiece=None):
        dlg = DLG_Saisie_piece.Dialog(self, -1, IDpiece=0, IDpersonne=self.IDpersonne, IDtypePiece=IDtypePiece)
        dlg.ShowModal()
        dlg.Destroy()

    def OnBoutonModifPiece(self, event):
        self.ModifierPiece()
        event.Skip()

    def ModifierPiece(self):
        """ Modification de coordonnées """
        index = self.list_ctrl_dossier.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(self, _(u"Vous devez d'abord sélectionner une pièce à modifier dans la liste."), "Information", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        varIDpiece = self.list_ctrl_dossier.GetItemData(index)
        dlg = DLG_Saisie_piece.Dialog(self, -1, IDpiece=varIDpiece, IDpersonne=self.IDpersonne)
        dlg.ShowModal()
        dlg.Destroy()

    def OnBoutonSupprPiece(self, event):
        self.SupprimerPiece()
        event.Skip()

    def SupprimerPiece(self):
        """ Suppression d'une coordonnée """
        index = self.list_ctrl_dossier.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(self, _(u"Vous devez d'abord sélectionner une pièce à supprimer dans la liste."), "Information", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        textePiece = self.list_ctrl_dossier.GetItemText(index)
        txtMessage = six.text_type((_(u"Voulez-vous vraiment supprimer cette pièce ? \n\n> ") + textePiece))
        dlgConfirm = wx.MessageDialog(self, txtMessage, _(u"Confirmation de suppression"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        reponse = dlgConfirm.ShowModal()
        dlgConfirm.Destroy()
        if reponse == wx.ID_NO:
            return

        varIDpiece = self.list_ctrl_dossier.GetItemData(index)
        DB = GestionDB.DB()
        DB.ReqDEL("pieces", "IDpiece", varIDpiece)
        DB.Close()

        self.list_ctrl_dossier.Remplissage()
        self.list_ctrl_pieces.Remplissage()
        self.MAJ_barre_problemes()


class ListCtrl_Diplomes(wx.ListCtrl):
    def __init__(self, parent, id):
        wx.ListCtrl.__init__(self, parent, id, style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL)
        self.parent = parent
        self.IDpersonne = self.GetParent().IDpersonne
        self.InsertColumn(0, _(u"Qualification"))
        self.Remplissage()
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def Remplissage(self):
        self.Importation()
        if self.GetItemCount() != 0:
            self.DeleteAllItems()
        index = 0
        for key, valeurs in self.DictDiplomes.items():
            IDtype_diplome = valeurs[0]
            self.listeDiplomes.append(IDtype_diplome)
            nom_diplome = valeurs[1]
            self.InsertItem(index, nom_diplome)
            self.SetItemData(index, key)
            index += 1
        self.SortItems(self.ColumnSorter)

    def ColumnSorter(self, key1, key2):
        item1 = self.DictDiplomes[key1][1]
        item2 = self.DictDiplomes[key2][1]
        if item1 < item2:
            return -1
        return 1

    def Importation(self):
        self.DictDiplomes = {}
        self.listeDiplomes = []
        DB = GestionDB.DB()
        req = "SELECT IDdiplome, diplomes.IDtype_diplome, nom_diplome FROM diplomes, types_diplomes WHERE diplomes.IDtype_diplome=types_diplomes.IDtype_diplome and IDpersonne=%d" % self.IDpersonne
        DB.ExecuterReq(req)
        donnees = DB.ResultatReq()
        DB.Close()
        for ligne in donnees:
            index = ligne[0]
            self.DictDiplomes[index] = (ligne[1], ligne[2])

    def OnSize(self, event):
        width = max(80, self.GetClientSize().width - 8)
        self.SetColumnWidth(0, width)
        event.Skip()

    def OnContextMenu(self, event):
        if self.GetFirstSelected() == -1:
            return False
        menuPop = UTILS_Adaptations.Menu()
        item = wx.MenuItem(menuPop, 10, _(u"Modifier"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Modifier, id=10)
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Menu_Modifier(self, event):
        index = self.GetFirstSelected()
        key = self.GetItemData(index)
        print("Modifier le num : ", key)


class ListCtrl_Pieces(wx.ListCtrl):
    def __init__(self, parent, id):
        wx.ListCtrl.__init__(self, parent, id, style=wx.LC_REPORT | wx.LC_NO_HEADER | wx.LC_HRULES | wx.LC_SINGLE_SEL)
        self.parent = parent
        self.IDpersonne = self.GetParent().IDpersonne
        self.InsertColumn(0, _(u"Pièce à fournir"))
        self.Remplissage()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def Remplissage(self):
        self.Importation()
        if self.GetItemCount() != 0:
            self.DeleteAllItems()
        index = 0
        colours = {
            "Ok": UTILS_Interface.GetToken("success"),
            "Attention": UTILS_Interface.GetToken("warning"),
            "PasOk": UTILS_Interface.GetToken("danger"),
        }
        symbols = {"Ok": u"✓", "Attention": u"⚠", "PasOk": u"✕"}
        for key, valeurs in self.DictPieces.items():
            etat = valeurs[0]
            nomPiece = valeurs[1]
            self.InsertItem(index, u"%s  %s" % (symbols.get(etat, u"•"), nomPiece))
            self.SetItemTextColour(index, colours.get(etat, UTILS_Interface.GetToken("on_surface")))
            self.SetItemData(index, key)
            index += 1
        self.SortItems(self.ColumnSorter)

    def ColumnSorter(self, key1, key2):
        item1 = self.DictPieces[key1][1]
        item2 = self.DictPieces[key2][1]
        if item1 < item2:
            return -1
        return 1

    def Importation(self):
        date_jour = datetime.date.today()
        DB = GestionDB.DB()

        req = """
        SELECT types_pieces.IDtype_piece, types_pieces.nom_piece
        FROM diplomes INNER JOIN diplomes_pieces ON diplomes.IDtype_diplome = diplomes_pieces.IDtype_diplome INNER JOIN types_pieces ON diplomes_pieces.IDtype_piece = types_pieces.IDtype_piece
        WHERE diplomes.IDpersonne=%d;
        """ % self.IDpersonne
        DB.ExecuterReq(req)
        listePiecesAFournir = DB.ResultatReq()
        if type(listePiecesAFournir) != list:
            listePiecesAFournir = list(listePiecesAFournir)

        req = """
        SELECT diplomes_pieces.IDtype_piece, types_pieces.nom_piece
        FROM diplomes_pieces INNER JOIN types_pieces ON diplomes_pieces.IDtype_piece = types_pieces.IDtype_piece
        WHERE diplomes_pieces.IDtype_diplome=0;
        """
        DB.ExecuterReq(req)
        listePiecesBasiquesAFournir = DB.ResultatReq()
        listePiecesAFournir.extend(listePiecesBasiquesAFournir)

        req = """
        SELECT types_pieces.IDtype_piece, pieces.date_debut, pieces.date_fin
        FROM types_pieces LEFT JOIN pieces ON types_pieces.IDtype_piece = pieces.IDtype_piece
        WHERE (pieces.IDpersonne=%d AND pieces.date_debut<='%s' AND pieces.date_fin>='%s')
        ORDER BY pieces.date_fin;
        """ % (self.IDpersonne, date_jour, date_jour)
        DB.ExecuterReq(req)
        listePieces = DB.ResultatReq()
        dictTmpPieces = {}
        for IDtype_piece, date_debut, date_fin in listePieces:
            dictTmpPieces[IDtype_piece] = (date_debut, date_fin)

        self.DictPieces = {}
        for IDtype_piece, nom_piece in listePiecesAFournir:
            if IDtype_piece in dictTmpPieces:
                date_fin = dictTmpPieces[IDtype_piece][1]
                date_fin = datetime.date(int(date_fin[:4]), int(date_fin[5:7]), int(date_fin[8:10]))
                reste = str(date_fin - date_jour)
                if reste != "0:00:00":
                    jours = int(reste[:reste.index("day")])
                    if jours < 15 and jours > 0:
                        etat = "Attention"
                    elif jours <= 0:
                        etat = "PasOk"
                    else:
                        etat = "Ok"
                else:
                    etat = "Attention"
            else:
                etat = "PasOk"
            self.DictPieces[IDtype_piece] = (etat, nom_piece)
        DB.Close()

    def OnSize(self, event):
        width = max(120, self.GetClientSize().width - 8)
        self.SetColumnWidth(0, width)
        event.Skip()

    def OnItemActivated(self, event):
        index = self.GetFirstSelected()
        IDtypePiece = self.GetItemData(index)
        self.parent.AjouterPiece(IDtypePiece=IDtypePiece)


class ListCtrl_Dossier(wx.ListCtrl):
    def __init__(self, parent, id):
        wx.ListCtrl.__init__(self, parent, id, style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES | wx.LC_SINGLE_SEL)
        self.parent = parent
        self.IDpersonne = self.GetParent().IDpersonne

        self.InsertColumn(0, _(u"Type de pièce"))
        self.InsertColumn(1, _(u"Obtention"))
        self.InsertColumn(2, _(u"Expiration"))
        self.InsertColumn(3, _(u"Observations"))

        self.Remplissage()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def Remplissage(self):
        self.Importation()
        if self.GetItemCount() != 0:
            self.DeleteAllItems()

        index = 0
        for key, valeurs in self.DictDossier.items():
            etat = valeurs[0]
            nomPiece = valeurs[1]
            dateDebut = DateEngFr(valeurs[2])
            dateFin = DateEngFr(valeurs[3])

            if key in self.dict_docs:
                self.nbre_documents = self.dict_docs[key]
            else:
                self.nbre_documents = 0
            prefix = u"▣  " if self.nbre_documents > 0 else u""
            self.InsertItem(index, prefix + nomPiece)

            if etat == "Perim":
                self.SetItemTextColour(index, UTILS_Interface.GetToken("disabled"))

            if dateFin == "01/01/2999":
                dateFin = _(u"Illimitée")
            self.SetItem(index, 1, dateDebut)
            self.SetItem(index, 2, dateFin)
            self.SetItem(index, 3, self.etatExpiration(valeurs[2], valeurs[3]))
            self.SetItemData(index, key)
            index += 1

        self.SortItems(self.ColumnSorter)
        nbreItems = self.GetItemCount()
        if nbreItems > 0:
            self.EnsureVisible(nbreItems - 1)
        self._resize_columns()

    def _resize_columns(self):
        width = max(400, self.GetClientSize().width - 12)
        proportions = (0.40, 0.14, 0.14, 0.32)
        remaining = width
        for index, proportion in enumerate(proportions[:-1]):
            col_width = max(90, int(width * proportion))
            self.SetColumnWidth(index, col_width)
            remaining -= col_width
        self.SetColumnWidth(3, max(140, remaining))

    def OnSize(self, event):
        self._resize_columns()
        event.Skip()

    def GetDocumentsScan(self):
        DB = GestionDB.DB(suffixe="DOCUMENTS")
        req = "SELECT IDdocument, IDpiece FROM documents;"
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        dictDocuments = {}
        for IDdocument, IDpiece in listeDonnees:
            if IDpiece not in dictDocuments:
                dictDocuments[IDpiece] = 1
            else:
                dictDocuments[IDpiece] += 1
        return dictDocuments

    def etatExpiration(self, dateDebut, dateFin):
        if dateFin == "2999-01-01":
            return ""

        dateJour = datetime.date.today()
        dateFin = datetime.date(int(dateFin[:4]), int(dateFin[5:7]), int(dateFin[8:10]))
        reste = str(dateFin - dateJour)
        if reste != "0:00:00":
            jours = int(reste[:reste.index("day")])
            if jours < 0:
                return _(u"Pièce expirée")
            elif jours == 1:
                return _(u"Expire demain !")
            return _(u"Expire dans %d jours") % jours
        return _(u"Expire aujourd'hui !")

    def ColumnSorter(self, key1, key2):
        if 'phoenix' in wx.PlatformInfo:
            item1 = self.GetItem(self.FindItem(-1, key1), 2).GetText()
            item2 = self.GetItem(self.FindItem(-1, key2), 2).GetText()
        else:
            item1 = self.GetItem(self.FindItemData(-1, key1), 2).GetText()
            item2 = self.GetItem(self.FindItemData(-1, key2), 2).GetText()
        if item1 == _(u"Illimitée"):
            item1 = "01/01/2999"
        if item2 == _(u"Illimitée"):
            item2 = "01/01/2999"
        item1 = DateFrEng(item1)
        item2 = DateFrEng(item2)
        if item1 < item2:
            return -1
        return 1

    def Importation(self):
        date_jour = datetime.date.today()
        self.dict_docs = self.GetDocumentsScan()

        DB = GestionDB.DB()
        self.DictDossier = {}
        req = """
        SELECT pieces.IDpiece, types_pieces.nom_piece, pieces.date_debut, pieces.date_fin, pieces.IDpersonne
        FROM pieces INNER JOIN types_pieces ON pieces.IDtype_piece = types_pieces.IDtype_piece
        WHERE (((pieces.IDpersonne)=%d));
        """ % self.IDpersonne
        DB.ExecuterReq(req)
        listePieces = DB.ResultatReq()

        for piece in listePieces:
            IDpiece = piece[0]
            nom_piece = piece[1]
            date_debut = piece[2]
            date_fin = piece[3]
            date_fin_2 = datetime.date(int(date_fin[:4]), int(date_fin[5:7]), int(date_fin[8:10]))
            reste = str(date_fin_2 - date_jour)
            if reste != "0:00:00":
                jours = int(reste[:reste.index("day")])
                if jours > 0:
                    etat = "Ok"
                else:
                    etat = "Perim"
            else:
                etat = "Ok"
            self.DictDossier[IDpiece] = (etat, nom_piece, date_debut, date_fin)
        DB.Close()

    def OnItemActivated(self, event):
        self.parent.ModifierPiece()

    def OnContextMenu(self, event):
        if self.GetFirstSelected() == -1:
            return False
        menuPop = UTILS_Adaptations.Menu()

        item = wx.MenuItem(menuPop, 10, _(u"Ajouter"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Ajouter, id=10)
        menuPop.AppendSeparator()

        item = wx.MenuItem(menuPop, 20, _(u"Modifier"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Modifier, id=20)

        item = wx.MenuItem(menuPop, 30, _(u"Supprimer"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Supprimer, id=30)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Menu_Ajouter(self, event):
        self.parent.AjouterPiece()

    def Menu_Modifier(self, event):
        self.parent.ModifierPiece()

    def Menu_Supprimer(self, event):
        self.parent.SupprimerPiece()
