# TW-034 — Audit salarial en lot à partir des contrats

`ContractSalaryBatchAuditService` est l’orchestrateur de domaine pur qui permet de partir directement d’un itérable de `Contract` et d’obtenir une synthèse d’audit salarial à une date de référence. Il reste stateless et immutable : il ne lit aucune persistance, ne modifie aucun contrat et ne déclenche aucune interface.

## Séparation entre évaluation et audit

L’orchestrateur ne remplace ni `ContractSalaryBatchEvaluationService`, ni `SalaryMinimumBatchAuditService`. Il appelle d’abord l’évaluation en lot exactement une fois, convertit explicitement les évaluations réussies avec `to_salary_minimum_audit_items()`, puis appelle l’audit salarial en lot exactement une fois. Les minima CCNS, le SMIC, les proratisations et les anomalies restent calculés par les services existants.

## Refus métier conservés

Les contrats non évaluables produisent des `ContractSalaryEvaluationFailure` et restent exposés dans le résultat final via les évaluations échouées et les refus métier. Ils ne sont pas transmis à l’audit salarial et ne sont donc pas comptés comme non conformes.

## Définition de `valid`

`ContractSalaryBatchAuditResult.valid` vaut `True` uniquement si tous les contrats ont pu être évalués et si l’audit salarial des contrats évalués ne contient aucune anomalie. Un lot avec un refus métier est donc globalement invalide, même lorsque tous les contrats auditables sont conformes.

## Compteurs

La synthèse expose le nombre total de contrats, le nombre de contrats évalués, le nombre de refus métier, le nombre de contrats conformes, le nombre de contrats non conformes et le nombre d’anomalies. L’invariant principal est : `total_contract_count = evaluated_contract_count + failed_contract_count`, puis `evaluated_contract_count = compliant_contract_count + non_compliant_contract_count`.

## Manque salarial total

`total_shortfall_amount` provient directement du `SalaryMinimumBatchAuditResult`. L’orchestrateur ne le recalcule pas et ne duplique pas la logique d’anomalie.

## Territoire

Le territoire propre d’un contrat reste prioritaire. Le territoire reçu par l’orchestrateur est seulement transmis comme territoire de secours à l’évaluation en lot. En son absence, aucun territoire implicite n’est inventé : les contrats sans territoire exploitable restent refusés par l’évaluation existante.

## Limites volontaires

L’orchestrateur n’ajoute pas de persistance, repository, API, interface graphique, notification, correction automatique, lecture automatique de tous les contrats, planification, paie, conversion annuel/mensuel, primes, absences, avantages ou heures supplémentaires.
