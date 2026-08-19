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
ACCENT = wx.Colour(24, 153, 166)
_TITLE_PATCHED = False


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


def LoadScaledBitmap(path, max_width, max_height, allow_upscale=False):
    if not path:
        return wx.NullBitmap
    image = wx.Image(str(path))
    if not image.IsOk() or image.GetWidth() <= 0 or image.GetHeight() <= 0:
        return wx.NullBitmap

    ratio = min(float(max_width) / image.GetWidth(), float(max_height) / image.GetHeight())
    if not allow_upscale:
        ratio = min(ratio, 1.0)
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
            "accent": ACCENT,
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
        "accent": ACCENT,
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


def _draw_centered_text(dc, text, y, font, colour, width):
    dc.SetFont(font)
    dc.SetTextForeground(colour)
    text_width, text_height = dc.GetTextExtent(text)
    dc.DrawText(text, max(0, (width - text_width) // 2), y)
    return text_height


def EnsureSplashImage():
    """Construit le splash au démarrage selon le thème et le logo utilisateur."""
    output = GetBrandingDir() / "splash_runtime.png"
    width, height = 720, 420
    dark = UTILS_Theme.is_dark_theme()

    background = wx.Colour(17, 24, 39) if dark else wx.Colour(248, 250, 252)
    foreground = wx.Colour(245, 247, 250) if dark else wx.Colour(28, 42, 56)
    muted = wx.Colour(166, 176, 190) if dark else wx.Colour(104, 116, 128)
    track = wx.Colour(62, 72, 87) if dark else wx.Colour(214, 221, 228)

    bitmap = wx.Bitmap(width, height)
    dc = wx.MemoryDC(bitmap)
    dc.SetBackground(wx.Brush(background))
    dc.Clear()

    mark_size = 64
    mark_x, mark_y = 78, 54
    dc.SetPen(wx.Pen(ACCENT))
    dc.SetBrush(wx.Brush(ACCENT))
    dc.DrawRoundedRectangle(mark_x, mark_y, mark_size, mark_size, 14)
    mark_font = wx.Font(22, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    dc.SetFont(mark_font)
    dc.SetTextForeground(wx.WHITE)
    tw_width, tw_height = dc.GetTextExtent("TW")
    dc.DrawText("TW", mark_x + (mark_size - tw_width) // 2, mark_y + (mark_size - tw_height) // 2)

    title_font = wx.Font(30, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    dc.SetFont(title_font)
    dc.SetTextForeground(foreground)
    dc.DrawText("Teamworks", 164, 57)
    team_width, _ = dc.GetTextExtent("Teamworks")
    dc.SetTextForeground(ACCENT)
    dc.DrawText("CCNS", 178 + team_width, 57)

    subtitle_font = wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
    dc.SetFont(subtitle_font)
    dc.SetTextForeground(muted)
    dc.DrawText("Gestion du personnel & planning", 166, 101)

    dc.SetPen(wx.Pen(track, 1))
    dc.DrawLine(78, 150, width - 78, 150)

    loading_font = wx.Font(13, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
    _draw_centered_text(dc, "Chargement en cours…", 210, loading_font, foreground, width)

    bar_x, bar_y, bar_width = 180, 252, 360
    dc.SetPen(wx.Pen(track, 4))
    dc.DrawLine(bar_x, bar_y, bar_x + bar_width, bar_y)
    dc.SetPen(wx.Pen(ACCENT, 4))
    dc.DrawLine(bar_x + 115, bar_y, bar_x + 245, bar_y)

    logo_bitmap = LoadScaledBitmap(GetAssociationLogoPath(), 190, 70)
    if logo_bitmap.IsOk():
        logo_x = (width - logo_bitmap.GetWidth()) // 2
        logo_y = 282
        dc.DrawBitmap(logo_bitmap, logo_x, logo_y, True)

    credit_font = wx.Font(9, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
    _draw_centered_text(dc, APPLICATION_CREDIT, 390, credit_font, muted, width)

    dc.SelectObject(wx.NullBitmap)
    bitmap.SaveFile(str(output), wx.BITMAP_TYPE_PNG)
    return str(output)


def EnsureAppIconImage():
    """Produit une petite icône TW cohérente avec la nouvelle identité."""
    output = GetBrandingDir() / "app_icon_runtime.png"
    size = 32
    bitmap = wx.Bitmap(size, size)
    dc = wx.MemoryDC(bitmap)
    dc.SetBackground(wx.Brush(wx.Colour(20, 42, 62)))
    dc.Clear()
    dc.SetPen(wx.Pen(ACCENT))
    dc.SetBrush(wx.Brush(ACCENT))
    dc.DrawRoundedRectangle(2, 2, size - 4, size - 4, 7)
    font = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    dc.SetFont(font)
    dc.SetTextForeground(wx.WHITE)
    text_width, text_height = dc.GetTextExtent("TW")
    dc.DrawText("TW", (size - text_width) // 2, (size - text_height) // 2)
    dc.SelectObject(wx.NullBitmap)
    bitmap.SaveFile(str(output), wx.BITMAP_TYPE_PNG)
    return str(output)


def GetRuntimeAssetOverride(relative_path):
    """Remplace uniquement les anciens assets de marque appelés par le runtime historique."""
    normalized = str(relative_path).replace("\\", "/")
    try:
        if normalized == "Images/Special/Logo_splash.png":
            return EnsureSplashImage()
        if normalized == "Images/16x16/Logo.png":
            return EnsureAppIconImage()
    except Exception:
        return ""
    return ""


def InstallLegacyTitleBranding():
    """Normalise les anciens titres `Teamworks v…` sans réécrire la frame historique."""
    global _TITLE_PATCHED
    if _TITLE_PATCHED:
        return
    _TITLE_PATCHED = True

    original_set_title = wx.Frame.SetTitle

    def branded_set_title(frame, title):
        if isinstance(title, str) and title.startswith("Teamworks v"):
            title = APPLICATION_NAME + title[len("Teamworks"):]
        return original_set_title(frame, title)

    wx.Frame.SetTitle = branded_set_title


# CTRL_Accueil importe ce module avant l'instanciation de la frame principale.
InstallLegacyTitleBranding()
