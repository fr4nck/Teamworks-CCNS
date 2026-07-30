# Règle de gestion des dates

## Principe obligatoire

Toute date entrante doit être normalisée par `Utils.UTILS_Dates.DateEnDateDD`.
Aucun code métier ou d’interface ne doit découper une date avec des indices (`[:4]`, `[5:7]`, `[8:10]`) ni construire directement un `datetime.date` depuis une chaîne.

## Formats historiques tolérés

- objets `datetime.date` et `datetime.datetime` ;
- `AAAA-MM-JJ`, y compris mois ou jour sur un chiffre ;
- `JJ/MM/AAAA` ;
- `JJ-MM-AAAA` ;
- valeurs ISO comportant une heure.

Une valeur absente ou invalide ne doit jamais faire planter une page. Elle retourne `None` au niveau métier et une chaîne vide à l’affichage.

## Fonctions de référence

- parsing : `DateEnDateDD` / `DateEngEnDateDD` ;
- affichage français : `DateEngFr` ;
- stockage ISO : `DateFrEng` ;
- âge : `CalculeAge` après normalisation.

## Interdictions

- parsing par tranches de chaîne ;
- duplication locale de `DateEngFr`, `FormateDate` ou `RetourneAge` ;
- exception non interceptée provoquée par une date importée ou historique.
