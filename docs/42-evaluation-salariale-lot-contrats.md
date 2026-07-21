# TW-033 — Évaluation salariale en lot des contrats

`ContractSalaryBatchEvaluationService` fournit le point d’entrée métier pour évaluer plusieurs `Contract` à une date de référence donnée. C’est un service de domaine pur, immutable et stateless : il ne lit aucune base, ne crée aucun contrat et ne déclenche aucun traitement de persistance ou d’interface.

## Relation avec TW-032

Le lot ne remplace pas `ContractSalaryEvaluationService`. Pour chaque contrat reçu, il appelle exactement une fois `ContractSalaryEvaluationService.evaluate(...)` et conserve le `ContractSalaryEvaluationResult` retourné. Le calcul du minimum salarial applicable reste donc porté par TW-032 et par `ApplicableSalaryMinimumService` ; TW-033 n’ajoute pas de second moteur CCNS/SMIC.

## Matérialisation et ordre

L’itérable d’entrée est matérialisé une seule fois dans un tuple avant traitement. L’ordre d’entrée est l’ordre de sortie : les évaluations, les succès, les échecs et les `SalaryMinimumAuditItem` dérivés conservent l’ordre relatif des contrats concernés.

Un lot vide est accepté. Il produit un `ContractSalaryBatchEvaluationResult` cohérent avec des compteurs à zéro, des tuples vides et aucune anomalie inventée.

## Refus métier conservés

Les refus fonctionnels retournés par `ContractSalaryEvaluationService` ne stoppent pas le lot. Ils restent dans `evaluations` sous forme de `ContractSalaryEvaluationResult` en échec et sont exposés par `failed_evaluations()` et `failures()`.

Les erreurs techniques restent strictes : mauvaise date, mauvais type de contrat, mauvais type de territoire ou incohérences de construction lèvent une exception.

## Règles de territoire

Le service accepte un territoire explicite optionnel de type `SmicTerritory`. Ce territoire est transmis tel quel à chaque évaluation individuelle. Le territoire porté par le contrat reste prioritaire, conformément à TW-032. Si ni le contrat ni le paramètre explicite ne fournissent de territoire, aucun territoire métropolitain implicite n’est inventé : l’évaluation individuelle retourne un refus métier `MISSING_TERRITORY`.

## Doublons

Deux contrats ayant le même identifiant métier de contrat sont refusés dans un même lot. La détection repose sur l’identifiant normalisé exposé par `ContractSalaryEvaluationResult.contract_id()`.

Deux contrats différents d’un même salarié sont acceptés. Les recherches par salarié (`evaluations_for_employee`) retournent toutes les évaluations du salarié, dans l’ordre du lot.

## Intégration explicite avec l’audit en lot

`ContractSalaryBatchEvaluationResult.to_salary_minimum_audit_items()` construit les `SalaryMinimumAuditItem` nécessaires à `SalaryMinimumBatchAuditService` uniquement à partir des évaluations réussies. La méthode :

- réutilise exactement l’instance `ApplicableSalaryMinimumResult` existante ;
- transmet les UUID salarié et contrat lorsqu’ils sont disponibles ;
- préserve l’ordre des contrats réussis ;
- ne recalcule aucun minimum ;
- ne crée aucun item pour les évaluations en échec.

L’audit en lot n’est jamais déclenché automatiquement depuis le résultat ou le service d’évaluation. L’appelant choisit explicitement s’il transmet ces items à `SalaryMinimumBatchAuditService`.

## Limites volontaires

TW-033 n’ajoute pas de persistance, repository, API, interface graphique, export, planification, notification, correction automatique de contrat, lecture automatique de tous les contrats, conversion annuel/mensuel, calcul de paie, gestion de primes, absences, avantages ou heures supplémentaires.
