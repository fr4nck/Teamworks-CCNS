#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Adaptateur du publiposteur pour les contrats TW-184.

Le publiposteur vanilla reste inchangé pour toutes les autres catégories.
Seule la liste des fichiers de modèles est filtrée selon le régime du contrat.
Les fichiers sans métadonnées restent visibles comme modèles historiques.
"""

import os
import wx
import Chemins
import GestionDB
from Utils.UTILS_Traduction import _
from Dlg import DLG_Publiposteur as _base
from Utils import (
    UTILS_Adaptations,
    UTILS_Contrats_modeles_documents,
    UTILS_Documents_RH,
    UTILS_Fichiers,
)


_TARGETS = [
    (u"Historique / tous contrats (aucun ciblage)", None, None, None),
    (u"CCNS — tous les groupes", "CCNS", None, None),
] + [
    (u"CCNS — G%d" % n, "CCNS", "G%d" % n, None) for n in range(1, 9)
] + [
    (u"CEE — toutes les qualifications", "CEE", None, None),
    (u"CEE — BAFA titulaire", "CEE", None, "BAFA_HOLDER"),
    (u"CEE — BAFA stagiaire", "CEE", None, "BAFA_TRAINEE"),
    (u"CEE — non diplômé", "CEE", None, "UNQUALIFIED"),
    (u"CEE — qualification équivalente", "CEE", None, "EQUIVALENT"),
    (u"CEE — BAFD titulaire", "CEE", None, "BAFD_HOLDER"),
    (u"CEE — BAFD stagiaire", "CEE", None, "BAFD_TRAINEE"),
]


def _target_index(metadata):
    if metadata is None:
        return 0
    target = (
        metadata.get("convention_code"),
        metadata.get("ccns_group"),
        metadata.get("cee_qualification"),
    )
    for index, (_, convention, group, qualification) in enumerate(_TARGETS):
        if target == (convention, group, qualification):
            return index
    return 0


def _apply_legacy_cee_aliases(dict_donnees):
    """Alimente les mots-clés historiques depuis la source moderne unique.

    Le modèle CEE livré historiquement avec Teamworks utilise ``{BRUTJOUR}``.
    TW-184 expose désormais ``{BAREMECEE}``, calculé à partir du barème
    employeur historisé. Pour éviter une deuxième saisie contradictoire, on
    fournit BRUTJOUR comme alias de BAREMECEE uniquement pour les CEE modernes.
    """
    if not dict_donnees or dict_donnees.get("CATEGORIE") != "contrat":
        return
    motcles = dict_donnees.setdefault("MOTSCLES", [])
    has_brutjour = any(motcle == "BRUTJOUR" for motcle, _type in motcles)
    for index in range(1, int(dict_donnees.get("NBREDOCUMENTS", 0)) + 1):
        document = dict_donnees.get(index, {})
        if not document.get("QUALIFICATIONCEE") or not document.get("BAREMECEE"):
            continue
        document["BRUTJOUR"] = document["BAREMECEE"]
        if not has_brutjour:
            motcles.append(("BRUTJOUR", "base"))
            has_brutjour = True


class Grid_donnees(_base.Grid_donnees):
    """Grille contrat dont la colonne des mots-clés s'adapte au contenu."""

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
        # Phoenix impose que le contrôle soit enfant du StaticBox. Le code
        # historique utilisait toutefois ``parent`` comme contrôleur Page4.
        # On transmet donc séparément le parent wx et le contrôleur métier.
        owner = controller
        if owner is None:
            owner = parent.GetParent() if isinstance(parent, wx.StaticBox) else parent
        super(ListCtrl_fichiers, self).__init__(parent, controller=owner)

    def GetListeDocuments(self):
        fichiers = super(ListCtrl_fichiers, self).GetListeDocuments()
        if _base.DICT_DONNEES.get("CATEGORIE") != "contrat":
            return fichiers
        contrat = _base.DICT_DONNEES.get(1, {})
        noms = [valeurs[0] for _, valeurs in sorted(fichiers.items())]
        DB = GestionDB.DB()
        try:
            compatibles = set(
                UTILS_Contrats_modeles_documents.FilterFilenames(DB, noms, contrat)
            )
        finally:
            DB.Close()
        resultat = {}
        index = 1
        for _, valeurs in sorted(fichiers.items()):
            if valeurs[0] in compatibles:
                resultat[index] = valeurs
                index += 1
        return resultat

    def OnContextMenu(self, event):
        if self.GetFirstSelected() == -1:
            return False

        menuPop = UTILS_Adaptations.Menu()
        item = wx.MenuItem(menuPop, 10, _(u"Créer un nouveau modèle de document"))
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

        item = wx.MenuItem(menuPop, 40, _(u"Parcourir"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Inbox.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Parcourir, id=40)

        menuPop.AppendSeparator()
        item = wx.MenuItem(menuPop, 184, _(u"Ciblage du modèle de contrat…"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_CiblageContrat, id=184)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    # L'audit de handlers est volontairement statique et ne suit pas
    # l'héritage : ces relais rendent explicites les actions vanilla conservées.
    def Menu_Ajouter(self, event):
        return super(ListCtrl_fichiers, self).Menu_Ajouter(event)

    def Menu_Modifier(self, event):
        return super(ListCtrl_fichiers, self).Menu_Modifier(event)

    def Menu_Supprimer(self, event):
        index = self.GetFirstSelected()
        nom_fichier = self.getColumnText(index, 0) if index != -1 else None
        resultat = super(ListCtrl_fichiers, self).Menu_Supprimer(event)

        # Le dialogue vanilla gère la confirmation. On ne retire les métadonnées
        # que si le fichier a réellement disparu ; une annulation ne change rien.
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

    def Menu_CiblageContrat(self, event):
        index = self.GetFirstSelected()
        if index == -1:
            return
        nom_fichier = self.getColumnText(index, 0)
        DB = GestionDB.DB()
        try:
            metadata = UTILS_Contrats_modeles_documents.GetMetadata(DB, nom_fichier)
        finally:
            DB.Close()

        choices = [item[0] for item in _TARGETS]
        dlg = wx.SingleChoiceDialog(
            self,
            _(u"Choisissez les contrats pour lesquels ce fichier doit être proposé."),
            _(u"Ciblage du modèle de contrat"),
            choices,
        )
        dlg.SetSelection(_target_index(metadata))
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        selection = dlg.GetSelection()
        dlg.Destroy()
        _, convention, group, qualification = _TARGETS[selection]

        DB = GestionDB.DB()
        try:
            if selection == 0:
                UTILS_Contrats_modeles_documents.DeleteMetadata(DB, nom_fichier)
            else:
                UTILS_Contrats_modeles_documents.SaveMetadata(
                    DB,
                    nom_fichier,
                    convention_code=convention,
                    ccns_group=group,
                    cee_qualification=qualification,
                )
                DB.Commit()
        finally:
            DB.Close()

        # Le fichier peut disparaître de la liste s'il vient d'être ciblé pour
        # un autre régime que le contrat actuellement imprimé.
        self.parent.nomFichier = ""
        self.parent.MAJ_ListCtrl()


class Dialog(_base.Dialog):
    """Publiposteur standard avec ergonomie et modèles filtrés pour un contrat."""

    def __init__(self, *args, **kwargs):
        dict_donnees = kwargs.get("dictDonnees")
        if dict_donnees is None and len(args) >= 3:
            dict_donnees = args[2]
        UTILS_Documents_RH.EnrichirDictDonneesContrat(dict_donnees)
        _apply_legacy_cee_aliases(dict_donnees)

        original_list = _base.ListCtrl_fichiers
        original_grid = _base.Grid_donnees
        _base.ListCtrl_fichiers = ListCtrl_fichiers
        _base.Grid_donnees = Grid_donnees
        try:
            _base.Dialog.__init__(self, *args, **kwargs)
        finally:
            # Les autres usages du publiposteur restent strictement vanilla.
            _base.ListCtrl_fichiers = original_list
            _base.Grid_donnees = original_grid
