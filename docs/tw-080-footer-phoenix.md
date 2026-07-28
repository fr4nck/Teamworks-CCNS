# TW-080 — Footer wxPython Phoenix

`CTRL_Footer.py` utilise désormais directement `wx.Control`.

La compatibilité avec `wx.PyControl` et la branche conditionnelle basée sur `wx.PlatformInfo` ont été supprimées. Le fichier est encodé en UTF-8 et un test ciblé empêche le retour de cette bifurcation historique.
