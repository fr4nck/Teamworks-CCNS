# Persistance minimale

Cette étape ajoute une persistance minimale en mémoire.

## Ce qui est ajouté

- repositories en mémoire pour :
  - personnes
  - contrats
  - convention
  - activité
  - moteur
- un conteneur d'exécution simple ;
- un bootstrap de chargement des données de référence et des règles par défaut.

## Pourquoi c'est utile

Ça permet enfin :
- de stocker des objets sans brancher encore une vraie base ;
- de relier les blocs du cœur entre eux ;
- de préparer les futurs services et écrans sur quelque chose d'exécutable.

## Ce que ça ne fait pas encore

- pas de SQL branché ;
- pas d'ORM ;
- pas d'API ;
- pas d'interface graphique.
