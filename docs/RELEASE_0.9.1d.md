# Teamworks-CCNS 0.9.1d

## Nature de la version

`0.9.1d` est une révision corrective immédiate de `0.9.1c`, destinée à fournir un paquet Windows exploitable avant la refonte plus large du parcours recrutement / contrat.

Elle n'embarque pas la refonte UI en cours des PR #359 et #360.

## Correctif inclus

- correction du dialogue `Coordonnées` sous wxPython Phoenix : les boutons `Fixe`, `Mobile`, `Fax` et `Email` utilisent désormais l'événement `EVT_TOGGLEBUTTON` attendu ;
- les champs de saisie correspondants sont de nouveau activés lorsqu'un type de coordonnée est sélectionné ;
- aucun changement de schéma de données ;
- aucun changement volontaire de logique métier ou CCNS.

## Stratégie de stabilisation

Cette version sert de point de travail propre avant d'engager davantage la refonte de Teamworks-CCNS :

- le hotfix fonctionnel est isolé et validé par la CI de la PR #358 ;
- la normalisation visuelle du dialogue `Coordonnées` reste dans la PR #359 ;
- la refonte du parcours recrutement / création de contrat reste dans la PR #360 ;
- ces évolutions ne sont pas mélangées au paquet correctif `0.9.1d`.

## Validation

Le build Windows doit être produit uniquement si les tests du socle et les parcours critiques Windows restent verts sur `master`.
