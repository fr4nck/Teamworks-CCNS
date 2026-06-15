# Seed des données de référence dans Teamworks

Cette étape ajoute un script de seed directement exploitable dans le dépôt Teamworks.

## But

Peupler rapidement :
- les tables historiques utiles (`contrats_class`, `contrats_types`) ;
- les nouvelles tables `tw_*` du cœur CCNS ;
- une première grille salariale 2026 ;
- quelques règles métier de base.

## Intérêt

C'est l'étape la plus rentable juste après le raccord au dépôt réel :
- on ne reste plus avec des tables vides ;
- on peut commencer à voir apparaître des classifications et références utiles ;
- on prépare les vrais tests dans Teamworks sans tout saisir à la main.

## Portée

Le script :
- évite les doublons par recherche préalable ;
- peut synchroniser les tables historiques ;
- charge une grille `CCNS-2026-01` datée du 1er janvier 2026.

## Limites

- ce n'est pas encore un assistant graphique ;
- ce n'est pas encore un menu intégré à Teamworks ;
- certaines valeurs de bootstrap restent des données de travail et doivent être consolidées avant usage large.
