# Version temporelle des grilles salariales CCNS

## Pourquoi conserver les versions

Un contrôle de rémunération doit utiliser le minimum conventionnel applicable à sa date de référence, et non le dernier montant connu. Chaque évolution de la CCNS produit donc une nouvelle `SalaryGridVersion` avec sa propre période d’application. Une ancienne grille n’est jamais modifiée ni écrasée : elle reste nécessaire aux contrôles historiques.

`SalaryGridCatalog` conserve les versions dans l’ordre fourni, refuse les codes et UUID dupliqués et interdit tout chevauchement de périodes. Les bornes sont inclusives. Des trous sont autorisés ; aucune grille n’est alors applicable pendant le trou. Aucune méthode ne consulte implicitement la date courante.

## Modèle métier

- `SalaryGridEntry` associe un `CCNSClassification` existant, un montant `Decimal` positif quantifié à deux décimales et une `SalaryMinimumPeriodicity` ;
- `SalaryGridVersion` contient les entrées et leurs dates d’effet ;
- `SalaryGridCatalog` sélectionne l’unique version applicable à une date ;
- tous les nouveaux objets sont immuables, utilisent des tuples et valident strictement UUID, dates, booléens et `Decimal`.

La périodicité suit l’article 9.2.1 : les groupes 1 à 6 portent un minimum mensuel brut à temps plein, tandis que les groupes 7 et 8 portent un minimum annuel brut de référence. Le modèle refuse une périodicité incohérente.

## Montants applicables au 1er janvier 2026

La fabrique publique `create_ccns_salary_grid_2026_01()` crée une nouvelle instance à chaque appel.

| Groupe | Périodicité | Minimum brut |
|---|---:|---:|
| 1 | Mensuelle | 1 848,42 € |
| 2 | Mensuelle | 1 885,14 € |
| 3 | Mensuelle | 1 997,87 € |
| 4 | Mensuelle | 2 099,37 € |
| 5 | Mensuelle | 2 333,99 € |
| 6 | Mensuelle | 2 865,97 € |
| 7 | Annuelle | 40 597,94 € |
| 8 | Annuelle | 46 833,81 € |

Source portée par la grille : « CCNS, article 9.2.1, montants applicables au 1er janvier 2026 ».

## Temps partiel inférieur à 24 heures

`PartTimeMinimumIncreaseRule` représente les deux tranches conventionnelles, sans calculer de paie :

- jusqu’à 10 heures hebdomadaires incluses : 5 % ;
- au-delà de 10 heures et strictement en dessous de 24 heures : 2 % ;
- à partir de 24 heures : 0 %.

`increase_rate_for_weekly_hours()` retourne seulement le taux applicable. Les heures sont des `Decimal` strictement positives.

## Limites volontaires de TW-026

Ce ticket ne calcule ni paie réelle, ni salaire contractuel, ni proratisation, ni conversion mensuelle/horaire ou annuelle/mensuelle. Il ne traite pas le SMIC, les heures supplémentaires ou complémentaires, les primes, l’ancienneté, les avantages, les rappels, la polyvalence ou la classification automatique. Il n’ajoute aucune persistance, API, interface, veille Internet ou modification de contrat.
