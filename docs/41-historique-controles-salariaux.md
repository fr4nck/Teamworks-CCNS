# Historique des contrôles salariaux — TW-055

Les snapshots de contrôle salarial conservent une photographie immuable d'un résultat déjà calculé. Ils servent à relire l'historique sans appeler le contrôleur salarial, sans relire les minima et sans recalculer les règles CCNS ou SMIC.

## Données conservées

Chaque snapshot stocke son identifiant UUID, la date de référence, la date d'exécution, les compteurs de contrats conformes, non conformes et non évaluables, le montant total exact des écarts en `Decimal`, l'auteur facultatif, la version de schéma et les lignes de contrats. Chaque ligne conserve les UUID contrat/salarié, le statut typé, les montants exacts, la classification, la source minimale, le territoire, les motifs d'échec et les anomalies métier. Les libellés d'interface ne sont pas une source de vérité persistée.

## Résultat courant et historique

Le résultat courant appartient à l'audit affiché et peut être filtré visuellement. L'historique enregistre le périmètre complet chargé avant filtre visuel. La consultation de l'historique lit uniquement les tables de snapshots et n'appelle jamais le contrôleur salarial.

## Déduplication

La règle choisie est le refus d'un doublon strictement identique : même date de référence, même ordre de `contract_id`, mêmes statuts, mêmes montants, mêmes échecs et mêmes anomalies. La date seule ne suffit pas à dédupliquer.

## Persistance

Deux tables SQLite idempotentes sont créées :

- `tw_contract_salary_control_snapshots` pour l'en-tête ;
- `tw_contract_salary_control_snapshot_rows` pour les lignes liées par `snapshot_id`.

Les index portent sur `reference_date`, `executed_at`, `contract_id` et `employee_id`. Les `Decimal` sont stockés en texte exact, jamais en `float`. Les UUID, dates, datetimes et Enum sont sérialisés en valeurs stables et désérialisés vers leurs types domaine.

## Création, migration et transaction

`SqliteContractSalaryControlSnapshotRepository.ensure_schema()` peut être rejoué sans perte de données. L'enregistrement de l'en-tête et des lignes est atomique dans une transaction SQLite. En cas d'échec, le rollback de la transaction empêche tout snapshot partiel et toute ligne orpheline.

## Consultation

L'interface `DLG_CCNS_salary_control_history` affiche la liste des snapshots et ouvre le détail des lignes en lecture seule. Elle ne dépend pas du contrôleur salarial.

## Sauvegarde et restauration

La sauvegarde doit inclure les deux tables ajoutées. Pour restaurer l'historique, restaurer d'abord `tw_contract_salary_control_snapshots`, puis `tw_contract_salary_control_snapshot_rows` afin de préserver la relation `snapshot_id`.
