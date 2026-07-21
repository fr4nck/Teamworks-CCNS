# TW-021 — Validation globale d’une affectation planifiée

Le service `AssignmentValidationService` fournit un point d’entrée métier unique pour contrôler une `MissionOccurrenceAssignment` avant planification.

## Périmètre

Le service reste un orchestrateur pur, stateless et sans dépendance technique. Il ne persiste rien, ne consulte aucune interface, n’appelle aucune API et ne lit pas la date ou l’heure courante.

## Contrôles orchestrés

Les contrôles spécialisés sont exécutés systématiquement dans cet ordre :

1. éligibilité par qualification avec `QualificationEligibilityService` ;
2. conflits entre affectations avec `PlanningConflictService` ;
3. conflits d’indisponibilité avec `UnavailabilityConflictService` ;
4. couverture par disponibilité hebdomadaire avec `WeeklyAvailabilityService`.

Le service ne réimplémente pas les règles de ces services. Il conserve dans chaque `AssignmentValidationIssue.detail` l’objet métier produit par le service spécialisé.

## Résultat

`AssignmentValidationResult` est valide uniquement si aucun problème n’est détecté. Les problèmes sont retournés dans l’ordre métier stable, sans arrêt au premier échec et sans doublon exact.

Les quatre catégories strictes sont représentées par `AssignmentValidationIssueType` : qualification, conflit de planning, indisponibilité et disponibilité hebdomadaire.

## Collections

Les collections d’entrée acceptent listes, tuples et générateurs. Elles sont matérialisées une seule fois, validées élément par élément, et ne sont jamais modifiées.
