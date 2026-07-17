# Domaine `Mission`

`Mission` définit une fonction ou une intervention métier réutilisable, par
exemple l'animation ou la direction d'un ALSH. C'est un objet domaine
immutable et pur : il ne dépend ni de la persistance, ni de l'interface
graphique, ni du Web ou d'une API.

## Données portées

- identifiant UUID ;
- code obligatoire, normalisé par suppression des espaces périphériques et
  conversion en majuscules ;
- nom obligatoire, normalisé par suppression des espaces périphériques ;
- description facultative, normalisée lorsqu'elle est fournie ;
- exigences de qualification stockées dans un tuple immutable ;
- indicateur d'activité booléen.

Chaque exigence doit être une `QualificationRequirement`. Deux exigences ayant
le même identifiant UUID ne peuvent pas être rattachées à une même mission.

## Questions métier

- `has_qualification_requirements()` indique si la mission a des exigences ;
- `qualification_requirement_count()` retourne leur nombre ;
- les méthodes `required_qualification_requirements()`,
  `recommended_qualification_requirements()` et
  `optional_qualification_requirements()` retournent respectivement les
  exigences du niveau correspondant, sous forme de tuples.

Le niveau de chaque exigence reste l'unique source de vérité : les méthodes de
filtrage délèguent cette détermination aux méthodes métier de
`QualificationRequirement`. La mission ne porte donc aucun indicateur
redondant d'obligation.

## Limites explicites

Une mission n'est ni une occurrence planifiée, ni une affectation de salarié.
Elle ne contient ni date, ni horaire, ni lieu, ni durée, ni récurrence, ni
contrat. Elle ne compare pas les qualifications détenues, ne décide pas de
l'éligibilité et n'applique aucune règle réglementaire ou d'équivalence.
