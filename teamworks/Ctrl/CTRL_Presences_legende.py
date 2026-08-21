#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Légende du planning de présences."""

import wx

from Ctrl import CTRL_Presences_common
from Utils import UTILS_Interface
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _


class ListCtrl_Legendes(wx.ListCtrl):
    """Liste compacte et responsive des catégories visibles dans le planning.

    Les pastilles de catégorie restent des données métier du planning. Tout le
    chrome autour d'elles dépend uniquement de la charte Teamworks.
    """

    def __init__(self, parent, ID=-1):
        wx.ListCtrl.__init__(
            self,
            parent,
            ID,
            style=wx.LC_REPORT | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL | wx.BORDER_NONE,
        )
        self.parent = parent
        self.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        self.InsertColumn(0, _(u"Catégories"))
        self.InsertColumn(1, _(u"Temps"), wx.LIST_FORMAT_RIGHT)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Remplissage()

    def Importation(self):
        panel = CTRL_Presences_common.find_presences_panel(self)
        if panel is None or not hasattr(panel, "panelPlanning"):
            self.DictCategories = {}
            self._images_categories = {}
            return
        self.DictCategories = panel.panelPlanning.DCplanning.dictCategories

        taille = UTILS_Styles.GetIconSize("small")[0]
        self.il = wx.ImageList(taille, taille)
        self._images_categories = {}
        for key, valeurs in self.DictCategories.items():
            r, v, b = self.FormateCouleur(valeurs[3])
            self._images_categories[key] = self.il.Add(
                self.CreationImage((taille, taille), r, v, b)
            )
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

    def Remplissage(self):
        self.Importation()
        self.DeleteAllItems()
        total_minutes = 0
        index = 0
        for key, valeurs in self.DictCategories.items():
            duree_minutes = valeurs[4]
            if duree_minutes == 0:
                continue
            total_minutes += duree_minutes
            heures, minutes = divmod(duree_minutes, 60)
            row = self.InsertItem(index, valeurs[0])
            self.SetItem(row, 1, "%dh%02d" % (heures, minutes))
            image = self._images_categories.get(key)
            if image is not None:
                self.SetItemImage(row, image)
            self.SetItemData(row, key)
            index += 1

        if total_minutes:
            heures, minutes = divmod(total_minutes, 60)
            row = self.InsertItem(index, _(u"Total"))
            self.SetItem(row, 1, "%dh%02d" % (heures, minutes))
            self.SetItemData(row, 0)
            item = self.GetItem(row)
            item.SetTextColour(UTILS_Interface.GetToken("primary"))
            item.SetFont(UTILS_Styles.GetFont("label"))
            self.SetItem(item)
        wx.CallAfter(self.AjusterColonnes)

    def MAJ(self):
        self.Remplissage()

    def OnSize(self, event):
        wx.CallAfter(self.AjusterColonnes)
        event.Skip()

    def AjusterColonnes(self):
        if self.GetColumnCount() < 2:
            return
        largeur = self.GetClientSize().GetWidth()
        if largeur <= 0:
            return
        temps = max(UTILS_Styles.Scale(72), int(largeur * 0.28))
        categories = max(
            UTILS_Styles.Scale(120),
            largeur - temps - UTILS_Styles.GetSpacing("xs"),
        )
        self.SetColumnWidth(0, categories)
        self.SetColumnWidth(1, temps)

    def FormateCouleur(self, texte):
        try:
            valeurs = texte.strip().strip("()[]").split(",")
            return tuple(int(valeur.strip()) for valeur in valeurs[:3])
        except Exception:
            couleur = UTILS_Interface.GetToken("primary")
            return couleur.Red(), couleur.Green(), couleur.Blue()

    def CreationImage(self, taille_images, r, v, b):
        fond = UTILS_Interface.GetToken("surface_container_lowest")
        bord = UTILS_Interface.GetToken("outline")
        largeur, hauteur = taille_images
        image = wx.Image(largeur, hauteur, True)
        image.SetRGB(
            (0, 0, largeur, hauteur),
            fond.Red(),
            fond.Green(),
            fond.Blue(),
        )
        marge = max(2, largeur // 5)
        taille = max(2, largeur - (marge * 2))
        image.SetRGB(
            (marge - 1, marge - 1, taille + 2, taille + 2),
            bord.Red(),
            bord.Green(),
            bord.Blue(),
        )
        image.SetRGB((marge, marge, taille, taille), r, v, b)
        return image.ConvertToBitmap()


class PanelLegendes(wx.Panel):
    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(self, parent, ID, style=wx.TAB_TRAVERSAL)
        self.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        self.listCtrlLegendes = ListCtrl_Legendes(self, -1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.listCtrlLegendes, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def MAJpanel(self):
        self.listCtrlLegendes.MAJ()
