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
from Ctrl import CTRL_Bouton_image
import GestionDB
import FonctionsPerso
import  wx.lib.scrolledpanel as scrolled
import win32com.client

COULEUR_SYNCHRO = (176, 251, 168)
COULEUR_MODIF = (255, 230, 169)
COULEUR_NON_SYNCHRO = (255, 169, 169)


class LibOutlook() :
    def __init__(self):
        # Chargement de Outlook
        self.echec = False
        try : 
            self.Outlook = win32com.client.Dispatch("Outlook.Application")
            self.echec = False
        except :
            print("pas de outlook")
            self.echec = True
        
    def Test(self):
        """ Teste si Outlook n'est pas verrouillé """
        try :
            # Test de lecture des contacts
            MAPI = self.Outlook.GetNamespace("MAPI")
            print("win32com.client.constants:", win32com.client.constants)
            dossierContacts = MAPI.GetDefaultFolder(10)  # win32com.client.constants.olFolderContacts
            nbreContacts = len(dossierContacts.Items)
            for i in range(nbreContacts):
                item = dossierContacts.Items.Item(i+1)
                test = item.Email1Address
            return True
        except :
            return False
        
    def Suppression(self, nometprenom):
        # Suppression d'un contact
        MAPI = self.Outlook.GetNamespace("MAPI")
        dossierContacts = MAPI.GetDefaultFolder(10)   # win32com.client.constants.olFolderContacts
        for i in range(len(dossierContacts.Items)):
            item = dossierContacts.Items.Item(i+1)
            if item.LastNameAndFirstName == nometprenom :
                item.Delete()
                break
                
    def Lecture(self):
        # Lecture des contacts
        MAPI = self.Outlook.GetNamespace("MAPI")
        dossierContacts = MAPI.GetDefaultFolder(10)   # win32com.client.constants.olFolderContacts
        
        dictContacts = {}

        for i in range(len(dossierContacts.Items)):
            item = dossierContacts.Items.Item(i+1)
            contact = {}
            
            # Généralités
            contact["civilite"] = item.Title
            contact["nom"] = item.LastName
            contact["prenom"] = item.FirstName
            contact["nom complet"] = item.FullName
            contact["nom et prenom"] = item.LastNameAndFirstName
            contact["file as"] = item.FileAs
            
            contact["anniversaire"] = item.Anniversary
            contact["categories"] = item.Categories

            # Adresses Mail
            contact["email1"] = item.Email1Address
            contact["email2"] = item.Email2Address
            contact["email3"] = item.Email3Address

            # Téléphones
            contact["fixe1"] = item.HomeTelephoneNumber
            contact["fixe2"] = item.Home2TelephoneNumber
            contact["fax"] = item.HomeFaxNumber
            contact["mobile"] = item.MobileTelephoneNumber

            # Adresse
            contact["ville"] = item.HomeAddressCity
            contact["pays"] = item.HomeAddressCountry
            contact["cp"] = item.HomeAddressPostalCode
            contact["adresse"] = item.HomeAddressStreet
            
            contact["mailing ville"] = item.MailingAddressCity
            contact["mailing pays"] = item.MailingAddressCountry
            contact["mailing cp"] = item.MailingAddressPostalCode
            contact["mailing adresse"] = item.MailingAddressStreet
            
            dictContacts[i+1] = contact
        
        return dictContacts

    def Enregistrement(self, civilite, nom, prenom, anniversaire, email1, email2, email3, fixe1, fixe2, fax, mobile, ville, pays, cp, adresse):
        # Enregistrement d'un contact sous Outlook
        contact = self.Outlook.CreateItem(2) # 2=outlook contact item
        contact.Title = civilite
        contact.FirstName = prenom
        contact.LastName = nom
##        contact.Anniversary = anniversaire
        contact.Email1Address = email1
        contact.Email2Address = email2
        contact.Email3Address = email3
        contact.HomeTelephoneNumber = fixe1
        contact.Home2TelephoneNumber = fixe2
        contact.HomeFaxNumber = fax
        contact.MobileTelephoneNumber = mobile
        contact.HomeAddressCity = ville
        contact.HomeAddressCountry = pays
        contact.HomeAddressPostalCode = cp
        contact.HomeAddressStreet = adresse
        contact.Categories = "TeamWorks"
        contact.Save()
        return True







class PanelContacts(scrolled.ScrolledPanel):
    def __init__(self, parent):
        scrolled.ScrolledPanel.__init__(self, parent, -1)
        print("1")
        self.outlook = LibOutlook()
        print(self.outlook)
        self.dictContacts = self.outlook.Lecture()
        
        self.listeContacts = self.Import_Donnees()
        gridSizer = wx.FlexGridSizer(cols=6, vgap=2, hgap=2)
        
        # Création des labels
        label_nom = wx.StaticText(self, -1, _(u"Nom et prénom"))
        label_adresse = wx.StaticText(self, -1, _(u"Adresse"))
        label_coords = wx.StaticText(self, -1, _(u"Coordonnées"))
        label_datenaiss = wx.StaticText(self, -1, _(u"Date de naiss."))
        
        font = wx.Font(7, wx.SWISS, wx.NORMAL, wx.NORMAL)
        label_nom.SetFont(font)
        label_adresse.SetFont(font)
        label_coords.SetFont(font)
        label_datenaiss.SetFont(font)
        
        gridSizer.Add((5, 5), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTRE, border=0)
        gridSizer.Add((5, 5), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTRE, border=0)
        gridSizer.Add(label_nom, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTRE, border=0)
        gridSizer.Add(label_adresse, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTRE, border=0)
        gridSizer.Add(label_coords, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTRE, border=0)
        gridSizer.Add(label_datenaiss, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTRE, border=0)

        for IDpersonne, civilite, nom, prenom, date_naiss, adresse_resid, cp_resid, ville_resid, emails, fixes, fax, mobile in self.listeContacts:
            
            # Création des contrôles
            exec("self.bouton_synchro_" + str(IDpersonne) + " = wx.BitmapButton(self, 10000+IDpersonne, wx.Bitmap('Images/16x16/Ok_2.png', wx.BITMAP_TYPE_ANY))")
            exec("self.bouton_synchro_" + str(IDpersonne) + ".SetBitmapDisabled(wx.Bitmap('Images/16x16/Ok_3.png', wx.BITMAP_TYPE_ANY))")
            exec("self.bouton_synchro_" + str(IDpersonne) + ".SetToolTip(wx.ToolTip(u'Cliquez ici pour synchroniser la fiche de ' + prenom + ' ' + nom + '.'))")
            exec("self.bouton_suppr_" + str(IDpersonne) + " = wx.BitmapButton(self, 20000+IDpersonne, wx.Bitmap('Images/16x16/Supprimer_2.png', wx.BITMAP_TYPE_ANY))")
            exec("self.bouton_suppr_" + str(IDpersonne) + ".SetBitmapDisabled(wx.Bitmap('Images/16x16/Supprimer_3.png', wx.BITMAP_TYPE_ANY))")
            exec("self.bouton_suppr_" + str(IDpersonne) + ".SetToolTip(wx.ToolTip(u'Cliquez ici pour supprimer la fiche de ' + prenom + ' ' + nom + ' de Outlook.'))")
            
            coords = []
            texte_coords = ""
            for email in emails : coords.append(email)
            for fixe in fixes : coords.append(fixe)
            coords.append(fax)
            coords.append(mobile)
            for coord in coords :
                if coord != "" : texte_coords += coord + ", "
            texte_coords = texte_coords[:-2]
            
            exec("self.text_nom_" + str(IDpersonne) + " = wx.TextCtrl(self, -1, nom + ', ' + prenom, size=(190,-1))")
            exec("self.text_adresse_" + str(IDpersonne) + " = wx.TextCtrl(self, -1, adresse_resid + ' ' + cp_resid + ' ' + ville_resid, size=(250,-1))")
            exec("self.text_coords_" + str(IDpersonne) + " = wx.TextCtrl(self, -1, texte_coords, size=(200,-1))")
            exec("self.text_datenaiss_" + str(IDpersonne) + " = wx.TextCtrl(self, -1, date_naiss, size=(75,-1))")
            
            # Définition de l'état
            etat = "non synchro"
            for key, valeurs in self.dictContacts.items():
                if valeurs["nom et prenom"] == nom + ", " + prenom :
                    # Ce contact est déjà dans Outlook
                    etat = "synchro"
            
            # Etat des contrôles
            self.Affiche_controles(IDpersonne, etat)
            
            # Layout des contrôles
            exec("gridSizer.Add(self.bouton_synchro_" + str(IDpersonne) + ", flag=wx.ALIGN_CENTER_VERTICAL, border=0)")
            exec("gridSizer.Add(self.bouton_suppr_" + str(IDpersonne) + ", flag=wx.ALIGN_CENTER_VERTICAL, border=0)")
            exec("gridSizer.Add(self.text_nom_" + str(IDpersonne) + ", flag=wx.ALIGN_CENTER_VERTICAL, border=0)")
            exec("gridSizer.Add(self.text_adresse_" + str(IDpersonne) + ", flag=wx.ALIGN_CENTER_VERTICAL, border=0)")
            exec("gridSizer.Add(self.text_coords_" + str(IDpersonne) + ", flag=wx.ALIGN_CENTER_VERTICAL, border=0)")
            exec("gridSizer.Add(self.text_datenaiss_" + str(IDpersonne) + ", flag=wx.ALIGN_CENTER_VERTICAL, border=0)")
            
            # Bind
            exec("self.Bind(wx.EVT_BUTTON, self.OnBoutonSynchro, self.bouton_synchro_" + str(IDpersonne) + ")")
            exec("self.Bind(wx.EVT_BUTTON, self.OnBoutonSuppr, self.bouton_suppr_" + str(IDpersonne) + ")")

        self.SetSizer(gridSizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()
        
        
    def Affiche_controles(self, IDpersonne, etat):
        if etat == "synchro" :
            exec("self.bouton_synchro_" + str(IDpersonne) + ".Enable(False)")
            exec("self.bouton_suppr_" + str(IDpersonne) + ".Enable(True)")
            exec("self.text_nom_" + str(IDpersonne) + ".SetBackgroundColour(COULEUR_SYNCHRO)") # Vert
            exec("self.text_adresse_" + str(IDpersonne) + ".SetBackgroundColour(COULEUR_SYNCHRO)") # Vert
            exec("self.text_coords_" + str(IDpersonne) + ".SetBackgroundColour(COULEUR_SYNCHRO)") # Vert
            exec("self.text_datenaiss_" + str(IDpersonne) + ".SetBackgroundColour(COULEUR_SYNCHRO)") # Vert
        if etat == "modif" :
            exec("self.bouton_synchro_" + str(IDpersonne) + ".Enable(True)")
            exec("self.bouton_suppr_" + str(IDpersonne) + ".Enable(True)")
            exec("self.text_nom_" + str(IDpersonne) + ".SetBackgroundColour(COULEUR_MODIF)") # Orange
            exec("self.text_adresse_" + str(IDpersonne) + ".SetBackgroundColour(COULEUR_MODIF)") # Orange
            exec("self.text_coords_" + str(IDpersonne) + ".SetBackgroundColour(COULEUR_MODIF)") # Orange
            exec("self.text_datenaiss_" + str(IDpersonne) + ".SetBackgroundColour(COULEUR_MODIF)") # Orange
        if etat == "non synchro" :
            exec("self.bouton_synchro_" + str(IDpersonne) + ".Enable(True)")
            exec("self.bouton_suppr_" + str(IDpersonne) + ".Enable(False)")
            exec("self.text_nom_" + str(IDpersonne) + ".SetBackgroundColour(COULEUR_NON_SYNCHRO)") # Rouge
            exec("self.text_adresse_" + str(IDpersonne) + ".SetBackgroundColour(COULEUR_NON_SYNCHRO)") # Rouge
            exec("self.text_coords_" + str(IDpersonne) + ".SetBackgroundColour(COULEUR_NON_SYNCHRO)") # Rouge
            exec("self.text_datenaiss_" + str(IDpersonne) + ".SetBackgroundColour(COULEUR_NON_SYNCHRO)") # Rouge
        self.Refresh()
        

    def OnBoutonSynchro(self, event):
        IDpersonne = event.GetId() - 10000
        self.Synchro(IDpersonne)
        self.Affiche_controles(IDpersonne, "synchro")
    
    def OnBoutonSuppr(self, event):
        IDpersonne = event.GetId() - 20000
        exec("nometprenom = self.text_nom_" + str(IDpersonne) + ".GetValue()")
        self.outlook.Suppression(nometprenom)
        self.Affiche_controles(IDpersonne, "non synchro")

    def Synchro(self, IDpersonne) :
        for ID, civilite, nom, prenom, date_naiss, adresse, cp, ville, emails, fixes, fax, mobile in self.listeContacts:
            if ID == IDpersonne :
                # Préparation des données
                anniversaire = "25/06/1981"
                pays = "France"
        
                if len(emails) == 0 :
                    email1 = ""
                    email2 = ""
                    email3 = ""
                if len(emails) == 1 :
                    email1 = emails[0]
                    email2 = ""
                    email3 = ""
                if len(emails) == 2 :
                    email1 = emails[0]
                    email2 = emails[1]
                    email3 = ""
                if len(emails) == 3 :
                    email1 = emails[0]
                    email2 = emails[1]
                    email3 = emails[2]
        
                if len(fixes) == 0 :
                    fixe1 = ""
                    fixe2 = ""
                if len(fixes) == 1 :
                    fixe1 = fixes[0]
                    fixe2 = ""
                if len(fixes) == 2 :
                    fixe1 = fixes[0]
                    fixe2 = fixes[1]
                
                self.outlook.Enregistrement(civilite, nom, prenom, anniversaire, email1, email2, email3, fixe1, fixe2, fax, mobile, ville, pays, cp, adresse)
                break
            
    def Import_Donnees(self):
        DB = GestionDB.DB()
        req = """SELECT IDindividu, IDcivilite, nom, prenom, date_naiss, adresse_auto, rue_resid, cp_resid, ville_resid
        FROM individus
        ORDER BY nom, prenom;"""
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        listeContacts = []
        for IDindividu, IDcivilite, nom, prenom, date_naiss, adresse_auto, rue_resid, cp_resid, ville_resid in listeDonnees :
            if IDcivilite == 1 : civilite = "Mr"
            if IDcivilite == 2 : civilite = "Mme"
            if IDcivilite == 3 : civilite = "Melle"
            if IDcivilite == 4 : civilite = ""
            if IDcivilite == 5 : civilite = ""
            
            # Recherche de l'adresse automatique
            if adresse_auto != None :
                req = """SELECT rue_resid, cp_resid, ville_resid
                FROM individus
                WHERE IDindividu=%d;""" % adresse_auto
                DB = GestionDB.DB()
                DB.ExecuterReq(req)
                listeDonnees = DB.ResultatReq()
                DB.Close()
                rue_resid, cp_resid, ville_resid = listeDonnees[0]
            
            # Recherche des coordonnées
            req = """SELECT categorie, coordonnee
            FROM coordonnees
            WHERE IDindividu=%d;""" % IDindividu
            DB = GestionDB.DB()
            DB.ExecuterReq(req)
            listeDonnees = DB.ResultatReq()
            DB.Close()
            emails = []
            fixes = []
            fax = ""
            mobile = ""
            for categorie, coordonnee in listeDonnees :
                if categorie == "Email" : emails.append(coordonnee)
                if categorie == "Fixe" : fixes.append(coordonnee)
                if categorie == "Fax" : fax = coordonnee
                if categorie == "Mobile" : mobile = coordonnee
            
            if date_naiss == None : date_naiss = ""
            if nom == None : nom = ""
            if prenom == None : prenom = ""
            if rue_resid == None : rue_resid = ""
            if cp_resid == None : cp_resid = ""
            if ville_resid == None : ville_resid = ""
            
            listeContacts.append((IDindividu, civilite, nom, prenom, date_naiss, rue_resid, cp_resid, ville_resid, emails, fixes, fax, mobile))
        return listeContacts

    def SynchroTout(self):
        for IDpersonne, civilite, nom, prenom, date_naiss, adresse_resid, cp_resid, ville_resid, emails, fixes, fax, mobile in self.listeContacts:
            self.Synchro(IDpersonne)
            self.Affiche_controles(IDpersonne, "synchro")

    def SupprTout(self):
        for IDpersonne, civilite, nom, prenom, date_naiss, adresse_resid, cp_resid, ville_resid, emails, fixes, fax, mobile in self.listeContacts:
            self.outlook.Suppression(nom + ", " + prenom)
            self.Affiche_controles(IDpersonne, "non synchro")


class Dialog(wx.Dialog):
    def __init__(self, parent, ID=-1, title="", size=(280, 200), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX):
        wx.Dialog.__init__(self, parent, ID, title, size, style)
        self.parent = parent
        self.panel_base = wx.Panel(self, -1)
        self.label_intro = wx.StaticText(self.panel_base, -1, _(u"Vous pouvez exporter ici les personnes de la base de données vers le carnet d'adresses de Outlook. La couleur vous indique l'état de synchronisation des fiches."))
        self.sizer_grid_staticbox = wx.StaticBox(self.panel_base, -1, _(u"Liste des personnes de la base de données"))
               
        # Préparation de la grid
        self.gridChamps = PanelContacts(self.sizer_grid_staticbox)
        
        self.label_synchro = wx.StaticText(self.sizer_grid_staticbox, -1, _(u"Synchro."))
        self.label_modif = wx.StaticText(self.sizer_grid_staticbox, -1, _(u"Synchro mais modifié"))
        self.label_non_synchro = wx.StaticText(self.sizer_grid_staticbox, -1, _(u"Non synchro."))
        
        self.label_synchro.SetBackgroundColour(COULEUR_SYNCHRO)
        self.label_modif.SetBackgroundColour(COULEUR_MODIF)
        self.label_non_synchro.SetBackgroundColour(COULEUR_NON_SYNCHRO)
        
        self.bouton_synchroTout = wx.Button(self.sizer_grid_staticbox, -1, _(u"Tout synchroniser"))
        self.bouton_supprTout = wx.Button(self.sizer_grid_staticbox, -1, _(u"Tout désynchroniser"))

        self.bouton_aide = CTRL_Bouton_image.CTRL(self.panel_base, texte=_(u"Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self.panel_base, texte=_(u"Fermer"), cheminImage=Chemins.GetStaticPath("Images/32x32/Fermer.png"))

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.Onbouton_aide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_annuler, self.bouton_annuler)
        self.Bind(wx.EVT_BUTTON, self.OnSynchroTout, self.bouton_synchroTout)
        self.Bind(wx.EVT_BUTTON, self.OnSupprTout, self.bouton_supprTout)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
                
    def __set_properties(self):
        self.SetTitle(_(u"Exportation des contacts vers Outlook"))
        if 'phoenix' in wx.PlatformInfo:
            _icon = wx.Icon()
        else :
            _icon = wx.EmptyIcon()
        _icon.CopyFromBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        self.SetIcon(_icon)
        self.bouton_aide.SetToolTip(wx.ToolTip("Cliquez ici pour obtenir de l'aide"))
        self.bouton_aide.SetSize(self.bouton_aide.GetBestSize())
        self.bouton_annuler.SetToolTip(wx.ToolTip("Cliquez ici pour annuler et fermer"))
        self.bouton_annuler.SetSize(self.bouton_annuler.GetBestSize())

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.label_intro, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 10)
        sizer_grid = wx.StaticBoxSizer(self.sizer_grid_staticbox, wx.VERTICAL)
        
        grid_sizer_2 = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        grid_sizer_2.Add(self.gridChamps, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_commandes = wx.FlexGridSizer(rows=1, cols=7, vgap=5, hgap=5)
        
        grid_sizer_commandes.Add( self.label_synchro, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_commandes.Add( self.label_modif, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_commandes.Add( self.label_non_synchro, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_commandes.Add( (5, 5), 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_commandes.Add(self.bouton_synchroTout, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_commandes.Add(self.bouton_supprTout, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_commandes.AddGrowableCol(3)
        
        grid_sizer_2.Add(grid_sizer_commandes, 1, wx.ALL|wx.EXPAND, 0)
        grid_sizer_2.AddGrowableRow(0)
        grid_sizer_2.AddGrowableCol(0)
        
        sizer_grid.Add(grid_sizer_2, 1, wx.ALL|wx.EXPAND, 0)
        
        grid_sizer_base.Add(sizer_grid, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.panel_base.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        sizer_base.Add(self.panel_base, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_base)
        self.Layout()
        self.SetMinSize((570, 400))
        self.SetSize((570, 550))
        self.CenterOnScreen()
    
    def Onbouton_aide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("ExporterlespersonnesdansMSOutl")

    def Onbouton_annuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnClose(self, event):
        """Ferme proprement la boîte de dialogue depuis la croix Windows."""
        if self.IsModal():
            self.EndModal(wx.ID_CANCEL)
        else:
            self.Destroy()

    def OnSynchroTout(self, event):
        self.gridChamps.SynchroTout()
        event.Skip()
        
    def OnSupprTout(self, event):
        self.gridChamps.SupprTout()
        event.Skip()
        


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
