# Inventaire moteur-indépendant d'une base historique

## Objectif

Avant toute migration réelle, répondre avec certitude à :

> Que contient réellement cette base, quelles anomalies contient-elle, et
> pouvons-nous commencer son analyse de migration sans risquer de perdre
> silencieusement une donnée ?

Cet outil ne convertit rien. Il mesure, détecte et rapporte.

## Architecture

```
domain/migration/
  inventory_model.py           structures pures : ColumnKind, ColumnDefinition,
                                ColumnStats, TableInventory, DatabaseInventory,
                                liste des colonnes sensibles
  inventory_port.py            Protocol LegacyDatabasePort (contrat moteur-indépendant)
  inventory_engine.py           orchestration pure : parcourt le port, construit l'inventaire
  finding.py / severity.py      anomalie (code, gravité, table, ligne, message)
  expense_inventory.py          analyse spécialisée du pilote Frais, réutilise
                                 normalize_reimbursement_id / parse_legacy_trip_list /
                                 MirrorAudit d'expense_pilot.py
  expense_inventory_loader.py   charge personnes/deplacements/remboursements
                                 depuis un LegacyDatabasePort générique
  migration_report.py           agrège findings génériques + Frais, décide
                                 READY_FOR_MIGRATION_ANALYSIS / REVIEW_REQUIRED,
                                 rend JSON et Markdown

infrastructure/persistence/
  legacy_inventory_sql.py               gabarits SQL d'agrégation partagés
                                         (COUNT/SUM/MIN/MAX), pas de connexion
  legacy_sqlite_inventory_adapter.py    LegacyDatabasePort via sqlite3 stdlib,
                                         ouverture en lecture seule (mode=ro)
  legacy_mysql_inventory_adapter.py     LegacyDatabasePort via une connexion
                                         DB-API 2.0 injectée ; mysql-connector-python
                                         n'est importé qu'à l'appel de connect_mysql()

tools/
  inventory_legacy_database.py  CLI : ouvre la source, ne l'écrit jamais,
                                 produit JSON et/ou Markdown
```

Le domaine (`domain/migration/`) ne dépend d'aucun moteur SQL, ni de wx,
ni de Qt, ni de `GestionDB`. Les adaptateurs (`infrastructure/persistence/`)
portent seule la dépendance à sqlite3 ou à mysql-connector-python.

## Ce qui est mesuré

Pour chaque table : nombre de lignes, clé primaire détectée, doublons de
clé, lignes sans clé exploitable.

Pour chaque colonne : type déclaré, type classé (affinité façon SQLite :
TEXT/INTEGER/REAL/DATE/DATETIME/BLOB/UNKNOWN), NULL, chaînes vides, zéros,
valeurs distinctes, longueur min/max de texte, min/max numérique, min/max
de date, exemples de valeurs limités en nombre.

Toutes les mesures sont calculées par agrégation SQL côté moteur (COUNT,
SUM(CASE...), MIN, MAX, COUNT(DISTINCT)) : aucune grosse table n'est
chargée intégralement en mémoire pour ces statistiques.

## Confidentialité

Une liste explicite de colonnes sensibles connues
(`DEFAULT_SENSITIVE_COLUMN_NAMES` dans `inventory_model.py` : nom, prénom,
adresse, téléphone, email, mot de passe, IBAN, ...) plus un filet de
sécurité par sous-chaîne empêchent tout échantillonnage de valeur pour ces
colonnes : seuls les comptages sont conservés. Les colonnes BLOB ne sont
jamais échantillonnées, quel que soit leur nom.

## Pilote Frais

Si les tables `personnes`, `deplacements` et `remboursements` sont
présentes, `expense_inventory.analyze_expense_pilot_source` exécute les
contrôles décrits dans `docs/67-pilote-migration-frais.md` directement sur
la base source (sans destination), avec les mêmes codes que
`domain/migration/expense_pilot.py` : `TRIP_PERSON_NOT_FOUND`,
`TRIP_REIMBURSEMENT_NOT_FOUND`, `TRIP_REIMBURSEMENT_PERSON_MISMATCH`,
`LEGACY_TRIP_LIST_UNPARSABLE`, `LEGACY_TRIP_LIST_REFERENCES_UNKNOWN_TRIP`,
`LEGACY_TRIP_LIST_PERSON_MISMATCH`,
`LEGACY_TRIP_LIST_CONFLICTS_WITH_CANONICAL_ASSIGNMENT`,
`LEGACY_TRIP_LIST_REBUILT_FROM_CANONICAL_ASSIGNMENTS`,
`ZERO_REIMBURSEMENT_NORMALIZED_TO_NULL`, ainsi que des codes propres à
l'inventaire (contrôles de valeur : `TRIP_POSTCODE_*`,
`TRIP_DISTANCE_NEGATIVE`, `TRIP_TARIFF_NEGATIVE`, `TRIP_DATE_UNPARSABLE`,
`REIMBURSEMENT_AMOUNT_*`, `TRIP_ID_DUPLICATED`,
`REIMBURSEMENT_ID_DUPLICATED`, ...).

## Gravité

Trois niveaux, indépendants de l'UI : `INFO`, `REVIEW`, `BLOCKING`. La
décision automatique du rapport (`READY_FOR_MIGRATION_ANALYSIS` ou
`REVIEW_REQUIRED`) dépend uniquement de la présence d'au moins une
anomalie `BLOCKING`.

## CLI

```bash
python tools/inventory_legacy_database.py --sqlite copie.sqlite \
    --json artifacts/inventaire.json --markdown artifacts/inventaire.md

python tools/inventory_legacy_database.py \
    --mysql-host db.example.org --mysql-user lecture --mysql-database noethys \
    --mysql-password-env TEAMWORKS_MYSQL_PASSWORD \
    --json artifacts/inventaire.json --markdown artifacts/inventaire.md
```

Le mot de passe MySQL n'est jamais un argument : il est lu dans la
variable d'environnement désignée par `--mysql-password-env`. La base
source n'est jamais ouverte en écriture (SQLite : `mode=ro` + `PRAGMA
query_only`; MySQL : transaction `readonly=True`). L'outil retourne un
code de sortie non nul uniquement en cas d'erreur technique (fichier
absent, connexion impossible, arguments incohérents) — jamais parce que
des anomalies `BLOCKING` ont été trouvées : c'est une donnée du rapport,
pas un échec du programme.

## Limites connues

- Le pilote Frais reconstruit `RawTripRow`/`RawReimbursementRow` via un
  `SELECT` complet sur `personnes`, `deplacements`, `remboursements` (pas
  d'agrégation SQL) : c'est volontaire, ces tables sont de taille
  maîtrisée dans le périmètre du pilote, et la logique de réconciliation
  du miroir a besoin des lignes matérialisées.
- L'adaptateur MySQL n'a pas été testé contre un serveur MySQL réel dans
  cette PR (aucun serveur disponible dans l'environnement d'exécution) :
  il est testé via un double de connexion DB-API 2.0 qui vérifie le SQL
  émis et le mapping des résultats, sans dépendance à
  mysql-connector-python au niveau du module.
- Les valeurs BLOB sont comptées (NULL vs présent) mais pas hachées dans
  cette première version.
