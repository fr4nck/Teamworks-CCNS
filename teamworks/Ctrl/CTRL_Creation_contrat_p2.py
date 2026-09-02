#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence GNU GPL
#-----------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
import wx
import six
import FonctionsPerso
import wx.lib.mixins.listctrl as listmix
from Dlg import DLG_Config_modeles_contrats as ConfigModeles
import GestionDB
from Ctrl import CTRL_Texte
from Utils import (
    UTILS_Adaptations,
    UTILS_Contrats_schema,
    UTILS_Interface,
    UTILS_Styles,
)


def _resolve_model_convention(current_convention, model_convention, is_legacy_model, is_cee_model):
    """Résout la convention sans confondre régime CEE et convention collective."""
    if is_cee_model and model_convention in (None, ""):
        return current_convention
    if is_legacy_model:
        return "OTHER"
    return model_convention


class Page(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)

        self.label_titre = CTRL_Texte.H2(self, _(u"1. Point de départ"))
        self.label_intro = CTRL_Texte.BodySecondary(
            self,
            _(u"Choisissez simplement comment démarrer. Vous pourrez modifier tous les éléments du contrat ensuite."),
        )

        self.radio_non = wx.RadioButton(
            self,
            -1,
            _(u"Créer le contrat sans modèle"),
            style=wx.RB_GROUP,
        )
        self.radio_oui = wx.RadioButton(
            self,
            -1,
            _(u"Utiliser un modèle existant"),
        )
        self.aide_sans_modele = CTRL_Texte.BodySecondary(
            self,
            _(u"Recommandé pour un contrat ponctuel ou lorsque vous voulez repartir d'une saisie propre."),
        )
        self.aide_avec_modele = CTRL_Texte.BodySecondary(
            self,
            _(u"Pratique pour reprendre une structure de contrat déjà utilisée sans ressaisir les mêmes paramètres."),
        )

        self.sizer_choix_modele_staticbox = wx.StaticBox(
            self,
            -1,
            _(u"Modèles disponibles"),
        )
        self.listCtrl_modeles = ListCtrl(
            self.sizer_choix_modele_staticbox,
            controller=self,
        )
        self.bouton_modeles = wx.Button(
            self.sizer_choix_modele_staticbox,
            -1,
            _(u"Gérer les modèles"),
        )

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioNon, self.radio_non)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioOui, self.radio_oui)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModeles, self.bouton_modeles)

        self.Init_radio(position="non")

    def __set_properties(self):
        self.bouton_modeles.SetMinSize(
            (-1, UTILS_Styles.GetControlMetric("button_min_height"))
        )
        self.bouton_modeles.SetToolTip(
            wx.ToolTip(
                _(u"Ajouter, modifier ou supprimer les modèles de contrat")
            )
        )
        self.listCtrl_modeles.SetMinSize(
            (-1, UTILS_Styles.Scale(180))
        )

    def __do_layout(self):
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        section_gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        field_gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        control_gap = UTILS_Styles.GetLayoutSpacing("control_gap")

        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.label_titre, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        sizer_base.Add(self.label_intro, 0, wx.EXPAND | wx.BOTTOM, section_gap)

        bloc_sans = wx.BoxSizer(wx.VERTICAL)
        bloc_sans.Add(self.radio_non, 0, wx.BOTTOM, control_gap)
        bloc_sans.Add(self.aide_sans_modele, 0, wx.LEFT, UTILS_Styles.GetSpacing("lg"))
        sizer_base.Add(bloc_sans, 0, wx.EXPAND | wx.BOTTOM, section_gap)

        bloc_avec = wx.BoxSizer(wx.VERTICAL)
        bloc_avec.Add(self.radio_oui, 0, wx.BOTTOM, control_gap)
        bloc_avec.Add(self.aide_avec_modele, 0, wx.LEFT, UTILS_Styles.GetSpacing("lg"))
        sizer_base.Add(bloc_avec, 0, wx.EXPAND | wx.BOTTOM, field_gap)

        sizer_choix_modele = wx.BoxSizer(wx.VERTICAL)
        sizer_choix_modele.Add(
            self.listCtrl_modeles,
            1,
            wx.EXPAND | wx.BOTTOM,
            field_gap,
        )
        ligne_actions = wx.BoxSizer(wx.HORIZONTAL)
        ligne_actions.AddStretchSpacer(1)
        ligne_actions.Add(self.bouton_modeles, 0)
        sizer_choix_modele.Add(ligne_actions, 0, wx.EXPAND)
        self.sizer_choix_modele_staticbox.SetSizer(sizer_choix_modele)

        sizer_base.Add(
            self.sizer_choix_modele_staticbox,
            1,
            wx.EXPAND | wx.TOP,
            field_gap,
        )

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(sizer_base, 1, wx.EXPAND | wx.ALL, page_gap)
        self.SetSizer(outer)

    def OnRadioNon(self, event):
        self.Init_radio(position="non")

    def OnRadioOui(self, event):
        self.Init_radio(position="oui")
        self.listCtrl_modeles.SetFocus()
        if self.listCtrl_modeles.GetItemCount() > 0:
            self.listCtrl_modeles.Select(0)

    def OnBoutonModeles(self, event):
        dlg = ConfigModeles.Dialog(self)
        dlg.ShowModal()
        dlg.Destroy()

    def Init_radio(self, position="non"):
        utilise_modele = position == "oui"
        self.radio_non.SetValue(not utilise_modele)
        self.radio_oui.SetValue(utilise_modele)
        self.listCtrl_modeles.Enable(utilise_modele)
        self.bouton_modeles.Enable(utilise_modele)
        self.sizer_choix_modele_staticbox.Show(utilise_modele)
        self.Layout()

    def MAJ_ListCtrl(self):
        self.listCtrl_modeles.MAJListeCtrl()

    def Validation(self):
        if self.radio_oui.GetValue() == False:
            return True

        index = self.listCtrl_modeles.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(
                self,
                _(u"Sélectionnez un modèle de contrat pour continuer."),
                _(u"Modèle de contrat"),
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False

        IDmodele = int(self.listCtrl_modeles.GetItem(index, 0).GetText())

        DB = GestionDB.DB()
        UTILS_Contrats_schema.EnsureContractModelColumns(DB)
        req = """
        SELECT IDclassification, IDtype, convention_code, ccns_group, cee_qualification
        FROM contrats_modeles WHERE IDmodele=%d;
        """ % IDmodele
        DB.ExecuterReq(req)
        rows = DB.ResultatReq()
        if not rows:
            DB.Close()
            wx.MessageBox(
                _(u"Le modèle sélectionné n'existe plus."),
                _(u"Modèle de contrat"),
                wx.OK | wx.ICON_ERROR,
                parent=self,
            )
            self.MAJ_ListCtrl()
            return False

        IDclassification, IDtype, convention_code, ccns_group, cee_qualification = rows[0]
        contrat = self.GetGrandParent().dictContrats
        current_convention = contrat.get("convention_code")
        contrat["IDclassification"] = IDclassification
        contrat["IDtype"] = IDtype

        is_legacy_model = (
            convention_code in (None, "")
            and ccns_group in (None, "")
            and cee_qualification in (None, "")
            and IDclassification not in (None, "")
        )
        is_cee_model = self.GetGrandParent().page3.dictTypeCodes.get(IDtype) == "CEE"
        contrat["convention_code"] = _resolve_model_convention(
            current_convention,
            convention_code,
            is_legacy_model,
            is_cee_model,
        )
        contrat["ccns_group"] = ccns_group
        contrat["cee_qualification"] = cee_qualification

        req = "SELECT IDchamp, valeur FROM contrats_valchamps WHERE (IDmodele=%d AND type='modele');" % IDmodele
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()

        self.GetGrandParent().dictChamps.clear()
        for IDchamp, valeur in listeDonnees:
            self.GetGrandParent().dictChamps[IDchamp] = valeur

        DB.Close()

        self.GetGrandParent().page3.Importation()
        self.GetGrandParent().page3.RefreshContractRules()
        self.GetGrandParent().page4.MAJ_ListCtrl()
        return True


class ListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.ColumnSorterMixin):
    def __init__(self, parent, controller):
        wx.ListCtrl.__init__(
            self,
            parent,
            -1,
            style=wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL | wx.LC_HRULES,
        )

        self.criteres = ""
        self.parent = controller

        tailleIcones = UTILS_Styles.GetIconSize("small")[0]
        self.il = wx.ImageList(tailleIcones, tailleIcones)
        self.imgTriAz = self.il.Add(
            wx.Bitmap(
                Chemins.GetStaticPath("Images/16x16/Tri_az.png"),
                wx.BITMAP_TYPE_PNG,
            )
        )
        self.imgTriZa = self.il.Add(
            wx.Bitmap(
                Chemins.GetStaticPath("Images/16x16/Tri_za.png"),
                wx.BITMAP_TYPE_PNG,
            )
        )
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        self.attr1 = wx.ItemAttr()
        self.attr1.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_low")
        )
        self.Remplissage()

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)

    def OnSize(self, event):
        self.Refresh()
        event.Skip()

    def Remplissage(self):
        self.Importation()
        self.nbreColonnes = 2
        self.InsertColumn(0, _(u"ID"))
        self.SetColumnWidth(0, 0)
        self.InsertColumn(1, _(u"Nom"))
        self.SetColumnWidth(1, UTILS_Styles.Scale(220))
        self.InsertColumn(2, _(u"Description"))
        self.SetColumnWidth(2, UTILS_Styles.Scale(320))

        self.itemDataMap = self.donnees
        self.itemIndexMap = list(self.donnees.keys())
        self.SetItemCount(self.nbreLignes)

        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, self.nbreColonnes)
        self.SortListItems(1, 1)

    def OnItemSelected(self, event):
        pass

    def OnItemDeselected(self, event):
        pass

    def Importation(self):
        DB = GestionDB.DB()
        req = """SELECT IDmodele, nom, description
        FROM contrats_modeles ORDER BY nom; """
        DB.ExecuterReq(req)
        liste = DB.ResultatReq()
        DB.Close()
        self.nbreLignes = len(liste)
        self.donnees = self.listeEnDict(liste)

    def MAJListeCtrl(self):
        self.ClearAll()
        self.Remplissage()
        self.resizeLastColumn(0)
        listmix.ColumnSorterMixin.__init__(self, self.nbreColonnes)

    def listeEnDict(self, liste):
        dictio = {}
        x = 1
        for ligne in liste:
            dictio[x] = ligne
            x += 1
        return dictio

    def OnItemActivated(self, event):
        self.parent.OnBoutonModeles(None)

    def getColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()

    def OnGetItemText(self, item, col):
        index = self.itemIndexMap[item]
        return six.text_type(self.itemDataMap[index][col])

    def OnGetItemImage(self, item):
        return -1

    def OnGetItemAttr(self, item):
        if item % 2 == 1:
            return self.attr1
        return None

    def SortItems(self, sorter=FonctionsPerso.cmp):
        items = list(self.itemDataMap.keys())
        items = FonctionsPerso.SortItems(items, sorter)
        self.itemIndexMap = items
        self.Refresh()

    def GetListCtrl(self):
        return self

    def GetSortImages(self):
        return (self.imgTriAz, self.imgTriZa)

    def OnContextMenu(self, event):
        if self.GetFirstSelected() == -1:
            return False
        menuPop = UTILS_Adaptations.Menu()

        item = wx.MenuItem(menuPop, 10, _(u"Ajouter"))
        item.SetBitmap(
            wx.Bitmap(
                Chemins.GetStaticPath("Images/16x16/Ajouter.png"),
                wx.BITMAP_TYPE_PNG,
            )
        )
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Ajouter, id=10)

        menuPop.AppendSeparator()
        item = wx.MenuItem(menuPop, 20, _(u"Modifier"))
        item.SetBitmap(
            wx.Bitmap(
                Chemins.GetStaticPath("Images/16x16/Modifier.png"),
                wx.BITMAP_TYPE_PNG,
            )
        )
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Modifier, id=20)

        item = wx.MenuItem(menuPop, 30, _(u"Supprimer"))
        item.SetBitmap(
            wx.Bitmap(
                Chemins.GetStaticPath("Images/16x16/Supprimer.png"),
                wx.BITMAP_TYPE_PNG,
            )
        )
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Supprimer, id=30)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Menu_Ajouter(self, event):
        self.parent.Ajouter()

    def Menu_Modifier(self, event):
        self.parent.Modifier()

    def Menu_Supprimer(self, event):
        self.parent.Supprimer()
