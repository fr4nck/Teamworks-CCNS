# TW-036 — Projection directe du contrôle salarial depuis les contrats

`ContractSalaryControlService` fournit le point d'entrée métier unique pour les couches applicatives qui disposent déjà d'un lot de `Contract` et veulent obtenir une `ContractSalaryControlProjection` prête à consommer.

La chaîne reste strictement déléguée aux services existants :

1. `ContractSalaryBatchAuditService.audit(...)` évalue les contrats puis audite les résultats salariaux exploitables ;
2. `ContractSalaryControlProjectionService.project(...)` transforme le résultat d'audit en lignes de contrôle ;
3. `ContractSalaryControlResult` conserve les deux instances retournées et expose les compteurs, recherches et filtres de la projection.

Le service d'orchestration est pur, stateless et immutable. Il ne matérialise pas l'itérable de contrats, ne le parcourt pas lui-même et ne lance pas de contrôle individuel par contrat. La consommation unique du lot reste donc la responsabilité du service de lot existant.

## Territoire

Le territoire optionnel est seulement transmis à l'audit de lot. Aucun territoire métropolitain implicite n'est inventé. Un territoire porté par un contrat reste prioritaire ; sans territoire contrat ni territoire de secours, l'évaluation métier échoue et la projection expose une ligne `NOT_EVALUATED`.

## Statuts finaux et validité

Les statuts finaux restent ceux de `ContractSalaryControlStatus` :

- `COMPLIANT` pour une évaluation réussie et un audit conforme ;
- `NON_COMPLIANT` pour une évaluation réussie avec manque salarial ;
- `NOT_EVALUATED` pour un refus métier d'évaluation.

`valid` est exactement celui de la projection : le résultat est valide uniquement lorsque toutes les lignes finales sont conformes. Un lot vide est valide, sans ligne, avec compteurs à zéro et `total_shortfall_amount == Decimal("0.00")`.

## Limites volontaires

Ce point d'entrée n'ajoute ni persistance, ni repository, ni API, ni interface graphique, ni export HTML/CSV/PDF, ni notification, ni tâche planifiée, ni correction automatique. Il ne crée aucune règle CCNS ou SMIC, aucun calcul salarial et aucune donnée externe de salarié.

Il sert de façade future pour une interface ou un export qui pourra consommer directement la projection finale sans réimplémenter l'enchaînement évaluation → audit → projection.
