#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Branding Teamworks CCNS et personnalisation de l'organisation utilisatrice."""

from pathlib import Path
import shutil

import wx

from Utils import UTILS_Customize
from Utils import UTILS_Fichiers
from Utils import UTILS_Theme


APPLICATION_NAME = "Teamworks CCNS"
APPLICATION_CREDIT = "© Teamworks CCNS"
SUPPORTED_LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp"}
MANAGED_LOGO_PREFIX = "logo_association"


def GetBrandingDir():
    path = Path(UTILS_Fichiers.GetRepUtilisateur("Branding"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _is_supported_logo(path):
    path = Path(path)
    return path.is_file() and path.suffix.lower() in SUPPORTED_LOGO_EXTENSIONS


def GetAssociationLogoPath():
    value = UTILS_Customize.GetValeur(
        "branding", "logo_association", "", ajouter_si_manquant=False
    ) or ""
    if not value:
        return ""

    path = Path(value)
    if not path.is_absolute():
        path = GetBrandingDir() / path
    if not _is_supported_logo(path):
        return ""
    return str(path)


def SetAssociationLogo(source_path):
    source = Path(source_path).expanduser()
    if not _is_supported_logo(source):
        raise ValueError("Le logo doit être une image PNG, JPEG ou BMP valide.")

    # wx valide réellement le contenu de l'image au lieu de se fier à l'extension.
    image = wx.Image(str(source))
    if not image.IsOk():
        raise ValueError("Le fichier sélectionné n'est pas une image lisible.")

    branding_dir = GetBrandingDir()
    target = branding_dir / (MANAGED_LOGO_PREFIX + source.suffix.lower())

    for old_path in branding_dir.glob(MANAGED_LOGO_PREFIX + ".*"):
        if old_path != target:
            try:
                old_path.unlink()
            except OSError:
                pass

    try:
        same_file = source.resolve() == target.resolve()
    except OSError:
        same_file = False
    if not same_file:
        shutil.copy2(str(source), str(target))

    UTILS_Customize.SetValeur("branding", "logo_association", target.name)
    return str(target)


def ClearAssociationLogo():
    branding_dir = GetBrandingDir()
    for old_path in branding_dir.glob(MANAGED_LOGO_PREFIX + ".*"):
        try:
            old_path.unlink()
        except OSError:
            pass
    UTILS_Customize.SetValeur("branding", "logo_association", "")


def LoadScaledBitmap(path, max_width, max_height):
    if not path:
        return wx.NullBitmap
    image = wx.Image(str(path))
    if not image.IsOk() or image.GetWidth() <= 0 or image.GetHeight() <= 0:
        return wx.NullBitmap

    ratio = min(float(max_width) / image.GetWidth(), float(max_height) / image.GetHeight(), 1.0)
    width = max(1, int(round(image.GetWidth() * ratio)))
    height = max(1, int(round(image.GetHeight() * ratio)))
    if width != image.GetWidth() or height != image.GetHeight():
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
    return wx.Bitmap(image)


def GetHomeColours():
    """Palette sobre pour l'accueil, cohérente avec le thème actif."""
    if UTILS_Theme.is_dark_theme():
        return {
            "background": (32, 32, 32),
            "text": wx.Colour(240, 240, 240),
            "muted": wx.Colour(170, 176, 185),
            "accent": wx.Colour(24, 153, 166),
        }

    try:
        system_background = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        background = (system_background.Red(), system_background.Green(), system_background.Blue())
    except Exception:
        background = (248, 250, 252)
    return {
        "background": background,
        "text": wx.Colour(28, 42, 56),
        "muted": wx.Colour(100, 112, 124),
        "accent": wx.Colour(24, 153, 166),
    }


def BuildWordmark(parent):
    """Retourne un bloc Teamworks CCNS natif, sans dépendre d'un PNG historique."""
    palette = GetHomeColours()
    panel = wx.Panel(parent)
    panel.SetBackgroundColour(palette["background"])

    row = wx.BoxSizer(wx.HORIZONTAL)
    mark = wx.StaticText(panel, label="TW")
    mark_font = mark.GetFont()
    mark_font.SetPointSize(max(12, mark_font.GetPointSize() + 6))
    mark_font.SetWeight(wx.FONTWEIGHT_BOLD)
    mark.SetFont(mark_font)
    mark.SetForegroundColour(palette["accent"])

    name = wx.StaticText(panel, label=APPLICATION_NAME)
    name_font = name.GetFont()
    name_font.SetPointSize(max(11, name_font.GetPointSize() + 3))
    name_font.SetWeight(wx.FONTWEIGHT_BOLD)
    name.SetFont(name_font)
    name.SetForegroundColour(palette["text"])

    row.Add(mark, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
    row.Add(name, 0, wx.ALIGN_CENTER_VERTICAL)
    panel.SetSizer(row)
    return panel
