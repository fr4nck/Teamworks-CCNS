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
import wx.grid as gridlib
import wx.lib.mixins.listctrl as listmix
import sys
import datetime
import os
import shutil
import time
import textwrap
from threading import Thread
import GestionDB
import FonctionsPerso
from Dlg import DLG_Saisie_champs_publipostage
from Dlg import DLG_Parametres_mail
from Utils import UTILS_Fichiers
from Utils import UTILS_Adaptations
import six

if "win" in sys.platform :
    import win32com.client
    from pythoncom import CoInitialize, CoUninitialize

DICT_DONNEES = {}



class Dialog(wx.Dialog):
    def __init__(self, parent, title="", dictDonnees=None):
        if dictDonnees is None:
            dictDonnees = {}
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)

        global DICT_DONNEES
        DICT_DONNEES = dictDonnees
        self.parent = parent
        self.listePages = ("Page1", "Page2", "Page3", "Page4", "Page5", "Page6")
        
        self.panel_base = wx.Panel(self, -1)
        self.static_line = wx.StaticLine(self.panel_base, -1)
        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self.panel_base,
            texte=_(u"Aide"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"),
            role="quiet",
        )
        self.bouton_retour = CTRL_Bouton_image.CTRL(
            self.panel_base,
            texte=_(u"Retour"),
            cheminImage=Chemins.GetStaticPath("Images/BoutonsImages/Retour_L72.png"),
            role="quiet",
        )
        self.bouton_suite = CTRL_Bouton_image.CTRL(
            self.panel_base,
            texte=_(u"Suivant"),
            cheminImage=Chemins.GetStaticPath("Images/BoutonsImages/Suite_L72.png"),
            role="primary",
        )
        self.bouton_annuler = CTRL_Bouton_image.CTRL(
            self.panel_base,
            texte=_(u"Annuler"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"),
            role="quiet",
        )
        self.__set_properties()
        self.__do_layout()
                
        self.Bind(wx.EVT_BUTTON, self.Onbouton_aide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_retour, self.bouton_retour)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_suite, self.bouton_suite)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_annuler, self.bouton_annuler)

        self.bouton_retour.Enable(False)
        self.nbrePages = len(self.listePages)    
        self.pageVisible = 1
                        
        # Création des pages
        self.Creation_Pages()

    def SetSuiteAction(self, texte, image, role="primary"):
        """Met à jour l'action principale sans revenir aux BitmapButton historiques."""
        self.bouton_suite.SetTexte(_(texte))
        self.bouton_suite.SetImage(Chemins.GetStaticPath("Images/BoutonsImages/%s" % image))
        self.bouton_suite.SetRole(role)
    
    def Creation_Pages(self):
        """ Creation des pages """
        for numPage in range(1, self.nbrePages+1) :
            page_class = globals().get(self.listePages[numPage-1])
            if not callable(page_class):
                raise RuntimeError("Page de publipostage inconnue : %s" % self.listePages[numPage-1])
            page = page_class(self.panel_base)
            setattr(self, "page" + str(numPage), page)
            self.sizer_pages.Add(page, 1, wx.EXPAND, 0)
            self.sizer_pages.Layout()
            page.Show(False)
        self.page1.Show(True)
        self.sizer_pages.Layout()

    def __set_properties(self):
        self.SetTitle(_(u"Edition de documents"))
        if 'phoenix' in wx.PlatformInfo:
            _icon = wx.Icon()
        else :
            _icon = wx.EmptyIcon()
        _icon.CopyFromBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        self.SetIcon(_icon)
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour obtenir de l'aide")))
        self.bouton_retour.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour revenir à la page précédente")))
        self.bouton_suite.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour passer à l'étape suivante")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Cliquez pour fermer l'assistant")))
        self.SetMinSize((540, 490))

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=0)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=6, vgap=10, hgap=10)
        sizer_pages = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_base.Add(sizer_pages, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(self.static_line, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_retour, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_suite, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, wx.LEFT, 10)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL|wx.EXPAND, 10)
        self.panel_base.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        sizer_base.Add(self.panel_base, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_base)
        sizer_base.Fit(self)
        self.Layout()
        self.CentreOnScreen()
        self.sizer_pages = sizer_pages

    def Onbouton_aide(self, event):
        dlg = wx.MessageDialog(self, _(u"L'aide pour ce nouveau module est en cours de rédaction."), _(u"Aide indisponible"), wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Imprimeruncontrat")

    def Onbouton_retour(self, event):
        # rend invisible la page affichée
        pageCible = getattr(self, "page" + str(self.pageVisible))
        pageCible.Show(False)
        # Fait apparaître nouvelle page
        self.pageVisible -= 1
        pageCible = getattr(self, "page" + str(self.pageVisible))
        pageCible.Show(True)
        self.sizer_pages.Layout()
        # Si on quitte la dernière page, on active le bouton Suivant
        if self.pageVisible == self.nbrePages-1 :
            self.bouton_suite.Enable(True)
            self.SetSuiteAction(u"Suivant", "Suite_L72.png")
        if self.pageVisible == self.nbrePages :
            self.bouton_suite.Enable(True)
            self.SetSuiteAction(u"Valider", "Valider_L72.png")
        # Si on revient à la première page, on désactive le bouton Retour
        if self.pageVisible == 1 :
            self.bouton_retour.Enable(False)
        # On active le bouton annuler
        self.bouton_annuler.Enable(True)

    def Onbouton_suite(self, event):
        # Vérifie que les données de la page en cours sont valides
        validation = self.ValidationPages()
        if validation == False : return
        # Si on est déjà sur la dernière page : on termine
        if self.pageVisible == self.nbrePages :
            self.Terminer()
            return
        # Rend invisible la page affichée
        pageCible = getattr(self, "page" + str(self.pageVisible))
        pageCible.Show(False)
        # Fait apparaître nouvelle page
        self.pageVisible += 1
        pageCible = getattr(self, "page" + str(self.pageVisible))
        pageCible.Show(True)
        self.sizer_pages.Layout()
        # Si on arrive à l'avant-dernière page, on désactive le bouton Suivant
        if self.pageVisible == self.nbrePages :
            self.SetSuiteAction(u"Valider", "Valider_L72.png")
        # Si on quitte la première page, on active le bouton Retour
        if self.pageVisible > 1 :
            self.bouton_retour.Enable(True)
            
    def Onbouton_annuler(self, event):
        self.EndModal(wx.ID_CANCEL)
        
    def ValidationPages(self) :
        """ Validation des données avant changement de pages """
        validation = getattr(self, "page%s" % self.pageVisible).Validation()
        return validation
    
    def Terminer(self):
        self.EndModal(wx.ID_OK)


# ------------------------------------------------------------------------------------------------------------
#---INTRODUCTION---#400080#80FF80------------------------------------------------------

class Page1(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.parent = self.GetGrandParent()
        
        self.imgBandeau = wx.StaticBitmap(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/Bandeaux/Contrat.png"), wx.BITMAP_TYPE_ANY) )
        
        self.label_titre = wx.StaticText(self, -1, _(u"Bienvenue dans l'assistant d'édition de documents"))
        
        # Label Html
        txtIntro = u"""
        <FONT face="Arial" color="#000000" size=2>
            <P>Vous pouvez ici éditer un document grâce à la technique du publipostage. Cette technique utilise des documents que vous avez créé avec Word, OpenOffice ou l'éditeur de texte intégré de Teamworks. 
            L'intérêt de cela est d'imprimer des documents totalement personnalisés.</P>
            
            <P>Vous devrez juste importer ou écrire un document avec l'un de ces logiciels, dans lequel vous placez tout simplement aux endroits de votre choix des mots-clés : 
            {NOM}, {PRENOM}, {CIVILITE}, etc... Ces mots-clés sont consultables sur la page suivante.</P>
            
            <P>Par exemple, le texte <I>"Je suis {PRENOM} {NOM}" </I> donnera après le publipostage : <I>"Je suis David DUPOND" </I>.</P>
            
            <P>Vous pouvez ainsi remplir tous vos documents à partir d'un simple modèle sans aucune difficulté ! Mais pour un petit coup de main, cliquez sur 'AIDE'...</P>
            </FONT>""" 
        self.label_intro = FonctionsPerso.TexteHtml(self, texte=txtIntro, Enabled=False)
        
        self.__set_properties()
        self.__do_layout()
        
    def __set_properties(self):
        self.label_titre.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=10, hgap=10)
        grid_sizer_boutons = wx.FlexGridSizer(rows=3, cols=1, vgap=5, hgap=5)
        grid_sizer_base.Add(self.label_titre, 0, 0, 0)
        grid_sizer_base.Add(self.imgBandeau, 0, wx.LEFT|wx.RIGHT, 30)
        grid_sizer_base.Add(self.label_intro, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 20)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(2)
        

    def Validation(self):
        return True


# ------------------------------------------------------------------------------------------------------------
#---DONNEES---#400080#80FF80------------------------------------------------------

class Page2(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.sizer_champs_staticbox = wx.StaticBox(self, -1, _(u"Données disponibles"))
        self.label_titre = wx.StaticText(self, -1, _(u"1. Vérification des données du document"))
        self.label_intro = wx.StaticText(self, -1, _(u"Vous pouvez vérifier et modifier ci-dessous les données qui seront fusionnées :"))
        
        self.ImportationChampsPerso()
        
        self.grid = Grid_donnees(self.sizer_champs_staticbox)
        self.grid.SetSize((50, 50))
        self.grid.Remplissage() 
        
        self.label_remarque = wx.StaticText(self.sizer_champs_staticbox, -1, _(u"*Champs personnalisés"))
        self.label_remarque.SetFont(wx.Font(7, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        
        self.bouton_imprimer = CTRL_Bouton_image.CTRL(
            self.sizer_champs_staticbox,
            texte=_(u"Imprimer"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Imprimante.png"),
        )
        self.bouton_ajouter = CTRL_Bouton_image.CTRL(
            self.sizer_champs_staticbox,
            texte=_(u"Ajouter"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Ajouter.png"),
        )
        self.bouton_modifier = CTRL_Bouton_image.CTRL(
            self.sizer_champs_staticbox,
            texte=_(u"Modifier"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Modifier.png"),
        )
        self.bouton_supprimer = CTRL_Bouton_image.CTRL(
            self.sizer_champs_staticbox,
            texte=_(u"Supprimer"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Supprimer.png"),
            role="danger",
        )

        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimer, self.bouton_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        
        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.bouton_imprimer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour afficher au format PDF la liste des mots-clés \ndisponibles pour votre modèle de document.\n\nUtilisez cette liste pour créer facilement votre modèle de documents : \nIl vous suffit de taper les mots-clés souhaités dans votre document.")))
        self.bouton_ajouter.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour créer un champ personnalisé")))
        self.bouton_modifier.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour modifier le champ personnalisé sélectionné dans la grille")))
        self.bouton_supprimer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour supprimer le champ personnalisé sélectionné dans la grille")))
        self.label_titre.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        sizer_champs = wx.StaticBoxSizer(self.sizer_champs_staticbox, wx.HORIZONTAL)
        grid_sizer_champs = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        grid_sizer_base.Add(self.label_titre, 0, 0, 0)
        grid_sizer_base.Add(self.label_intro, 0, wx.LEFT, 20)
        grid_sizer_champs.Add(self.grid, 1, wx.EXPAND, 0)
        
        grid_sizer_boutons = wx.FlexGridSizer(rows=5, cols=1, vgap=5, hgap=5)
        grid_sizer_boutons.Add(self.bouton_imprimer, 0, 0, 0)
        grid_sizer_boutons.Add((10, 10), 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ajouter, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_modifier, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_supprimer, 0, 0, 0)
        grid_sizer_boutons.AddGrowableRow(1)
        
        grid_sizer_champs.Add(grid_sizer_boutons, 1, wx.EXPAND, 0)
        grid_sizer_champs.AddGrowableRow(0)
        grid_sizer_champs.AddGrowableCol(0)
        grid_sizer_champs.Add(self.label_remarque, 0, wx.LEFT, 10)
        sizer_champs.Add(grid_sizer_champs, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(sizer_champs, 1, wx.LEFT|wx.EXPAND, 20)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)
    
    def ImportationChampsPerso(self):
        DB = GestionDB.DB()
        req = "SELECT IDchamp, categorie, nom, mot_cle, defaut FROM publipostage_champs WHERE categorie='%s' order by IDchamp" % DICT_DONNEES["CATEGORIE"]
        DB.ExecuterReq(req)
        listeChamps = DB.ResultatReq()
        DB.Close()
        for IDchamp, categorie, nom, mot_cle, defaut in listeChamps :
            self.AjouterChampPerso(IDchamp, mot_cle, defaut)
        
    def OnBoutonChamps(self, event):
        dlg = Config_ChampsContrats.Dialog(self)
        dlg.ShowModal()
        dlg.Destroy()
    
    def OnBoutonAjouter(self, event):
        self.Ajouter()

    def OnBoutonModifier(self, event):
        listeSelections = self.grid.GetSelectedRows()
        if len(listeSelections) == 0 :
            dlg = wx.MessageDialog(self, _(u"Sélectionnez d'abord un champ personnalisé à modifier en cliquant sur son entête de ligne"), "Information", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        elif len(listeSelections) > 1 :
            dlg = wx.MessageDialog(self, _(u"Vous ne pouvez sélectionner qu'un seul champ personnalisé à la fois"), "Information", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        else :
            index = listeSelections[0]
            self.Modifier(index)
        
    def OnBoutonSupprimer(self, event):
        listeSelections = self.grid.GetSelectedRows()
        if len(listeSelections) == 0 :
            dlg = wx.MessageDialog(self, _(u"Sélectionnez d'abord un champ personnalisé à supprimer en cliquant sur son entête de ligne"), "Information", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        elif len(listeSelections) > 1 :
            dlg = wx.MessageDialog(self, _(u"Vous ne pouvez sélectionner qu'un seul champ personnalisé à la fois"), "Information", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        else :
            index = listeSelections[0]
            self.Supprimer(index)
    
    def AjouterChampPerso(self, IDchamp=0, motcle="", valeurDefaut=""):
        global DICT_DONNEES
        DICT_DONNEES["MOTSCLES"].append( (motcle, IDchamp) )
        for numDoc in range(1, DICT_DONNEES["NBREDOCUMENTS"]+1):
            DICT_DONNEES[numDoc][motcle] = valeurDefaut
    
    def ModifierChampPerso(self, IDchamp=0, nouveauMotcle="", ancienMotcle="", valeurDefaut=""):
        global DICT_DONNEES
        index = 0
        for motcleTmp, type in DICT_DONNEES["MOTSCLES"] :
            if type == IDchamp :
                DICT_DONNEES["MOTSCLES"][index] = (nouveauMotcle, IDchamp)
            index += 1
        for numDoc in range(1, DICT_DONNEES["NBREDOCUMENTS"]+1):
            del DICT_DONNEES[numDoc][ancienMotcle]
            DICT_DONNEES[numDoc][nouveauMotcle] = valeurDefaut
        
    def SupprimerChampPerso(self, IDchamp=0, motcle=""):
        global DICT_DONNEES
        DICT_DONNEES["MOTSCLES"].remove((motcle, IDchamp))
        for numDoc in range(1, DICT_DONNEES["NBREDOCUMENTS"]+1):
            del DICT_DONNEES[numDoc][motcle]        
        
 
    

    def Ajouter(self):
        dlg = DLG_Saisie_champs_publipostage.Dialog(self, IDchamp=0, categorie=DICT_DONNEES["CATEGORIE"], listeMotsCles=DICT_DONNEES["MOTSCLES"])
        dlg.ShowModal()
        dlg.Destroy()

    def Modifier(self, numLigne=0):
        index = numLigne        
        motcle, IDchamp = DICT_DONNEES["MOTSCLES"][index]

        dlg = DLG_Saisie_champs_publipostage.Dialog(self, IDchamp=IDchamp, categorie=DICT_DONNEES["CATEGORIE"], listeMotsCles=DICT_DONNEES["MOTSCLES"])
        dlg.ShowModal()
        dlg.Destroy()

    def Supprimer(self, numLigne=0):
        index = numLigne
        motcle, IDchamp = DICT_DONNEES["MOTSCLES"][index]

        # Demande de confirmation
        txtMessage = six.text_type((_(u"Voulez-vous vraiment supprimer ce champ ? \n\n> ") + motcle))
        dlgConfirm = wx.MessageDialog(self, txtMessage, _(u"Confirmation de suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
        reponse = dlgConfirm.ShowModal()
        dlgConfirm.Destroy()
        if reponse == wx.ID_NO:
            return
        
        # Suppression du type de pièce
        DB = GestionDB.DB()
        DB.ReqDEL("publipostage_champs", "IDchamp", IDchamp)
        DB.Close() 
        
        # MàJ du ListCtrl
        self.SupprimerChampPerso(IDchamp=IDchamp, motcle=motcle)
        self.grid.Remplissage()
        
    def Validation(self):
        return True

    def OnBoutonImprimer(self, event):
        """ Imprime la liste des mots-clés et des valeurs attachées """
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.rl_config import defaultPageSize
        from reportlab.lib.units import inch, cm
        from reportlab.lib import colors
        self.hauteur_page = defaultPageSize[1]
        self.largeur_page = defaultPageSize[0]
        self.inch = inch
        PAGE_HEIGHT=defaultPageSize[1]
        PAGE_WIDTH=defaultPageSize[0]
        nomDoc = UTILS_Fichiers.GetRepTemp("motscles_documents.pdf")
        if "win" in sys.platform : nomDoc = nomDoc.replace("/", "\\")
        doc = SimpleDocTemplate(nomDoc)
        story = []
        dataTableau = []
        largeursColonnes = ( (420, 100) )
        dateDuJour = str(datetime.date.today())
        dateDuJour = str(dateDuJour[8:10]) + "/" + str(dateDuJour[5:7]) + "/" + str(dateDuJour[:4])
        dataTableau.append( (_(u"Mots-clés pour documents"), _(u"Edité le %s") % dateDuJour )  )
        style = TableStyle([
                            ('BOX', (0,0), (-1,-1), 0.25, colors.black), 
                            ('VALIGN', (0,0), (-1,-1), 'TOP'), 
                            ('ALIGN', (0,0), (0,0), 'LEFT'), 
                            ('FONT',(0,0),(0,0), "Helvetica-Bold", 16), 
                            ('ALIGN', (1,0), (1,0), 'RIGHT'), 
                            ('FONT',(1,0),(1,0), "Helvetica", 6), 
                            ])
        tableau = Table(dataTableau, largeursColonnes)
        tableau.setStyle(style)
        story.append(tableau)
        story.append(Spacer(0,20))
        for IDdocument in range(1, DICT_DONNEES["NBREDOCUMENTS"]+1) :
            dataTableau = []
            largeursColonnes = (150, 370)
            dataTableau.append( (_(u"Mots-clés"), _(u"Valeurs du document n°%d") % IDdocument) )
            for motcle, type_motcle in DICT_DONNEES["MOTSCLES"] :
                nomMotcle = "{%s}" % motcle
                if type_motcle != "base" : nomMotcle += "*"
                if motcle in DICT_DONNEES[IDdocument] :
                    valeur = DICT_DONNEES[IDdocument][motcle]
                else:
                    valeur = ""
                dataTableau.append( (nomMotcle, valeur) )
            style = TableStyle([
                                ('GRID', (0,0), (-1,-1), 0.25, colors.black),
                                ('ALIGN', (0,0), (-1,0), 'CENTRE'),
                                ('FONT',(0,0),(-1,-1), "Helvetica", 8),
                                ('FONT',(0,0),(-1,0), "Helvetica-Bold", 8),
                                ])
            tableau = Table(dataTableau, largeursColonnes)
            tableau.setStyle(style)
            story.append(tableau)
            story.append(Spacer(0,20))
        doc.build(story)
        FonctionsPerso.LanceFichierExterne(nomDoc)
        

class Grid_donnees(gridlib.Grid): 
    def __init__(self, parent):
        gridlib.Grid.__init__(self, parent, -1, size=(100, 100))
        self.moveTo = None
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.OnContextMenu)
        self.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.OnContextMenu)
        self.CreateGrid(0, 0)
        
    def Remplissage(self):
        nbreDocuments = DICT_DONNEES["NBREDOCUMENTS"]
        nbre_motscles = len(DICT_DONNEES["MOTSCLES"])
        nbreLignesTotal = nbre_motscles
        if nbreDocuments == 1 :
            largeurColonnes = 260
        else:
            largeurColonnes = 190
        if self.GetNumberRows() > 0 : 
            self.DeleteRows(0, self.GetNumberRows())
        if self.GetNumberCols() > 0 : 
            self.DeleteCols(0, self.GetNumberCols())
        self.ClearGrid()
        self.SetRowLabelSize(140)
        self.SetColLabelSize(20)
        if self.GetNumberRows() == 0 : 
            self.AppendRows(nbreLignesTotal)
        if self.GetNumberCols() == 0 : 
            self.AppendCols(nbreDocuments)
        indexLigne = 0
        for motcle, type_motcle in DICT_DONNEES["MOTSCLES"] :
            motcle = "{%s}" % motcle
            if type_motcle != "base" : motcle += "*"
            self.SetRowLabelValue(indexLigne, motcle)
            indexLigne += 1
        for IDdocument in range(1, nbreDocuments+1) :
            indexColonne = IDdocument-1
            self.SetColLabelValue(indexColonne, _(u"Document n°%d") % IDdocument)
            self.SetColSize(indexColonne, largeurColonnes)
            dict_valeurs = DICT_DONNEES[IDdocument]
            indexLigne = 0
            for motcle, type_motcle in DICT_DONNEES["MOTSCLES"] :
                if motcle in dict_valeurs :
                    valeur = dict_valeurs[motcle]
                    if type(valeur) == int: valeur = str(valeur)
                    if type(valeur) == float: valeur = str(valeur)
                    self.SetCellValue(indexLigne, indexColonne, valeur)
                indexLigne += 1
        if 'phoenix' in wx.PlatformInfo:
            self.Bind(gridlib.EVT_GRID_CELL_CHANGED, self.OnCellChange)
        else :
            self.Bind(gridlib.EVT_GRID_CELL_CHANGE, self.OnCellChange)

    def OnCellChange(self, evt):
        global DICT_DONNEES
        indexLigne = evt.GetRow()
        indexColonnes = evt.GetCol()
        IDdocument = indexColonnes+1
        valeur = self.GetCellValue(indexLigne, indexColonnes)
        motcle = DICT_DONNEES["MOTSCLES"][indexLigne][0]
        DICT_DONNEES[IDdocument][motcle] = valeur

    def OnIdle(self, evt):
        if self.moveTo != None:
            self.SetGridCursor(self.moveTo[0], self.moveTo[1])
            self.moveTo = None
        evt.Skip()
        
    def OnContextMenu(self, event):
        self.numLigneTmp = event.GetRow()
        if self.numLigneTmp == -1 : return
        motcle, IDchamp = DICT_DONNEES["MOTSCLES"][self.numLigneTmp]
        menuPop = UTILS_Adaptations.Menu()
        item = wx.MenuItem(menuPop, 10, _(u"Ajouter un champ personnalisé"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Ajouter, id=10)
        menuPop.AppendSeparator()
        item = wx.MenuItem(menuPop, 20, _(u"Modifier le champ personnalisé '%s'") % motcle)
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Modifier, id=20)
        if IDchamp == "base" : item.Enable(False)
        item = wx.MenuItem(menuPop, 30, _(u"Supprimer le champ personnalisé '%s'") % motcle)
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Supprimer, id=30)
        if IDchamp == "base" : item.Enable(False)
        menuPop.AppendSeparator()
        item = wx.MenuItem(menuPop, 90, _(u"Imprimer la liste de tous les champs disponibles"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Imprimer, id=90)
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Menu_Ajouter(self, event):
        self.GetParent().Ajouter()
        
    def Menu_Modifier(self, event):
        self.GetParent().Modifier(self.numLigneTmp)

    def Menu_Supprimer(self, event):
        self.GetParent().Supprimer(self.numLigneTmp)

    def Menu_Imprimer(self, event):
        self.GetParent().OnBoutonImprimer(None)
                
# ------------------------------------------------------------------------------------------------------------
#---CHOIX DU LOGICIEL---#400080#80FF80-----------------------------------------------
        
class Page3(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        categorie_document = DICT_DONNEES["CATEGORIE"]
        self.numChoix = FonctionsPerso.Parametres(mode="get", categorie="document_%s" % categorie_document, nom="choix_editeur", valeur=1)
        self.sizer_staticbox_1 = wx.StaticBox(self, -1, _(u"Création d'un courrier"))
        self.label_titre = wx.StaticText(self, -1, _(u"2. Choix du logiciel de publipostage"))
        self.label_intro = wx.StaticText(self, -1, _(u"Sélectionnez le logiciel qui sera utilisé pour l'édition du document :"))
        self.radio_1 = wx.RadioButton(self.sizer_staticbox_1, -1, "", style=wx.RB_GROUP)
        self.bitmap_1 = wx.StaticBitmap(self.sizer_staticbox_1, -1, wx.Bitmap(Chemins.GetStaticPath("Images/48x48/MsWord.png"), wx.BITMAP_TYPE_ANY))
        self.label_choix_1_titre = wx.StaticText(self.sizer_staticbox_1, -1, "Microsoft WORD")
        self.label_choix_1_description = wx.StaticText(self.sizer_staticbox_1, -1, "Suite Microsoft Office")
        self.radio_2 = wx.RadioButton(self.sizer_staticbox_1, -1, "")
        self.bitmap_2 = wx.StaticBitmap(self.sizer_staticbox_1, -1, wx.Bitmap(Chemins.GetStaticPath("Images/48x48/Writer.png"), wx.BITMAP_TYPE_ANY))
        self.label_choix_2_titre = wx.StaticText(self.sizer_staticbox_1, -1, "WRITER")
        self.label_choix_2_description = wx.StaticText(self.sizer_staticbox_1, -1, "Suite OpenOffice")
        self.radio_3 = wx.RadioButton(self.sizer_staticbox_1, -1, "")
        self.bitmap_3 = wx.StaticBitmap(self.sizer_staticbox_1, -1, wx.Bitmap(Chemins.GetStaticPath("Images/48x48/Texte.png"), wx.BITMAP_TYPE_ANY))
        self.label_choix_3_titre = wx.StaticText(self.sizer_staticbox_1, -1, _(u"Traitement de texte intégré"))
        self.label_choix_3_description = wx.StaticText(self.sizer_staticbox_1, -1, _(u"Ecrivez et imprimer des documents directement dans Teamworks-CCNS \ngrâce à Teamword, le traitement de texte intégré"))
        self.sizer_staticbox_2 = wx.StaticBox(self, -1, _(u"Création d'un Email"))
        self.radio_4 = wx.RadioButton(self.sizer_staticbox_2, -1, "")
        self.bitmap_4 = wx.StaticBitmap(self.sizer_staticbox_2, -1, wx.Bitmap(Chemins.GetStaticPath("Images/48x48/Email.png"), wx.BITMAP_TYPE_ANY))
        self.label_choix_4_titre = wx.StaticText(self.sizer_staticbox_2, -1, _(u"Editeur d'Email"))
        self.label_choix_4_description = wx.StaticText(self.sizer_staticbox_2, -1, _(u"Ecrivez et envoyez des Emails directement dans Teamworks-CCNS \ngrâce à Teamword, l'éditeur d'Email intégré"))
        if "linux" in sys.platform :
            self.radio_2.SetValue(True)
            self.numChoix = 2
            self.radio_1.Enable(False)
            self.bitmap_1.Enable(False)
            self.label_choix_1_titre.Enable(False)
            self.label_choix_1_description.Enable(False)
        self.__set_properties()
        self.__do_layout()
        self.SetChoix()
        self.bitmap_1.Bind(wx.EVT_LEFT_DOWN, self.OnClickImg1)
        self.bitmap_2.Bind(wx.EVT_LEFT_DOWN, self.OnClickImg2)
        self.bitmap_3.Bind(wx.EVT_LEFT_DOWN, self.OnClickImg3)
        self.bitmap_4.Bind(wx.EVT_LEFT_DOWN, self.OnClickImg4)
        self.label_choix_1_titre.Bind(wx.EVT_LEFT_DOWN, self.OnClickImg1)
        self.label_choix_2_titre.Bind(wx.EVT_LEFT_DOWN, self.OnClickImg2)
        self.label_choix_3_titre.Bind(wx.EVT_LEFT_DOWN, self.OnClickImg3)
        self.label_choix_4_titre.Bind(wx.EVT_LEFT_DOWN, self.OnClickImg4)
        self.label_choix_1_description.Bind(wx.EVT_LEFT_DOWN, self.OnClickImg1)
        self.label_choix_2_description.Bind(wx.EVT_LEFT_DOWN, self.OnClickImg2)
        self.label_choix_3_description.Bind(wx.EVT_LEFT_DOWN, self.OnClickImg3) 
        self.label_choix_4_description.Bind(wx.EVT_LEFT_DOWN, self.OnClickImg4) 

    def __set_properties(self):
        self.label_titre.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.radio_1.SetToolTip(wx.ToolTip("Choix 1"))
        self.label_choix_1_titre.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.label_choix_1_description.SetFont(wx.Font(7, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.radio_2.SetToolTip(wx.ToolTip("Choix 2"))
        self.label_choix_2_titre.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.label_choix_2_description.SetFont(wx.Font(7, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.radio_3.SetToolTip(wx.ToolTip("Choix 3"))
        self.label_choix_3_titre.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.label_choix_3_description.SetFont(wx.Font(7, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.radio_4.SetToolTip(wx.ToolTip("Choix 4"))
        self.label_choix_4_titre.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.label_choix_4_description.SetFont(wx.Font(7, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.label_titre, 0, 0, 0)
        grid_sizer_base.Add(self.label_intro, 0, wx.LEFT|wx.RIGHT, 20)
        sizer_choix_1 = wx.StaticBoxSizer(self.sizer_staticbox_1, wx.VERTICAL)
        grid_sizer_choix = wx.FlexGridSizer(rows=4, cols=3, vgap=10, hgap=10)
        grid_sizer_choix.Add(self.radio_1, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_choix.Add(self.bitmap_1, 0, 0, 0)
        grid_sizer_1 = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        grid_sizer_1.Add(self.label_choix_1_titre, 0, 0, 0)
        grid_sizer_1.Add(self.label_choix_1_description, 0, 0, 0)
        grid_sizer_choix.Add(grid_sizer_1, 1, wx.EXPAND, 0)
        grid_sizer_choix.Add(self.radio_2, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_choix.Add(self.bitmap_2, 0, 0, 0)
        grid_sizer_2 = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        grid_sizer_2.Add(self.label_choix_2_titre, 0, 0, 0)
        grid_sizer_2.Add(self.label_choix_2_description, 0, 0, 0)
        grid_sizer_choix.Add(grid_sizer_2, 1, wx.EXPAND, 0)
        grid_sizer_choix.Add(self.radio_3, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_choix.Add(self.bitmap_3, 0, 0, 0)
        grid_sizer_3 = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        grid_sizer_3.Add(self.label_choix_3_titre, 0, 0, 0)
        grid_sizer_3.Add(self.label_choix_3_description, 0, 0, 0)
        grid_sizer_choix.Add(grid_sizer_3, 1, wx.EXPAND, 0)
        grid_sizer_choix.AddGrowableCol(2)
        sizer_choix_1.Add(grid_sizer_choix, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(sizer_choix_1, 1, wx.LEFT|wx.EXPAND, 20)
        sizer_choix_2 = wx.StaticBoxSizer(self.sizer_staticbox_2, wx.VERTICAL)
        grid_sizer_choix_2 = wx.FlexGridSizer(rows=4, cols=3, vgap=10, hgap=10)
        grid_sizer_choix_2.Add(self.radio_4, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_choix_2.Add(self.bitmap_4, 0, 0, 0)
        grid_sizer_1 = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        grid_sizer_1.Add(self.label_choix_4_titre, 0, 0, 0)
        grid_sizer_1.Add(self.label_choix_4_description, 0, 0, 0)
        grid_sizer_choix_2.Add(grid_sizer_1, 1, wx.EXPAND, 0)
        grid_sizer_choix_2.AddGrowableCol(2)
        sizer_choix_2.Add(grid_sizer_choix_2, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(sizer_choix_2, 1, wx.LEFT|wx.EXPAND, 20)
        grid_sizer_base.AddGrowableCol(0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)

    def GetChoix(self):
        if self.radio_1.GetValue() == True : numChoix = 1
        if self.radio_2.GetValue() == True : numChoix = 2
        if self.radio_3.GetValue() == True : numChoix = 3
        if self.radio_4.GetValue() == True : numChoix = 4
        return numChoix

    def SetChoix(self):
        if self.numChoix == 1 : self.radio_1.SetValue(True)
        if self.numChoix == 2 : self.radio_2.SetValue(True)
        if self.numChoix == 3 : self.radio_3.SetValue(True)
        if self.numChoix == 4 : self.radio_4.SetValue(True)

    def OnClickImg1(self, event):
        self.radio_1.SetValue(True)
        event.Skip()

    def OnClickImg2(self, event):
        self.radio_2.SetValue(True)
        event.Skip()

    def OnClickImg3(self, event):
        self.radio_3.SetValue(True)
        event.Skip()

    def OnClickImg4(self, event):
        self.radio_4.SetValue(True)
        event.Skip()
                        
    def Validation(self):
        self.numChoix = self.GetChoix()
        categorie_document = DICT_DONNEES["CATEGORIE"]
        FonctionsPerso.Parametres(mode="set", categorie="document_%s" % categorie_document, nom="choix_editeur", valeur=self.numChoix)
        self.GetGrandParent().page4.MAJaffichage()
        return True

# ------------------------------------------------------------------------------------------------------------
#---CHOIX DU FICHIER---#400080#80FF80------------------------------------------------------


class Page4(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.repCourant = os.getcwd()
        self.nomFichier = ""
        self.cheminDest = UTILS_Fichiers.GetRepModeles()
        self.choixLogiciel = 1
        self.choixModele = ""
        
        self.sizer_choix_staticbox = wx.StaticBox(self, -1, _(u"Liste des documents disponibles"))
        self.label_titre = wx.StaticText(self, -1, _(u"3. Choix du document de publipostage"))
        self.label_intro = wx.StaticText(self, -1, _(u"Sélectionnez un fichier dans la liste ou importez-en un en cliquant sur 'importer'."))
        
        self.listCtrl = ListCtrl_fichiers(self.sizer_choix_staticbox, controller=self)
        
        self.bouton_importer = CTRL_Bouton_image.CTRL(
            self.sizer_choix_staticbox,
            texte=_(u"Importer"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Inbox.png"),
        )
        self.bouton_actualiser = CTRL_Bouton_image.CTRL(
            self.sizer_choix_staticbox,
            texte=_(u"Actualiser"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Actualiser.png"),
        )
        self.bouton_ajouter = CTRL_Bouton_image.CTRL(
            self.sizer_choix_staticbox,
            texte=_(u"Ajouter"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Ajouter.png"),
        )
        self.bouton_modifier = CTRL_Bouton_image.CTRL(
            self.sizer_choix_staticbox,
            texte=_(u"Modifier"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Modifier.png"),
        )
        self.bouton_supprimer = CTRL_Bouton_image.CTRL(
            self.sizer_choix_staticbox,
            texte=_(u"Supprimer"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Supprimer.png"),
            role="danger",
        )

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImporter, self.bouton_importer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonActualiser, self.bouton_actualiser)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        
    def __set_properties(self):
        self.label_titre.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.bouton_importer.SetToolTip(wx.ToolTip(_(u"Cliquer ici pour importer un document présent à un autre endroit sur votre ordinateur.")))
        self.bouton_actualiser.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour actualiser l'affichage des noms de fichiers")))
        self.bouton_ajouter.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour créer un document")))
        self.bouton_modifier.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour modifier le document sélectionné dans la liste")))
        self.bouton_supprimer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour supprimer le document sélectionné dans la liste")))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=10, hgap=10)
        sizer_choix = wx.StaticBoxSizer(self.sizer_choix_staticbox, wx.VERTICAL)
        grid_sizer_choix = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_boutons = wx.FlexGridSizer(rows=6, cols=1, vgap=5, hgap=5)
        grid_sizer_base.Add(self.label_titre, 0, 0, 0)
        grid_sizer_base.Add(self.label_intro, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 20)
        grid_sizer_choix.Add(self.listCtrl, 1, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_importer, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_actualiser, 0, 0, 0)
        grid_sizer_boutons.Add((10, 10), 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ajouter, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_modifier, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_supprimer, 0, 0, 0)
        grid_sizer_boutons.AddGrowableRow(2)
        grid_sizer_choix.Add(grid_sizer_boutons, 1, wx.EXPAND, 0)
        grid_sizer_choix.AddGrowableCol(0)
        grid_sizer_choix.AddGrowableRow(0)
        sizer_choix.Add(grid_sizer_choix, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(sizer_choix, 1, wx.LEFT|wx.EXPAND, 20)
        grid_sizer_base.AddGrowableRow(2)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        self.grid_sizer_base = grid_sizer_base
        self.grid_sizer_choix = grid_sizer_choix
        self.grid_sizer_boutons = grid_sizer_boutons
        
    def MAJaffichage(self):
        self.choixLogiciel = self.GetChoixLogiciel()
        categorie_document = DICT_DONNEES["CATEGORIE"]
        self.choixModele = FonctionsPerso.Parametres(mode="get", categorie="document_%s" % categorie_document, nom="choix_modele", valeur="")
        self.grid_sizer_base.Layout()
        self.grid_sizer_choix.Layout()
        self.grid_sizer_boutons.Layout()
        self.MAJ_ListCtrl()
        
    def GetChoixLogiciel(self):
        return self.GetGrandParent().page3.numChoix
        
    def OnBoutonImporter(self, event):
        if self.choixLogiciel == 1 : 
            wildcard = "Microsoft WORD (*.doc)|*.doc|All files (*.*)|*.*"
        if self.choixLogiciel == 2 : 
            wildcard = "OpenOffice WRITER (*.odt)|*.odt|All files (*.*)|*.*"
        if self.choixLogiciel == 3 or self.choixLogiciel == 4 : 
            wildcard = "Teamword (*.twd)|*.twd|All files (*.*)|*.*"
        cheminDefaut = UTILS_Fichiers.GetRepModeles()
        dlg = wx.FileDialog(self, message=_(u"Choisissez un document"), defaultDir=cheminDefaut, defaultFile="", wildcard=wildcard, style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            nomFichierCourt = dlg.GetFilename()
            nomFichierLong = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            self.MAJ_ListCtrl()
            return
        self.cheminDest = UTILS_Fichiers.GetRepModeles()
        exists = self.FichierExists(self.cheminDest, nomFichierCourt)
        if exists :
            dlg = wx.MessageDialog(self, _(u"Un fichier '") + nomFichierCourt + _(u"' porte déjà ce nom dans le répertoire des modèles de documents \n\nSi vous souhaitez quand même l'importer, vous devez modifier son nom."), "Information", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.MAJ_ListCtrl()
            return
        shutil.copy(nomFichierLong, self.cheminDest)
        dlg = wx.MessageDialog(self, _(u"Le fichier '") + nomFichierCourt + _(u"' a été copié dans le répertoire des modèles de documents"), "Information", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        self.MAJ_ListCtrl()
    
    def OnBoutonActualiser(self, event):
        self.MAJ_ListCtrl()
        
    def OnBoutonAjouter(self, event):
        if self.choixLogiciel == 1 :
            try : 
                Word = win32com.client.gencache.EnsureDispatch("Word.Application")
            except :
                dlg = wx.MessageDialog(self, _(u"Le logiciel Microsoft Word ne peut pas être ouvert. \nEtes-vous bien sûr qu'il est présent sur votre ordinateur ?"), "Information", wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return False
            Word.Visible = True
            Word.Documents.Add()
            texte = u"""Je viens de créer pour vous un nouveau document WORD. Vous pouvez maintenant y saisir le texte de votre choix. Pour insérer des données pour le publipostage, c'est très simple : tapez son mot-clé ! Exemple : "Je suis {CIVILITE} {NOM}" donnera après le publipostage "Je suis David DUPOND"... \n
Voici la liste des mots-clés du contrat en cours. Elle vous aidera à écrire votre texte : \n\n"""
            for motcle, type_motcle in DICT_DONNEES["MOTSCLES"] :
                texte += "  - {" + motcle + "} \n"
            texte += _(u"\n(Effacez bien-sûr ce petit texte d'introduction après l'avoir lu !!!)")
            Word.Selection.TypeText(texte)
            Word.Activate
        if self.choixLogiciel == 2 :
            if "win" in sys.platform :
                try : 
                    objServiceManager = win32com.client.Dispatch("com.sun.star.ServiceManager")
                    objDesktop = objServiceManager.CreateInstance("com.sun.star.frame.Desktop")  
                except :
                    dlg = wx.MessageDialog(self, _(u"Le logiciel OpenOffice WRITER ne peut pas être ouvert. \nEtes-vous bien sûr qu'il est présent sur votre ordinateur ?"), "Information", wx.OK | wx.ICON_INFORMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return False
                args = []
                objDocument = objDesktop.loadComponentFromURL("private:factory/swriter", "_blank", 0, args) 
                objDocument.CurrentController.Frame.ContainerWindow.Visible = True
                texte = u"""Je viens de créer pour vous un nouveau document WORD. Vous pouvez maintenant y saisir le texte de votre choix. Pour insérer des données pour le publipostage, c'est très simple : tapez son mot-clé ! Exemple : "Je suis {CIVILITE} {NOM}" donnera après le publipostage "Je suis David DUPOND"... \n
Voici la liste des mots-clés du contrat en cours. Elle vous aidera à écrire votre texte : \n\n"""
                for motcle, type_motcle in DICT_DONNEES["MOTSCLES"] :
                    texte += "  - {" + motcle + "} \n"
                texte += _(u"\n(Effacez bien-sûr ce petit texte d'introduction après l'avoir lu !!!)")
                objText = objDocument.GetText()
                objCursor = objText.createTextCursor()
                objText.insertString(objCursor, texte, 0)
            if "linux" in sys.platform :
                from Utils import UTILS_Pilotageooo
                ooo = UTILS_Pilotageooo.Pilotage()
                ooo.Creer_doc()
                ooo.Ecrire_exemple(DICT_DONNEES["MOTSCLES"])
        if self.choixLogiciel == 3 or self.choixLogiciel == 4 :
            listeMotsCles = []
            for motcle, type_motcle in DICT_DONNEES["MOTSCLES"] :
                listeMotsCles.append(u"{%s}" % motcle)
            from Dlg import DLG_Teamword
            Twd = DLG_Teamword.MyFrame(None, motsCles=listeMotsCles)
            Twd.Show()
            Twd.CreateNewFile()
            texte = u"""Je viens de créer pour vous un nouveau document Teamword Vous pouvez maintenant y saisir le texte de votre choix. Pour insérer des données pour le publipostage, c'est très simple : tapez son mot-clé ! Exemple : "Je suis {CIVILITE} {NOM}" donnera après le publipostage "Je suis David DUPOND"... \n
La liste des mots-clés disponibles est présentée dans le cadre ci-contre. Double-cliquez sur un mot-clé pour l'insérer dans votre document. \n\n"""
            texte += _(u"\n(Effacez bien-sûr ce petit texte d'introduction après l'avoir lu !!!)")
            Twd.rtc.WriteText(texte)
                
    def OnBoutonModifier(self, event):
        index = self.listCtrl.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(self, _(u"Vous devez d'abord sélectionner un fichier à modifier dans la liste."), "Information", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        if self.choixLogiciel == 1 :
            try : Word = win32com.client.Dispatch("Word.Application")
            except :
                dlg = wx.MessageDialog(self, _(u"Le logiciel Microsoft Word ne peut pas être ouvert. \nEtes-vous bien sûr qu'il est présent sur votre ordinateur ?"), "Information", wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return False
            Word.Visible = True
            fichier = self.cheminDest + "/" + self.nomFichier
            Word.Documents.Open(fichier)
        if self.choixLogiciel == 2 :
            if "win" in sys.platform :
                try : 
                    objServiceManager = win32com.client.Dispatch("com.sun.star.ServiceManager")
                    objDesktop = objServiceManager.CreateInstance("com.sun.star.frame.Desktop")  
                except :
                    dlg = wx.MessageDialog(self, _(u"Le logiciel OpenOffice WRITER ne peut pas être ouvert. \nEtes-vous bien sûr qu'il est présent sur votre ordinateur ?"), "Information", wx.OK | wx.ICON_INFORMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return False
                fichier = self.cheminDest + "/" + self.nomFichier
                args = []
                modele = "file:///" + fichier.replace("\\", "/")
                objDocument = objDesktop.loadComponentFromURL(modele, "_blank", 0, args)
                objDocument.CurrentController.Frame.ContainerWindow.Visible = True
            if "linux" in sys.platform :
                fichier = self.cheminDest + "/" + self.nomFichier
                from Utils import UTILS_Pilotageooo
                ooo = UTILS_Pilotageooo.Pilotage()
                ooo.Ouvrir_doc(fichier)
        if self.choixLogiciel == 3 or self.choixLogiciel == 4 :
            listeMotsCles = []
            for motcle, type_motcle in DICT_DONNEES["MOTSCLES"] :
                listeMotsCles.append(u"{%s}" % motcle)
            from Dlg import DLG_Teamword
            Twd = DLG_Teamword.MyFrame(None, motsCles=listeMotsCles)
            Twd.Show()
            fichier = self.cheminDest + "/" + self.nomFichier
            Twd.OpenFile(fichier)
        
    def OnBoutonSupprimer(self, event):
        index = self.listCtrl.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(self, _(u"Vous devez d'abord sélectionner un fichier à modifier dans la liste."), "Information", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        dlg = wx.MessageDialog(self, _(u"Souhaitez-vous vraiment supprimer le fichier suivant ? \n\n>  ") + self.nomFichier + _(u" \n\nAttention, la suppression est définitive !!!"),  _(u"Confirmation de suppression"), wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT)
        if dlg.ShowModal() == wx.ID_NO :
            return
        fichier = UTILS_Fichiers.GetRepModeles() + "/" + self.nomFichier
        os.remove(fichier)
        self.MAJ_ListCtrl()

    def FichierExists(self, rep, fichier):
        for nomFichier in os.listdir(rep) :
            if not(os.path.isdir(rep + '/' + nomFichier)):
                if os.fsdecode(nomFichier) == fichier :
                    return True
        return False    
            
    def MAJ_ListCtrl(self):
        self.listCtrl.MAJListeCtrl()   
                
    def Validation(self):
        if self.nomFichier == "" or self.listCtrl.GetFirstSelected() == -1 :
            dlg = wx.MessageDialog(self, _(u"Vous devez sélectionner un fichier de publipostage dans la liste."), "Information", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        index = self.listCtrl.GetFirstSelected()
        nomModele = self.listCtrl.getColumnText(index, 0)
        categorie_document = DICT_DONNEES["CATEGORIE"]
        self.choixModele = FonctionsPerso.Parametres(mode="set", categorie="document_%s" % categorie_document, nom="choix_modele", valeur=nomModele)
        self.GetGrandParent().page5.MAJaffichage()
        return True


class ListCtrl_fichiers(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.ColumnSorterMixin):
    def __init__(self, parent, controller=None):
        wx.ListCtrl.__init__( self, parent, -1, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_SINGLE_SEL)
        self.criteres = ""
        self.parent = controller or parent
        tailleIcones = 16
        self.il = wx.ImageList(tailleIcones, tailleIcones)
        self.imgTriAz= self.il.Add(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Tri_az.png"), wx.BITMAP_TYPE_PNG))
        self.imgTriZa= self.il.Add(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Tri_za.png"), wx.BITMAP_TYPE_PNG))
        self.img1 = self.il.Add(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/MsWord.png"), wx.BITMAP_TYPE_PNG))
        self.img2 = self.il.Add(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Writer.png"), wx.BITMAP_TYPE_PNG))
        self.img3 = self.il.Add(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte.png"), wx.BITMAP_TYPE_PNG))
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        self.attr1 = wx.ItemAttr()
        self.attr1.SetBackgroundColour("#EEF4FB")
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def OnSize(self, event):
        self.Refresh()
        event.Skip()

    def Remplissage(self):
        self.Importation()
        self.nbreColonnes = 3
        self.InsertColumn(0, _(u"Nom du fichier"))
        self.SetColumnWidth(0, 270) 
        self.InsertColumn(1, _(u"Taille"))
        self.SetColumnWidth(1, 50) 
        self.InsertColumn(2, _(u"Dernière modification"))
        self.SetColumnWidth(2, 100) 
        self.itemDataMap = self.donnees
        self.itemIndexMap = list(self.donnees.keys())
        self.SetItemCount(self.nbreLignes)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, self.nbreColonnes)
        self.SortListItems(0, 1)

    def OnItemSelected(self, event):
        if self.GetFirstSelected() == -1:
            return False
        index = self.GetFirstSelected()
        self.parent.nomFichier = self.getColumnText(index, 0)
        
    def OnItemDeselected(self, event):
        pass
        
    def Importation(self):
        self.dictFichiers = self.GetListeDocuments()
        self.nbreLignes = len(self.dictFichiers)
        self.donnees = {}
        x = 1
        for ID, valeurs in self.dictFichiers.items():
            index = x
            self.donnees[index] = valeurs
            x += 1
        
    def MAJListeCtrl(self):
        self.ClearAll()
        self.Remplissage()
        self.resizeLastColumn(0)
        listmix.ColumnSorterMixin.__init__(self, self.nbreColonnes)
        self.SelectionChoixModele()
        
    def SelectionChoixModele(self):
        choixModele = self.parent.choixModele
        if choixModele == "" : return
        for index in range(self.GetItemCount()) :
            nom = self.getColumnText(index, 0)
            if nom == choixModele : 
                self.Select(index)
                break

    def listeEnDict(self, liste):
        dictio = {}
        x = 1
        for ligne in liste:
            index = x
            dictio[index] = ligne
            x += 1
        return dictio
           
    def OnItemActivated(self, event):
        self.parent.Modifier()
        
    def getColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()

    def OnGetItemText(self, item, col):
        index=self.itemIndexMap[item]
        valeur = self.itemDataMap[index][col]
        if col == 2 :
            if valeur[4:5]=="-" and valeur[7:8]=="-":
                valeur = str(valeur[8:10])+"/"+str(valeur[5:7])+"/"+str(valeur[0:4])
        return valeur

    def OnGetItemImage(self, item):
        index=self.itemIndexMap[item]
        extension =self.dictFichiers[index][0][-3:]
        if extension == "doc" : return self.img1
        if extension == "odt" : return self.img2
        if extension == "twd" : return self.img3
        return -1

    def OnGetItemAttr(self, item):
        if item % 2 == 1:
            return self.attr1
        else:
            return None

    def SortItems(self,sorter=FonctionsPerso.cmp):
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
        menuPop.AppendSeparator()
        item = wx.MenuItem(menuPop, 40, _(u"Parcourir"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Inbox.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Parcourir, id=40)
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Menu_Ajouter(self, event):
        self.parent.OnBoutonAjouter(None)
        
    def Menu_Modifier(self, event):
        self.parent.OnBoutonModifier(None)

    def Menu_Supprimer(self, event):
        self.parent.OnBoutonSupprimer(None)

    def Menu_Parcourir(self, event):
        self.parent.OnBoutonImporter(None)
        
    def GetListeDocuments(self):
        cheminRep = UTILS_Fichiers.GetRepModeles()
        contenuRep = os.listdir(cheminRep)
        if self.parent.choixLogiciel == 1 : listeExtensions = [".doc",]
        if self.parent.choixLogiciel == 2 : listeExtensions = [".odt",]
        if self.parent.choixLogiciel == 3 : listeExtensions = [".twd",]
        if self.parent.choixLogiciel == 4 : listeExtensions = [".twd",]
        dictFichiers = {}
        x = 1
        for nomFichier in contenuRep :
            if not(os.path.isdir(cheminRep + '/' + nomFichier)):
                nomLong, extension = os.path.splitext(cheminRep + "/" + nomFichier)
                tailleFichier = os.path.getsize(cheminRep + '/' + nomFichier)
                if tailleFichier > 1000 :
                    tailleFichier = str(int(tailleFichier/1000)) + " Kb"
                else:
                    tailleFichier = str(tailleFichier) + " b"
                derniereModif = time.strftime('%d/%m/%Y %H:%M', time.localtime(os.path.getmtime(cheminRep + '/' + nomFichier)))
                if extension in listeExtensions :
                    dictFichiers[x] = (nomFichier, tailleFichier, derniereModif)
                    x += 1
        return dictFichiers
    
# ------------------------------------------------------------------------------------------------------------
#---OPTIONS D'IMPRESSION---#400080#80FF80---------------------------------------
        
class Page5(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.choixLogiciel = 1
        self.repertoire = UTILS_Fichiers.GetRepEditions()
        self.dictParamMail = {}
        self.sizer_contenu_staticbox = wx.StaticBox(self, -1, _(u"Options d'édition"))
        self.label_titre = wx.StaticText(self, -1, _(u"4. Edition du document"))
        self.label_intro = wx.StaticText(self, -1, _(u"Vous pouvez définir les options d'édition ci-dessous puis cliquez sur 'Valider'."))
        self.label_envoi_mail = wx.StaticText(self.sizer_contenu_staticbox, -1, _(u"Paramètres d'envoi des Emails :"))
        self.panel_param_mail = DLG_Parametres_mail.Panel(self.sizer_contenu_staticbox, activer_a=False, activer_cci=False, activer_bouton_envoyer=False)
        self.ctrl_apercu_avant_envoi = wx.CheckBox(self.sizer_contenu_staticbox, -1, _(u"Aperçu du document avant l'envoi par mail"))
        self.checkbox_impression = wx.CheckBox(self.sizer_contenu_staticbox, -1, "")
        self.label_impress1 = wx.StaticText(self.sizer_contenu_staticbox, -1, "Impression en")
        self.combo_box_exemplaires = wx.Choice(self.sizer_contenu_staticbox, -1, choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
        self.label_impress2 = wx.StaticText(self.sizer_contenu_staticbox, -1, "exemplaire(s)")
        self.label_imprimante = wx.StaticText(self.sizer_contenu_staticbox, -1, _(u"     Imprimante :"))
        nomImprimanteDefaut, listeImprimantes, a, b = FonctionsPerso.ListeImprimantes()
        self.combo_box_imprimante = wx.Choice(self.sizer_contenu_staticbox, -1, choices=listeImprimantes)
        self.combo_box_imprimante.SetStringSelection(nomImprimanteDefaut)
        self.checkbox_save = wx.CheckBox(self.sizer_contenu_staticbox, -1, "")
        self.label_save = wx.StaticText(self.sizer_contenu_staticbox, -1, "Sauvegarde :")
        self.label_repertoire = wx.StaticText(self.sizer_contenu_staticbox, -1, _(u"Répertoire :"))
        self.text_repertoire = wx.TextCtrl(self.sizer_contenu_staticbox, -1, "")
        self.bouton_repertoire = CTRL_Bouton_image.CTRL(
            self.sizer_contenu_staticbox,
            texte=_(u"Parcourir…"),
            role="quiet",
        )
        self.label_nom_fichier = wx.StaticText(self.sizer_contenu_staticbox, -1, "Noms des fichiers :")
        self.ctrl_nom_fichiers = Grid_noms_fichiers(self.sizer_contenu_staticbox)
        self.label_prefixe = wx.StaticText(self.sizer_contenu_staticbox, -1, _(u"Préfixe des noms :"))
        self.text_prefixe = wx.TextCtrl(self.sizer_contenu_staticbox, -1, "")
        self.text_prefixe.Enable(False)
        self.bouton_prefixe = CTRL_Bouton_image.CTRL(
            self.sizer_contenu_staticbox,
            texte=_(u"Préfixe…"),
            role="quiet",
        )
        self.checkbox_apercu = wx.CheckBox(self.sizer_contenu_staticbox, -1, "")
        self.label_apercu = wx.StaticText(self.sizer_contenu_staticbox, -1, _(u"Aperçu avant impression"))
        self.__set_properties()
        self.__do_layout()
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImporter, self.bouton_repertoire)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonPrefixe, self.bouton_prefixe)
        self.text_repertoire.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocusRep)
        self.Bind(wx.EVT_CHECKBOX, self.Oncheckbox_impression, self.checkbox_impression)
        self.Bind(wx.EVT_CHECKBOX, self.Oncheckbox_save, self.checkbox_save)
        categorie_document = DICT_DONNEES["CATEGORIE"]
        check_impression = FonctionsPerso.Parametres(mode="get", categorie="document_%s" % categorie_document, nom="check_impression", valeur=True)
        check_save = FonctionsPerso.Parametres(mode="get", categorie="document_%s" % categorie_document, nom="check_save", valeur=True)
        nbre_impression = FonctionsPerso.Parametres(mode="get", categorie="document_%s" % categorie_document, nom="nbre_impression", valeur=True)
        repertoire_save = FonctionsPerso.Parametres(mode="get", categorie="document_%s" % categorie_document, nom="repertoire_save", valeur=self.repertoire)
        check_apercu = FonctionsPerso.Parametres(mode="get", categorie="document_%s" % categorie_document, nom="check_apercu", valeur=False)
        self.checkbox_impression.SetValue(check_impression)
        self.checkbox_save.SetValue(check_save)
        self.combo_box_exemplaires.SetSelection(nbre_impression)
        self.text_repertoire.SetValue(self.repertoire)
        self.checkbox_apercu.SetValue(check_apercu)
        self.Oncheckbox_save(None)
        self.Oncheckbox_impression(None)
        self.AfficherPanelMail(False)

    def __set_properties(self):
        self.label_titre.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.combo_box_exemplaires.SetMinSize((40, -1))
        self.bouton_repertoire.SetToolTip(wx.ToolTip(_(u"Cliquez ici définir un autre répertoire de destination")))
        self.text_repertoire.SetToolTip(wx.ToolTip(_(u"Vous pouvez sélectionner un autre répertoire en cliquant sur le bouton 'Parcourir…' ou en tapant directement dans ce cadre de texte.")))
        self.ctrl_nom_fichiers.SetToolTip(wx.ToolTip(_(u"Vous pouvez saisir un autre nom de fichier en tapant directement dans ce cadre de texte.")))
        self.bouton_prefixe.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour modifier le préfixe des noms de fichiers pour ce modèle de document")))
        self.text_prefixe.SetToolTip(wx.ToolTip(_(u"Vous devez définir ici le préfixe des noms de fichiers pour ce modèle de document")))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=10, hgap=10)
        sizer_contenu = wx.StaticBoxSizer(self.sizer_contenu_staticbox, wx.VERTICAL)
        grid_sizer_contenu = wx.FlexGridSizer(rows=12, cols=2, vgap=0, hgap=10)
        grid_sizer_options_save = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=5)
        grid_sizer_repertoire = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_base.Add(self.label_titre, 0, 0, 0)
        grid_sizer_base.Add(self.label_intro, 0, wx.LEFT, 20)
        grid_sizer_contenu.Add((1, 1), 0, wx.EXPAND, 0)
        grid_sizer_contenu.Add(self.label_envoi_mail, 0, wx.EXPAND, 0) 
        grid_sizer_contenu.Add((1, 1), 0, wx.EXPAND, 0)
        grid_sizer_contenu.Add(self.panel_param_mail, 0, wx.EXPAND, 0) 
        grid_sizer_contenu.Add((1, 1), 0, wx.EXPAND, 0)
        grid_sizer_contenu.Add(self.ctrl_apercu_avant_envoi, 0, wx.EXPAND, 0) 
        grid_sizer_contenu.Add(self.checkbox_impression, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options_impress = wx.FlexGridSizer(rows=1, cols=3, vgap=5, hgap=5)
        grid_sizer_options_impress.Add(self.label_impress1, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options_impress.Add(self.combo_box_exemplaires, 0, 0, 0)
        grid_sizer_options_impress.Add(self.label_impress2, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.Add(grid_sizer_options_impress, 1, wx.EXPAND, 0)
        grid_sizer_contenu.Add((10, 10), 0, 0, 0)
        grid_sizer_contenu.Add((10, 10), 0, 0, 0)
        grid_sizer_contenu.Add((5, 5), 1, wx.EXPAND, 0)
        grid_sizer_imprimantes = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_imprimantes.Add(self.label_imprimante, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_imprimantes.Add(self.combo_box_imprimante, 0, wx.EXPAND, 0)
        grid_sizer_imprimantes.AddGrowableCol(1)
        grid_sizer_contenu.Add(grid_sizer_imprimantes, 1, wx.EXPAND, 0)
        grid_sizer_contenu.Add((10, 10), 0, 0, 0)
        grid_sizer_contenu.Add((10, 10), 0, 0, 0)
        grid_sizer_contenu.Add(self.checkbox_save, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.Add(self.label_save, 0, wx.EXPAND, 0)
        grid_sizer_contenu.Add((10, 10), 0, 0, 0)
        grid_sizer_contenu.Add((10, 10), 0, 0, 0)
        grid_sizer_contenu.Add((10, 10), 0, 0, 0)
        grid_sizer_options_save.Add(self.label_repertoire, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_repertoire.Add(self.text_repertoire, 0, wx.EXPAND, 0)
        grid_sizer_repertoire.Add(self.bouton_repertoire, 0, 0, 0)
        grid_sizer_repertoire.AddGrowableCol(0)
        grid_sizer_options_save.Add(grid_sizer_repertoire, 1, wx.EXPAND, 0)
        grid_sizer_options_save.Add(self.label_nom_fichier, 0, wx.ALIGN_RIGHT, 0)
        grid_sizer_options_save.Add(self.ctrl_nom_fichiers, 0, wx.EXPAND, 0)
        grid_sizer_options_save.Add(self.label_prefixe, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_prefixe = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_prefixe.Add(self.text_prefixe, 0, wx.EXPAND, 0)
        grid_sizer_prefixe.Add(self.bouton_prefixe, 0, 0, 0)
        grid_sizer_prefixe.AddGrowableCol(0)
        grid_sizer_options_save.Add(grid_sizer_prefixe, 1, wx.EXPAND, 0)
        grid_sizer_options_save.AddGrowableCol(1)
        grid_sizer_contenu.Add(grid_sizer_options_save, 1, wx.EXPAND, 0)
        grid_sizer_contenu.Add((10, 10), 0, 0, 0)
        grid_sizer_contenu.Add((10, 10), 0, 0, 0)
        grid_sizer_contenu.Add(self.checkbox_apercu, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.Add(self.label_apercu, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.AddGrowableCol(1)
        sizer_contenu.Add(grid_sizer_contenu, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(sizer_contenu, 1, wx.LEFT|wx.EXPAND, 20)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        self.grid_sizer_base = grid_sizer_base
        self.grid_sizer_contenu = grid_sizer_contenu
                    
    def AfficherPanelMail(self, etat=True):
        if etat == True :
            self.panel_param_mail.Show(True)
            self.ctrl_apercu_avant_envoi.Show(True)
            self.label_envoi_mail.Show(True)
            etat = False
        else:
            self.panel_param_mail.Show(False)
            self.ctrl_apercu_avant_envoi.Show(False)
            self.label_envoi_mail.Show(False)
            etat = True
        self.checkbox_impression.Show(etat)
        self.label_impress1.Show(etat)
        self.combo_box_exemplaires.Show(etat)
        self.label_impress2.Show(etat)
        self.label_imprimante.Show(etat)
        self.combo_box_imprimante.Show(etat)
        self.checkbox_save.Show(etat)
        self.label_save.Show(etat)
        self.label_repertoire.Show(etat)
        self.text_repertoire.Show(etat)
        self.bouton_repertoire.Show(etat)
        self.label_nom_fichier.Show(etat)
        self.ctrl_nom_fichiers.Show(etat)
        self.label_prefixe.Show(etat)
        self.text_prefixe.Show(etat)
        self.bouton_prefixe.Show(etat)
        self.checkbox_apercu.Show(etat)
        self.label_apercu.Show(etat)
        self.grid_sizer_base.Layout() 
        self.grid_sizer_contenu.Layout() 
    
    def Oncheckbox_save(self, event):
        if self.checkbox_save.GetValue() == True :
            self.text_repertoire.Enable(True)
            self.ctrl_nom_fichiers.Enable(True)
            self.bouton_repertoire.Enable(True)
            self.bouton_prefixe.Enable(True)
        else:
            self.text_repertoire.Enable(False)
            self.ctrl_nom_fichiers.Enable(False)
            self.bouton_repertoire.Enable(False)
            self.bouton_prefixe.Enable(False)

    def Oncheckbox_impression(self, event):
        if self.checkbox_impression.GetValue() == True :
            self.combo_box_exemplaires.Enable(True)
            self.combo_box_imprimante.Enable(True)
        else:
            self.combo_box_exemplaires.Enable(False)
            self.combo_box_imprimante.Enable(False)

    def OnKillFocusRep(self, event):
        self.repertoire = self.text_repertoire.GetValue()
        event.Skip()
        
    def MAJaffichage(self):
        self.choixLogiciel = self.GetChoixLogiciel()
        self.text_repertoire.SetValue(self.repertoire)
        if self.choixLogiciel == 1 : self.extension = ".doc"
        if self.choixLogiciel == 2 : self.extension = ".odt"
        if self.choixLogiciel == 3 or self.choixLogiciel == 4 : self.extension = ".twd"
        if self.choixLogiciel == 1 : 
            self.label_save.SetLabel(_(u"Sauvegarde du contrat au format WORD :"))
            self.label_apercu.SetLabel(_(u"Aperçu avant impression sous WORD"))
        if self.choixLogiciel == 2 : 
            self.label_save.SetLabel(_(u"Sauvegarde du contrat au format OpenOffice Writer :"))
            self.label_apercu.SetLabel(_(u"Aperçu avant impression sous OpenOffice Writer"))
        prefixe = self.SetPrefixe()
        self.MAJ_nomsFichiers(prefixe)
        if self.choixLogiciel == 4 :
            self.AfficherPanelMail(True)
        else:
            self.AfficherPanelMail(False)
    
    def MAJ_nomsFichiers(self, prefixe):
        dict_noms_fichiers = {}
        for IDdocument in range(1, DICT_DONNEES["NBREDOCUMENTS"]+1):
            nomFichier = u"%s_%s" % (prefixe, self.FormatageSuffixeFichier(IDdocument))
            dict_noms_fichiers[IDdocument] = { "SELECTION" : 1, "NOMFICHIER" : nomFichier }
        self.ctrl_nom_fichiers.Remplissage(dict_noms_fichiers) 
    
    def FormatageSuffixeFichier(self, IDdocument):
        formatageNom = DICT_DONNEES["NOMEDITION"]
        listeElements = []
        for champ in formatageNom.split("_") :
            if champ == "IDdocument" :
                element = str(IDdocument)
            elif champ == "datedujour" :    
                element = time.strftime("%d-%m-%Y",time.localtime())  
            elif "*" in champ :
                champTemp, nbreCaracteres = champ.split("*")
                element = DICT_DONNEES[IDdocument][champTemp][:int(nbreCaracteres)]
            else:
                element = DICT_DONNEES[IDdocument][champ]
            element = element.replace("/", "-")
            listeElements.append(element)
        nomFichier = "_".join(listeElements)
        return nomFichier
    
    def OnBoutonImporter(self, event):
        if self.choixLogiciel == 1 : 
            wildcard = "Microsoft WORD (*.doc)|*.doc|All files (*.*)|*.*"
        if self.choixLogiciel == 2 : 
            wildcard = "OpenOffice WRITER (*.png)|*.png|All files (*.*)|*.*"
        cheminDefaut = UTILS_Fichiers.GetRepEditions()
        dlg = wx.DirDialog(self, _(u"Sélectionnez un répertoire de destination"), defaultPath=cheminDefaut, style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.repertoire = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        self.MAJaffichage()
    
    def OnBoutonPrefixe(self, event):
        prefixe = self.SetPrefixe(modeModification=True)
        self.MAJ_nomsFichiers(prefixe)
    
    def SetPrefixe(self, modeModification=False):
        categorie_document = DICT_DONNEES["CATEGORIE"]
        nomModele = self.GetGrandParent().page4.nomFichier
        prefixe = FonctionsPerso.Parametres(mode="get", categorie="document_%s" % categorie_document, nom=_(u"prefixe_%s") % nomModele, valeur="")
        if prefixe == "" or modeModification == True :
            prefixeValide = False
            while prefixeValide == False :
                texte = _(u"Veuillez saisir le préfixe pour les noms de fichiers rattachés au modèle de document '%s'.") % nomModele
                dlg = wx.TextEntryDialog(self, textwrap.fill(texte, width=80) + "\n\n(Exemples : 'CDD', 'Invitation', 'Attestation'...)", _(u"Choix d'un préfixe"), prefixe)
                if dlg.ShowModal() == wx.ID_OK :
                    prefixe = dlg.GetValue()
                    FonctionsPerso.Parametres(mode="set", categorie="document_%s" % categorie_document, nom=_(u"prefixe_%s") % nomModele, valeur=prefixe)
                dlg.Destroy()
                if prefixe == "" : 
                    prefixeValide = False
                else:
                    prefixeValide = True
        self.text_prefixe.SetValue(prefixe)
        return prefixe
            
    def GetChoixLogiciel(self):
        return self.GetGrandParent().page3.numChoix        
                
    def Validation(self):
        if self.choixLogiciel == 4 :
            etat = self.panel_param_mail.ValidationDonnees()
            if etat == False : 
                return False
            self.dictParamMail = self.panel_param_mail.GetParametresPourPublipostage()
        else:
            if self.checkbox_impression.GetValue() == False and self.checkbox_save.GetValue() == False and self.checkbox_apercu.GetValue() == False :
                dlg = wx.MessageDialog(self, _(u"Vous devez cocher au moins une option d'édition."), "Erreur de saisie", wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return False
            if self.checkbox_save.GetValue() == True and (self.text_repertoire.GetValue() == "" or os.path.isdir(self.text_repertoire.GetValue()) == False) :
                dlg = wx.MessageDialog(self, _(u"Vous devez saisir un répertoire valide pour la sauvegarde"), "Erreur de saisie", wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                self.text_repertoire.SetFocus()
                return False
            erreurNomFichier = False
            dictNomsFichiers = self.ctrl_nom_fichiers.GetDictNomsFichiers()
            for IDdocument, dictValeurs in dictNomsFichiers.items():
                if dictValeurs["NOMFICHIER"] == "" :
                    erreurNomFichier = True
            if self.checkbox_save.GetValue() == True and erreurNomFichier == True :
                dlg = wx.MessageDialog(self, _(u"Un ou plusieurs noms de fichiers ne sont pas valides"), "Erreur de saisie", wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                self.text_repertoire.SetFocus()
                return False
            categorie_document = DICT_DONNEES["CATEGORIE"]
            FonctionsPerso.Parametres(mode="set", categorie="document_%s" % categorie_document, nom="check_impression", valeur=self.checkbox_impression.GetValue())
            FonctionsPerso.Parametres(mode="set", categorie="document_%s" % categorie_document, nom="check_save", valeur=self.checkbox_save.GetValue())
            FonctionsPerso.Parametres(mode="set", categorie="document_%s" % categorie_document, nom="nbre_impression", valeur=self.combo_box_exemplaires.GetSelection())
            FonctionsPerso.Parametres(mode="set", categorie="document_%s" % categorie_document, nom="repertoire_save", valeur=self.repertoire)
            FonctionsPerso.Parametres(mode="set", categorie="document_%s" % categorie_document, nom="check_apercu", valeur=self.checkbox_apercu.GetValue())
        self.GetGrandParent().page6.termine = False
        self.GetGrandParent().page6.choixLogiciel = self.choixLogiciel
        return True
    

class Grid_noms_fichiers(gridlib.Grid): 
    def __init__(self, parent):
        gridlib.Grid.__init__(self, parent, -1, size=(100, 90))
        self.moveTo = None
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.dict_noms_fichiers = {}
        self.CreateGrid(0, 0)
        
    def Remplissage(self, dict_noms_fichiers=None ):
        if dict_noms_fichiers is None:
            dict_noms_fichiers = {}
        self.dict_noms_fichiers = dict_noms_fichiers
        nbreDocuments = DICT_DONNEES["NBREDOCUMENTS"] + 5
        if self.GetNumberRows() > 0 : 
            self.DeleteRows(0, self.GetNumberRows())
        if self.GetNumberCols() > 0 : 
            self.DeleteCols(0, self.GetNumberCols())
        self.ClearGrid()
        if self.GetNumberRows() == 0 : 
            self.AppendRows(nbreDocuments)
        if self.GetNumberCols() == 0 : 
            self.AppendCols(2)
        self.SetRowLabelSize(70)
        self.SetColLabelSize(1)
        self.SetColSize(0, 20)
        self.SetColSize(1, 200)
        self.SetColLabelValue(0, "")
        self.SetColLabelValue(1, "")
        indexLigne = 0
        for IDdocument in range(1, nbreDocuments+1) :
            if IDdocument in dict_noms_fichiers :
                self.SetRowLabelValue(indexLigne, _(u"Doc n°%d") % IDdocument)
                self.SetCellValue(indexLigne, 0, str(dict_noms_fichiers[IDdocument]["SELECTION"]))
                self.SetCellEditor(indexLigne, 0, gridlib.GridCellBoolEditor())
                self.SetCellRenderer(indexLigne, 0, gridlib.GridCellBoolRenderer())
                self.SetCellValue(indexLigne, 1, dict_noms_fichiers[IDdocument]["NOMFICHIER"])
            else:
                self.SetRowLabelValue(indexLigne, u"")
                self.SetCellValue(indexLigne, 0, "")
                self.SetCellValue(indexLigne, 1, "")
                self.SetReadOnly(indexLigne, 0, True)
                self.SetReadOnly(indexLigne, 1, True)
            indexLigne += 1
        if 'phoenix' in wx.PlatformInfo:
            self.Bind(gridlib.EVT_GRID_CELL_CHANGED, self.OnCellChange)
        else :
            self.Bind(gridlib.EVT_GRID_CELL_CHANGE, self.OnCellChange)

    def GetDictNomsFichiers(self):
        return self.dict_noms_fichiers
        
    def OnCellChange(self, evt):
        indexLigne = evt.GetRow()
        indexColonne = evt.GetCol()
        IDdocument = indexLigne+1
        valeur = self.GetCellValue(indexLigne, indexColonne)
        if valeur == "" and indexColonne == 1:
            self.moveTo = indexLigne, indexColonne
            self.SetCellValue(indexLigne, indexColonne, valeur)
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement saisir un nom de fichier pour ce document"), _(u"Erreur de saisie"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        if indexColonne == 0 :
            self.dict_noms_fichiers[IDdocument]["SELECTION"] = valeur
        if indexColonne == 1 :
            self.dict_noms_fichiers[IDdocument]["NOMFICHIER"] = valeur
        
    def OnIdle(self, evt):
        if self.moveTo != None:
            self.SetGridCursor(self.moveTo[0], self.moveTo[1])
            self.moveTo = None
        evt.Skip()
        
# ------------------------------------------------------------------------------------------------------------
#---TRAITEMENT ET FIN---#400080#80FF80----------------------------------------------


class Page6(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.choixLogiciel = 1
        self.repertoire = UTILS_Fichiers.GetRepEditions()
        self.nomFichier = ""
        self.pause = False
        self.termine = False
        self.useTeamword = False
        self.listeDocTraites = []
        self.label_titre = wx.StaticText(self, -1, _(u"5. Traitement du publipostage"))
        self.label_intro = wx.StaticText(self, -1, _(u"Cliquez sur 'Valider' pour lancer le publipostage ou revenez en arrière en cliquant sur 'retour'."))
        self.gauge = wx.Gauge(self, -1, 1, size=(-1, 10))
        self.ctrl_actions = listCtrl_Actions(self)
        self.bouton_continuer = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Continuer"),
            cheminImage=Chemins.GetStaticPath("Images/BoutonsImages/ContinuerPublipostage.png"),
            role="primary",
        )
        self.bouton_continuer.Show(False)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_continuer, self.bouton_continuer)
        self.__set_properties()
        self.__do_layout()
        
    def __set_properties(self):
        self.label_titre.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.bouton_continuer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour continuer le processus de publipostage\naprès une pause aperçu du document.")))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.label_titre, 0, 0, 0)
        grid_sizer_base.Add(self.label_intro, 1, wx.LEFT|wx.BOTTOM|wx.EXPAND, 20)
        grid_sizer_base.Add(self.gauge, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 20)
        grid_sizer_base.Add(self.ctrl_actions, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 20)
        grid_sizer_base.Add(self.bouton_continuer, 0, wx.LEFT|wx.RIGHT, 20)
        grid_sizer_base.Add( (10, 10), 1, wx.EXPAND, 0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(3)
    
    def Validation(self):
        threadEnCours = False
        try :
            if self.thread.isAlive():
                threadEnCours = True
                self.thread.abort()
                if self.pause == True :
                    self.bouton_continuer.Show(False)
                    self.Layout()
                    self.pause = False
        except :
            pass
        if threadEnCours == False and self.termine == False :
            self.ctrl_actions.Remplissage()
            self.gauge.SetValue(0)
            self.GetGrandParent().SetSuiteAction(u"Arrêter", "Arreter_L72.png", role="danger")
            self.GetGrandParent().bouton_annuler.Enable(False)
            self.GetGrandParent().bouton_retour.Enable(False)
            self.GetGrandParent().bouton_aide.Enable(False)
            self.GetGrandParent().EnableCloseButton(False)
            if self.choixLogiciel == 3 or self.choixLogiciel == 4 :
                self.Publipostage() 
                return False
            else:
                self.thread = threadPublipostage(self)
                self.thread.start()
                return False
        if self.termine == True :       
            return True
        else:
            return False
    
    def Publipostage(self) :
        if self.useTeamword == True and self.pause == True :
            self.bouton_continuer.Show(False)
            self.Layout()
            self.pause = False
            self.publipostage.FermerDocument()
            if self.publipostage.erreur != None :
                self.publipostage.OuvertureLogiciel()
                self.publipostage.erreur = None
        else:
            self.interrompu = False
            self.pause = False
            self.termine = False
            self.useTeamword = False
            self.listeDocTraites = []
            self.nbreDocuments = DICT_DONNEES["NBREDOCUMENTS"]
            if self.choixLogiciel ==  4 :
                nbreEtapes = 5
            else:
                nbreEtapes = 6
            self.nbreCrans = (self.nbreDocuments*nbreEtapes)+3
            self.gauge.SetRange(self.nbreCrans)
            self.x = 1
            self.label_intro.SetLabel(_(u"Opération en cours : Ouverture du logiciel de publipostage"))
            self.gauge.SetValue(self.x)
            self.x += 1
            if self.choixLogiciel == 1 : 
                self.publipostage = Publipostage_Word(self)
                self.publipostage.OuvertureLogiciel()
            if self.choixLogiciel == 2 : 
                if "win" in sys.platform :
                    self.publipostage = Publipostage_Writer_Windows(self)
                    self.publipostage.OuvertureLogiciel()
                else:
                    self.publipostage = Publipostage_Writer_Linux(self)
                    self.publipostage.OuvertureLogiciel()
            if self.choixLogiciel == 3 or self.choixLogiciel ==  4 : 
                self.useTeamword = True
                self.publipostage = Publipostage_Teamword(self)
                self.publipostage.OuvertureLogiciel()
            if self.publipostage.erreur != None : self.OnErreur(None, self.publipostage.erreur);return False
        for IDdocument in range(1, self.nbreDocuments+1) :
            if IDdocument not in self.listeDocTraites :
                self.AfficheProgression(IDdocument, "actuel" , _(u"Création du document"), _(u"Opération en cours : Création du document n°%d") % IDdocument)
                self.publipostage.CreationDocument(cheminModele=self.GetGrandParent().page4.cheminDest + "/" + self.GetGrandParent().page4.nomFichier)
                if self.publipostage.erreur != None : self.OnErreur(IDdocument, self.publipostage.erreur);return False
                self.AfficheProgression(IDdocument, "actuel" , _(u"Remplacement des valeurs"), _(u"Opération en cours : Remplacement des valeurs du document n°%d") % IDdocument)
                listeValeurs = []
                for motcle, valeur in DICT_DONNEES[IDdocument].items() :
                    listeValeurs.append((motcle, valeur))
                self.publipostage.RemplacementValeurs(listeValeurs=listeValeurs)
                if self.publipostage.erreur != None : self.OnErreur(IDdocument, self.publipostage.erreur);return False
                if self.choixLogiciel != 4 :
                    sauvegarde = self.GetGrandParent().page5.checkbox_save.GetValue()
                    if sauvegarde == True : 
                        dictNomsFichiers = self.GetGrandParent().page5.ctrl_nom_fichiers.GetDictNomsFichiers()
                        if dictNomsFichiers[IDdocument]["SELECTION"] == 1 :
                            self.AfficheProgression(IDdocument, "actuel" , _(u"Sauvegarde du document"), _(u"Opération en cours : Sauvegarde du document n°%d") % IDdocument)
                            nomFichier = dictNomsFichiers[IDdocument]["NOMFICHIER"]
                            repertoire = self.GetGrandParent().page5.text_repertoire.GetValue()
                            extension = self.GetGrandParent().page5.extension
                            cheminDoc = repertoire + "/" + nomFichier + extension
                            self.publipostage.SauvegardeDocument(cheminDoc)
                            if self.publipostage.erreur != None : self.OnErreur(IDdocument, self.publipostage.erreur);return False
                        else:
                            self.x += 1
                    else:
                        self.x += 1
                if self.choixLogiciel != 4 :
                    impression = self.GetGrandParent().page5.checkbox_impression.GetValue()
                    if impression == True :
                        self.AfficheProgression(IDdocument, "actuel" , _(u"Impression du document"), _(u"Opération en cours : Impression du document n°%d") % IDdocument)
                        nbre_exemplaires = int(self.GetGrandParent().page5.combo_box_exemplaires.GetStringSelection())
                        nom_imprimante = self.GetGrandParent().page5.combo_box_imprimante.GetStringSelection()
                        self.publipostage.ImprimerDocument(nom_imprimante, nbre_exemplaires)
                        if self.publipostage.erreur != None : self.OnErreur(IDdocument, self.publipostage.erreur);return False
                    else:
                        self.x += 1
                if self.choixLogiciel == 4 :
                    dictParamMail = self.GetGrandParent().page5.dictParamMail
                    adresseExpediteur = dictParamMail["adresseExpediteur"] 
                    serveur = dictParamMail["serveur"]
                    port = dictParamMail["port"]
                    connexionssl = dictParamMail["connexionssl"]
                    sujetMail = dictParamMail["sujetMail"]
                    listeFichiersJoints = dictParamMail["listeFichiersJoints"]
                    adresseDestinataire = DICT_DONNEES[IDdocument]["EMAILS"]
                    self.publipostage.SetParamMail(adresseExpediteur, adresseDestinataire, sujetMail, listeFichiersJoints, serveur, port, connexionssl)
                apercu = self.GetGrandParent().page5.checkbox_apercu.GetValue()
                apercu_mail = self.GetGrandParent().page5.ctrl_apercu_avant_envoi.GetValue()
                if (self.choixLogiciel == 4 and apercu_mail == True) or  (self.choixLogiciel != 4 and apercu == True):
                    self.AfficheProgression(IDdocument, "actuel" , _(u"Apercu du document"), _(u"Opération en cours : Aperçu du document n°%d") % IDdocument)
                    self.publipostage.ApercuDocument()
                    if self.publipostage.erreur != None : self.OnErreur(self.publipostage.erreur);return False
                else:
                    self.AfficheProgression(IDdocument, "actuel" , _(u"Fermeture du document"), _(u"Opération en cours : Fermeture du document n°%d") % IDdocument)
                    self.publipostage.FermerDocument()
                    if self.publipostage.erreur != None : self.OnErreur(IDdocument, self.publipostage.erreur);return False
                if self.choixLogiciel == 4 and apercu_mail == False :
                    self.AfficheProgression(IDdocument, "actuel" , _(u"Envoi par mail"), _(u"Opération en cours : Envoi par mail du document n°%d") % IDdocument)
                    self.publipostage.EnvoyerMail()
                else:
                    self.x += 1
                self.AfficheProgression(IDdocument, "ok" , _(u"Terminé"), None)
                self.listeDocTraites.append(IDdocument)
                if apercu == True and IDdocument < self.nbreDocuments :
                    self.pause = True
                    self.bouton_continuer.Show(True)
                    self.Layout()
                    if self.useTeamword == True :
                        return
                    else:
                        while self.pause == True :
                            time.sleep(1)
                        self.bouton_continuer.Show(False)
                        self.Layout()
                        self.pause = False
                        self.publipostage.FermerDocument()
                        if self.publipostage.erreur != None :
                            self.publipostage.OuvertureLogiciel()
                            self.publipostage.erreur = None
            if self.useTeamword == False :
                if self.thread.stop == True:
                    self.interrompu = True
                    break
        if apercu == False :
            self.label_intro.SetLabel(_(u"Opération en cours : Fermeture du logiciel"))
            self.gauge.SetValue(self.x)
            self.x += 1
            self.publipostage.QuitterLogiciel()
            if self.publipostage.erreur != None : self.OnErreur(None, self.publipostage.erreur);return False
        else:
            self.x += 1
        self.termine = True
        if self.useTeamword == True :
            self.stop = True
            self.GetGrandParent().bouton_annuler.Enable(True)
            self.GetGrandParent().bouton_retour.Enable(True)
            self.GetGrandParent().bouton_aide.Enable(True)
            self.GetGrandParent().EnableCloseButton(True)
            self.GetGrandParent().SetSuiteAction(u"Fermer", "Fermer_L72.png")
        else:
            self.thread.abort()
        if self.interrompu == True :
            message = _(u"Vous avez interrompu le publipostage ! ")
            self.label_intro.SetLabel(message)
        else:
            message = _(u"Le publipostage est terminé.")
            self.label_intro.SetLabel(message)
        self.gauge.SetValue(self.x)
        self.x += 1

    def AfficheProgression(self, IDdocument, etat, info, intro=None):
        if IDdocument != None : self.ctrl_actions.MAJitem(IDdocument, etat, info)
        if intro != None : self.label_intro.SetLabel(intro)
        self.gauge.SetValue(self.x)
        self.x += 1
        
    def OnErreur(self, IDdocument=None, txtErreur=""):
        self.AfficheProgression(IDdocument, "erreur" , _(u"Erreur : %s") % txtErreur, _(u"Erreur : %s") % txtErreur)
        if self.useTeamword == False :
            self.thread.abort()
    
    def Onbouton_continuer(self, event):
        if self.useTeamword == True :
            self.Publipostage() 
        else:
            self.pause = False
    

class Publipostage_Word():
    def __init__(self, parent): 
        self.erreur = None
        CoInitialize()
    
    def OuvertureLogiciel(self):
        try : 
            self.Word = win32com.client.Dispatch("Word.Application")
            self.Word.Visible = False 
        except Exception as err :
            print("Erreur dans l'ouverture de Word : %s" % err)
            self.erreur = _(u"Impossible d'ouvrir Word")
            self.QuitterLogiciel()
    
    def CreationDocument(self, cheminModele=None):
        try :
            self.Word.Documents.Add(cheminModele)
            self.doc = self.Word.ActiveDocument
        except Exception as err :
            print("Erreur dans creation du nouveau du document : %s" % err)
            self.erreur = _(u"Impossible de créer un nouveau du document")
            self.QuitterLogiciel()
    
    def RemplacementValeurs(self, listeValeurs=None):
        if listeValeurs is None:
            listeValeurs = []
        try :
            find = self.doc.Content.Find
            for motCle, valeur in listeValeurs :
                self.Word.Selection.HomeKey(Unit=6)
                find = self.Word.Selection.Find
                find.Text = "{" + motCle + "}"
                while self.Word.Selection.Find.Execute() :
                    self.Word.Selection.TypeText(Text=valeur)
        except Exception as err :
            print("Erreur dans le remplacement des valeurs du document : %s" % err)
            self.erreur = _(u"Impossible de remplacer les valeurs")
            self.QuitterLogiciel()
            
    def SauvegardeDocument(self, cheminDoc=None):
        try :
            self.doc.SaveAs(cheminDoc)
        except Exception as err :
            print("Erreur dans la sauvegarde du document : %s" % err)
            self.erreur = _(u"Impossible de sauvegarder le document")
            self.QuitterLogiciel()
            
    def ImprimerDocument(self, nom_imprimante=None, nbre_exemplaires=1):
        try :
            for x in range(nbre_exemplaires) :
                self.doc.PrintOut()
                time.sleep(2)
        except Exception as err :
            print("Erreur dans l'impression du document : %s" % err)
            self.erreur = _(u"Impossible d'imprimer le document")
            self.QuitterLogiciel()
            
    def ApercuDocument(self):
        try :
            self.Word.Visible = True
            self.Word.Activate
        except Exception as err :
            print("Erreur dans la creation de l'apercu du document : %s" % err)
            self.erreur = _(u"Impossible de créer un aperçu du document")
            self.QuitterLogiciel()
    
    def FermerDocument(self):
        try : 
            self.doc.Close(SaveChanges = 0)
        except Exception as err :
            print("Erreur dans la fermeture du document : %s" % err)
            self.erreur = _(u"Impossible de fermer le document")
            self.QuitterLogiciel()
        
    def QuitterLogiciel(self):
        try : 
            self.doc.Close(SaveChanges = 0)
        except : pass
        try :
            self.Word.Quit()
            CoUninitialize()
        except Exception as err :
            print("Erreur dans la fermeture de Word : %s" % err)
            self.erreur = _(u"Impossible de quitter Word")


class Publipostage_Writer_Windows():
    def __init__(self, parent): 
        self.erreur = None
        CoInitialize()
    
    def OuvertureLogiciel(self):
        try : 
            objServiceManager = win32com.client.Dispatch("com.sun.star.ServiceManager")
            self.objDesktop = objServiceManager.CreateInstance("com.sun.star.frame.Desktop")  
        except Exception as err :
            print("Erreur dans l'ouverture de Writer : %s" % err)
            self.erreur = _(u"Impossible d'ouvrir Writer")
            self.QuitterLogiciel()
    
    def CreationDocument(self, cheminModele=None):
        try :
            self.args = []
            modele = "file:///" + cheminModele.replace("\\", "/")
            self.objDocument = self.objDesktop.loadComponentFromURL(modele, "_blank", 0, self.args)
            self.objDocument.CurrentController.Frame.ContainerWindow.Visible = False
        except Exception as err :
            print("Erreur dans creation du nouveau du document : %s" % err)
            self.erreur = _(u"Impossible de créer un nouveau du document")
            self.QuitterLogiciel()
            
    def RemplacementValeurs(self, listeValeurs=None):
        if listeValeurs is None:
            listeValeurs = []
        try :
            for motCle, valeur in listeValeurs :
                orempl = self.objDocument.createReplaceDescriptor()
                orempl.SearchString= "{" + motCle + "}"
                orempl.ReplaceString= valeur
                orempl.SearchWords = True
                orempl.SearchCaseSensitive = True
                self.objDocument.replaceAll(orempl)
        except Exception as err :
            print("Erreur dans le remplacement des valeurs du document : %s" % err)
            self.erreur = _(u"Impossible de remplacer les valeurs")
            self.QuitterLogiciel()
                
    def SauvegardeDocument(self, cheminDoc=None):
        try :
            dest = "file:///" + cheminDoc.replace("\\", "/")
            self.objDocument.storeAsURL(dest, self.args)
        except Exception as err :
            print("Erreur dans la sauvegarde du document : %s" % err)
            self.erreur = _(u"Impossible de sauvegarder le document")
            self.QuitterLogiciel()
                    
    def ImprimerDocument(self, nom_imprimante=None, nbre_exemplaires=1):
        try :
            warg = []
            for x in range(nbre_exemplaires) :
                self.objDocument.Print(warg)
                time.sleep(2)
        except Exception as err :
            print("Erreur dans l'impression du document : %s" % err)
            self.erreur = _(u"Impossible d'imprimer le document")
            self.QuitterLogiciel()
                
    def ApercuDocument(self):
        try :
            self.objDocument.CurrentController.Frame.ContainerWindow.Visible = True
        except Exception as err :
            print("Erreur dans la creation de l'apercu du document : %s" % err)
            self.erreur = _(u"Impossible de créer un aperçu du document")
            self.QuitterLogiciel()
    
    def FermerDocument(self):
        try : 
            self.objDocument.Close(False)
        except Exception as err :
            print("Erreur dans la fermeture du document : %s" % err)
            self.erreur = _(u"Impossible de fermer le document")
            self.QuitterLogiciel()
        
    def QuitterLogiciel(self):
        try : 
            self.doc.Close(SaveChanges = 0)
        except : pass
        try :
            self.objDesktop.Terminate() 
            CoUninitialize()
        except Exception as err :
            print("Erreur dans la fermeture de Writer : %s" % err)
            self.erreur = _(u"Impossible de quitter Writer")

    
class Publipostage_Writer_Linux():
    def __init__(self, parent): 
        self.erreur = None
        from Utils import UTILS_Pilotageooo

    def OuvertureLogiciel(self):
        try : 
            self.ooo = UTILS_Pilotageooo.Pilotage()
        except Exception as err :
            print("Erreur dans l'ouverture de Writer : %s" % err)
            self.erreur = _(u"Impossible d'ouvrir Writer")
            self.QuitterLogiciel()

    def CreationDocument(self, cheminModele=None):
        try :
            fichier = cheminModele.replace("\\", "/")
            self.ooo.Ouvrir_doc(fichier)
        except Exception as err :
            print("Erreur dans creation du nouveau du document : %s" % err)
            self.erreur = _(u"Impossible de créer un nouveau du document")
            self.QuitterLogiciel()

    def RemplacementValeurs(self, listeValeurs=None):
        if listeValeurs is None:
            listeValeurs = []
        try :
            self.ooo.Remplacer_valeurs(listeValeurs)
        except Exception as err :
            print("Erreur dans le remplacement des valeurs du document : %s" % err)
            self.erreur = _(u"Impossible de remplacer les valeurs")
            self.QuitterLogiciel()

    def SauvegardeDocument(self, cheminDoc=None):
        try :
            self.ooo.Sauvegarder_doc(cheminDoc)
        except Exception as err :
            print("Erreur dans la sauvegarde du document : %s" % err)
            self.erreur = _(u"Impossible de sauvegarder le document")
            self.QuitterLogiciel()
            
    def ImprimerDocument(self, nom_imprimante=None, nbre_exemplaires=1):
        try :
            self.ooo.Imprimer_doc(nbre_exemplaires)
        except Exception as err :
            print("Erreur dans l'impression du document : %s" % err)
            self.erreur = _(u"Impossible d'imprimer le document")
            self.QuitterLogiciel()

    def ApercuDocument(self):
        pass
    
    def FermerDocument(self):
        try : 
            self.ooo.Fermer_doc()
        except Exception as err :
            print("Erreur dans la fermeture du document : %s" % err)
            self.erreur = _(u"Impossible de fermer le document")
            self.QuitterLogiciel()
        
    def QuitterLogiciel(self):
        try : 
            self.ooo.Fermer_doc()
        except : pass
        try :
            self.ooo.Quitter() 
            CoUninitialize()
        except Exception as err :
            print("Erreur dans la fermeture de Writer : %s" % err)
            self.erreur = _(u"Impossible de quitter Writer")


class Publipostage_Teamword():
    def __init__(self, parent): 
        self.parent = parent
        self.erreur = None
    
    def OuvertureLogiciel(self):
        try : 
            from Dlg import DLG_Teamword
            self.Twd = DLG_Teamword.MyFrame(self.parent.GetGrandParent())
        except Exception as err :
            print("Erreur dans l'ouverture de Teamword : %s" % err)
            self.erreur = _(u"Impossible d'ouvrir Teamword")
            self.QuitterLogiciel()
        
    def CreationDocument(self, cheminModele=None):
        try :
            self.Twd.CreateNewFile(cheminModele)
        except Exception as err :
            print("Erreur dans creation du nouveau du document : %s" % err)
            self.erreur = _(u"Impossible de créer un nouveau du document")
            self.QuitterLogiciel()
    
    def RemplacementValeurs(self, listeValeurs=None):
        if listeValeurs is None:
            listeValeurs = []
        try :
            listeValeurs2 = []
            for motcle, valeur in listeValeurs :
                listeValeurs2.append(("{%s}" % motcle, valeur))
            self.Twd.RemplaceMotscles(listeValeurs2)
        except Exception as err :
            print("Erreur dans le remplacement des valeurs du document : %s" % err)
            self.erreur = _(u"Impossible de remplacer les valeurs")
            self.QuitterLogiciel()
            
    def SauvegardeDocument(self, cheminDoc=None):
        try :
            self.Twd.FileSaveAs(cheminDoc)
        except Exception as err :
            print("Erreur dans la sauvegarde du document : %s" % err)
            self.erreur = _(u"Impossible de sauvegarder le document")
            self.QuitterLogiciel()
            
    def ImprimerDocument(self, nom_imprimante=None, nbre_exemplaires=1):
        try :
            activeDir = os.getcwd()
            self.Twd.Publipostage_impression(nom_imprimante=nom_imprimante, nbre_exemplaires=nbre_exemplaires)
            os.chdir(activeDir)
        except Exception as err :
            print("Erreur dans l'impression du document : %s" % err)
            self.erreur = _(u"Impossible d'imprimer le document")
            self.QuitterLogiciel()
    
    def SetParamMail(self, adresseExpediteur, adresseDestinaire, sujetMail, listeFichiersJoints, serveur, port, connexionssl) :
        self.Twd.panelMail.SetParamMail(adresseExpediteur, adresseDestinaire, sujetMail, listeFichiersJoints, serveur, port, connexionssl)
        self.Twd.OnMail(None)
        
    def EnvoyerMail(self):
        self.Twd.panelMail.OnboutonEnvoyer(None)
    
    def ApercuDocument(self):
        try : 
            self.Twd.Show()
        except Exception as err :
            print("Erreur dans la creation de l'apercu du document : %s" % err)
            self.erreur = _(u"Impossible de créer un aperçu du document")
            self.QuitterLogiciel()
    
    def FermerDocument(self):
        try : 
            self.Twd.CloseFile(enregistrer=False)
        except Exception as err :
            print("Erreur dans la fermeture du document : %s" % err)
            self.erreur = _(u"Impossible de fermer le document")
            self.QuitterLogiciel()
        
    def QuitterLogiciel(self):
        try :
            self.Twd.Quitter(enregistrer=False)
        except Exception as err :
            print("Erreur dans la fermeture de Teamword : %s" % err)
            self.erreur = _(u"Impossible de quitter Teamword")


class Abort(Exception): 
    pass 

class threadPublipostage(Thread): 
    def __init__(self, parent): 
        Thread.__init__(self) 
        self.parent = parent
        self.stop = False 

    def run(self): 
        try: 
            self.parent.Publipostage() 
        except Abort:
            pass
        except: 
            self.stop = True 
            raise 

    def abort(self): 
        self.stop = True
        self.parent.GetGrandParent().bouton_annuler.Enable(True)
        self.parent.GetGrandParent().bouton_retour.Enable(True)
        self.parent.GetGrandParent().bouton_aide.Enable(True)
        self.parent.GetGrandParent().EnableCloseButton(True)
        if self.parent.termine == True :
            self.parent.GetGrandParent().SetSuiteAction(u"Fermer", "Fermer_L72.png")
        else:
            self.parent.GetGrandParent().SetSuiteAction(u"Valider", "Valider_L72.png")


class listCtrl_Actions(wx.ListCtrl):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, id=-1, style=wx.LC_REPORT)
        self.InsertColumn(0, _(u"N° document"))
        self.InsertColumn(1, _(u"Etat"))
        self.SetColumnWidth(0, 120)
        self.SetColumnWidth(1, 290)
        images = [Chemins.GetStaticPath("images/16x16/Vide.png"), Chemins.GetStaticPath("images/16x16/Fleche_droite.png"), Chemins.GetStaticPath("images/16x16/Ok.png"), Chemins.GetStaticPath("images/16x16/Interdit.png")]
        self.il = wx.ImageList(16, 16)
        for i in images:
            self.il.Add(wx.Bitmap(i))
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        self.Remplissage()
    
    def Remplissage(self):
        self.DeleteAllItems() 
        indexLigne = 0
        for IDdocument in range(1, DICT_DONNEES["NBREDOCUMENTS"]+1) :
            self.InsertItem(indexLigne, _(u"Document n°%d") % IDdocument)
            self.SetItem(indexLigne, 1, u"")
            indexLigne += 1
            
    def ChangeImage(self, indexLigne, etat=None):
        if etat == "actuel" : img = 1
        elif etat == "ok" : img = 2
        elif etat == "erreur" : img = 3
        else: img = 0
        self.SetItemImage(indexLigne, img)
        self.EnsureVisible(indexLigne)
    
    def MAJitem(self, IDdocument, etat, info):
        indexLigne = IDdocument-1
        self.SetItem(indexLigne, 1, info)
        self.ChangeImage(indexLigne, etat)
        

if __name__ == "__main__":
    from Utils import UTILS_Publipostage_donnees
    DICT_DONNEES_TEST = UTILS_Publipostage_donnees.GetDictDonnees(categorie="contrat", listeID=[2,])
    app = wx.App(0)
    dlg = Dialog(None, "", dictDonnees=DICT_DONNEES_TEST)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
