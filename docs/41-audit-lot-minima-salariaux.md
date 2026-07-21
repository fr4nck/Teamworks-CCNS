# TW-031 — Audit en lot des minima salariaux applicables

## Rôle

L'audit en lot des minima salariaux applicables agrège plusieurs résultats `ApplicableSalaryMinimumResult` déjà calculés afin de produire une synthèse métier immutable. Il sert à exploiter ensemble des contrôles individuels sans relancer le calcul du minimum CCNS ou SMIC applicable.

Chaque entrée du lot est portée par un `SalaryMinimumAuditItem`. Cet item associe uniquement le résultat de conformité et, lorsque l'appelant les connaît, les UUID stricts du salarié et du contrat.

## Délégation au service individuel

`SalaryMinimumBatchAuditService` ne recrée pas les anomalies et ne recalcule aucun minimum salarial. Pour chaque item, dans l'ordre reçu, il délègue au service individuel `SalaryMinimumAuditService.audit(...)` avec le résultat de conformité et les références salarié/contrat de l'item.

Cette délégation conserve les règles existantes : un résultat conforme ne produit aucune anomalie ; un résultat non conforme produit exactement l'anomalie bloquante `REMUNERATION_BELOW_APPLICABLE_MINIMUM`.

## Ordre et déterminisme

Le lot matérialise l'itérable reçu une seule fois sous forme de tuple. Les listes, tuples et générateurs sont acceptés. L'ordre d'entrée est conservé pour :

- les items exposés par le résultat global ;
- les résultats individuels ;
- les anomalies concaténées ;
- les regroupements par salarié ou par contrat.

Aucun tri automatique n'est appliqué par ce service.

## Détection des doublons

Un même `ApplicableSalaryMinimumResult` ne peut pas être audité plusieurs fois dans un même lot. La détection repose exclusivement sur l'UUID du résultat de conformité.

Deux résultats distincts restent autorisés même s'ils concernent le même salarié, le même contrat, la même classification ou la même date. Seul l'UUID du résultat de conformité fait foi.

## Synthèse globale

`SalaryMinimumBatchAuditResult` expose :

- tous les items ;
- tous les résultats individuels ;
- toutes les anomalies concaténées dans l'ordre ;
- l'indicateur global `valid` ;
- le nombre de résultats conformes ;
- le nombre de résultats non conformes ;
- le déficit total.

Le déficit total est la somme Decimal des déficits individuels déjà quantifiés. La somme reste en `Decimal`, ne passe jamais par `float` et est quantifiée à `Decimal("0.01")` avec `ROUND_HALF_UP`.

## Taux de conformité

Le taux de conformité est calculé explicitement par :

```python
Decimal(compliant_count) / Decimal(item_count)
```

Le résultat est quantifié à `Decimal("0.0001")` avec `ROUND_HALF_UP`. Par exemple :

- tous conformes : `Decimal("1.0000")` ;
- aucun conforme : `Decimal("0.0000")` ;
- un conforme sur trois : `Decimal("0.3333")`.

## Regroupements salarié et contrat

Le résultat global fournit des méthodes de regroupement par UUID strict :

- `results_for_employee(employee_id)` ;
- `results_for_contract(contract_id)` ;
- `issues_for_employee(employee_id)` ;
- `issues_for_contract(contract_id)`.

Ces méthodes valident strictement les UUID, conservent l'ordre d'origine et retournent un tuple vide lorsqu'aucune correspondance n'existe.

## Compatibilité avec les filtres et tris

Les anomalies produites restent des `SalaryMinimumAuditIssue`. Elles conservent les propriétés existantes `person_id`, `object_type` et `object_id`, ainsi que le code et la gravité utilisés par les filtres et tris d'audit existants.

## Limites du ticket

L'audit en lot ne lit pas automatiquement les salariés ou les contrats. Il ne consulte aucune base de données, n'exécute pas `ApplicableSalaryMinimumService`, ne convertit pas de montants historiques et ne déclenche aucune correction automatique.

Le ticket ne traite pas les groupes annuels, apprentis, mineurs, contrats de professionnalisation, éléments de paie, primes, heures supplémentaires, notifications, e-mails, exports CSV/PDF ni interface utilisateur.
