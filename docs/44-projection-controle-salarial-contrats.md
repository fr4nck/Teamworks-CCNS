# Projection de contrôle salarial des contrats

La projection de contrôle salarial transforme un `ContractSalaryBatchAuditResult` déjà calculé en lignes immutables directement lisibles par une interface, une couche applicative ou un export futur. Elle ne relit aucune persistance, ne dépend pas de wxPython et ne déclenche aucun nouveau calcul de minimum salarial.

## Statuts exposés

- `COMPLIANT` : le contrat a été évalué, audité et ne porte aucune anomalie salariale.
- `NON_COMPLIANT` : le contrat a été évalué, audité et porte l'anomalie salariale produite par le domaine.
- `NOT_EVALUATED` : le contrat a été refusé pour une raison métier lors de l'évaluation. Ce statut n'est pas une non-conformité salariale.

## Champs de ligne

Chaque `ContractSalaryControlRow` expose les identifiants contrat et salarié, la date de référence, le statut, le code de classification disponible, les montants déjà calculés, la source du minimum, le territoire, le motif/message d'échec métier et les informations d'anomalie lorsqu'elles existent.

Les montants sont des `Decimal` stricts quantifiés à deux décimales. Les identifiants sont des `UUID` stricts et la date est une `date` stricte, jamais un `datetime`.

## Validité et manque salarial total

`ContractSalaryControlProjection.valid` vaut `True` uniquement si toutes les lignes sont `COMPLIANT`. Un lot vide est valide. La présence d'une ligne `NON_COMPLIANT` ou `NOT_EVALUATED` rend la projection invalide.

`total_shortfall_amount` est la somme exacte des `shortfall_amount` des lignes, sans conversion flottante, quantifiée à deux décimales.

## Ordre et absence de recalcul

Le service `ContractSalaryControlProjectionService` préserve exactement l'ordre de `ContractSalaryBatchAuditResult.evaluations` et produit exactement une ligne par contrat. Pour chaque évaluation réussie, il récupère le résultat d'audit correspondant via les méthodes publiques du résultat d'audit en lot. Pour chaque refus métier, il vérifie qu'aucun audit salarial n'existe.

La projection reprend les montants, la source, le territoire, l'écart et les anomalies existants. Le domaine d'audit salarial impose actuellement exactement une anomalie pour un résultat non conforme ; le service vérifie cet invariant avant d'exposer `issue_code` et `issue_message`. Elle ne recalcule pas le minimum, ne réévalue pas les contrats et ne recrée pas d'anomalies.

## Limites volontaires

La projection n'ajoute ni repository, ni API, ni interface graphique, ni export CSV/PDF/HTML, ni notification, ni correction automatique, ni nouvelle règle CCNS ou SMIC. Elle ne contient que les données disponibles dans le résultat d'audit.

## Usage futur

Les couches applicatives, écrans et exports pourront consommer `ContractSalaryControlProjection.rows` et les méthodes de filtrage par contrat, salarié ou statut sans connaître les agrégats internes d'évaluation et d'audit.
