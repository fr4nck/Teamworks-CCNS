#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publiposteur RH des documents rattachés directement au salarié."""

import os

import wx

import Chemins
import GestionDB
from Dlg import DLG_Publiposteur as _base
from domain.documents import DocumentScope, list_document_types
from Utils import (
    UTILS_Adaptations,
    UTILS_Contrats_modeles_documents,
    UTILS_Documents_RH,
    UTILS_Fichiers,
)
from Utils.UTILS_Traduction import _


_DOCUMENT_TYPES = [(u"Historique / non classé", None)] + [
    (item.label, item.code)
    for item in list_document_types(
        scope=DocumentScope.EMPLOYEE,
        generated_by_teamworks=True,
    )
]


def _document_type_index(metadata):
    current = (metadata or {}).get("document_kind")
    for index, (_label, code) in enumerate(_DOCUMENT_TYPES):
        if code == current:
            return index
    return 0


class Grid_donnees(_base.Grid_donnees):
    """Élargit les libellés pour les mots-clés STRUCTURE_/SALARIE_."""

    def Remplissage(self):
        super(Grid_donnees, self).Remplissage()
        labels = [
            u"{%s}%s" % (motcle, "*" if type_motcle != "base" else "")
            for motcle, type_motcle in _base.DICT_DONNEES.get("MOTSCLES", [])
        ]
        if not labels:
            return
        largeur = max(self.GetTextExtent(label)[0] for label in labels) + 28
        self.SetRowLabelSize(max(140, min(320, largeur)))


class ListCtrl_fichiers(_base.ListCtrl_fichiers):
    def __init__(self, parent, controller=None):
        owner = controller
        if owner is None:
            owner = parent.GetParent() if isinstance(parent, wx.StaticBox) else parent
        super(ListCtrl_fichiers, self).__init__(parent, controller=owner)

    def GetListeDocuments(self):
        fichiers = super(ListCtrl_fichiers, self).GetListeDocuments()
        document_kind = _base.DICT_DONNEES.get("DOCUMENT_KIND")
        if not document_kind:
            return fichiers

        resultat = {}
        index = 1
        DB = GestionDB.DB()
        try:
            for _numero, valeurs in sorted(fichiers.items()):
                nom_fichier = valeurs[0]
                metadata = UTILS_Contrats_modeles_documents.GetMetadata(DB, nom_fichier)
                if UTILS_Contrats_modeles_documents.IsDocumentKindCompatible(
                    metadata,
                    document_kind,
                    include_legacy=True,
                ):
                    resultat[index] = valeurs
                    index += 1
        finally:
            DB.Close()
        return resultat

    def OnContextMenu(self, event):
        if self.GetFirstSelected() == -1:
            return False

        menu = UTILS_Adaptations.Menu()
        item = wx.MenuItem(menu, 10, _(u"Créer un nouveau modèle de document"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Ajouter, id=10)

        menu.AppendSeparator()
        item = wx.MenuItem(menu, 20, _(u"Modifier"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Modifier, id=20)

        item = wx.MenuItem(menu, 30, _(u"Supprimer"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Supprimer, id=30)

        item = wx.MenuItem(menu, 40, _(u"Parcourir"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Inbox.png"), wx.BITMAP_TYPE_PNG))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Parcourir, id=40)

        menu.AppendSeparator()
        item = wx.MenuItem(menu, 185, _(u"Type de document RH…"))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_TypeDocumentRH, id=185)

        self.PopupMenu(menu)
        menu.Destroy()

    def Menu_Ajouter(self, event):
        return super(ListCtrl_fichiers, self).Menu_Ajouter(event)

    def Menu_Modifier(self, event):
        return super(ListCtrl_fichiers, self).Menu_Modifier(event)

    def Menu_Supprimer(self, event):
        index = self.GetFirstSelected()
        nom_fichier = self.getColumnText(index, 0) if index != -1 else None
        resultat = super(ListCtrl_fichiers, self).Menu_Supprimer(event)
        if nom_fichier:
            chemin = os.path.join(UTILS_Fichiers.GetRepModeles(), nom_fichier)
            if not os.path.isfile(chemin):
                DB = GestionDB.DB()
                try:
                    UTILS_Contrats_modeles_documents.DeleteMetadata(DB, nom_fichier)
                finally:
                    DB.Close()
        return resultat

    def Menu_Parcourir(self, event):
        return super(ListCtrl_fichiers, self).Menu_Parcourir(event)

    def Menu_TypeDocumentRH(self, event):
        index = self.GetFirstSelected()
        if index == -1:
            return
        nom_fichier = self.getColumnText(index, 0)

        DB = GestionDB.DB()
        try:
            metadata = UTILS_Contrats_modeles_documents.GetMetadata(DB, nom_fichier)
        finally:
            DB.Close()

        choices = [label for label, _code in _DOCUMENT_TYPES]
        dlg = wx.SingleChoiceDialog(
            self,
            _(u"Classez ce modèle dans le catalogue documentaire RH."),
            _(u"Type de document RH"),
            choices,
        )
        dlg.SetSelection(_document_type_index(metadata))
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        selection = dlg.GetSelection()
        dlg.Destroy()
        document_kind = _DOCUMENT_TYPES[selection][1]

        DB = GestionDB.DB()
        try:
            if document_kind is None:
                UTILS_Contrats_modeles_documents.DeleteMetadata(DB, nom_fichier)
            else:
                UTILS_Contrats_modeles_documents.SaveMetadata(
                    DB,
                    nom_fichier,
                    document_kind=document_kind,
                )
                DB.Commit()
        finally:
            DB.Close()

        self.parent.nomFichier = ""
        self.parent.MAJ_ListCtrl()


class Dialog(_base.Dialog):
    """Publiposteur vanilla filtré sur le type documentaire RH sélectionné."""

    def __init__(self, *args, **kwargs):
        dict_donnees = kwargs.get("dictDonnees")
        if dict_donnees is None and len(args) >= 3:
            dict_donnees = args[2]
        document_code = (dict_donnees or {}).get("DOCUMENT_KIND")
        if not document_code:
            raise ValueError("Le type de document RH est requis pour le publiposteur salarié.")
        UTILS_Documents_RH.EnrichirDictDonneesPersonne(
            dict_donnees,
            document_code=document_code,
        )

        original_list = _base.ListCtrl_fichiers
        original_grid = _base.Grid_donnees
        _base.ListCtrl_fichiers = ListCtrl_fichiers
        _base.Grid_donnees = Grid_donnees
        try:
            _base.Dialog.__init__(self, *args, **kwargs)
        finally:
            _base.ListCtrl_fichiers = original_list
            _base.Grid_donnees = original_grid
