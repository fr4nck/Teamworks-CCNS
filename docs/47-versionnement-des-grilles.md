# Versionnement des grilles salariales

## Objectif

Le versionnement des grilles salariales introduit une couche descriptive entre le contrat et la grille utilisée par les contrôles existants : `SalaryGridVersion`. Cette couche ne modifie aucun calcul, aucun montant et aucune règle de contrôle. Elle prépare uniquement l'historisation réglementaire des grilles et leur activation future après validation.

## Modèle

`SalaryGridVersion` décrit une version de grille par :

- un identifiant technique hérité de l'entité de base ;
- `grid_code`, le code de la grille concernée, par exemple `CCNS-2026` ;
- `version`, le libellé stable de version ;
- `effective_date` et `end_date`, qui bornent la période d'applicabilité ;
- `status`, avec les états `DRAFT`, `SCHEDULED`, `ACTIVE`, `SUPERSEDED` et `ARCHIVED` ;
- `comment`, pour documenter le contexte ;
- `rule_version`, lien optionnel vers la version de règle qui justifie la grille ;
- `rule_reference`, lien optionnel direct vers la référence réglementaire ;
- `validation_level`, réutilisé depuis les versions de règles pour éviter une taxonomie parallèle ;
- `validation_date`, date de validation documentaire ou métier.

Le modèle reste volontairement descriptif. Il ne contient pas les montants, ne choisit pas de ligne de grille et ne remplace pas `SalaryGrid` ni `SalaryGridLine`.

## Relation avec `RuleVersion`

`RuleVersion` versionne une règle métier : elle explique quelle version d'une règle de calcul ou de contrôle est applicable à une date donnée. `SalaryGridVersion` versionne le support salarial : elle explique quelle édition de grille est documentée pour une période donnée.

Les deux concepts sont complémentaires : une grille peut pointer vers une `RuleVersion` lorsque la grille matérialise une règle déjà tracée, par exemple les minima conventionnels. Ce lien permet de préparer le chemin :

`Contrat -> SalaryGridVersion -> SalaryGrid -> RuleVersion -> RuleReference -> source officielle`.

`SalaryGridVersion` ne duplique donc pas `RuleVersion`, car elle ne décrit pas l'algorithme ni les paramètres de contrôle ; elle décrit l'édition réglementaire de la grille et son cycle de validation.

## Relation avec `RuleReference`

`RuleReference` demeure la trace de la source officielle : Légifrance, avenant, article conventionnel ou autre publication reconnue. `SalaryGridVersion` peut y être reliée directement ou indirectement via `RuleVersion`.

Le lien direct est utile lorsqu'une source publie une grille complète. Le lien indirect via `RuleVersion` est utile lorsqu'une règle métier documentée porte déjà la référence réglementaire commune.

## Sélection par date

`SalaryGridVersionSelector` répond à la question : « quelle version de grille était applicable le 15 septembre 2026 ? ».

La sélection filtre :

1. le code de grille ;
2. la période d'effet ;
3. les statuts applicables (`ACTIVE` et `SCHEDULED`) ;
4. le niveau de validation pour les versions planifiées.

Une version `SCHEDULED` n'est sélectionnable que si elle a atteint un niveau de validation suffisant (`LEGAL_REVIEWED` ou `BUSINESS_VALIDATED`). Les versions `DRAFT`, `SUPERSEDED` et `ARCHIVED` restent historisées mais ne sont pas applicables.

Dans l'audit Teamworks réel, la sélection reste compatible avec les bases déjà installées : lorsqu'aucune version n'est disponible, qu'aucune version n'est applicable, qu'une version applicable ne pointe vers aucune grille réelle ou que plusieurs grilles partagent le code retenu, le diagnostic est conservé mais l'audit charge une grille réelle si elle existe. Le repli est déterministe : grille applicable à la date de référence la plus récente, puis à défaut grille à la date d'effet la plus ancienne, puis plus petit `IDtw_salary_grid` en cas d'égalité. L'absence de grille n'est donc conclue que si la lecture `tw_salary_grids` ne retourne réellement aucun enregistrement.

## Veille réglementaire et mises à jour futures

La veille réglementaire produit des `RegulatorySnapshot` et des `RegulatoryChange` pour détecter les changements de sources officielles. Le versionnement des grilles prépare l'étape suivante : transformer une variation détectée en proposition de nouvelle `SalaryGridVersion`.

Cette préparation n'implique aucune application automatique en production. Une mise à jour future devra rester en brouillon ou planifiée tant qu'elle n'aura pas été relue, qualifiée juridiquement et validée métier. Les futures automatisations pourront donc créer, comparer et documenter des versions, mais l'activation effective restera conditionnée au statut et au niveau de validation.

## Première intégration

Une première version `CCNS-2026 / 2026-01` représente la grille actuellement utilisée. Elle est raccordée à la référence des minima mensuels déjà présente et n'altère pas les montants existants.

## Capacités préparées

Cette architecture permet désormais de préparer :

- la coexistence de plusieurs grilles ;
- la création d'une grille future sans activation immédiate ;
- l'activation différée après validation ;
- l'historisation complète des versions remplacées ou archivées ;
- la comparaison de deux versions de grille ;
- le rattachement aux `RuleVersion` et `RuleReference` ;
- l'exploitation contrôlée des résultats de veille réglementaire.
