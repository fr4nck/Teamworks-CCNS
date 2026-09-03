# POC isolé — moteur de thème Qt

Objectif : tester une nouvelle couche UI sans toucher au code wxPython de Teamworks.

Ce POC reproduit volontairement un écran métier dense de type **Individus / fiche salarié** :

- navigation principale Accueil / Individus / Présences / Recrutement ;
- liste filtrable de salariés ;
- résumé du salarié sélectionné ;
- onglets Généralités / Qualifications / Contrats / Présences / Frais ;
- tableau de contrats ;
- alertes métier ;
- changement de thème clair/sombre à chaud.

Le prototype n'importe **aucun module de production** et n'accède à **aucune base Teamworks**. Il peut donc être supprimé intégralement sans impact sur l'application.

## Stack testée

- PySide6 : couche Qt officielle pour Python ;
- qt-material : moteur de thèmes QSS open source (BSD-2-Clause), utilisé ici comme moteur interchangeable.

L'objectif n'est pas de figer Material comme direction graphique. Le moteur sert seulement à vérifier qu'une application Teamworks peut être construite sur des composants Qt thémables globalement. La direction UI reste celle du design system du projet : Fluent 2 pour la structure desktop, tokens sémantiques, densité métier et thèmes clair/sombre.

## Lancer le POC

Sous Windows :

```powershell
cd poc\qt-theme
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Critères de décision

Le POC doit permettre de juger rapidement :

1. la qualité des tableaux, formulaires, onglets et boutons ;
2. la densité d'information disponible ;
3. le thème sombre sans zones blanches résiduelles ;
4. le changement global de thème sans retouche écran par écran ;
5. le comportement HiDPI et redimensionnement ;
6. la facilité de migration progressive depuis wxPython.

Si le résultat est convaincant, l'étape suivante sera de remplacer les données factices par un **adaptateur de lecture** vers les services métier existants, sans déplacer la logique métier dans Qt.
