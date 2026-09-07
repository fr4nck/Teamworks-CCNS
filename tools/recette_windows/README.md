# Pilote de recette Windows wx

Ce pilote complete les tests existants par de vraies interactions bureau Windows. Il ne charge ni n'appelle directement les handlers Python de Teamworks.

## Prerequis

- Windows avec une session bureau **interactive et non verrouillee** ;
- l'environnement Python fonctionnel de la Vanilla wx ;
- `pip install -r requirements/recette-windows.txt`.

Le backend par defaut est Microsoft UI Automation (`uia`). `win32` est disponible en diagnostic si Inspect.exe montre mieux les controles natifs wx sur un poste donne.

Le seul delta apporte a l'interface est un `SetLabel(label)` natif sur le bouton de navigation custom-peint : il ne change pas son rendu, mais expose son nom a MSAA/UI Automation pour permettre un ciblage stable.

## Lancer le pilote

Depuis la racine du depot :

```powershell
py -3.11 -m pip install -r requirements\recette-windows.txt
py -3.11 -m tools.recette_windows --scenario individus-smoke
```

Le scenario lance `run_teamworks.py`, attend `Teamworks - ...`, clique le controle de navigation `Individus`, puis cherche la liste wx nommee `OL_personnes` (avec repli sur la plus grande List/ListView native visible si le nom wx n'est pas expose par UIA).

- Si UI Automation expose au moins une ligne, il selectionne puis double-clique la premiere ligne, attend la fiche modale, verifie sa reactivite, la ferme par `Echap` et verifie le retour a la fenetre principale.
- Si aucune ligne exploitable n'est exposee, il utilise un vrai clic droit puis l'entree `Options`, action non destructive, et effectue les memes controles de dialogue/retour.

Les artefacts vont dans `artifacts/recette-windows/<horodatage>-individus-smoke/` : stdout, stderr, resultat, code retour, dump des fenetres, logs applicatifs recents et screenshot en cas d'echec.

## Garde destructive

Avant `Entree`, avant un clic generique nomme et a l'ouverture d'un nouveau dialogue, le texte accessible est analyse. Un dialogue de confirmation comportant un marqueur de suppression/effacement/destruction interrompt le scenario avec le code 3 sans envoyer de validation.

## Extension

Ajouter un module dans `scenarios/` puis l'enregistrer dans `SCENARIOS`. Les primitives du driver couvrent clic, selection, double-clic, Tab, Shift+Tab, Entree, Echap, attente de dialogue, reactivite, fermeture et diagnostic. Cela permet d'ajouter ensuite Individus, fiche individuelle, Presences, Recrutement et menus principaux sans modifier les ecrans wx.
