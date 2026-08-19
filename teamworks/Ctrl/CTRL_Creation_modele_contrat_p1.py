#!/usr/bin/env python
# -*- coding: utf-8 -*-
from Utils.UTILS_Traduction import _
import wx
import GestionDB
from Dlg import DLG_Config_classifications, DLG_Config_types_contrats, DLG_Config_champs_contrats

CCNS_GROUPS = ["G%d" % n for n in range(1, 9)]
CEE_QUALIFICATIONS = [
    ("BAFA_HOLDER", "BAFA titulaire"),
    ("BAFA_TRAINEE", "BAFA stagiaire"),
    ("UNQUALIFIED", "Non diplômé"),
    ("EQUIVALENT", "Équivalence"),
    ("BAFD_HOLDER", "BAFD titulaire"),
    ("BAFD_TRAINEE", "BAFD stagiaire"),
]

class Page(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.dictTypes = {}
        self.label_titre = wx.StaticText(self, -1, _(u"Création d'un modèle de contrat"))
        self.label_intro = wx.StaticText(self, -1, _(u"Définissez les contrats auxquels ce modèle peut s'appliquer :"))
        self.label_type = wx.StaticText(self, -1, "Type de contrat :")
        self.choice_type = wx.Choice(self, -1, choices=[])
        self.bouton_type = wx.Button(self, -1, "...", style=wx.BU_EXACTFIT)
        self.label_convention = wx.StaticText(self, -1, "Régime / convention :")
        self.choice_convention = wx.Choice(self, -1, choices=["Historique / autre", "CCNS", "CEE"])
        self.label_cible = wx.StaticText(self, -1, "Ciblage :")
        self.choice_cible = wx.Choice(self, -1, choices=[])
        self.label_class = wx.StaticText(self, -1, "Classification historique :")
        self.choice_class = wx.Choice(self, -1, choices=[])
        self.bouton_class = wx.Button(self, -1, "...", style=wx.BU_EXACTFIT)
        self.listCtrl_champs = ListCtrl_champs(self)
        self.bouton_champs = wx.Button(self, -1, "...", style=wx.BU_EXACTFIT)
        self.Importation_Type(); self.Importation_classifications()
        self.__do_layout()
        self.Bind(wx.EVT_CHOICE, self.OnConvention, self.choice_convention)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonClassifications, self.bouton_class)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonType, self.bouton_type)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonChamps, self.bouton_champs)
        self.Importation()

    def __do_layout(self):
        base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        base.Add(self.label_titre, 0, 0, 0); base.Add(self.label_intro, 0, wx.LEFT, 20)
        box = wx.StaticBoxSizer(wx.StaticBox(self, -1, _(u"Caractéristiques générales")), wx.VERTICAL)
        grid = wx.FlexGridSizer(rows=4, cols=3, vgap=5, hgap=5)
        for label, ctrl, button in ((self.label_type,self.choice_type,self.bouton_type),(self.label_convention,self.choice_convention,None),(self.label_cible,self.choice_cible,None),(self.label_class,self.choice_class,self.bouton_class)):
            grid.Add(label,0,wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL,0); grid.Add(ctrl,0,wx.EXPAND,0); grid.Add(button if button else (1,1),0,0,0)
        grid.AddGrowableCol(1); box.Add(grid,1,wx.ALL|wx.EXPAND,5); base.Add(box,0,wx.LEFT|wx.EXPAND,20)
        champs = wx.StaticBoxSizer(wx.StaticBox(self,-1,_(u"Champs personnalisés")),wx.VERTICAL)
        row=wx.BoxSizer(wx.HORIZONTAL); row.Add(self.listCtrl_champs,1,wx.EXPAND,0); row.Add(self.bouton_champs,0,wx.LEFT,5); champs.Add(row,1,wx.ALL|wx.EXPAND,5); base.Add(champs,1,wx.LEFT|wx.EXPAND,20)
        base.AddGrowableCol(0); base.AddGrowableRow(3); self.SetSizer(base)

    def Importation(self):
        d=self.GetGrandParent().dictModeles
        self.SelectChoice(self.choice_type,d.get("IDtype")); self.SelectChoice(self.choice_class,d.get("IDclassification"))
        convention=d.get("convention_code")
        self.choice_convention.SetSelection(1 if convention=="CCNS" else 2 if d.get("cee_qualification") else 0)
        self.MAJ_Cible()
        cible=d.get("ccns_group") if convention=="CCNS" else d.get("cee_qualification")
        self.SelectChoice(self.choice_cible,cible); self.MAJ_Visibilite()

    def OnConvention(self,event): self.MAJ_Cible(); self.MAJ_Visibilite()
    def MAJ_Cible(self):
        self.choice_cible.Clear(); mode=self.choice_convention.GetSelection()
        if mode==1:
            self.choice_cible.Append("Tous les groupes CCNS", None)
            for g in CCNS_GROUPS: self.choice_cible.Append(g,g)
        elif mode==2:
            self.choice_cible.Append("Toutes les qualifications CEE", None)
            for code,label in CEE_QUALIFICATIONS: self.choice_cible.Append(label,code)
        else: self.choice_cible.Append("Classification historique",None)
        self.choice_cible.SetSelection(0)
    def MAJ_Visibilite(self):
        historique=self.choice_convention.GetSelection()==0
        for c in (self.label_class,self.choice_class,self.bouton_class): c.Show(historique)
        self.label_cible.Show(not historique); self.choice_cible.Show(not historique); self.Layout()

    def GetChoiceData(self,c):
        i=c.GetSelection(); return c.GetClientData(i) if i!=-1 else None
    def SelectChoice(self,c,data):
        for i in range(c.GetCount()):
            if c.GetClientData(i)==data: c.SetSelection(i); return
    def Importation_Type(self):
        self.choice_type.Clear(); DB=GestionDB.DB(); DB.ExecuterReq("SELECT * FROM contrats_types"); rows=DB.ResultatReq(); DB.Close()
        for key,nom,abbr,di in rows: self.dictTypes[key]=di; self.choice_type.Append(nom,key)
    def Importation_classifications(self):
        self.choice_class.Clear(); DB=GestionDB.DB(); DB.ExecuterReq("SELECT * FROM contrats_class"); rows=DB.ResultatReq(); DB.Close()
        for key,valeur in rows: self.choice_class.Append(valeur,key)
    def OnBoutonClassifications(self,event):
        dlg=DLG_Config_classifications.Dialog(self); dlg.ShowModal(); dlg.Destroy(); self.Importation_classifications()
    def OnBoutonType(self,event):
        dlg=DLG_Config_types_contrats.Dialog(self); dlg.ShowModal(); dlg.Destroy(); self.Importation_Type()
    def OnBoutonChamps(self,event):
        dlg=DLG_Config_champs_contrats.Dialog(self); dlg.ShowModal(); dlg.Destroy(); self.listCtrl_champs.MAJListeCtrl()

    def Validation(self):
        typ=self.GetChoiceData(self.choice_type)
        if typ is None:
            wx.MessageBox(_(u"Vous devez sélectionner un type de contrat."),"Erreur",wx.OK|wx.ICON_ERROR); return False
        d=self.GetGrandParent().dictModeles; mode=self.choice_convention.GetSelection(); cible=self.GetChoiceData(self.choice_cible)
        d["IDtype"]=typ; d["convention_code"]=None; d["ccns_group"]=None; d["cee_qualification"]=None
        if mode==0:
            d["IDclassification"]=self.GetChoiceData(self.choice_class)
            if d["IDclassification"] is None:
                wx.MessageBox(_(u"Sélectionnez une classification historique."),"Erreur",wx.OK|wx.ICON_ERROR); return False
        elif mode==1:
            d["IDclassification"]=None; d["convention_code"]="CCNS"; d["ccns_group"]=cible
        else:
            d["IDclassification"]=None; d["cee_qualification"]=cible
        self.GetGrandParent().page2.MAJ_panelDefilant(); return True

class ListCtrl_champs(wx.ListCtrl):
    def __init__(self,parent):
        wx.ListCtrl.__init__(self,parent,-1,style=wx.LC_REPORT|wx.LC_NO_HEADER); self.EnableCheckBoxes(True); self.parent=parent
        self.selections=list(self.GetGrandParent().GetParent().dictChamps.keys()); self.Remplissage()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnItemChecked)
        self.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnItemUnchecked)
    def Import_Donnees(self):
        DB=GestionDB.DB(); DB.ExecuterReq("SELECT IDchamp, nom, description, mot_cle, defaut, exemple FROM contrats_champs ORDER BY nom"); rows=DB.ResultatReq(); DB.Close(); return {r[0]:r for r in rows}
    def Remplissage(self):
        self.dictChamps=self.Import_Donnees(); self.ClearAll(); self.InsertColumn(0,"Nom")
        for key,v in self.dictChamps.items():
            i=self.InsertItem(self.GetItemCount(),v[1]); self.SetItemData(i,key); self.CheckItem(i,key in self.selections)
        self.SetColumnWidth(0,wx.LIST_AUTOSIZE)
    def MAJListeCtrl(self): self.Remplissage()
    def OnItemActivated(self, evt):
        self.CheckItem(evt.Index, not self.IsItemChecked(evt.Index))
    def OnItemChecked(self, evt):
        ID=self.GetItemData(evt.Index)
        if ID not in self.selections: self.selections.append(ID)
        evt.Skip()
    def OnItemUnchecked(self, evt):
        ID=self.GetItemData(evt.Index)
        if ID in self.selections: self.selections.remove(ID)
        evt.Skip()
