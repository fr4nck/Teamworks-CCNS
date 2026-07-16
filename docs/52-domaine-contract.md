# Domaine `Contract`

`Contract` représente l'engagement d'un `Employee` envers l'association. Il
est immutable et indépendant de la persistance, de l'interface graphique et de
toute dépendance technique.

## Données portées

- identifiant UUID ;
- salarié concerné (`Employee`) ;
- type (`ContractType`) et statut (`ContractStatus`) ;
- date de début, date de fin facultative, date de signature facultative et fin
  de période d'essai facultative ;
- référence interne facultative.

Les contrats à durée déterminée (`CDD`, `CEE`, apprentissage, stage et service
civique) imposent une date de fin. `is_effective(on_date)` retourne `True`
uniquement pour un contrat au statut `ACTIVE` dont la date évaluée est comprise
dans la période contractuelle, bornes incluses.

## Limites explicites

Ce modèle ne porte aucune donnée de salaire, classification CCNS, temps de
travail, planning, activité, avenant, renouvellement, paie ou document.
