#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-15 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

from pathlib import Path

from Utils import UTILS_Interface, UTILS_Styles
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


def _echelle_taille(taille):
    return tuple(UTILS_Styles.Scale(valeur) for valeur in taille)


def _echelle_marges(marges):
    if isinstance(marges, tuple):
        return tuple(UTILS_Styles.Scale(valeur, minimum=0) for valeur in marges)
    return UTILS_Styles.Scale(marges, minimum=0)


def _chemin_image_existant(chemin):
    """Renvoie une ressource existante, avec repli 32x32 -> 16x16."""
    if chemin in ("", None):
        return None

    path = Path(chemin)
    if path.is_file():
        return path

    # Quelques écrans historiques demandaient une version 32x32 alors que
    # seule l'icône 16x16 a toujours été livrée. Le bouton reste fonctionnel
    # et laisse ensuite Pillow/Teamworks la mettre à l'échelle normalement.
    parts = list(path.parts)
    if "32x32" in parts:
        parts[parts.index("32x32")] = "16x16"
        fallback = Path(*parts)
        if fallback.is_file():
            return fallback

    return None


class CTRL(wx.Button):
    """Bouton natif Teamworks consommant la charte graphique centrale."""

    def __init__(
        self,
        parent,
        id=-1,
        texte="",
        cheminImage=None,
        tailleImage=None,
        margesImage=None,
        positionImage=wx.LEFT,
        margesTexte=None,
    ):
        wx.Button.__init__(self, parent, id=id, label=texte)
        self.parent = parent
        self.texte = texte
        self.cheminImage = cheminImage
        taille_defaut = UTILS_Styles.ICON_SIZES["medium"]
        self.tailleImage = tailleImage or (taille_defaut, taille_defaut)
        if isinstance(self.tailleImage, tuple) is False:
            self.tailleImage = (self.tailleImage, self.tailleImage)
        marge_icone = UTILS_Styles.CONTROL_METRICS["button_icon_margin"]
        self.margesImage = margesImage if margesImage is not None else (marge_icone, 0, 0, 0)
        self.positionImage = positionImage
        self.margesTexte = margesTexte if margesTexte is not None else (0, 1)
        self.MAJ()

    def _bitmap(self):
        chemin = _chemin_image_existant(self.cheminImage)
        if chemin is None:
            return wx.NullBitmap

        try:
            img = Image.open(chemin)
        except (OSError, ValueError):
            # Une ressource décorative ne doit jamais rendre une action métier
            # inutilisable. Le libellé du bouton reste affiché.
            return wx.NullBitmap

        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resample_filter = getattr(Image, "LANCZOS", Image.BICUBIC)

        img = img.resize(_echelle_taille(self.tailleImage), resample_filter)
        img = ImageOps.expand(img, border=_echelle_marges(self.margesImage))
        return PILtoWx(img).ConvertToBitmap()

    def MAJ(self):
        bitmap = self._bitmap()
        self.SetBitmap(bitmap, self.positionImage)
        if bitmap.IsOk():
            self.SetBitmapMargins(_echelle_marges(self.margesTexte))

        self.AppliquerTheme()
        self.SetInitialSize()

        best = self.GetBestSize()
        hauteur_min = UTILS_Styles.GetControlMetric("button_min_height")
        largeur_min = best.GetWidth()
        if bitmap.IsOk() and not self.texte:
            largeur_min = max(largeur_min, hauteur_min)
        self.SetMinSize((largeur_min, max(best.GetHeight(), hauteur_min)))

    def AppliquerTheme(self):
        """Conserve le rendu natif et applique la typographie de la charte."""
        self.SetFont(UTILS_Styles.GetFont("label"))
        self.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))

    def SetImage(self, cheminImage=""):
        self.SetBitmap(wx.NullBitmap)
        self.cheminImage = cheminImage
        self.MAJ()

    def SetTexte(self, texte=""):
        self.texte = texte
        self.SetLabel(texte)
        self.MAJ()
