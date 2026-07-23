# -*- coding: utf-8 -*-
"""
Compatibilité Python 2 pour UTIL_Html2text sous Python 3 / PyInstaller.
Expose l'ancien module htmlentitydefs à partir de la bibliothèque standard Python 3.
"""

from html.entities import name2codepoint, codepoint2name, entitydefs, html5
