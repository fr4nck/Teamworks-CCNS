# TW-029 — Minimum salarial mensuel le plus favorable

Le contrôle du minimum salarial mensuel opposable retient le montant le plus favorable au salarié entre le minimum conventionnel CCNS et le SMIC applicable. Le résultat expose séparément les deux minima, le minimum exigé, sa source (`CCNS`, `SMIC` ou `EQUAL`), l'écart de rémunération et le statut final de conformité.

## Réutilisation des référentiels existants

Le service `ApplicableSalaryMinimumService` reste un service de domaine pur, immutable et stateless. Il délègue la sélection temporelle de la grille et le calcul du minimum conventionnel à `SalaryMinimumComplianceService.evaluate(...)`, appelé avec la périodicité mensuelle. Les majorations conventionnelles de temps partiel inférieures à 24 heures restent donc portées uniquement par le contrôle CCNS existant.

La version du SMIC est sélectionnée exclusivement par `SmicCatalog.version_applicable_on(reference_date, territory)`. Le service ne parcourt pas les périodes, ne consulte pas la date courante, ne choisit pas la dernière version connue et ne prévoit aucun repli silencieux.

## Proratisation du SMIC mensuel

Le montant `SmicVersion.monthly_gross_amount_35h` correspond à 35 heures hebdomadaires. La référence temps plein utilisée est exactement `Decimal("35.00")`.

Pour une durée strictement inférieure à 35 heures, le SMIC mensuel exigé est proratisé :

```text
SMIC mensuel 35h × heures hebdomadaires / Decimal("35.00")
```

Pour une durée supérieure ou égale à 35 heures, le montant mensuel 35 heures est conservé. TW-029 ne majore pas le SMIC au-delà de 35 heures et n'applique pas au SMIC les majorations conventionnelles CCNS de 5 % ou 2 %.

Tous les montants calculés sont quantifiés à `Decimal("0.01")` avec `ROUND_HALF_UP`.

## Source et conformité

Après quantification :

- `CCNS` signifie que le minimum CCNS est strictement supérieur au SMIC proratisé ;
- `SMIC` signifie que le SMIC proratisé est strictement supérieur au minimum CCNS ;
- `EQUAL` signifie que les deux minima sont exactement égaux.

Le champ `difference_amount` suit la convention :

```text
rémunération mensuelle brute - minimum salarial exigé
```

Un écart positif indique un surplus, zéro indique une rémunération exactement au minimum, et un écart négatif indique une insuffisance. Le statut final est conforme lorsque cet écart est positif ou nul ; il ne dépend pas uniquement de la conformité CCNS intermédiaire.

## Refus des minima annuels et limites

TW-029 couvre uniquement les minima mensuels CCNS, soit les groupes 1 à 6 dans les données actuelles. Les groupes 7 et 8, annuels, sont refusés avec le message métier stable :

```text
Le contrôle du minimum le plus favorable est limité aux minima CCNS mensuels.
```

Le ticket ne convertit pas les périodicités, ne calcule pas une paie complète, ne traite pas les heures supplémentaires ou complémentaires, les primes, absences, congés, arrêts maladie, rappels, treizième mois, rémunérations variables, apprentis, contrats de professionnalisation, mineurs, abattements de SMIC, minimum garanti, alertes, interface utilisateur, persistance ou correction automatique de contrat.
