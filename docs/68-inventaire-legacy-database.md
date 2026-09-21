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
sécurité par sous-chaîne identifient les colonnes sensibles. Pour ces
colonnes, `inventory_engine.build_database_inventory` transmet
`sample_limit=0` au port : la requête d'échantillonnage n'est **jamais
émise**, pas seulement filtrée après coup dans le résultat — une colonne
sensible n'est donc jamais lue par SQL ni placée en mémoire pour être
échantillonnée. Seuls les comptages (NULL, vide, zéro, distinct, longueur)
restent calculés pour ces colonnes. Les colonnes BLOB ne sont jamais
échantillonnées non plus, quel que soit leur nom.

Preuve testée à deux niveaux (`tests/test_migration_inventory_engine.py`,
`tests/test_legacy_sqlite_inventory_adapter.py`) : le port reçoit bien
`sample_limit=0` pour une colonne sensible (pas seulement un résultat vide
en sortie), et un `sqlite3.Connection` réel instrumenté par
`set_trace_callback` confirme qu'aucune requête `SELECT DISTINCT ...
LIMIT` n'est exécutée pour cette colonne.

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
query_only`; MySQL : voir « Compatibilité MySQL » ci-dessous — la
stratégie de lecture seule dépend de la version réelle du serveur).
L'outil retourne un code de sortie non nul uniquement en cas d'erreur
technique (fichier absent, connexion impossible, lecture seule non
garantie, arguments incohérents) — jamais parce que des anomalies
`BLOCKING` ont été trouvées : c'est une donnée du rapport, pas un échec
du programme.

## Compatibilité MySQL, y compris un serveur 5.5 historique

`start_transaction(readonly=True)` n'existe côté serveur qu'à partir de
**MySQL 5.6.5**. L'environnement historique de ce dépôt peut encore
compter un serveur **MySQL 5.5** : y appeler `readonly=True` sans
condition provoquerait une erreur Connector/Python, ou pire, laisserait
croire à une garantie de lecture seule qui n'existe pas.

`connect_mysql()` (`infrastructure/persistence/legacy_mysql_inventory_adapter.py`)
négocie donc explicitement la stratégie selon la version réelle,
détectée via `SELECT VERSION()` :

- **Serveur ≥ 5.6.5** : `connection.start_transaction(readonly=True)` est
  utilisé, garantie native du serveur.
- **Serveur < 5.6.5** (MySQL 5.5 compris) : l'adaptateur n'émet lui-même
  aucune commande DDL/DML, mais cela ne suffit pas comme garantie
  automatique. Il vérifie donc, via `SHOW GRANTS FOR CURRENT_USER()`, que
  le compte connecté ne dispose que de privilèges `SELECT`/`USAGE`. Si ce
  n'est pas le cas — ou si les droits ne peuvent pas être lus — la
  connexion est **fermée immédiatement** et une `MySqlReadOnlyGuaranteeError`
  explicite est levée, demandant un compte MySQL strictement SELECT-only.
  Aucune tentative d'écriture n'est jamais faite « pour tester ».

**Statut de qualification : MySQL 5.5 réel NON QUALIFIÉ.** La logique de
négociation ci-dessus est testée unitairement (`tests/test_legacy_mysql_readonly_negotiation.py`,
`tests/test_legacy_mysql_connect_mysql.py`) via des doubles de connexion
DB-API 2.0 et un faux module `mysql.connector` injecté dans `sys.modules` :
aucun serveur MySQL 5.5 réel n'était disponible dans cet environnement
d'exécution pour vérifier le comportement contre un vrai serveur ancien
(négociation de version, réponse effective de `SHOW GRANTS`, comportement
réseau/SSL propre à ce genre de serveur). Ces tests prouvent la logique de
décision, pas une qualification contre l'infrastructure historique réelle.
Avant tout usage contre un MySQL 5.5 de production, une qualification
manuelle sur un serveur réel (ou une copie) reste nécessaire.

La dépendance `mysql-connector-python>=9,<10` (`requirements/python311-core.txt`)
est un choix indépendant de cette PR, qui n'est pas remise en cause ici : le
connecteur cible avant tout MySQL récent. Si une qualification contre un
MySQL 5.5 réel montre que ce connecteur ne s'y connecte pas correctement,
la solution ne serait pas de downgrader la dépendance globale du nouveau
Teamworks, mais, si nécessaire, un environnement Python isolé (ou un outil
autonome) dédié à la lecture ponctuelle de l'ancien serveur — à documenter
séparément le cas échéant plutôt qu'introduire une dépendance durable ici.

## Limites connues

- Le pilote Frais reconstruit `RawTripRow`/`RawReimbursementRow` via un
  `SELECT` complet sur `personnes`, `deplacements`, `remboursements` (pas
  d'agrégation SQL) : c'est volontaire, ces tables sont de taille
  maîtrisée dans le périmètre du pilote, et la logique de réconciliation
  du miroir a besoin des lignes matérialisées.
- L'adaptateur MySQL n'a pas été testé contre un serveur MySQL réel dans
  cette PR (aucun serveur disponible dans l'environnement d'exécution),
  ni contre MySQL 5.5 ni contre une version récente : il est testé via un
  double de connexion DB-API 2.0 et un faux module `mysql.connector`, qui
  vérifient le SQL émis, le mapping des résultats et la logique de
  négociation de version, sans dépendance à mysql-connector-python
  installé. Voir « Compatibilité MySQL » ci-dessus.
- Les valeurs BLOB sont comptées (NULL vs présent) mais pas hachées dans
  cette première version.
