# Agrégat métier Planning

Le `Planning` représente un planning CCNS autonome, identifié par un UUID métier,
nommé par un code et un libellé, borné par deux dates civiles inclusives, et
porteur d'un tuple ordonné d'affectations de missions.

## Responsabilités

L'agrégat garantit uniquement les invariants structurels locaux :

- identité UUID stricte ;
- code et nom obligatoires, normalisés par suppression des espaces de bord ;
- code converti en majuscules sans autre transformation ;
- période civile valide, avec date de fin supérieure ou égale à la date de début ;
- affectations stockées dans un tuple, sans conversion silencieuse des collections reçues ;
- affectations toutes entièrement comprises dans la période du planning ;
- absence de doublon d'affectation par UUID métier ;
- statut déclaré appartenant à `PlanningStatus` ;
- indicateur `active` strictement booléen.

## Hors périmètre volontaire

Le planning ne valide pas les qualifications, les conflits entre salariés, les
indisponibilités, la disponibilité hebdomadaire ou les conditions de publication.
Ces règles restent portées par les services métier dédiés, notamment
`PlanningValidationService`.

Aucune transition entre statuts n'est contrôlée dans cet agrégat. `with_status()`
remplace uniquement le statut déclaré par une nouvelle instance immutable.

## Immutabilité et ordre

Toutes les transformations (`with_assignment`, `without_assignment`,
`replace_assignment`, `with_status`) retournent une nouvelle instance et laissent
l'instance d'origine inchangée. L'ordre fourni par l'appelant est conservé et les
affectations ne sont jamais triées automatiquement.
