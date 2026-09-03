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
from Ctrl import CTRL_Page_generalites_091e as CTRL_Page_generalites
from Ctrl import CTRL_Page_questionnaire
from Ctrl import CTRL_Page_qualifications
from Ctrl import CTRL_Page_contrats
from Ctrl import CTRL_Page_presences
from Ctrl import CTRL_Page_frais
from Ctrl import CTRL_Page_scenarios
from Ctrl import CTRL_Page_candidatures
import FonctionsPerso
import datetime
import GestionDB
from wx.lib.ticker import Ticker
from Ctrl import CTRL_Photo
from Utils import UTILS_Customize
from Utils import UTILS_Interface


def _echelle_interface():
    try:
        return max(80, min(200, UTILS_Customize.GetValeur(
            "interface", "echelle_police", "100", type_valeur=int
        )))
    except Exception:
        return 100


def _taille_echelle(valeur, minimum=None, maximum=None):
    resultat = int(round(valeur * _echelle_interface() / 100.0))
    if minimum is not None:
        resultat = max(minimum, resultat)
    if maximum is not None:
        resultat = min(maximum, resultat)
    return resultat


def _bitmap_onglet(nom, taille):
    bitmap = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/%s" % nom), wx.BITMAP_TYPE_PNG)
    if bitmap.IsOk() and (bitmap.GetWidth() != taille or bitmap.GetHeight() != taille):
        image = bitmap.ConvertToImage().Scale(taille, taille, wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.Bitmap(image)
    return bitmap


class Notebook(wx.Notebook):
    def __init__(self, parent, id=-1, IDpersonne=0):
        wx.Notebook.__init__(self, parent, id, style=wx.BK_DEFAULT)
        self.IDpersonne = IDpersonne

        taille_icone = _taille_echelle(18, minimum=16, maximum=26)
        il = wx.ImageList(taille_icone, taille_icone)
        self.img1 = il.Add(_bitmap_onglet("Identite.png", taille_icone))
        self.img2 = il.Add(_bitmap_onglet("BlocNotes.png", taille_icone))
        self.img3 = il.Add(_bitmap_onglet("Document.png", taille_icone))
        self.img4 = il.Add(_bitmap_onglet("Presences.png", taille_icone))
        self.img5 = il.Add(_bitmap_onglet("Scenario.png", taille_icone))
        self.img6 = il.Add(_bitmap_onglet("Calculatrice.png", taille_icone))
        self.img7 = il.Add(_bitmap_onglet("Candidature.png", taille_icone))
        self.img8 = il.Add(_bitmap_onglet("Document2.png", taille_icone))
        self.AssignImageList(il)

        self.pageGeneralites = CTRL_Page_generalites.Panel_general(self, -1, IDpersonne=self.IDpersonne)
        self.AddPage(self.pageGeneralites, _(u"Généralités"))
        self.SetPageImage(0, self.img1)

        if self.IDpersonne == 0:
            self.GetGrandParent().nouvelleFiche = True
            self.pageGeneralites.Sauvegarde()
            self.IDpersonne = self.pageGeneralites.IDpersonne
        else:
            self.GetGrandParent().nouvelleFiche = False

        self.pageQuestionnaire = CTRL_Page_questionnaire.Panel(self, -1, IDpersonne=self.IDpersonne)
        self.AddPage(self.pageQuestionnaire, _(u"Questionnaire"))
        self.SetPageImage(1, self.img8)

        self.pageStatut = CTRL_Page_qualifications.Panel_Statut(self, -1, IDpersonne=self.IDpersonne)
        self.AddPage(self.pageStatut, _(u"Qualifications"))
        self.SetPageImage(2, self.img2)

        self.pageContrats = CTRL_Page_contrats.Panel_Contrats(self, -1, IDpersonne=self.IDpersonne)
        self.AddPage(self.pageContrats, _(u"Contrats"))
        self.SetPageImage(3, self.img3)

        self.pagePresences = CTRL_Page_presences.Panel(self, IDpersonne=self.IDpersonne)
        self.AddPage(self.pagePresences, _(u"Présences"))
        self.SetPageImage(4, self.img4)

        self.pageScenarios = CTRL_Page_scenarios.Panel(self, IDpersonne=self.IDpersonne)
        self.AddPage(self.pageScenarios, _(u"Scénarios"))
        self.SetPageImage(5, self.img5)

        self.pageFrais = CTRL_Page_frais.Panel(self, IDpersonne=self.IDpersonne)
        self.AddPage(self.pageFrais, _(u"Frais"))
        self.SetPageImage(6, self.img6)

        self.pageCandidatures = CTRL_Page_candidatures.Panel(self, IDpersonne=self.IDpersonne)
        self.AddPage(self.pageCandidatures, _(u"Recrutement"))
        self.SetPageImage(7, self.img7)

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def AfficheAutresPages(self, etat=True):
        """Affiche ou masque les pages complémentaires à Généralités."""
        if etat and self.GetPageCount() <= 1:
            pages = (
                (self.pageQuestionnaire, _(u"Questionnaire"), self.img8),
                (self.pageStatut, _(u"Qualifications"), self.img2),
                (self.pageContrats, _(u"Contrats"), self.img3),
                (self.pagePresences, _(u"Présences"), self.img4),
                (self.pageScenarios, _(u"Scénarios"), self.img5),
                (self.pageFrais, _(u"Frais"), self.img6),
                (self.pageCandidatures, _(u"Recrutement"), self.img7),
            )
            for page, label, image in pages:
                self.AddPage(page, label)
                self.SetPageImage(self.GetPageCount() - 1, image)
        elif not etat and self.GetPageCount() > 1:
            while self.GetPageCount() > 1:
                self.RemovePage(self.GetPageCount() - 1)

    def OnPageChanged(self, event):
        oldPage = event.GetOldSelection()
        newPage = event.GetSelection()
        if newPage != wx.NOT_FOUND:
            page = self.GetPage(newPage)
            page.Refresh()
        if oldPage == 0:
            self.GetGrandParent().AnnulationImpossible = True
            self.GetGrandParent().bitmap_button_annuler.Enable(False)
            self.pageGeneralites.Sauvegarde()
        event.Skip()


class Dialog(wx.Dialog):
    def __init__(self, parent, titre=_(u"Fiche individuelle"), IDpersonne=0):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            name="FicheIndividuelle",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        )
        self.IDpersonne = IDpersonne
        self.contratEnCours = None
        self.AnnulationImpossible = False
        self.barre_problemes = None
        self.photo = None

        import locale
        self.locale = wx.Locale(wx.LANGUAGE_FRENCH)
        try:
            locale.setlocale(locale.LC_ALL, 'FR')
        except Exception:
            pass

        self.panel_1 = wx.Panel(self, -1)
        self.label_hd_CatId = wx.StaticText(self.panel_1, -1, u"")
        self.static_line_1 = wx.StaticLine(self.panel_1, -1)
        self.label_hd_nomPrenom = wx.StaticText(self.panel_1, -1, _(u"NOM, Prénom"))
        self.label_hd_adresse = wx.StaticText(self.panel_1, -1, _(u"Résidant 42 rue des oiseaux 29870 LANNILIS"))
        self.label_hd_naiss = wx.StaticText(self.panel_1, -1, _(u"Date et lieu de naissance inconnus"))
        self.bitmap_photo = CTRL_Photo.CTRL_Photo(self.panel_1, style=wx.SUNKEN_BORDER)
        self.bitmap_photo.SetPhoto(
            IDindividu=None,
            nomFichier=Chemins.GetStaticPath("Images/128x128/Personne.png"),
            taillePhoto=(128, 128),
            qualite=100,
        )

        self.bitmap_button_aide = CTRL_Bouton_image.CTRL(
            self.panel_1, texte=_(u"Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png")
        )
        self.bitmap_button_Ok = CTRL_Bouton_image.CTRL(
            self.panel_1, texte=_(u"Ok"), cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png")
        )
        self.bitmap_button_annuler = CTRL_Bouton_image.CTRL(
            self.panel_1, texte=_(u"Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png")
        )

        self.notebook = Notebook(self.panel_1, IDpersonne=self.IDpersonne)
        if self.nouvelleFiche:
            self.notebook.AfficheAutresPages(False)

        self.barre_problemes = self.IDpersonne in FonctionsPerso.Recherche_ContratsEnCoursOuAVenir()

        self.bitmap_problemes_G = wx.StaticBitmap(
            self.panel_1, -1, wx.Bitmap(Chemins.GetStaticPath("Images/Special/Problemes_G.png"), wx.BITMAP_TYPE_PNG)
        )
        self.bitmap_problemes_D = wx.StaticBitmap(
            self.panel_1, -1, wx.Bitmap(Chemins.GetStaticPath("Images/Special/Problemes_D.png"), wx.BITMAP_TYPE_PNG)
        )
        hauteur_ticker = _taille_echelle(20, minimum=20, maximum=30)
        self.txtDefilant = Ticker(
            self.panel_1,
            size=(-1, hauteur_ticker),
            fgcolor=(255, 255, 255),
            bgcolor=(180, 35, 35),
        )
        self.txtPbPersonne = self.Recup_txt_pb_personne()
        self.txtDefilant.SetText(self.txtPbPersonne)

        self.MaJ_header()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bitmap_button_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bitmap_button_Ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bitmap_button_annuler)
        self.txtDefilant.Bind(wx.EVT_MOTION, self.OnMotionTxtDefilant)
        self.txtDefilant.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveTxtDefilant)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.__set_properties(titre)
        self.__do_layout()
        self.Affichage_barre_problemes()

    def __set_properties(self, titre):
        self.SetTitle(titre)
        if 'phoenix' in wx.PlatformInfo:
            _icon = wx.Icon()
        else:
            _icon = wx.EmptyIcon()
        _icon.CopyFromBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        self.SetIcon(_icon)

        police_meta = self.label_hd_CatId.GetFont()
        police_meta.SetPointSize(max(8, police_meta.GetPointSize() - 1))
        self.label_hd_CatId.SetFont(police_meta)

        police_nom = self.label_hd_nomPrenom.GetFont()
        police_nom.SetWeight(wx.FONTWEIGHT_BOLD)
        police_nom.SetPointSize(max(14, police_nom.GetPointSize() + 5))
        self.label_hd_nomPrenom.SetFont(police_nom)

        self.bitmap_photo.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.panel_1.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.txtDefilant.SetToolTip(wx.ToolTip(_(u"Cette barre d'information recense les points\nà contrôler sur le dossier de cette personne.")))
        self.bitmap_photo.SetToolTip(wx.ToolTip("Cliquez sur le bouton droit de votre souris pour modifier cette image"))
        self.bitmap_button_aide.SetToolTip(wx.ToolTip("Cliquez ici pour obtenir de l'aide"))
        self.bitmap_button_Ok.SetToolTip(wx.ToolTip("Cliquez ici pour valider"))
        self.bitmap_button_annuler.SetToolTip(wx.ToolTip("Cliquez ici pour annuler"))

        display_index = wx.Display.GetFromWindow(self)
        if display_index == wx.NOT_FOUND:
            display_index = 0
        zone = wx.Display(display_index).GetClientArea()
        largeur = min(1400, max(900, int(zone.GetWidth() * 0.78)))
        hauteur = min(950, max(680, int(zone.GetHeight() * 0.82)))
        self.SetMinSize((820, 620))
        self.SetSize((largeur, hauteur))

    def __do_layout(self):
        sizer_header_textes = wx.BoxSizer(wx.VERTICAL)
        sizer_header_textes.Add(self.label_hd_CatId, 0, wx.EXPAND)
        sizer_header_textes.Add(self.static_line_1, 0, wx.TOP | wx.BOTTOM | wx.EXPAND, 6)
        sizer_header_textes.Add(self.label_hd_nomPrenom, 0, wx.BOTTOM, 8)
        sizer_header_textes.Add(self.label_hd_adresse, 0, wx.BOTTOM, 3)
        sizer_header_textes.Add(self.label_hd_naiss, 0, 0)

        sizer_problemes = wx.BoxSizer(wx.HORIZONTAL)
        sizer_problemes.Add(self.bitmap_problemes_G, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer_problemes.Add(self.txtDefilant, 1, wx.EXPAND)
        sizer_problemes.Add(self.bitmap_problemes_D, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer_header_textes.Add(sizer_problemes, 0, wx.EXPAND | wx.TOP, 12)

        sizer_header = wx.BoxSizer(wx.HORIZONTAL)
        sizer_header.Add(sizer_header_textes, 1, wx.EXPAND | wx.RIGHT, 12)
        sizer_header.Add(self.bitmap_photo, 0, wx.ALIGN_TOP)

        sizer_boutons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_boutons.Add(self.bitmap_button_aide, 0)
        sizer_boutons.AddStretchSpacer(1)
        sizer_boutons.Add(self.bitmap_button_Ok, 0, wx.RIGHT, 8)
        sizer_boutons.Add(self.bitmap_button_annuler, 0)

        sizer_panel = wx.BoxSizer(wx.VERTICAL)
        sizer_panel.Add(sizer_header, 0, wx.EXPAND | wx.ALL, 12)
        sizer_panel.Add(self.notebook, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        sizer_panel.Add(sizer_boutons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        self.panel_1.SetSizer(sizer_panel)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel_1, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()
        self.CentreOnParent()

        self.sizer_header_textes = sizer_header_textes

    def OnSize(self, event):
        try:
            largeur = max(320, self.GetClientSize().GetWidth() - 190)
            self.label_hd_adresse.Wrap(largeur)
            self.label_hd_naiss.Wrap(largeur)
            self.panel_1.Layout()
        except Exception:
            pass
        event.Skip()

    def Affichage_barre_problemes(self):
        if self.txtPbPersonne == "" or self.barre_problemes == False:
            self.bitmap_problemes_G.Show(False)
            self.bitmap_problemes_D.Show(False)
            self.txtDefilant.Show(False)
            self.txtDefilant.Stop()
        else:
            self.bitmap_problemes_G.Show(True)
            self.bitmap_problemes_D.Show(True)
            self.txtDefilant.Show(True)
            self.txtDefilant.Start()
        self.panel_1.Layout()

    def MAJ_barre_problemes(self):
        if self.barre_problemes is None:
            return
        if self.barre_problemes == False:
            self.Affichage_barre_problemes()
        else:
            self.txtPbPersonne = self.MAJ_txt_pb_personne()
            self.txtDefilant.SetText(self.txtPbPersonne)
            self.Affichage_barre_problemes()

    def Recup_txt_pb_personne(self):
        dictNomsPersonnes, dictProblemesPersonnes = FonctionsPerso.Recup_liste_pb_personnes()
        if self.IDpersonne in dictProblemesPersonnes:
            txtProblemes = ""
            for labelCategorie, listeProblemes in dictProblemesPersonnes[self.IDpersonne].items():
                txtProblemes += labelCategorie + " ("
                for labelProbleme in listeProblemes:
                    txtProblemes += labelProbleme + ", "
                txtProblemes = txtProblemes[:-2] + ")       "
            return txtProblemes
        return ""

    def MAJ_txt_pb_personne(self):
        civilite = self.notebook.pageGeneralites.combo_box_civilite.GetStringSelection()
        nom = self.notebook.pageGeneralites.text_nom.GetValue()
        nom_jfille = self.notebook.pageGeneralites.text_ctrl_nomjf.GetValue()
        prenom = self.notebook.pageGeneralites.text_prenom.GetValue()

        temp = self.notebook.pageGeneralites.text_date_naiss.GetValue()
        if temp == "  /  /    ":
            date_naiss = None
        else:
            jour = int(temp[:2])
            mois = int(temp[3:5])
            annee = int(temp[6:10])
            date_naiss = datetime.date(annee, mois, jour)

        cp_naiss = self.notebook.pageGeneralites.text_cp_naiss.GetValue()
        ville_naiss = self.notebook.pageGeneralites.text_ville_naiss.GetValue()
        pays_naiss = self.notebook.pageGeneralites.IDpays_naiss
        nationalite = self.notebook.pageGeneralites.IDpays_nation
        num_secu = self.notebook.pageGeneralites.text_numsecu.GetValue()
        adresse_resid = self.notebook.pageGeneralites.text_adresse.GetValue()
        cp_resid = self.notebook.pageGeneralites.text_cp.GetValue()
        ville_resid = self.notebook.pageGeneralites.text_ville.GetValue()

        try:
            temp = self.notebook.pageGeneralites.combo_box_situation.GetClientData(
                self.notebook.pageGeneralites.combo_box_situation.GetSelection()
            )
            IDsituation = 0 if temp in (None, '') else temp
        except Exception:
            IDsituation = 0

        infosPersonne = ((
            self.IDpersonne, civilite, nom, nom_jfille, prenom, date_naiss,
            cp_naiss, ville_naiss, pays_naiss, nationalite, num_secu,
            adresse_resid, cp_resid, ville_resid, IDsituation
        ),)
        dictNomsPersonnes, dictProblemesPersonnes = FonctionsPerso.Recherche_problemes_personnes(
            listeIDpersonnes=(self.IDpersonne,), infosPersonne=infosPersonne
        )
        if self.IDpersonne in dictProblemesPersonnes:
            txtProblemes = ""
            for labelCategorie, listeProblemes in dictProblemesPersonnes[self.IDpersonne].items():
                txtProblemes += labelCategorie + " ("
                for labelProbleme in listeProblemes:
                    txtProblemes += labelProbleme + ", "
                txtProblemes = txtProblemes[:-2] + ")       "
            return txtProblemes
        return ""

    def MaJ_header(self):
        if self.IDpersonne == 0:
            ID = "Attribution de l'ID en cours"
        else:
            ID = self.IDpersonne

        if self.contratEnCours is None:
            txtContrat = _(u"Aucun contrat en cours")
        else:
            date_debut = FonctionsPerso.DateEngFr(self.contratEnCours[1])
            if self.contratEnCours[2] == "2999-01-01":
                txtContrat = _(u"Contrat en cours : ") + self.contratEnCours[0] + " depuis le " + date_debut + _(u" (Durée ind.)")
            else:
                date_fin = FonctionsPerso.DateEngFr(self.contratEnCours[2])
                date_rupture = FonctionsPerso.DateEngFr(self.contratEnCours[3])
                if date_rupture != "//":
                    date_fin = date_rupture
                txtContrat = _(u"Contrat en cours : ") + self.contratEnCours[0] + " du " + date_debut + " au " + date_fin

        self.label_hd_CatId.SetLabel(txtContrat + " | ID : " + str(ID))
        try:
            self.sizer_header_textes.Layout()
        except Exception:
            pass

    def OnMotionTxtDefilant(self, event):
        self.txtDefilant.Stop()
        event.Skip()

    def OnLeaveTxtDefilant(self, event):
        self.txtDefilant.Start()
        event.Skip()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Laficheindividuelle")

    def OnBoutonOk(self, event):
        self.AnnulationImpossible = False
        self.Fermer(save=True)
        event.Skip()

    def OnBoutonAnnuler(self, event):
        if self.AnnulationImpossible == True:
            self.Fermer(save=True)
        else:
            self.Fermer(save=False)
        event.Skip()

    def OnClose(self, event):
        if self.AnnulationImpossible == True:
            self.Fermer(save=True)
        else:
            self.Fermer(save=False)
        event.Skip()

    def Fermer(self, save=True):
        if save == False:
            if self.nouvelleFiche == True:
                db = GestionDB.DB()
                db.ReqDEL("coordonnees", "IDpersonne", self.IDpersonne)
                db.ReqDEL("personnes", "IDpersonne", self.IDpersonne)
                db.Close()
        else:
            if self.Verifie_validite_donnees() == True:
                self.notebook.pageGeneralites.Sauvegarde()
                self.notebook.pageQuestionnaire.Sauvegarde()
            else:
                return

        frm = FonctionsPerso.FrameOuverte("Personnes")
        if frm is not None:
            frm.listCtrl_personnes.MAJ(IDpersonne=self.IDpersonne)
            frm.panel_dossiers.tree_ctrl_problemes.MAJ_treeCtrl()
        self.EndModal(wx.ID_OK)

    def Verifie_validite_donnees(self):
        if self.notebook.pageGeneralites.combo_box_civilite.GetStringSelection() == "":
            dlg = wx.MessageDialog(self, _(u"Vous devez saisir obligatoirement une civilité !"), "Information", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.notebook.pageGeneralites.combo_box_civilite.SetFocus()
            return False
        if self.notebook.pageGeneralites.text_nom.GetValue() == "":
            dlg = wx.MessageDialog(self, _(u"Vous devez saisir obligatoirement un nom de famille !"), "Information", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.notebook.pageGeneralites.text_nom.SetFocus()
            return False
        if self.notebook.pageGeneralites.text_prenom.GetValue() == "":
            dlg = wx.MessageDialog(self, _(u"Vous devez saisir obligatoirement un prénom !"), "Information", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.notebook.pageGeneralites.text_prenom.SetFocus()
            return False
        return True


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None, IDpersonne=1)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
