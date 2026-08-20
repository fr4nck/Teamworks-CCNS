#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

from Utils.UTILS_Traduction import _
from Utils import UTILS_Interface
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

    def MAJ_treeCtrl(self):
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
                self.SetItemData(newItem, None)

                if parentItem == self.root:
                    self.SetItemTextColour(newItem, self.couleurPersonne)
                    self.SetItemBold(newItem, True)
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
        dictNoms, dictProblemes = FonctionsPerso.Creation_liste_pb_personnes()
        listeProblemes = []
        index1 = 0
        for IDpersonne, dictCategories in dictProblemes.items():
            if IDpersonne in dictNoms:
                listeProblemes.append([dictNoms[IDpersonne], []])
                for nomCategorie, valeurs in dictCategories.items():
                    nomCategorie = self._GetCategoryLabel(nomCategorie, valeurs)
                    listeProblemes[index1][1].append([nomCategorie, valeurs])
                index1 += 1
        return listeProblemes
