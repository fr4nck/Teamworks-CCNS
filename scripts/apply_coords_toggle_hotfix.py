#!/usr/bin/env python3
from pathlib import Path

PATH = Path("teamworks/Dlg/DLG_Saisie_coords.py")
text = PATH.read_text(encoding="utf-8")

old = '''        self.Bind(wx.EVT_BUTTON, self.OnBouton_Fixe, self.bouton_fixe)\n        self.Bind(wx.EVT_BUTTON, self.OnBouton_Mobile, self.bouton_mobile)\n        self.Bind(wx.EVT_BUTTON, self.OnBouton_Fax, self.bouton_fax)\n        self.Bind(wx.EVT_BUTTON, self.OnBouton_Email, self.bouton_email)\n'''
new = '''        # wx.ToggleButton émet EVT_TOGGLEBUTTON (et non EVT_BUTTON sous Phoenix).\n        # Avec EVT_BUTTON les boutons semblaient cliquables mais la catégorie\n        # n'était jamais sélectionnée : les champs restaient donc désactivés.\n        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnBouton_Fixe, self.bouton_fixe)\n        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnBouton_Mobile, self.bouton_mobile)\n        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnBouton_Fax, self.bouton_fax)\n        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnBouton_Email, self.bouton_email)\n'''
if text.count(old) != 1:
    raise SystemExit("Bloc de bindings des catégories introuvable ou ambigu")
text = text.replace(old, new, 1)

old = '''        else:\n            self.ActivationChamps(False)\n        self._update_category_buttons()\n'''
new = '''        else:\n            self.ActivationChamps(False)\n            # Premier contrôle logique pour une saisie clavier immédiate.\n            self.bouton_fixe.SetFocus()\n        self._update_category_buttons()\n'''
if text.count(old) != 1:
    raise SystemExit("Bloc d'initialisation de la saisie introuvable ou ambigu")
text = text.replace(old, new, 1)

PATH.write_text(text, encoding="utf-8", newline="\n")

for handler in ("Fixe", "Mobile", "Fax", "Email"):
    expected = f"self.Bind(wx.EVT_TOGGLEBUTTON, self.OnBouton_{handler}, self.bouton_{handler.lower()})"
    assert expected in text, expected
assert "self.bouton_fixe.SetFocus()" in text
assert "self.Bind(wx.EVT_BUTTON, self.OnBouton_Fixe, self.bouton_fixe)" not in text
print("Hotfix ToggleButton coordonnées appliqué.")
