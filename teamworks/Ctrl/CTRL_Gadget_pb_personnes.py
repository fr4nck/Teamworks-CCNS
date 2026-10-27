#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

from Utils.UTILS_Traduction import _
from Utils import UTILS_Interface
from Utils import UTILS_Diagnostic_performance as DiagnosticPerformance
from Utils import UTILS_Personnes_performance as PersonnesPerformance
import wx
import FonctionsPerso
import wx.lib.agw.customtreectrl as CT


class Panel(wx.Panel):
    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(self, parent, ID, name="panel_gadget_pb_personnes", style=wx.TAB_TRAVERSAL)

        self.titre = wx.StaticText(self, -1, _(u"Problèmes des fiches"))
        font = self.titre.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.titre.SetFont(font)
        self.treeCtrl = TreeCtrl(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
        sizer.Add(self.treeCtrl, 1, wx.EXPAND | wx.ALL, 6)
        self.SetSizer(sizer)


class PanelGadget(wx.Panel):
    """Version compacte pour le gadget de la page d'accueil."""

    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(self, parent, ID, name="panel_gadget_pb_personnes", style=wx.TAB_TRAVERSAL)
        self.treeCtrl = TreeCtrl(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.treeCtrl, 1, wx.EXPAND)
        self.SetSizer(sizer)


class TreeCtrl(CT.CustomTreeCtrl):
    def __init__(
        self,
        parent,
        fichier="",
        id=wx.ID_ANY,
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=wx.NO_BORDER,
    ):
        CT.CustomTreeCtrl.__init__(self, parent, id, pos, size, style)
        self.parent = parent

        self.SetAGWWindowStyleFlag(
            wx.TR_HIDE_ROOT
            | wx.TR_HAS_BUTTONS
            | wx.TR_HAS_VARIABLE_ROW_HEIGHT
            | CT.TR_AUTO_CHECK_CHILD
        )
        self.EnableSelectionVista(True)

        self.AppliquerTheme()

        if self.parent.GetName() != "panel_gadget_dossiersincomplets":
            self.expandPersonnes = True
            self.expandTypes = True
        else:
            self.expandPersonnes = False
            self.expandTypes = False

        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeftDown)
        # CustomTreeCtrl: double-clic ou Entrée ouvre l'action ciblée.
        self.Bind(CT.EVT_TREE_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(CT.EVT_TREE_ITEM_GETTOOLTIP, self.OnItemTooltip)
        self.SetToolTip(_(u"Double-cliquez sur une alerte pour la traiter."))

    def AppliquerTheme(self):
        self.couleurFond = UTILS_Interface.GetToken("surface_container_lowest")
        self.couleurPersonne = UTILS_Interface.GetToken("primary")
        self.couleurType = UTILS_Interface.GetToken("on_surface")
        self.couleurProbleme = UTILS_Interface.GetToken("on_surface_variant")
        self.couleurTraits = UTILS_Interface.GetToken("outline_variant")

        self.SetBackgroundColour(self.couleurFond)
        self.SetForegroundColour(self.couleurType)

    def OnLeftDown(self, event):
        self.Unselect()
        event.Skip()

    def OnItemTooltip(self, event):
        item = event.GetItem()
        if item and item.IsOk():
            label = self.GetItemText(item)
            target = self.GetItemData(item)
            if isinstance(target, dict) and target.get("kind") != "category":
                label += _(u"\nDouble-cliquez ou appuyez sur Entrée pour ouvrir.")
            event.SetToolTip(label)

    def OnItemActivated(self, event):
        item = event.GetItem()
        target = self.GetItemData(item) if item and item.IsOk() else None
        if not isinstance(target, dict) or target.get("kind") == "category":
            event.Skip()  # Garde le repliement/expansion des catégories.
            return
        self._OpenProblem(target)

    def _OpenProblem(self, target):
        """Ouvre la bonne fiche et garde la confirmation des actes sensibles."""
        from Dlg import DLG_Fiche_individuelle

        person_id = target.get("IDpersonne")
        if person_id is None:
            return
        owner = wx.GetTopLevelParent(self)
        dialog = DLG_Fiche_individuelle.Dialog(owner, IDpersonne=int(person_id))
        try:
            # Exécuter après l'entrée dans la boucle modale : la page et les
            # dialogues enfants restent alors attachés à une fiche visible.
            wx.CallAfter(self._OpenProblemPage, dialog, dict(target))
            dialog.ShowModal()
        finally:
            dialog.Destroy()
            self.MAJ_treeCtrl()

    def _OpenProblemPage(self, dialog, target):
        kind = target.get("kind")
        page_index = {"information": 0, "piece": 2, "contract": 3}.get(kind, 0)
        notebook = dialog.notebook
        if notebook.GetPageCount() <= page_index:
            return
        notebook.SetSelection(page_index)

        if kind == "information":
            controls = {
                _(u"Civilité"): "combo_box_civilite",
                _(u"Nom de famille"): "text_nom",
                _(u"Nom de jeune fille"): "text_ctrl_nomjf",
                _(u"Prénom"): "text_prenom",
                _(u"Date de naissance"): "text_date_naiss",
                _(u"Code postal de la ville de naissance"): "text_cp_naiss",
                _(u"Ville de naissance"): "text_ville_naiss",
                _(u"Numéro de sécurité sociale"): "text_numsecu",
                _(u"Adresse de résidence"): "text_adresse",
                _(u"Code postal de résidence"): "text_cp",
                _(u"Ville de résidence"): "text_ville",
                _(u"Situation sociale"): "combo_box_situation",
            }
            control = getattr(notebook.pageGeneralites, controls.get(target.get("field")), None)
            if control is not None and control.IsEnabled():
                control.SetFocus()
            return

        if kind == "piece":
            page = notebook.pageStatut
            if page is not None:
                # Le dialogue de saisie vérifie le type, les dates et les
                # documents ; aucune pièce n'est validée par un double-clic.
                page.AjouterPiece(IDtypePiece=int(target["IDtype_piece"]))
            return

        if kind == "contract":
            page = notebook.pageContrats
            if page is None:
                return
            contracts = page.list_ctrl_contrats
            contract_id = int(target["IDcontrat"])
            selected = -1
            for row in range(contracts.GetItemCount()):
                if contracts.GetItemData(row) == contract_id:
                    selected = row
                    break
            if selected == -1:
                wx.MessageBox(
                    _(u"Ce contrat n'est plus présent dans la fiche. Actualisez la liste."),
                    _(u"Contrat introuvable"), wx.OK | wx.ICON_INFORMATION,
                    parent=dialog,
                )
                return
            contracts.Select(selected)
            contracts.Focus(selected)
            contracts.EnsureVisible(selected)

            if target.get("operation") == "signature":
                if contracts.GetItem(selected, 4).GetText() == "Oui":
                    return
                confirm = wx.MessageDialog(
                    dialog,
                    _(u"Le contrat sélectionné est-il effectivement signé ?\n\n"
                      u"Confirmer enregistre uniquement le statut « signé ». "
                      u"Le document signé doit être conservé séparément."),
                    _(u"Confirmer la signature"),
                    wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
                )
                try:
                    if confirm.ShowModal() == wx.ID_YES:
                        page.OnBoutonSignature(None)
                finally:
                    confirm.Destroy()
            elif target.get("operation") == "due":
                # Préparation/édition de la DPAE ; produire le PDF ne prouve
                # PAS son dépôt. Le statut reste à renseigner après déclaration.
                page.ImprimerDUE()

    def MAJ_treeCtrl(self):
        DiagnosticPerformance.installer_instrumentation_sql(PersonnesPerformance.GestionDB)
        with DiagnosticPerformance.mesurer_action("wx.personnes.dossiers.rafraichissement"):
            self.DeleteAllItems()
            self.AppliquerTheme()
            self.SetHilightFocusColour(UTILS_Interface.GetToken("selection"))
            self.SetHilightNonFocusColour(UTILS_Interface.GetToken("selection"))
            self.SetConnectionPen(wx.Pen(self.couleurTraits, 1, style=wx.PENSTYLE_DOT))

            self.listeDonnees = self.GetListeProblemes()
            self.root = self.AddRoot("Root")
            self.SetItemData(self.root, None)
            self.AddTreeNodes(self.root, self.listeDonnees)

    def AddTreeNodes(self, parentItem, items, img=None):
        for item in items:
            if isinstance(item, str):
                newItem = self.AppendItem(parentItem, item)
                self.SetItemData(newItem, None)
                self.SetItemTextColour(newItem, self.couleurProbleme)
            else:
                texte = item[0]
                newItem = self.AppendItem(parentItem, texte)
                self.SetItemData(newItem, item[2] if len(item) > 2 else None)

                if parentItem == self.root:
                    self.SetItemTextColour(newItem, self.couleurPersonne)
                    self.SetItemBold(newItem, True)
                elif not item[1]:
                    self.SetItemTextColour(newItem, self.couleurProbleme)
                else:
                    self.SetItemTextColour(newItem, self.couleurType)
                    if self.expandPersonnes:
                        self.Expand(parentItem)

                self.AddTreeNodes(newItem, item[1], img)
                if self.expandTypes:
                    self.Expand(newItem)

    def _GetCategoryLabel(self, nomCategorie, valeurs):
        """Corrige le vocabulaire historique du groupe contrat/DUE."""
        if nomCategorie == _(u"1 contrat à voir"):
            return _(u"1 document à traiter")
        if nomCategorie.endswith(_(u" contrats à voir")):
            return str(len(valeurs)) + _(u" documents à traiter")
        return nomCategorie

    def GetListeProblemes(self):
        dictNoms, dictProblemes, dictTargets = (
            PersonnesPerformance.Creation_liste_pb_personnes(include_targets=True)
        )
        listeProblemes = []
        for IDpersonne, dictCategories in dictProblemes.items():
            if IDpersonne not in dictNoms:
                continue
            groups = []
            for nomCategorie, valeurs in dictCategories.items():
                raw_targets = dictTargets.get(IDpersonne, {}).get(nomCategorie, ())
                entries = []
                for index, label in enumerate(valeurs):
                    target = dict(raw_targets[index]) if index < len(raw_targets) else {}
                    target["IDpersonne"] = IDpersonne
                    entries.append([label, [], target])
                groups.append([
                    self._GetCategoryLabel(nomCategorie, valeurs),
                    entries,
                    {"kind": "category", "IDpersonne": IDpersonne},
                ])
            listeProblemes.append([
                dictNoms[IDpersonne], groups,
                {"kind": "person", "IDpersonne": IDpersonne},
            ])
        return listeProblemes
