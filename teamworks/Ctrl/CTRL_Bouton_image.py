#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-15 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

from Utils import UTILS_Customize
from Utils import UTILS_Interface
import wx

import PIL.Image as Image
import PIL.ImageOps as ImageOps


def PILtoWx(image):
    """Convertit une image PIL en wx.Image avec canal alpha."""
    largeur, hauteur = image.size
    imagewx = wx.Image(largeur, hauteur)
    imagewx.SetData(image.tobytes("raw", "RGB"))
    imagewx.SetAlpha(image.convert("RGBA").tobytes()[3::4])
    return imagewx


def _echelle_interface():
    try:
        return max(80, min(200, UTILS_Customize.GetValeur(
            "interface", "echelle_police", "100", type_valeur=int
        )))
    except Exception:
        return 100


def _echelle_valeur(valeur, minimum=0):
    return max(minimum, int(round(valeur * _echelle_interface() / 100.0)))


def _echelle_taille(taille):
    return (
        _echelle_valeur(taille[0], 1),
        _echelle_valeur(taille[1], 1),
    )


def _echelle_marges(marges):
    if isinstance(marges, tuple):
        return tuple(_echelle_valeur(valeur) for valeur in marges)
    return _echelle_valeur(marges)


class CTRL(wx.Button):
    """Bouton natif Teamworks avec icône et texte adaptés à l'échelle UI."""

    def __init__(
        self,
        parent,
        id=-1,
        texte="",
        cheminImage=None,
        tailleImage=(20, 20),
        margesImage=(4, 0, 0, 0),
        positionImage=wx.LEFT,
        margesTexte=(0, 1),
    ):
        wx.Button.__init__(self, parent, id=id, label=texte)
        self.parent = parent
        self.texte = texte
        self.cheminImage = cheminImage
        self.tailleImage = tailleImage
        self.margesImage = margesImage
        self.positionImage = positionImage
        self.margesTexte = margesTexte
        self.MAJ()

    def _bitmap(self):
        if self.cheminImage in ("", None):
            return wx.NullBitmap

        img = Image.open(self.cheminImage)
        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resample_filter = getattr(Image, "LANCZOS", Image.BICUBIC)

        img = img.resize(_echelle_taille(self.tailleImage), resample_filter)
        img = ImageOps.expand(img, border=_echelle_marges(self.margesImage))
        return PILtoWx(img).ConvertToBitmap()

    def MAJ(self):
        self.SetBitmap(self._bitmap(), self.positionImage)
        if self.cheminImage not in ("", None):
            self.SetBitmapMargins(_echelle_marges(self.margesTexte))

        self.AppliquerTheme()
        self.SetInitialSize()

        # Une augmentation de police doit aussi agrandir la cible d'action.
        best = self.GetBestSize()
        hauteur_min = _echelle_valeur(32, 32)
        self.SetMinSize((best.GetWidth(), max(best.GetHeight(), hauteur_min)))

    def AppliquerTheme(self):
        """Conserve le rendu natif et utilise la typographie de la plateforme."""
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.SetFont(font)
        self.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))

    def SetImage(self, cheminImage=""):
        self.SetBitmap(wx.NullBitmap)
        self.cheminImage = cheminImage
        self.MAJ()

    def SetTexte(self, texte=""):
        self.texte = texte
        self.SetLabel(texte)
        self.MAJ()
