#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-14 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import datetime

import wx
from wx import Control
from Utils import UTILS_Customize
from Utils import UTILS_Interface


def _echelle_interface():
    try:
        valeur = UTILS_Customize.GetValeur(
            "interface", "echelle_interface", "", ajouter_si_manquant=False
        )
        if valeur in (None, ""):
            valeur = UTILS_Customize.GetValeur(
                "interface", "echelle_police", "100", type_valeur=int
            )
        return max(80, min(200, int(valeur)))
    except Exception:
        return 100


class Footer(Control):
    def __init__(
        self,
        parent,
        id=-1,
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=wx.NO_BORDER,
        name="footer",
    ):
        self.afficherColonneDroite = True
        self.listview = None
        self.dictColonnes = {}
        self.dictTotaux = {}
        self.listeImpression = []

        Control.__init__(self, parent, id=id, pos=pos, size=size, style=style, name=name)

        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.SetFont(font)
        hauteur_texte = self.GetTextExtent("Ag")[1]
        self.hauteur = max(24, int(round((hauteur_texte + 10) * _echelle_interface() / 100.0)))
        self.SetMinSize((-1, self.hauteur))
        self.SetInitialSize(size)
        self.AppliquerTheme()

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnErase)
        self.Bind(wx.EVT_SIZE, self.MAJ_affichage)

    def AppliquerTheme(self):
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_high"))
        self.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))

    def MAJ_affichage(self, event=None):
        self.Refresh()

    def MAJ_totaux(self):
        self.dictTotaux = {}
        for track in self.listview.innerList:
            for nomColonne, dictColonne in list(self.dictColonnes.items()):
                if dictColonne["mode"] == "total" and hasattr(track, nomColonne):
                    total = getattr(track, nomColonne)
                    if nomColonne not in self.dictTotaux:
                        self.dictTotaux[nomColonne] = 0
                        if dictColonne.get("format") in ("temps", "duree"):
                            self.dictTotaux[nomColonne] = datetime.timedelta(0)
                    if total is not None:
                        self.dictTotaux[nomColonne] += total

    def MAJ(self):
        self.MAJ_totaux()
        self.MAJ_affichage()

    def DrawColonne(self, dc, x, largeur, label="", alignement=None, couleur=None, font=None):
        render = wx.RendererNative.Get()
        options = wx.HeaderButtonParams()
        options.m_labelText = label
        if alignement:
            options.m_labelAlignment = alignement
        if couleur:
            options.m_labelColour = couleur
        if font:
            options.m_labelFont = font
        render.DrawHeaderButton(self, dc, (x, 1, max(0, largeur), self.hauteur - 1), params=options)

    def _largeur_colonne(self, index, colonne):
        """Suit la largeur réellement visible, pas la largeur historique OLV."""
        try:
            largeur = self.listview.GetColumnWidth(index)
            if largeur >= 0:
                return largeur
        except Exception:
            pass
        return colonne.width

    def Paint(self, dc):
        dc.SetFont(self.GetFont())
        x = 0 - self.listview.GetScrollPos(wx.HORIZONTAL)
        self.listeImpression = []
        dernierTexte = ""

        for indexColonne, col in enumerate(self.listview.columns):
            texte = ""
            font = self.GetFont()
            couleur = UTILS_Interface.GetToken("on_surface_variant", wx.Colour(140, 140, 140))
            largeur = self._largeur_colonne(indexColonne, col)
            converter = col.stringConverter
            nom = col.valueGetter

            if col.align == "left":
                alignement = wx.ALIGN_LEFT
            elif col.align == "centre":
                alignement = wx.ALIGN_CENTER
            elif col.align == "right":
                alignement = wx.ALIGN_RIGHT
            else:
                alignement = wx.ALIGN_LEFT

            mode = None
            if nom in self.dictColonnes:
                infoColonne = self.dictColonnes[nom]
                mode = infoColonne["mode"]

                if mode == "total":
                    if nom in self.dictTotaux:
                        texte = self.dictTotaux[nom]
                    else:
                        texte = datetime.timedelta(0) if infoColonne.get("format") in ("temps", "duree") else 0
                    if converter is not None:
                        texte = converter(texte)
                    if isinstance(texte, (int, float)):
                        texte = str(texte)

                elif mode == "nombre":
                    nombre = len(self.listview.innerList)
                    libelle = infoColonne["pluriel"] if nombre > 1 else infoColonne["singulier"]
                    texte = u"%d %s" % (nombre, libelle)

                elif mode == "texte":
                    texte = infoColonne["texte"]

                if "alignement" in infoColonne:
                    alignement = infoColonne["alignement"]
                if "font" in infoColonne:
                    font = infoColonne["font"]
                if "couleur" in infoColonne:
                    couleur = infoColonne["couleur"]

            ajustement = 5 if mode != "total" and dernierTexte == "" else 0
            self.DrawColonne(dc, x - ajustement, largeur + ajustement, texte, alignement, couleur, font)
            x += largeur

            self.listeImpression.append({"texte": texte, "alignement": alignement})
            dernierTexte = texte if mode == "total" else ""

        if self.afficherColonneDroite:
            self.DrawColonne(dc, x, max(0, self.GetClientSize().GetWidth() - x))

    def GetDonneesImpression(self, typeInfo="texte"):
        return [info[typeInfo] for info in self.listeImpression][1:]

    def OnPaint(self, evt):
        dc = wx.BufferedPaintDC(self)
        dc.SetBackground(wx.Brush(UTILS_Interface.GetToken("surface_container_high")))
        dc.Clear()
        if self.listview is not None:
            self.Paint(dc)

    def OnErase(self, evt):
        pass

    def AcceptsFocus(self):
        return False

    def DoGetBestSize(self):
        return (100, self.hauteur)

    def ShouldInheritColours(self):
        return False
