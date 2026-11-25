"""Couleurs et contrastes des controles dessines."""

import wx


def couleur(value):
    if isinstance(value, (tuple, list)):
        return wx.Colour(*value)
    return wx.Colour(value)


def rgb(value):
    c = couleur(value)
    return c.Red(), c.Green(), c.Blue()


def luminance(value):
    vals = [v / 255 for v in rgb(value)]
    vals = [
        v / 12.92 if v <= 0.04045
        else ((v + 0.055) / 1.055) ** 2.4
        for v in vals
    ]
    return sum(a*b for a,b in zip(vals, (0.2126, 0.7152, 0.0722)))


def contraste(a, b):
    x, y = sorted((luminance(a), luminance(b)))
    return (y + 0.05) / (x + 0.05)


def texte_lisible(fond, prefere):
    if contraste(fond, prefere) >= 4.5:
        return couleur(prefere)
    return max(
        (wx.Colour(0, 0, 0), wx.Colour(255, 255, 255)),
        key=lambda c: contraste(fond, c),
    )


def melanger(fond, accent, proportion=0.20):
    return wx.Colour(*(
        round(a*(1-proportion) + b*proportion)
        for a,b in zip(rgb(fond), rgb(accent))
    ))
