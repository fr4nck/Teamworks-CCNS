# Domaine `EmployeeQualification`

`EmployeeQualification` représente le fait qu'un `Employee` détient une
`Qualification`. C'est un objet domaine immutable, sans dépendance vers la
persistance, une API, le Web ou une interface graphique.

## Données portées

- identifiant UUID ;
- salarié et qualification obligatoires ;
- statut (`QualificationStatus`) : valide, expiré, suspendu, en attente ou
  révoqué ;
- dates facultatives d'obtention et d'expiration ;
- organisme délivrant, numéro de certificat et observations facultatifs ;
- indicateur d'activité.

Les textes facultatifs fournis sont normalisés par suppression des espaces en
début et fin de valeur. Les deux dates, lorsqu'elles sont présentes, respectent
l'ordre `expiration >= obtention`.

## Questions métier

- `is_valid()` vérifie que le statut déclaré est `VALID` ;
- `is_expired()` vérifie que le statut déclaré est `EXPIRED` ;
- `has_expiration()` vérifie la présence d'une date d'expiration.

Ces méthodes ne calculent jamais le statut à partir de la date courante ni de
la durée de validité de `Qualification`.

## Limites explicites

Ce domaine ne porte ni alertes, ni renouvellements automatiques, ni
équivalences, passerelles, exigences réglementaires, missions, planning ou
contrats. Il modélise uniquement la possession déclarée d'une qualification.
