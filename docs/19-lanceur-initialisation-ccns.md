# Lanceur d'initialisation CCNS

Cette étape ajoute un point d'entrée simple pour lancer le seed CCNS sans passer uniquement par un script.

## Fichiers ajoutés

- `teamworks/Dlg/DLG_CCNS_seed.py`
- `teamworks/CcnsCore/menu_seed_integration.txt`

## But

Permettre, dans Teamworks, de :
- lancer l'initialisation des données de référence CCNS ;
- choisir si l'on synchronise aussi les tables historiques ;
- voir un premier retour lisible.

## Pourquoi c'est rentable

Après les tables, le seed et le raccord au dépôt réel, c'est le moyen le plus court pour rendre le tout utilisable sans rester dans une logique purement script.

## Limites

- l'intégration au menu principal reste volontairement légère ;
- le dialogue ne gère pas encore les logs avancés ;
- il n'y a pas encore de rollback.
