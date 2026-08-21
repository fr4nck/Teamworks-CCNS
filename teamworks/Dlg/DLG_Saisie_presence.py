#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Saisie d'une ou plusieurs présences.

Le moteur métier (validation, chevauchements, enregistrement) est conservé,
mais la présentation consomme désormais exclusivement le design system
Teamworks.
"""

import datetime
import wx
import wx.lib.dialogs
import wx.lib.masked as masked
from wx.lib.mixins.listctrl import CheckListCtrlMixin

import Chemins
import GestionDB
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Section
from Ctrl import CTRL_Texte
from Utils import UTILS_Interface
from Utils import UTILS_Presences
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _


_PHOENIX = "phoenix" in wx.PlatformInfo
_CheckboxFallback = object if _PHOENIX else CheckListCtrlMixin


def DatetimeDateEnStr(date):
    liste_jours = (
        _(u"Lundi"), _(u"Mardi"), _(u"Mercredi"), _(u"Jeudi"),
        _(u"Vendredi"), _(u"Samedi"), _(u"Dimanche"),
    )
    liste_mois = (
        _(u"janvier"), _(u"février"), _(u"mars"), _(u"avril"),
        _(u"mai"), _(u"juin"), _(u"juillet"), _(u"août"),
        _(u"septembre"), _(u"octobre"), _(u"novembre"), _(u"décembre"),
    )
    return "%s %d %s %d" % (
        liste_jours[date.weekday()],
        date.day,
        liste_mois[date.month - 1],
        date.year,
    )


def StrEnDatetime(texteHeure):
    texte = texteHeure[:5]
    heures, minutes = texte.split(":")
    return datetime.time(int(heures), int(minutes))


def StrEnDatetimeDate(texteDate):
    return datetime.date(
        int(texteDate[:4]),
        int(texteDate[5:7]),
        int(texteDate[8:10]),
    )


def _dialog_ancestor(window):
    current = window
    while current is not None:
        if isinstance(current, wx.Dialog):
            return current
        try:
            current = current.GetParent()
        except Exception:
            current = None
    return None


class Panel(wx.Panel):
    def __init__(
        self,
        parent,
        id=-1,
        listeDonnees=None,
        IDmodif=0,
        mode="planning",
        panelPlanning=None,
    ):
        listeDonnees = list(listeDonnees or [])
        wx.Panel.__init__(
            self,
            parent,
            id=id,
            name="panel_saisiePresences",
            style=wx.TAB_TRAVERSAL,
        )
        self.parent = parent
        self.mode = mode
        self.panelPlanning = panelPlanning
        self.IDmodif = IDmodif
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        if self.IDmodif != 0 and mode == "planning":
            donnees_modif = self.ImportDonneesModif()
            if donnees_modif is None:
                dialog = _dialog_ancestor(self)
                if dialog is not None:
                    wx.CallAfter(dialog.EndModal, wx.ID_CANCEL)
                return
            self.donneesModif = donnees_modif
            listeDonnees = [(donnees_modif[1], donnees_modif[2])]

        if self.IDmodif != 0 and mode == "modele":
            self.listeDonnees = listeDonnees

        self.dictDonnees = {}
        if mode == "planning":
            self.CreationDictDonnees(listeDonnees)

        self.dictPersonnes = self.ImportPersonnes()

        # Dates et personnes sélectionnées.
        self.section_donnees = CTRL_Section.Section(
            self,
            titre=_(u"Dates et personnes"),
            niveau=2,
        )
        contenu_donnees = self.section_donnees.GetContentPanel()
        self.label_selection = CTRL_Texte.BodySecondary(contenu_donnees, u"")
        self.listCtrl_donnees = ListCtrl_donnees(
            contenu_donnees,
            owner=self,
        )
        donnees_sizer = wx.BoxSizer(wx.VERTICAL)
        donnees_sizer.Add(self.label_selection, 0, wx.EXPAND | wx.BOTTOM, UTILS_Styles.GetLayoutSpacing("field_gap"))
        donnees_sizer.Add(self.listCtrl_donnees, 1, wx.EXPAND)
        contenu_donnees.SetSizer(donnees_sizer)

        # Horaires et légende.
        self.section_details = CTRL_Section.Section(
            self,
            titre=_(u"Horaires et légende"),
            niveau=2,
        )
        contenu_details = self.section_details.GetContentPanel()
        self.label_heure_debut = CTRL_Texte.Label(contenu_details, _(u"Début"))
        self.text_heure_debut = masked.TextCtrl(
            contenu_details,
            -1,
            "",
            style=wx.TE_CENTRE,
            mask="##:##",
            validRegex="[0-2][0-9]:[0-5][0-9]",
        )
        self.label_heure_fin = CTRL_Texte.Label(contenu_details, _(u"Fin"))
        self.text_heure_fin = masked.TextCtrl(
            contenu_details,
            -1,
            "",
            style=wx.TE_CENTRE,
            mask="##:##",
            validRegex="[0-2][0-9]:[0-5][0-9]",
        )
        self.label_intitule = CTRL_Texte.Label(contenu_details, _(u"Légende"))
        self.text_intitule = wx.TextCtrl(
            contenu_details,
            -1,
            "",
            style=wx.TE_MULTILINE,
        )
        self.text_heure_debut.SetFont(UTILS_Styles.GetFont("data-large"))
        self.text_heure_fin.SetFont(UTILS_Styles.GetFont("data-large"))
        taille_heure = UTILS_Styles.Scale(96)
        self.text_heure_debut.SetMinSize((taille_heure, -1))
        self.text_heure_fin.SetMinSize((taille_heure, -1))
        self.text_intitule.SetMinSize((-1, UTILS_Styles.Scale(96)))

        # Catégorie : texte hiérarchique uniquement, sans arc-en-ciel décoratif.
        self.section_categorie = CTRL_Section.Section(
            self,
            titre=_(u"Catégorie"),
            niveau=2,
        )
        contenu_categorie = self.section_categorie.GetContentPanel()
        self.treeCtrl_categories = TreeCtrlCategories(
            contenu_categorie,
            owner=self,
        )
        categorie_sizer = wx.BoxSizer(wx.VERTICAL)
        categorie_sizer.Add(self.treeCtrl_categories, 1, wx.EXPAND)
        contenu_categorie.SetSizer(categorie_sizer)

        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Aide"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"),
        )
        self.bouton_ok = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_OK,
            texte=_(u"Valider"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"),
        )
        self.bouton_annuler = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_CANCEL,
            texte=_(u"Annuler"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"),
        )

        if self.IDmodif != 0 and mode == "planning":
            self.text_heure_debut.SetValue(str(self.donneesModif[3])[:5])
            self.text_heure_fin.SetValue(str(self.donneesModif[4])[:5])
            self.text_intitule.SetValue(
                UTILS_Presences.normaliser_intitule_presence(self.donneesModif[6])
            )
        if self.IDmodif != 0 and mode == "modele":
            self.text_heure_debut.SetValue(listeDonnees[5])
            self.text_heure_fin.SetValue(listeDonnees[6])
            self.text_intitule.SetValue(
                UTILS_Presences.normaliser_intitule_presence(listeDonnees[8])
            )

        self.__set_properties()
        self.__do_layout(contenu_details)
        self.UpdateSelectionSummary()

        # En modification ou dans un modèle, la liste de dates/personnes n'est
        # pas un choix à faire dans ce formulaire.
        if self.IDmodif != 0 or self.mode == "modele":
            self.section_donnees.Hide()

        self.text_heure_debut.SetFocus()
        self.Bind(wx.EVT_TEXT, self.OnTextHeureDebutText, self.text_heure_debut)
        self.Bind(wx.EVT_TEXT, self.OnTextHeureFinText, self.text_heure_fin)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

        # Attributs historiques conservés comme références de compatibilité.
        self.sizer_1 = donnees_sizer
        self.sizer_donnees_staticbox = self.section_donnees.titre
        self.grid_sizer_base = self.GetSizer()

    def __set_properties(self):
        self.text_intitule.SetToolTip(
            wx.ToolTip(_(u"Saisissez ici une légende optionnelle"))
        )
        self.treeCtrl_categories.SetToolTip(
            wx.ToolTip(_(u"Sélectionnez ici une catégorie"))
        )
        self.listCtrl_donnees.SetToolTip(
            wx.ToolTip(
                _(u"Décochez les dates ou personnes que vous ne souhaitez finalement pas enregistrer.")
            )
        )
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_(u"Valider la saisie")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Annuler la saisie")))

    def __do_layout(self, contenu_details):
        field_gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        section_gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        toolbar_gap = UTILS_Styles.GetLayoutSpacing("toolbar_gap")

        ligne_heures = wx.BoxSizer(wx.HORIZONTAL)
        ligne_heures.Add(self.label_heure_debut, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, field_gap)
        ligne_heures.Add(self.text_heure_debut, 0, wx.RIGHT, section_gap)
        ligne_heures.Add(self.label_heure_fin, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, field_gap)
        ligne_heures.Add(self.text_heure_fin, 0)
        ligne_heures.AddStretchSpacer(1)

        details_sizer = wx.BoxSizer(wx.VERTICAL)
        details_sizer.Add(ligne_heures, 0, wx.EXPAND | wx.BOTTOM, section_gap)
        details_sizer.Add(self.label_intitule, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        details_sizer.Add(self.text_intitule, 1, wx.EXPAND)
        contenu_details.SetSizer(details_sizer)

        milieu = wx.BoxSizer(wx.HORIZONTAL)
        milieu.Add(self.section_details, 3, wx.EXPAND | wx.RIGHT, section_gap)
        milieu.Add(self.section_categorie, 2, wx.EXPAND)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_aide, 0)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0, wx.RIGHT, toolbar_gap)
        actions.Add(self.bouton_annuler, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.section_donnees, 2, wx.EXPAND | wx.ALL, page_gap)
        sizer.Add(
            milieu,
            3,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            page_gap,
        )
        sizer.Add(
            actions,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            page_gap,
        )
        self.SetSizer(sizer)

    def CreationDictDonnees(self, listeDonnees=None):
        listeDonnees = list(listeDonnees or [])
        self.dictDonnees = {
            index: [IDpersonne, date, True]
            for index, (IDpersonne, date) in enumerate(listeDonnees, start=1)
        }
        if hasattr(self, "listCtrl_donnees"):
            self.listCtrl_donnees.SetDonnees(self.dictDonnees)
        if hasattr(self, "label_selection"):
            self.UpdateSelectionSummary()

    def UpdateSelectionSummary(self):
        if self.mode != "planning":
            return
        nombre = sum(1 for valeurs in self.dictDonnees.values() if valeurs[2])
        if nombre == 0:
            texte = _(u"Aucune présence ne sera créée")
        elif nombre == 1:
            texte = _(u"1 présence sera créée")
        else:
            texte = str(nombre) + _(u" présences seront créées")
        self.label_selection.SetLabel(texte)
        self.section_donnees.titre.SetLabel(_(u"Dates et personnes"))

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Saisirunetcheunique")

    def OnBoutonAnnuler(self, event):
        dialog = _dialog_ancestor(self)
        if dialog is not None:
            dialog.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event):
        if not self.ValidationDonnees():
            return
        if self.mode == "planning":
            if self.IDmodif == 0:
                etat = self.SauvegardeNouveau()
            else:
                etat = self.SauvegardeModif()
            if etat == "PasOk":
                return
        dialog = _dialog_ancestor(self)
        if dialog is not None:
            dialog.EndModal(wx.ID_OK)

    def ValidationDonnees(self):
        if self.mode == "planning":
            if not any(valeurs[2] for valeurs in self.dictDonnees.values()):
                wx.MessageBox(
                    _(u"Vous devez sélectionner au moins une date."),
                    _(u"Erreur de saisie"),
                )
                return False

        heure_debut = self.text_heure_debut.GetValue()
        heure_fin = self.text_heure_fin.GetValue()
        if heure_debut == "  :  ":
            wx.MessageBox(_(u"Vous devez saisir une heure de début."), _(u"Erreur de saisie"))
            self.text_heure_debut.SetFocus()
            return False
        if heure_debut[3:] >= "60" or " " in heure_debut[3:]:
            wx.MessageBox(_(u"L'heure de début n'est pas valide."), _(u"Erreur de saisie"))
            self.text_heure_debut.SetFocus()
            return False
        if heure_fin == "  :  ":
            wx.MessageBox(_(u"Vous devez saisir une heure de fin."), _(u"Erreur de saisie"))
            self.text_heure_fin.SetFocus()
            return False
        if heure_debut < "00:00" or heure_debut > "24:00":
            wx.MessageBox(_(u"L'heure de début n'est pas valide."), _(u"Erreur de saisie"))
            self.text_heure_debut.SetFocus()
            return False
        if heure_fin[3:] >= "60" or " " in heure_fin[3:]:
            wx.MessageBox(_(u"L'heure de fin n'est pas valide."), _(u"Erreur de saisie"))
            self.text_heure_fin.SetFocus()
            return False
        if heure_fin < "00:00" or heure_fin > "24:00":
            wx.MessageBox(_(u"L'heure de fin n'est pas valide."), _(u"Erreur de saisie"))
            self.text_heure_fin.SetFocus()
            return False
        if heure_debut > heure_fin:
            wx.MessageBox(
                _(u"L'heure de fin doit être supérieure à l'heure de début."),
                _(u"Erreur de saisie"),
            )
            self.text_heure_debut.SetFocus()
            return False

        debut = datetime.timedelta(
            hours=int(heure_debut[:2]),
            minutes=int(heure_debut[3:]),
        )
        fin = datetime.timedelta(
            hours=int(heure_fin[:2]),
            minutes=int(heure_fin[3:]),
        )
        if ((fin - debut).seconds // 60.0) < 15:
            wx.MessageBox(
                _(u"La durée de la tâche doit être au minimum de 15 minutes."),
                _(u"Erreur de saisie"),
            )
            self.text_heure_debut.SetFocus()
            return False

        if self.treeCtrl_categories.GetDataSelection() is None:
            wx.MessageBox(
                _(u"Vous devez sélectionner une catégorie dans la liste proposée."),
                _(u"Erreur de saisie"),
            )
            return False

        intitule = UTILS_Presences.normaliser_intitule_presence(
            self.text_intitule.GetValue()
        )
        if len(intitule) > 200:
            wx.MessageBox(
                _(u"Vous devez écrire une légende plus courte."),
                _(u"Erreur de saisie"),
            )
            self.text_intitule.SetFocus()
            return False
        return True

    def _valider_heure_pendant_saisie(self, controle, suivant):
        texte_brut = controle.GetPlainValue()
        if len(texte_brut) != 4 or not texte_brut.isdigit():
            return
        if not (0 <= int(texte_brut[:2]) <= 24):
            return
        if not (0 <= int(texte_brut[2:]) <= 59):
            return
        debut = self.text_heure_debut.GetPlainValue()
        fin = self.text_heure_fin.GetPlainValue()
        if len(debut) == 4 and len(fin) == 4 and debut.isdigit() and fin.isdigit():
            if int(fin) <= int(debut):
                return
        suivant.SetFocus()

    def OnTextHeureDebutText(self, event):
        self._valider_heure_pendant_saisie(
            self.text_heure_debut,
            self.text_heure_fin,
        )
        event.Skip()

    def OnTextHeureFinText(self, event):
        self._valider_heure_pendant_saisie(
            self.text_heure_fin,
            self.text_intitule,
        )
        event.Skip()

    def SauvegardeModif(self):
        DB = GestionDB.DB()
        IDpersonne = self.donneesModif[1]
        date = self.donneesModif[2]
        heure_debut = self.text_heure_debut.GetValue()
        heure_fin = self.text_heure_fin.GetValue()
        IDcategorie = self.treeCtrl_categories.GetDataSelection()
        intitule = UTILS_Presences.normaliser_intitule_presence(
            self.text_intitule.GetValue()
        )
        liste_donnees = [
            ("heure_debut", heure_debut),
            ("heure_fin", heure_fin),
            ("IDcategorie", IDcategorie),
            ("intitule", intitule),
        ]
        req = """
        SELECT IDpresence, date, heure_debut, heure_fin
        FROM presences
        WHERE (date='%s' AND IDpersonne=%d) AND
        (heure_debut<'%s' And heure_fin>'%s');
        """ % (str(date), IDpersonne, heure_fin, heure_debut)
        DB.ExecuterReq(req)
        liste_presences = DB.ResultatReq()
        pas_chevauchement = True
        if len(liste_presences) == 1:
            if liste_presences[0][0] != self.IDmodif:
                pas_chevauchement = False
        elif len(liste_presences) > 1:
            pas_chevauchement = False

        if not pas_chevauchement:
            dlg = wx.MessageDialog(
                self,
                _(u"Les horaires modifiés chevauchent une autre tâche de la même personne sur cette journée. Modifiez les horaires avant d'enregistrer."),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_WARNING,
            )
            dlg.ShowModal()
            dlg.Destroy()
            DB.Close()
            return "PasOk"

        DB.ReqMAJ("presences", liste_donnees, "IDpresence", self.IDmodif)
        DB.Commit()
        DB.Close()
        return self.IDmodif

    def SauvegardeNouveau(self):
        liste_exceptions = []
        nombre_selectionne = sum(1 for valeurs in self.dictDonnees.values() if valeurs[2])
        DB = GestionDB.DB()

        for valeurs in self.dictDonnees.values():
            if not valeurs[2]:
                continue
            IDpersonne = valeurs[0]
            date = str(valeurs[1])
            heure_debut = self.text_heure_debut.GetValue()
            heure_fin = self.text_heure_fin.GetValue()
            req = """
            SELECT IDpresence, date, heure_debut, heure_fin
            FROM presences
            WHERE (date='%s' AND IDpersonne=%d) AND
            (heure_debut<'%s' And heure_fin>'%s');
            """ % (date, IDpersonne, heure_fin, heure_debut)
            DB.ExecuterReq(req)
            liste_presences = DB.ResultatReq()

            if liste_presences:
                nom = self.dictPersonnes[IDpersonne][0] + " " + self.dictPersonnes[IDpersonne][1]
                liste_exceptions.append((nom, DatetimeDateEnStr(valeurs[1])))
                continue

            DB.ReqInsert(
                "presences",
                [
                    ("IDpersonne", IDpersonne),
                    ("date", date),
                    ("heure_debut", heure_debut),
                    ("heure_fin", heure_fin),
                    ("IDcategorie", self.treeCtrl_categories.GetDataSelection()),
                    (
                        "intitule",
                        UTILS_Presences.normaliser_intitule_presence(
                            self.text_intitule.GetValue()
                        ),
                    ),
                ],
            )
            DB.Commit()
        DB.Close()

        nombre_invalides = len(liste_exceptions)
        nombre_valides = nombre_selectionne - nombre_invalides
        if nombre_invalides:
            if nombre_valides == 0:
                message = _(u"Aucune tâche n'a été enregistrée.")
            elif nombre_valides == 1:
                message = _(u"1 tâche a été enregistrée.")
            else:
                message = str(nombre_valides) + _(u" tâches ont été enregistrées.")
            message += "\n\n" + _(
                u"Les tâches suivantes n'ont pas été enregistrées car elles chevauchent des tâches existantes :"
            ) + "\n\n"
            for nom, date in liste_exceptions:
                message += "• %s — %s\n" % (date, nom)
            dlg = wx.lib.dialogs.ScrolledMessageDialog(
                self,
                message,
                _(u"Rapport d'enregistrement"),
            )
            dlg.ShowModal()
            dlg.Destroy()
        return "Ok"

    def GetDonneesModele(self):
        ID = self.IDmodif
        heure_debut = self.text_heure_debut.GetValue()
        heure_fin = self.text_heure_fin.GetValue()
        IDcategorie = self.treeCtrl_categories.GetDataSelection()
        intitule = UTILS_Presences.normaliser_intitule_presence(
            self.text_intitule.GetValue()
        )
        if ID != 0:
            IDmodele = self.listeDonnees[1]
            type_modele = self.listeDonnees[2]
            periode = self.listeDonnees[3]
            jour = self.listeDonnees[4]
        else:
            IDmodele = None
            type_modele = None
            periode = None
            jour = None
        return (
            ID,
            IDmodele,
            type_modele,
            periode,
            jour,
            heure_debut,
            heure_fin,
            IDcategorie,
            intitule,
        )

    def ImportPersonnes(self):
        DB = GestionDB.DB()
        DB.ExecuterReq("SELECT IDpersonne, nom, prenom FROM personnes")
        liste_personnes = DB.ResultatReq()
        DB.Close()
        return {
            item[0]: (item[1], item[2])
            for item in liste_personnes
        }

    def ImportDonneesModif(self):
        DB = GestionDB.DB()
        DB.ExecuterReq(
            "SELECT * FROM presences WHERE IDpresence=%d" % self.IDmodif
        )
        resultats = DB.ResultatReq()
        DB.Close()
        if not resultats:
            wx.MessageBox(
                _(u"Cette présence n'existe plus dans la base de données."),
                _(u"Présence introuvable"),
                wx.OK | wx.ICON_ERROR,
            )
            return None
        donnees = resultats[0]
        return (
            donnees[0],
            donnees[1],
            StrEnDatetimeDate(donnees[2]),
            StrEnDatetime(donnees[3]),
            StrEnDatetime(donnees[4]),
            donnees[5],
            donnees[6],
        )


class ListCtrl_donnees(wx.ListCtrl, _CheckboxFallback):
    """Dates/personnes avec une seule implémentation de checkbox par plateforme."""

    def __init__(self, parent, owner):
        wx.ListCtrl.__init__(
            self,
            parent,
            -1,
            style=wx.LC_REPORT | wx.LC_NO_HEADER | wx.LC_HRULES | wx.BORDER_NONE,
        )
        if _PHOENIX:
            self.EnableCheckBoxes(True)
        else:
            CheckListCtrlMixin.__init__(self)
        self.owner = owner
        self._suspend_checks = False
        self.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        self.InitColonnes()
        self.SetDonnees(owner.dictDonnees if owner.mode == "planning" else {})
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        if _PHOENIX:
            if hasattr(wx, "EVT_LIST_ITEM_CHECKED"):
                self.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnNativeCheckItem)
            if hasattr(wx, "EVT_LIST_ITEM_UNCHECKED"):
                self.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnNativeCheckItem)

    def _is_checked(self, index):
        return self.IsItemChecked(index) if _PHOENIX else self.IsChecked(index)

    def _set_checked(self, index, etat=True):
        self.CheckItem(index, etat)

    def InitColonnes(self):
        self.InsertColumn(0, "")
        self.InsertColumn(1, _(u"Personne"))
        self.InsertColumn(2, _(u"Date"))

    def SetDonnees(self, dictDonnees):
        self.dictDonnees = dictDonnees
        self.Remplissage()

    def Remplissage(self):
        self.DeleteAllItems()
        if not hasattr(self, "dictDonnees"):
            return
        dict_personnes = self.owner.dictPersonnes if hasattr(self.owner, "dictPersonnes") else self.owner.ImportPersonnes()
        self._suspend_checks = True
        try:
            for ID, valeurs in sorted(self.dictDonnees.items()):
                IDpersonne, date, selection = valeurs
                index = self.InsertItem(self.GetItemCount(), "")
                nom = dict_personnes.get(IDpersonne, (_(u"Personne inconnue"), ""))
                self.SetItem(index, 1, (nom[0] + " " + nom[1]).strip())
                self.SetItem(index, 2, DatetimeDateEnStr(date))
                self.SetItemData(index, ID)
                self._set_checked(index, bool(selection))
        finally:
            self._suspend_checks = False
        self.MAJ_listeDonnees()
        wx.CallAfter(self.AjusterColonnes)

    def OnSize(self, event):
        wx.CallAfter(self.AjusterColonnes)
        event.Skip()

    def AjusterColonnes(self):
        largeur = self.GetClientSize().GetWidth()
        if largeur <= 0 or self.GetColumnCount() < 3:
            return
        coche = UTILS_Styles.Scale(34)
        personne = max(UTILS_Styles.Scale(150), int(largeur * 0.38))
        date = max(UTILS_Styles.Scale(220), largeur - coche - personne - UTILS_Styles.GetSpacing("xs"))
        self.SetColumnWidth(0, coche)
        self.SetColumnWidth(1, personne)
        self.SetColumnWidth(2, date)

    def OnItemActivated(self, event):
        self._suspend_checks = True
        try:
            self._set_checked(event.Index, not self._is_checked(event.Index))
        finally:
            self._suspend_checks = False
        self.MAJ_listeDonnees()

    def OnCheckItem(self, index, flag):
        if not self._suspend_checks:
            self.MAJ_listeDonnees()

    def OnNativeCheckItem(self, event):
        if not self._suspend_checks:
            self.MAJ_listeDonnees()
        event.Skip()

    def MAJ_listeDonnees(self):
        if not hasattr(self, "dictDonnees"):
            return
        for index in range(self.GetItemCount()):
            ID = self.GetItemData(index)
            if ID in self.dictDonnees:
                self.dictDonnees[ID][2] = self._is_checked(index)
        if hasattr(self.owner, "UpdateSelectionSummary"):
            self.owner.UpdateSelectionSummary()


class TreeCtrlCategories(wx.TreeCtrl):
    """Arbre de catégories textuel, sans palette locale par catégorie."""

    def __init__(self, parent, owner):
        wx.TreeCtrl.__init__(
            self,
            parent,
            -1,
            style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT,
        )
        self.owner = owner
        self.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        self.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))
        self.listeCategories = self.Importation()
        self.root = self.AddRoot(_(u"Catégories"))
        self.SetItemData(self.root, None)
        self.Remplissage()
        self.ExpandAll()

    def Remplissage(self):
        if not self.listeCategories:
            return
        self.Boucle(0, self.root)

    def Boucle(self, IDparent, itemParent):
        for item in self.listeCategories:
            if item[2] != IDparent:
                continue
            new_item = self.AppendItem(itemParent, item[1])
            self.SetItemData(new_item, item[0])

            if self.owner.IDmodif != 0 and self.owner.mode == "planning":
                if self.owner.donneesModif[5] == item[0]:
                    self.SelectItem(new_item, True)
            if self.owner.IDmodif != 0 and self.owner.mode == "modele":
                if self.owner.listeDonnees[7] == item[0]:
                    self.SelectItem(new_item, True)
            self.Boucle(item[0], new_item)

    def Importation(self):
        DB = GestionDB.DB()
        DB.ExecuterReq("SELECT * FROM cat_presences")
        liste_categories = DB.ResultatReq()
        DB.Close()
        return liste_categories

    def GetDataSelection(self):
        item = self.GetSelection()
        if not item.IsOk():
            return None
        return self.GetItemData(item)


class Dialog(wx.Dialog):
    def __init__(
        self,
        parent,
        listeDonnees=None,
        IDmodif=0,
        mode="planning",
        panelPlanning=None,
    ):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.panelPlanning = panelPlanning
        self.panel = Panel(
            self,
            listeDonnees=listeDonnees or [],
            IDmodif=IDmodif,
            mode=mode,
            panelPlanning=self.panelPlanning,
        )
        self.SetTitle(
            _(u"Saisie d'une présence")
            if IDmodif == 0
            else _(u"Modification d'une présence")
        )
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        UTILS_Styles.ApplyWindowProfile(self, "standard")

    def Fermer(self):
        self.EndModal(wx.ID_CANCEL)


if __name__ == "__main__":
    app = wx.App(0)
    liste_donnees = [
        (2, datetime.date(2008, 1, 1)),
        (2, datetime.date(2008, 1, 15)),
    ]
    dlg = Dialog(None, liste_donnees)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
