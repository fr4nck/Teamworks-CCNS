# Raccord au dépôt Teamworks réel

Ce paquet commence le raccord direct au dépôt Teamworks existant.

## Ce qui est ajouté

- un sous-package `teamworks/CcnsCore/`
- un bridge simple pour charger le cœur Teamworks-CCNS déjà présent à la racine du dépôt
- des tables CCNS ajoutées à `teamworks/Data/DATA_Tables.py`
- une montée de version dans `teamworks/UpgradeDB.py` pour créer ces tables si elles n'existent pas

## But

Faire le premier vrai pas entre :
- le cœur Teamworks-CCNS déjà construit ;
- et la structure historique de Teamworks.

## Ce que ça ne fait pas encore

- pas de branchement UI dans les dialogues existants ;
- pas de synchronisation entre les contrats historiques et les contrats `tw_`;
- pas d'écran CCNS réel dans l'interface wx.

## Utilisation rapide

Après intégration :
- lancer l'application Teamworks ;
- ouvrir ou créer une base ;
- laisser l'upgrade créer les tables `tw_*` ;
- exécuter `python demo_teamworks_bridge.py` depuis `teamworks/CcnsCore/` pour vérifier le bridge.

## Remarque

Le bridge ajoute le dépôt parent au `sys.path` pour rendre importables les dossiers déjà créés à la racine :
- `domain/`
- `application/`
- `infrastructure/`
