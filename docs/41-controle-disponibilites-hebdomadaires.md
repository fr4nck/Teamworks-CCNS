# TW-020 — Contrôle des disponibilités hebdomadaires

Le contrôle de disponibilité hebdomadaire vérifie qu'une affectation à une occurrence de mission est entièrement couverte par une disponibilité hebdomadaire active du salarié affecté.

## Périmètre métier

Le service `WeeklyAvailabilityService` est un service de domaine pur et stateless. Il ne consulte ni la persistance, ni l'interface graphique, ni l'heure courante. Il ne traite pas les qualifications, indisponibilités exceptionnelles, contrats, repos, paie, jours fériés, trajets ou conflits entre affectations.

## Règle de couverture

Une affectation est couverte uniquement lorsqu'une seule `EmployeeWeeklyAvailability` :

- concerne le même salarié que la `MissionOccurrenceAssignment` ;
- est active ;
- s'applique à la date de début de la `MissionOccurrence` ;
- couvre le début inclus et la fin incluse de l'occurrence ;
- utilise des horaires compatibles avec ceux de l'occurrence.

Plusieurs disponibilités ne sont jamais fusionnées. Ainsi, deux créneaux adjacents 09:00–12:00 et 12:00–17:00 ne couvrent pas une affectation 09:00–17:00.

## Limites volontaires

Le modèle hebdomadaire courant ne garantit pas la couverture des affectations traversant plusieurs dates. Ces affectations sont donc considérées comme non couvertes.

Aucune conversion automatique de fuseau horaire n'est effectuée. Les horaires naïfs doivent être comparés avec des horaires naïfs, et les horaires zonés doivent utiliser le même objet de fuseau horaire compatible.

## Résultat métier

Le service retourne toujours un `WeeklyAvailabilityCheckResult` pour une absence simple de couverture. En cas d'échec, le résultat contient un `WeeklyAvailabilityConflict` avec une raison stable :

`L’affectation n’est couverte par aucune disponibilité hebdomadaire active du salarié.`
