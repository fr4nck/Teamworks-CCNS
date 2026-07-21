# Audit du minimum salarial applicable

Le service `SalaryMinimumAuditService` est le pont métier pur entre le contrôle mensuel déjà calculé par `ApplicableSalaryMinimumService` et une anomalie exploitable par les couches d'audit. Il consomme uniquement un `ApplicableSalaryMinimumResult` : il ne relit pas de contrat, ne recalcule ni la grille CCNS ni le SMIC, et ne choisit pas à nouveau le minimum le plus favorable.

Lorsque la rémunération brute mensuelle est conforme au minimum applicable, le résultat d'audit est valide et sa collection d'anomalies est vide. Aucune alerte ni avertissement n'est créé pour une conformité, y compris lorsque la rémunération est exactement égale au minimum.

Lorsque la rémunération est insuffisante, le service crée une anomalie unique de code stable `REMUNERATION_BELOW_APPLICABLE_MINIMUM` avec le message : « La rémunération brute mensuelle est inférieure au minimum salarial applicable. » Cette anomalie conserve le résultat source et expose le déficit sous forme de `Decimal` via `shortfall_amount`.

La gravité retenue est `AnomalyLevel.BLOCKING`, car un salaire inférieur au minimum légal ou conventionnel applicable représente une non-conformité nécessitant une correction. Cette gravité réutilise l'échelle existante du moteur d'anomalies et permet aux tris d'audit de classer ce code parmi les anomalies bloquantes.

Les montants restent structurés dans les détails de l'anomalie : rémunération, minimum requis, différence, déficit, minimum CCNS, minimum SMIC proratisé, source déterminante (`CCNS`, `SMIC` ou `EQUAL`), classification, date de référence, territoire et durée hebdomadaire. Les montants ne sont pas uniquement sérialisés dans un texte.

Les références `employee_id` et `contract_id` sont optionnelles et strictement typées en `UUID`. Le service les recopie seulement lorsqu'elles sont fournies explicitement ; il ne tente jamais de les retrouver ailleurs. Lorsqu'un `contract_id` est présent, l'anomalie expose un identifiant d'objet compatible avec l'ouverture ultérieure de la fiche contrat par les couches d'intégration.

Le service est stateless, sans persistance, sans interface graphique, sans API technique et sans usage de la date courante. Il ne corrige jamais automatiquement le contrat et ne déclenche aucun audit global.

Limites du ticket : pas de lecture automatique des contrats, pas d'audit en masse, pas de conversion historique en `Decimal`, pas de calcul de paie, pas de prise en compte des apprentis, contrats de professionnalisation, mineurs, primes, avantages en nature, heures supplémentaires, absences ou rappels de salaire.
