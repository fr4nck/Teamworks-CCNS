# Validation globale d’un planning

## Objectif métier

La validation globale d’un planning contrôle un ensemble complet d’affectations déjà construites. Elle ne crée pas, ne modifie pas et ne supprime aucune affectation. Elle sert à fournir à une future interface de planning un résultat exploitable pour afficher les affectations valides et invalides sans interrompre le contrôle au premier problème.

## Périmètre

Le service `PlanningValidationService` appartient au domaine pur :

- aucune persistance ;
- aucune interface graphique ;
- aucune API ;
- aucune dépendance technique ;
- aucune consultation de la date ou de l’heure courante.

Il orchestre uniquement `AssignmentValidationService`, qui reste le point d’entrée des contrôles individuels : qualifications, conflits de planning, indisponibilités et disponibilités hebdomadaires.

## Points d’entrée

Le service expose deux points d’entrée métier :

- `validate(assignments, qualification_requirements, employee_qualifications, unavailabilities, weekly_availabilities)` pour valider une collection d’affectations déjà disponible ;
- `validate_planning(planning, qualification_requirements, employee_qualifications, unavailabilities, weekly_availabilities)` pour valider directement les affectations immutables portées par un agrégat `Planning`.

Lorsque l’agrégat `Planning` existe déjà, `validate_planning()` est le point d’entrée recommandé. Il utilise exactement `planning.assignments`, sans tri, filtre, reconstruction ni changement de statut, refuse explicitement un planning sans affectation, puis délègue à `validate()` afin de produire un `PlanningValidationResult` compatible avec `PlanningStatusTransitionService`. Le statut et le champ `active` du planning ne modifient pas le résultat de validation.

## Règles de validation

Pour chaque affectation du planning, le service appelle `AssignmentValidationService` une seule fois. Les affectations existantes transmises à cet appel contiennent toutes les autres affectations du planning, mais jamais l’affectation en cours de contrôle.

Pour un planning contenant `A`, `B` et `C` :

- `A` est validée avec `B` et `C` comme affectations existantes ;
- `B` est validée avec `A` et `C` comme affectations existantes ;
- `C` est validée avec `A` et `B` comme affectations existantes.

Le service conserve strictement l’ordre d’entrée. Aucun tri par date, salarié, mission ou statut n’est réalisé. Le planning est valide uniquement si tous les résultats individuels sont valides.

## Collections acceptées

Les collections d’entrée peuvent être des listes, tuples ou générateurs. Elles sont matérialisées une seule fois, validées élément par élément et jamais modifiées. Les chaînes, les bytes, les valeurs non itérables, les collections d’affectations vides et les éléments de type inattendu sont refusés.

Deux affectations portant le même identifiant métier ne peuvent pas apparaître dans le même planning. Cette situation est refusée par une erreur métier explicite afin d’éviter un résultat ambigu.

## Résultat métier

`PlanningValidationResult` est immutable. Il contient :

- les `AssignmentValidationResult` dans l’ordre initial ;
- le booléen strict `valid`, cohérent avec tous les résultats individuels.

Il expose des méthodes de lecture pour connaître le nombre total d’affectations, les comptes valides et invalides, les sous-ensembles de résultats valides et invalides, ainsi que le résultat associé à une affectation donnée par son identité métier. Si l’affectation recherchée n’est pas présente, une erreur est levée plutôt que de retourner silencieusement `None`.

## Limites volontaires

Cette validation ne couvre pas les durées maximales de travail, les jours fériés, les coûts, les déplacements, la paie, les propositions automatiques de remplacement, l’optimisation de planning, la publication, les autorisations ou la persistance. Ces sujets restent hors périmètre de ce service métier.
