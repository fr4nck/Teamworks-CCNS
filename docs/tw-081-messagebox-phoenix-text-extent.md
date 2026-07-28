# TW-081 — MessageBox wxPython Phoenix

`DLG_Messagebox.py` utilise désormais directement l’API Phoenix `GetFullMultiLineTextExtent()`.

La branche historique vers `GetMultiLineTextExtent()` a été supprimée, sans modification du calcul de largeur ou de hauteur de la boîte de dialogue.

Le fichier est également déclaré et enregistré en UTF-8.
