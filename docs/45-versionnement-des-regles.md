# Versionnement des règles métier CCNS

## Objectif

Le versionnement des règles ajoute une couche descriptive au moteur métier CCNS. Il permet d'identifier quelle version d'une règle était applicable à une date donnée, sans modifier les calculs, les montants, les salaires ni les anomalies existantes.

Cette PR introduit l'architecture nécessaire pour historiser les versions. La première intégration porte uniquement sur la règle d'ancienneté standard des groupes 1 à 6.

## Modèle `RuleVersion`

`RuleVersion` représente une version datée d'une règle métier. Le modèle contient :

- un identifiant technique hérité de l'entité de base ;
- le code de la règle concernée (`rule_code`) ;
- le libellé de version (`version`) ;
- une date d'effet obligatoire (`effective_date`) ;
- une date de fin optionnelle (`end_date`) ;
- un statut de cycle de vie (`status`) ;
- un commentaire libre (`comment`) ;
- une référence réglementaire (`rule_reference`) ;
- un niveau de validation (`validation_level`).

Les dates sont inclusives : une version est applicable à partir de sa date d'effet et jusqu'à sa date de fin lorsqu'elle existe.

## Statuts et validation

Les statuts prévus couvrent les usages futurs :

- `DRAFT` : version préparatoire non sélectionnable ;
- `SCHEDULED` : version prête avec une date d'effet future ou atteinte, sélectionnable seulement après validation suffisante ;
- `ACTIVE` : version applicable ;
- `SUPERSEDED` : version remplacée ;
- `ARCHIVED` : version conservée pour historique mais non sélectionnable.

Le niveau de validation distingue la documentation initiale, la revue juridique et la validation métier. Cette séparation évite qu'une veille réglementaire ou une documentation en cours déclenche automatiquement un changement de calcul.

## Lien avec `RuleReference`

`RuleReference` reste la trace de la source officielle : Légifrance, avenant, article ou autre source reconnue. `RuleVersion` pointe vers cette référence pour dire quelle source justifie une version donnée de la règle.

Ainsi :

- une même règle peut avoir plusieurs versions successives ;
- une version peut rester reliée à la source officielle utilisée pour la documenter ;
- les contrôles historiques peuvent expliquer quelle version et quelle référence étaient applicables à la date étudiée.

## Sélection de la version applicable

Le service `RuleVersionSelector` répond à la question : « quelle version de cette règle était applicable le 15 septembre 2026 ? ».

Il filtre les versions par code de règle, statut sélectionnable, validation suffisante et période de validité. Une version `SCHEDULED` dont le niveau reste `DRAFT`, `DOCUMENTED` ou `LEGAL_REVIEW_REQUIRED` n'est pas sélectionnable, même lorsque sa date d'effet est atteinte. Elle doit être revue juridiquement (`LEGAL_REVIEWED`) ou validée métier (`BUSINESS_VALIDATED`) avant de pouvoir être considérée applicable par le sélecteur. En cas de coexistence technique de plusieurs versions applicables, il retient la version dont la date d'effet est la plus récente.

Cette sélection est purement descriptive dans cette étape : elle ne pilote pas encore les calculs du moteur.

## Lien avec la veille réglementaire

La veille réglementaire peut détecter une nouvelle source, un avenant ou une modification de contenu. Le versionnement fournit le point d'atterrissage métier :

1. la veille détecte une source nouvelle ou modifiée ;
2. une `RuleReference` documente cette source ;
3. une `RuleVersion` est préparée en `DRAFT` ou `SCHEDULED` ;
4. les calculs restent inchangés tant que la version n'est pas validée ;
5. une PR métier dédiée pourra ensuite modifier les paramètres ou algorithmes si nécessaire.

Cette chaîne conserve l'historique complet et limite le risque de mise à jour réglementaire non maîtrisée.

## Lien avec les futures grilles salariales

Les grilles salariales pourront utiliser le même principe : chaque grille ou famille de lignes pourra être reliée à une version de règle et à une référence officielle. Cela permettra de préparer une nouvelle grille avant sa date d'effet, de désactiver l'ancienne à la bonne date et de comparer deux versions sans modifier immédiatement les contrôles existants.

Le versionnement prépare notamment :

- la coexistence de plusieurs grilles ;
- la comparaison entre deux versions de minima ;
- l'audit d'un contrat à une date passée ;
- la justification de la source utilisée pour une ligne salariale.

## Première intégration

La règle `SENIORITY_G1_G6` expose désormais une version initiale `2026-01`, active à compter du 1er janvier 2026 et reliée à `REF_CCNS_SENIORITY_G1_G6_2026`.

Les paramètres de calcul de l'ancienneté ne sont pas modifiés. Cette première version sert uniquement à démontrer la sélection datée et à préparer les futures évolutions.
