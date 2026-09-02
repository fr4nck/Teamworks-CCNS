#!/usr/bin/env python3
from pathlib import Path

PATH = Path("teamworks/Ctrl/CTRL_Page_generalites.py")
ENCODING = "iso-8859-15"

text = PATH.read_text(encoding=ENCODING)

old = '''        self.text_numsecu.SetMinSize((170, -1))\n        self.text_adresse.SetToolTip(wx.ToolTip("Saisissez l'adresse"))\n'''
new = '''        self.text_numsecu.SetMinSize((170, -1))\n        # wxPython/Phoenix peut calculer une hauteur quasi nulle pour un TextCtrl\n        # multiligne dans un FlexGridSizer. Une hauteur minimale garantit que le\n        # champ d'adresse reste réellement saisissable, y compris avec le zoom\n        # d'interface Windows.\n        self.text_adresse.SetMinSize((-1, 60))\n        self.text_adresse.SetToolTip(wx.ToolTip("Saisissez l'adresse"))\n        self.text_memo.SetMinSize((-1, 45))\n'''
if text.count(old) != 1:
    raise SystemExit("Bloc propriétés adresse introuvable ou ambigu")
text = text.replace(old, new, 1)

old = '''        grid_sizer_adresse.AddGrowableCol(1)\n        sizer_adresse.Add(grid_sizer_adresse, 1, wx.ALL|wx.EXPAND, 5)\n'''
new = '''        grid_sizer_adresse.AddGrowableCol(1)\n        grid_sizer_adresse.AddGrowableRow(0)\n        sizer_adresse.Add(grid_sizer_adresse, 1, wx.ALL|wx.EXPAND, 5)\n'''
if text.count(old) != 1:
    raise SystemExit("Bloc layout adresse introuvable ou ambigu")
text = text.replace(old, new, 1)

PATH.write_text(text, encoding=ENCODING, newline="\n")

# Garde-fous minimaux du hotfix.
assert text.count("self.text_adresse.SetMinSize((-1, 60))") == 1
assert text.count("self.text_memo.SetMinSize((-1, 45))") == 1
assert text.count("grid_sizer_adresse.AddGrowableRow(0)") == 1
print("Hotfix adresse/mémo appliqué.")
