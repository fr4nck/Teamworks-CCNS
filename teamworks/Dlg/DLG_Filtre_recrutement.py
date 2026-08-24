#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import datetime
import wx

from Utils.UTILS_Traduction import _
from Ctrl import CTRL_Bouton_image, CTRL_Section, CTRL_Texte
from Utils import UTILS_Interface, UTILS_Styles
import GestionDB

from Dlg import DLG_Filtre_coches
from Dlg import DLG_Filtre_choice
from Dlg import DLG_Filtre_texte
from Dlg import DLG_Selection_periode


def GetListeChoix_emplois():
    DB = GestionDB.DB()
    req = """SELECT IDemploi, intitule
    FROM emplois; """
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    listeDonnees.insert(0, (0, _(u"Candidature spontanée")))
    return listeDonnees


def GetListeChoix_fonctions():
    DB = GestionDB.DB()
    req = """SELECT IDfonction, fonction
    FROM fonctions; """
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    return listeDonnees


def GetListeChoix_affectations():
    DB = GestionDB.DB()
    req = """SELECT IDaffectation, affectation
    FROM affectations; """
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    return listeDonnees


def GetListeChoix_decisions():
    return [(0, _(u"Décision non prise")), (1, _(u"Oui")), (2, _(u"Non"))]


def GetListeChoix_reponses():
    return [(0, _(u"Non")), (1, _(u"Oui"))]


def GetListeChoix_civilites():
    return [(0, _(u"Mr")), (1, _(u"Melle")), (2, _(u"Mme"))]


def GetListeChoix_avis():
    return [
        (0, _(u"Avis inconnu")),
        (1, _(u"Pas convaincant")),
        (2, _(u"Mitigé")),
        (3, _(u"Bien")),
        (4, _(u"Très bien")),
    ]


def GetListeChoix_diffuseurs():
    DB = GestionDB.DB()
    req = """SELECT IDdiffuseur, diffuseur
    FROM diffuseurs; """
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    return listeDonnees


def GetListeChoix_diplomes():
    DB = GestionDB.DB()
    req = """SELECT IDtype_diplome, nom_diplome
    FROM types_diplomes; """
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    return listeDonnees


def ResoudreListeChoix(nom_liste):
    """Retourne une liste de choix déclarée sans exécution dynamique."""
    nom_fonction = "GetListeChoix_%s" % nom_liste
    fonction = globals().get(nom_fonction)
    if not callable(fonction):
        raise ValueError("Liste de choix inconnue : %s" % nom_liste)
    return fonction()


def ResoudreTypeControle(nom_type):
    """Résout uniquement les contrôles de filtre explicitement autorisés."""
    types_autorises = {
        "hyperlink_date": hyperlink_date,
        "hyperlink_choice": hyperlink_choice,
        "hyperlink_liste": hyperlink_liste,
        "hyperlink_texte": hyperlink_texte,
    }
    if nom_type not in types_autorises:
        raise ValueError("Type de filtre inconnu : %s" % nom_type)
    return types_autorises[nom_type]


class MyDialog(wx.Dialog):
    """Sélection des filtres de recrutement."""

    TITRES_CATEGORIES = {
        "candidats": _(u"Candidats"),
        "candidatures": _(u"Candidatures"),
        "entretiens": _(u"Entretiens"),
        "emplois": _(u"Offres d'emploi"),
    }

    def __init__(self, parent, id=-1, categorie="", listeValeursDefaut=None, title=_(u"Sélection de filtres de liste")):
        if listeValeursDefaut is None:
            listeValeursDefaut = []
        wx.Dialog.__init__(
            self,
            parent,
            id,
            title,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.categorie = categorie
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.dictControles = {
            "candidats": [
                [_(u"Nom"), "candidats_nom", "hyperlink_texte", None, "nom", None],
                [_(u"Prénom"), "candidats_prenom", "hyperlink_texte", None, "prenom", None],
                [_(u"Adresse"), "candidats_adresse_resid", "hyperlink_texte", None, "adresse_resid", None],
                [_(u"Code postal"), "candidats_cp_resid", "hyperlink_texte", None, "cp_resid", None],
                [_(u"Ville"), "candidats_ville_resid", "hyperlink_texte", None, "ville_resid", None],
                [_(u"Mémo"), "candidats_memo", "hyperlink_texte", None, "memo", None],
                [_(u"Qualifications"), "candidats_qualifications", "hyperlink_liste", "diplomes", "IDdiplome", None],
            ],
            "candidatures": [
                [_(u"Date de dépôt"), "candidature_date", "hyperlink_date", None, "date_depot", None],
                [_(u"Offre d'emploi"), "candidature_emploi", "hyperlink_liste", "emplois", "IDemploi", None],
                [_(u"Disponibilités"), "candidature_dispo", "hyperlink_date", None, ("date_debut", "date_fin"), None],
                [_(u"Fonctions"), "candidature_fonctions", "hyperlink_liste", "fonctions", "IDfonction", None],
                [_(u"Affectations"), "candidature_affectations", "hyperlink_liste", "affectations", "IDaffectation", None],
                [_(u"Décision"), "candidature_decision", "hyperlink_liste", "decisions", "IDdecision", None],
                [_(u"Réponse envoyée"), "candidature_reponse", "hyperlink_liste", "reponses", "reponse", None],
                [_(u"Date de réponse"), "candidature_date_reponse", "hyperlink_date", None, "date_reponse", None],
            ],
            "entretiens": [
                [_(u"Date"), "entretiens_date", "hyperlink_date", None, "date", None],
                [_(u"Avis"), "entretiens_avis", "hyperlink_liste", "avis", "avis", None],
                [_(u"Commentaire"), "entretiens_commentaire", "hyperlink_texte", None, "remarques", None],
            ],
            "emplois": [
                [_(u"Date de lancement"), "emplois_date_debut", "hyperlink_date", None, "date_debut", None],
                [_(u"Date de clôture"), "emplois_date_fin", "hyperlink_date", None, "date_fin", None],
                [_(u"Disponibilités"), "emplois_dispo", "hyperlink_date", None, ("date_debut", "date_fin"), None],
                [_(u"Fonctions"), "emplois_fonctions", "hyperlink_liste", "fonctions", "IDfonction", None],
                [_(u"Affectations"), "emplois_affectations", "hyperlink_liste", "affectations", "IDaffectation", None],
                [_(u"Diffuseurs"), "emplois_diffuseurs", "hyperlink_liste", "diffuseurs", "IDdiffuseur", None],
            ],
        }

        if self.categorie not in self.dictControles:
            raise ValueError("Catégorie de filtres inconnue : %s" % self.categorie)

        if listeValeursDefaut:
            self.SetValeursDefaut(listeValeursDefaut)

        self.titre = CTRL_Texte.H1(self, _(u"Filtres"))
        self.introduction = CTRL_Texte.BodySecondary(
            self,
            _(u"Définissez uniquement les critères utiles. Les autres restent sans importance."),
        )
        self.section = CTRL_Section.Section(
            self,
            titre=self.TITRES_CATEGORIES[self.categorie],
            niveau=2,
        )
        panel = self.section.GetContentPanel()
        self.listeControles = self.dictControles[self.categorie]

        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        grille = wx.FlexGridSizer(rows=len(self.listeControles), cols=2, vgap=gap, hgap=gap)
        grille.AddGrowableCol(1)

        for label, nomControle, typeControle, listeChoix, motSQL, valeur in self.listeControles:
            ctrl_label = CTRL_Texte.Label(panel, u"%s :" % label)
            grille.Add(ctrl_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
            classe_controle = ResoudreTypeControle(typeControle)
            if listeChoix is not None:
                controle = classe_controle(
                    panel,
                    valeur=valeur,
                    nomFiltre=label,
                    listeChoix=listeChoix,
                    motSQL=motSQL,
                )
            else:
                controle = classe_controle(
                    panel,
                    valeur=valeur,
                    nomFiltre=label,
                    motSQL=motSQL,
                )
            setattr(self, "ctrl_%s" % nomControle, controle)
            grille.Add(controle, 1, wx.EXPAND)
        panel.SetSizer(grille)

        self.bouton_reinitialiser = CTRL_Bouton_image.CTRL(self, texte=_(u"Réinitialiser"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, id=wx.ID_OK, texte=_(u"Appliquer"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Annuler"))

        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonReinit, self.bouton_reinitialiser)

        self._layout()
        UTILS_Styles.ApplyWindowProfile(self, "standard")

    def _layout(self):
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        toolbar_gap = UTILS_Styles.GetLayoutSpacing("toolbar_gap")

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_reinitialiser, 0)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0, wx.RIGHT, toolbar_gap)
        actions.Add(self.bouton_annuler, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)
        sizer.Add(self.introduction, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)
        sizer.Add(self.section, 1, wx.EXPAND | wx.ALL, gap)
        sizer.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        self.SetSizer(sizer)

    def OnBoutonOk(self, event):
        self.EndModal(wx.ID_OK)

    def OnBoutonReinit(self, event):
        for item in self.dictControles[self.categorie]:
            nomControle = item[1]
            controle = getattr(self, "ctrl_%s" % nomControle)
            controle.valeur = None
            controle.SetLabel(_(u"Sans importance"))

    def GetListeFiltres(self):
        listeFiltres = []
        for labelTemp, nomControle, typeControle, listeChoix, motSQL, valeurTemp in self.dictControles[self.categorie]:
            controle = getattr(self, "ctrl_%s" % nomControle)
            valeur = controle.valeur
            if valeur is not None:
                listeFiltres.append({
                    "nomControle": nomControle,
                    "label": controle.GetLabel(),
                    "labelControle": controle.nomFiltre,
                    "valeur": valeur,
                    "sql": controle.GetSQL(),
                })
        return listeFiltres

    def SetValeursDefaut(self, listeFiltres):
        for filtre in listeFiltres:
            nomControle = filtre["nomControle"]
            valeur = filtre["valeur"]
            for index, item in enumerate(self.dictControles[self.categorie]):
                if item[1] == nomControle:
                    self.dictControles[self.categorie][index][5] = valeur


class Hyperlink(wx.Button):
    """Contrôle de valeur de filtre, conservant l'API historique sans rendu hyperlink."""

    def __init__(self, parent, id=-1, label="", infobulle=_(u"Cliquez ici pour sélectionner un filtre"), URL="", size=(-1, -1)):
        wx.Button.__init__(self, parent, id=id, label=label)
        self.SetFont(UTILS_Styles.GetFont("body"))
        self.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))
        self.SetMinSize((-1, UTILS_Styles.GetControlMetric("button_min_height")))
        self.SetToolTip(wx.ToolTip(infobulle))
        self.Bind(wx.EVT_BUTTON, self.OnLeftLink)

    def OnLeftLink(self, event):
        self.ChangeValeur()


class hyperlink_date(Hyperlink):
    def __init__(self, parent, valeur=None, nomFiltre="", motSQL="", infobulle=_(u"Cliquez ici pour sélectionner un filtre")):
        self.valeur = valeur
        self.nomFiltre = nomFiltre
        self.motSQL = motSQL
        Hyperlink.__init__(self, parent, label=self.GetLabel(), infobulle=infobulle)

    def GetLabel(self):
        if self.valeur is None:
            return _(u"Sans importance")
        date_debut, date_fin = self.valeur
        if date_debut == date_fin:
            return _(u"Le %s") % date_debut.strftime("%d/%m/%Y")
        return _(u"Entre le %s et le %s") % (
            date_debut.strftime("%d/%m/%Y"),
            date_fin.strftime("%d/%m/%Y"),
        )

    def ChangeValeur(self):
        dlg = DLG_Selection_periode.SelectionPeriode(self)
        if self.valeur is not None:
            dlg.SetDates(date_debut=self.valeur[0], date_fin=self.valeur[1])
        if dlg.ShowModal() == wx.ID_OK:
            self.valeur = dlg.GetDates()
            dlg.Destroy()
            self.SetLabel(self.GetLabel())
        else:
            dlg.Destroy()

    def GetSQL(self):
        if self.valeur is None:
            return ""
        date_debut, date_fin = self.valeur
        if isinstance(self.motSQL, tuple):
            return "(%s>='%s' AND %s<='%s')" % (self.motSQL[1], date_debut, self.motSQL[0], date_fin)
        if date_debut == date_fin:
            return "%s='%s'" % (self.motSQL, date_debut)
        return "%s>='%s' AND %s<='%s'" % (self.motSQL, date_debut, self.motSQL, date_fin)


class hyperlink_choice(Hyperlink):
    def __init__(self, parent, valeur=None, nomFiltre="", motSQL="", listeChoix=None, infobulle=_(u"Cliquez ici pour sélectionner un filtre")):
        self.valeur = valeur
        self.nomFiltre = nomFiltre
        self.listeChoix = listeChoix or []
        self.motSQL = motSQL
        Hyperlink.__init__(self, parent, label=self.GetLabel(), infobulle=infobulle)

    def GetLabel(self):
        if self.valeur is None:
            return _(u"Sans importance")
        return self.valeur[1]

    def ChangeValeur(self):
        selection = None if self.valeur is None else self.valeur[0]
        liste = ResoudreListeChoix(self.listeChoix)
        dlg = DLG_Filtre_choice.MyDialog(
            self,
            nom_filtre=self.nomFiltre,
            titre_frame=_(u"Filtre"),
            selection=selection,
            listeChoix=liste,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self.valeur = dlg.GetSelection()
            dlg.Destroy()
            self.SetLabel(self.GetLabel())
        else:
            dlg.Destroy()

    def GetSQL(self):
        if self.valeur is None:
            return ""
        return "%s=%s" % (self.motSQL, self.valeur[0])


class hyperlink_liste(Hyperlink):
    def __init__(self, parent, valeur=None, nomFiltre="", motSQL="", listeChoix=None, infobulle=_(u"Cliquez ici pour sélectionner un filtre")):
        self.valeur = valeur
        self.nomFiltre = nomFiltre
        self.listeChoix = listeChoix or []
        self.motSQL = motSQL
        Hyperlink.__init__(self, parent, label=self.GetLabel(), infobulle=infobulle)

    def GetLabel(self):
        if self.valeur is None:
            return _(u"Sans importance")
        if len(self.valeur) == 0:
            return _(u"Aucun élément")
        return ", ".join(texte for ID, texte in self.valeur)

    def ChangeValeur(self):
        listeSelection = None if self.valeur is None else [ID for ID, texte in self.valeur]
        liste = ResoudreListeChoix(self.listeChoix)
        dlg = DLG_Filtre_coches.MyDialog(
            self,
            nom_filtre=self.nomFiltre,
            titre_frame=_(u"Filtre"),
            listeSelection=listeSelection,
            listeChoix=liste,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self.valeur = dlg.GetListeSelections()
            dlg.Destroy()
            self.SetLabel(self.GetLabel())
        else:
            dlg.Destroy()

    def GetSQL(self):
        if self.valeur is None:
            return ""
        if len(self.valeur) == 0:
            return "%s=Null" % self.motSQL
        if len(self.valeur) == 1:
            return "%s=%d" % (self.motSQL, self.valeur[0][0])
        listeID = [ID for ID, label in self.valeur]
        return "%s IN %s" % (self.motSQL, tuple(listeID))


class hyperlink_texte(Hyperlink):
    def __init__(self, parent, valeur=None, nomFiltre="", motSQL="", infobulle=_(u"Cliquez ici pour sélectionner un filtre")):
        self.valeur = valeur
        self.nomFiltre = nomFiltre
        self.motSQL = motSQL
        Hyperlink.__init__(self, parent, label=self.GetLabel(), infobulle=infobulle)

    def GetLabel(self):
        if self.valeur is None:
            return _(u"Sans importance")
        return _(u"Avec l'expression '%s'") % self.valeur

    def ChangeValeur(self):
        dlg = DLG_Filtre_texte.MyDialog(
            self,
            nom_filtre=self.nomFiltre,
            titre_frame=_(u"Filtre"),
            texte=self.valeur,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self.valeur = dlg.GetTexte()
            dlg.Destroy()
            self.SetLabel(self.GetLabel())
        else:
            dlg.Destroy()

    def GetSQL(self):
        if self.valeur is None:
            return ""
        valeur = self.valeur.replace("'", "''")
        return "%s LIKE '%%%s%%'" % (self.motSQL, valeur)


if __name__ == "__main__":
    app = wx.App(0)
    frm = MyDialog(None, categorie="emplois")
    frm.ShowModal()
    app.MainLoop()
