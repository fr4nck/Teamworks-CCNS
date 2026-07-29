# TW-121 — Validation des préférences d’affichage sous Windows

## Objectif

Valider sur l’exécutable Windows que les préférences introduites par TW-119 restent accessibles, persistantes et lisibles sur les parcours prioritaires, sans imposer le thème sombre.

## Contrat fonctionnel

- valeur par défaut : thème **Système**, échelle **100 %** ;
- thèmes disponibles : **Système**, **Clair**, **Sombre** ;
- échelle de police : **80 à 200 %** ;
- réglages enregistrés dans la configuration utilisateur ;
- application après redémarrage ;
- aucune base métier ne doit être modifiée par un changement d’affichage.

## Matrice manuelle Windows

| Parcours | Système | Clair | Sombre | 80 % | 125 % | 150 % | 200 % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Démarrage sans base | À valider | À valider | À valider | À valider | À valider | À valider | À valider |
| Fenêtre principale et menus | À valider | À valider | À valider | À valider | À valider | À valider | À valider |
| Préférences d’affichage | À valider | À valider | À valider | À valider | À valider | À valider | À valider |
| Ouverture d’une base | À valider | À valider | À valider | À valider | À valider | À valider | À valider |
| Accueil | À valider | À valider | À valider | À valider | À valider | À valider | À valider |
| Fiche salarié | À valider | À valider | À valider | À valider | À valider | À valider | À valider |
| Contrôles CCNS | À valider | À valider | À valider | À valider | À valider | À valider | À valider |
| Export essentiel | À valider | À valider | À valider | À valider | À valider | À valider | À valider |

## Critères de validation

1. aucun texte essentiel tronqué à 125 % et 150 % ;
2. à 200 %, les écrans restent utilisables avec défilement lorsque nécessaire ;
3. contraste suffisant pour les libellés, champs, listes, tableaux et sélections ;
4. changement conservé après fermeture et relance ;
5. retour à **Système / 100 %** fonctionnel ;
6. absence de gel ou d’erreur lors de l’ouverture des fenêtres prioritaires ;
7. captures ou anomalies associées à chaque échec de la matrice.

## Automatisation conservée

`tests/test_tw121_display_preferences_contract.py` verrouille sans importer wxPython :

- la présence des trois fichiers de raccord ;
- les valeurs par défaut ;
- les trois thèmes ;
- les bornes 80–200 % ;
- l’entrée de menu Préférences ;
- l’installation des hooks globaux de thème et d’échelle.

La validation visuelle réelle reste nécessaire sur l’artefact Windows.
