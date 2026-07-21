# TW-024 — Transitions de statut du planning

Le service `PlanningStatusTransitionService` encadre les changements de statut de l'agrégat immutable `Planning` sans persistance, sans interface graphique et sans consultation de la date courante.

## Transitions autorisées

Seules les transitions suivantes sont autorisées :

- `DRAFT` → `VALIDATED` ;
- `VALIDATED` → `DRAFT` ;
- `VALIDATED` → `PUBLISHED` ;
- `PUBLISHED` → `ARCHIVED` ;
- `ARCHIVED` → `DRAFT`.

Toute transition vers le statut déjà porté par le planning est refusée avec la raison `same_status`. Toute autre transition absente de cette liste est refusée avec la raison `transition_not_allowed`.

## Passage de brouillon à validé

La transition `DRAFT` → `VALIDATED` exige un `PlanningValidationResult` fourni explicitement. Le service ne recalcule jamais la validation globale.

Le résultat fourni doit être globalement valide et ses résultats d'affectation doivent correspondre exactement aux affectations du planning, par comparaison des UUID métier :

- aucune affectation du planning ne doit manquer ;
- aucune affectation étrangère ne doit être présente ;
- les doublons sont refusés ;
- l'ordre des résultats n'a pas d'importance.

## Résultats métier

Un succès retourne un `PlanningStatusTransitionResult` avec `successful=True` et une nouvelle instance de `Planning` produite par `Planning.with_status()`. L'UUID, les affectations et leur ordre sont conservés, et le planning d'origine reste inchangé.

Un refus métier ne lève pas d'exception : il retourne `successful=False` et un `PlanningStatusTransitionFailure` contenant une raison stable et un message métier stable. Les `ValueError` sont réservées aux entrées techniquement invalides.
