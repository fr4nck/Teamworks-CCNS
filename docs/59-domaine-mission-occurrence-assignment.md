# Domaine `MissionOccurrenceAssignment`

`MissionOccurrenceAssignment` représente l'affectation déclarée d'un `Employee`
à une `MissionOccurrence` précise. Elle formalise uniquement le lien concret
entre un salarié et un créneau daté et horaire déjà porté par l'occurrence.

L'objet est immutable et appartient au domaine pur : il ne dépend ni de
wxPython, ni de SQLite, ni de SQLAlchemy, ni d'une API, ni du Web, ni de
l'interface graphique, ni d'un module de persistance.

## Données portées

- identifiant `UUID` ;
- salarié obligatoire de type `Employee` ;
- occurrence obligatoire de type `MissionOccurrence` ;
- statut obligatoire `MissionOccurrenceAssignmentStatus` ;
- observations facultatives, normalisées par suppression des espaces
  périphériques ;
- indicateur `active` strictement booléen.

Les observations sont optionnelles. Lorsqu'une valeur est fournie, elle est
nettoyée par suppression des espaces en début et fin ; une chaîne vide après
normalisation est refusée.

## Statuts déclarés

`MissionOccurrenceAssignmentStatus` porte les valeurs suivantes :

- `PLANNED` ;
- `CONFIRMED` ;
- `CANCELLED` ;
- `COMPLETED` ;
- `ABSENT`.

Ces statuts sont déclaratifs. Ils ne sont jamais calculés automatiquement à
partir des dates de l'occurrence.

## Méthodes métier

- `is_planned()` indique si le statut déclaré est `PLANNED` ;
- `is_confirmed()` indique si le statut déclaré est `CONFIRMED` ;
- `is_cancelled()` indique si le statut déclaré est `CANCELLED` ;
- `is_completed()` indique si le statut déclaré est `COMPLETED` ;
- `is_absent()` indique si le statut déclaré est `ABSENT` ;
- `is_active()` retourne uniquement la valeur déclarée de `active`.

Chaque prédicat de statut lit exclusivement le champ `status`. `is_active()` lit
exclusivement le champ `active`.

## Limites explicites

`MissionOccurrenceAssignment` ne recopie ni la `Mission`, ni les dates et
horaires, ni le lieu, ni les exigences de qualification, ni les données
contractuelles, ni les qualifications détenues. Ces informations restent
accessibles via `MissionOccurrence` et `Mission` lorsque le domaine appelant en a
besoin.

L'objet ne vérifie pas qu'une affectation générale `MissionAssignment` existe. Il
ne contrôle pas la disponibilité, les conflits de planning, le contrat, le temps
de travail, les qualifications, l'éligibilité, la rémunération, les heures
supplémentaires, les pauses, le pointage, la présence réelle, les remplacements
ou les notifications.
