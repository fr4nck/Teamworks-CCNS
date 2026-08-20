#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import wx
from Ctrl import CTRL_Questionnaire
from Utils import UTILS_Interface
import GestionDB


class Panel(wx.Panel):
    def __init__(self, parent, id=-1, IDpersonne=0):
        wx.Panel.__init__(self, parent, id, name="panel_pageQuestionnaire", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDpersonne = IDpersonne
        self.majEffectuee = False
        self._ajustement_en_cours = False
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.titre = wx.StaticText(self, -1, "Questionnaire")
        font = self.titre.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        font.SetPointSize(max(11, font.GetPointSize() + 2))
        self.titre.SetFont(font)

        # Les valeurs ne sont que des minima d'initialisation : OnSize répartit
        # ensuite toute la largeur réellement disponible.
        self.ctrl_questionnaire = CTRL_Questionnaire.CTRL(
            self,
            type="individu",
            IDindividu=self.IDpersonne,
            largeurQuestion=300,
            largeurReponse=420,
        )
        self.ctrl_questionnaire.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer.Add(self.ctrl_questionnaire, 1, wx.EXPAND | wx.ALL, 8)
        self.SetSizer(sizer)

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.MAJ()
        wx.CallAfter(self.AjusterLargeurs)

    def OnSize(self, event):
        wx.CallAfter(self.AjusterLargeurs)
        event.Skip()

    def AjusterLargeurs(self):
        """Répartit la largeur entre question et réponse, contrôles compris."""
        if self._ajustement_en_cours:
            return
        try:
            largeur = self.ctrl_questionnaire.GetClientSize().GetWidth() - 28
        except Exception:
            return
        if largeur < 520:
            return

        largeur_question = max(240, int(largeur * 0.38))
        largeur_reponse = max(280, largeur - largeur_question)
        largeur_ctrl = max(260, largeur_reponse - 12)

        self._ajustement_en_cours = True
        try:
            self.ctrl_questionnaire.largeurQuestion = largeur_question
            self.ctrl_questionnaire.largeurReponse = largeur_reponse
            self.ctrl_questionnaire.SetColumnWidth(0, largeur_question)
            self.ctrl_questionnaire.SetColumnWidth(1, largeur_reponse)

            for categorie in self.ctrl_questionnaire.dictCategories.values():
                for track in categorie.get("questions", []):
                    ctrl = getattr(track, "ctrl", None)
                    if ctrl is None:
                        continue
                    track.largeur = largeur_ctrl
                    try:
                        taille = ctrl.GetSize()
                        ctrl.SetMinSize((largeur_ctrl, taille.GetHeight()))
                        ctrl.SetSize((largeur_ctrl, taille.GetHeight()))
                    except Exception:
                        pass

            try:
                self.ctrl_questionnaire.GetMainWindow().CalculatePositions()
            except Exception:
                pass
            self.ctrl_questionnaire.Refresh()
        finally:
            self._ajustement_en_cours = False

    def MAJ(self):
        """MAJ intégrale du contrôle avec MAJ des données."""
        if self.majEffectuee:
            return
        self.ctrl_questionnaire.MAJ()
        self.majEffectuee = True
        wx.CallAfter(self.AjusterLargeurs)

    def ValidationData(self):
        return True

    def Sauvegarde(self):
        valeurs = self.ctrl_questionnaire.GetValeurs()
        dictReponses = self.ctrl_questionnaire.GetDictReponses()
        dictValeursInitiales = self.ctrl_questionnaire.GetDictValeursInitiales()

        DB = GestionDB.DB()
        for IDquestion, reponse in valeurs.items():
            if reponse != dictValeursInitiales[IDquestion] or reponse == "##DOCUMENTS##":
                if IDquestion in dictReponses:
                    IDreponse = dictReponses[IDquestion]["IDreponse"]
                else:
                    IDreponse = None

                sauvegarder = True
                if reponse == "##DOCUMENTS##":
                    nbreDocuments = self.ctrl_questionnaire.GetNbreDocuments(IDquestion)
                    if nbreDocuments == 0:
                        sauvegarder = False

                if sauvegarder:
                    listeDonnees = [
                        ("IDquestion", IDquestion),
                        ("IDindividu", self.IDpersonne),
                        ("reponse", reponse),
                    ]
                    if IDreponse is None:
                        IDreponse = DB.ReqInsert("questionnaire_reponses", listeDonnees)
                    else:
                        DB.ReqMAJ("questionnaire_reponses", listeDonnees, "IDreponse", IDreponse)

                if reponse == "##DOCUMENTS##":
                    nbreDocuments = self.ctrl_questionnaire.SauvegardeDocuments(IDquestion, IDreponse)
                    if nbreDocuments == 0 and IDreponse is not None:
                        DB.ReqDEL("questionnaire_reponses", "IDreponse", IDreponse)
        DB.Close()
