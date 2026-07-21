# TW-032 — Évaluation du minimum salarial depuis un contrat

`ContractSalaryEvaluationService` est un service de domaine pur, immutable et stateless. Il orchestre l'évaluation d'un `Contract` existant et délègue le calcul au moteur `ApplicableSalaryMinimumService` sans recalculer de minimum CCNS, de SMIC, de proratisation ni de statut de conformité.

## Concepts réutilisés

Le service réutilise le modèle `domain.contracts.Contract` et ses champs métier dédiés à l'évaluation directe :

- `ccns_classification` pour la classification `CCNSClassification` exploitable ;
- `monthly_gross_salary_amount` pour la rémunération brute mensuelle en `Decimal` ;
- `weekly_hours` pour la durée hebdomadaire en `Decimal` ;
- `smic_territory` pour le territoire `SmicTerritory` porté par le contrat ;
- `start_date`, `end_date` et `is_applicable_on()` pour l'applicabilité temporelle.

Les anciens champs techniques ou historiques exprimés en `float` (`base_salary_amount`, `weekly_reference_hours`) ne sont pas convertis automatiquement.

## Ordre stable des validations

L'évaluation applique toujours l'ordre suivant :

1. validité technique des entrées ;
2. applicabilité temporelle du contrat ;
3. classification CCNS ;
4. rémunération présente ;
5. périodicité brute mensuelle (`salary_unit == "monthly"`) ;
6. durée hebdomadaire ;
7. territoire ;
8. compatibilité avec un minimum mensuel ;
9. appel à `ApplicableSalaryMinimumService`.

Cet ordre rend les refus déterministes lorsque plusieurs données sont absentes ou incompatibles.

## Territoire

Le territoire porté par le contrat est prioritaire. À défaut, le territoire explicite fourni à `evaluate(..., territory=...)` est utilisé. Aucun territoire métropolitain implicite n'est inventé : l'absence de territoire produit un refus métier `MISSING_TERRITORY`.

## Refus métier

Les absences ou incompatibilités fonctionnelles produisent un `ContractSalaryEvaluationResult` en échec, avec un `ContractSalaryEvaluationFailure` immuable. Les erreurs techniques de type invalide continuent de lever une exception.

Les minima CCNS annuels, notamment les groupes 7 et 8 lorsque la grille applicable les définit comme annuels, sont refusés avec `ANNUAL_CCNS_MINIMUM_NOT_SUPPORTED` et le message :

> Le contrôle salarial direct du contrat est limité aux minima CCNS mensuels.

## Limites volontaires

Le service ne réalise aucune conversion annuel/mensuel, horaire/mensuel, net/brut, mensuel/hebdomadaire ou depuis un pourcentage de temps de travail. Il ne reconstitue pas une paie, n'intègre pas de primes, absences, heures supplémentaires, ancienneté ou avantages en nature, ne corrige pas le contrat et n'ajoute aucune persistance, interface graphique, API ou notification.
