# CRH-22 — Persistance Teamworks des démarches RH et du journal d'audit

## Statut

Lot empilé sur **CRH-21**. Il remplace, pour les dossiers `HrCase` et le journal `HrAuditEvent`, la persistance SQLite de qualification CRH-09 par un adaptateur de production utilisant la base Teamworks active via `GestionDB`.

La validation manuelle Windows de **0.9.1b** reste un verrou de release distinct. CRH-22 ne doit pas être confondu avec le build 0.9.1b déjà qualifié automatiquement et aucune fusion automatique n'est demandée.

## Objectif

Les modèles CRH-03 et CRH-04 existent déjà mais leurs dossiers et événements n'étaient pas encore raccordables à la base de production. Le futur cockpit structure ne doit pas dépendre d'un fichier SQLite parallèle.

`TeamworksHrCasesRepository` apporte donc la frontière de production pour :

- les dossiers de démarches RH ;
- leurs pièces attendues sous forme de métadonnées ;
- le statut métier et le statut technique d'échange, conservés séparément ;
- les échéances ;
- le journal d'audit append-only ;
- les métadonnées d'audit déjà filtrées par le domaine CRH-04.

## Schéma additif

Le lot ajoute uniquement :

- `tw_hr_cases` ;
- `tw_hr_case_expected_documents` ;
- `tw_hr_audit_events` ;
- `tw_hr_audit_fields` ;
- une entrée de version `hr_cases_runtime` dans `tw_hr_schema_versions`.

Aucune table historique n'est modifiée et aucune clé étrangère n'est créée vers les salariés, contrats ou autres données anciennes de Teamworks.

Le composant de version est indépendant du composant `hr_connections_runtime` de CRH-16. Une évolution des dossiers pourra ainsi être migrée sans faire croire qu'une modification du suivi salarié est nécessaire.

## Compatibilité SQLite / MySQL

Comme CRH-16, l'adaptateur utilise `db.isNetwork` pour traduire les paramètres :

- `?` pour SQLite ;
- `%s` pour MySQL.

Les constructions spécifiques à SQLite (`ON CONFLICT`, `INSERT OR IGNORE`, `REPLACE INTO`, `PRAGMA`) sont exclues du chemin de production.

La création du schéma et des index est idempotente.

## Dossiers RH

`save_case()` conserve la clé `(structure_ref, case_id)`, met à jour le dossier dans une transaction et remplace sa collection de pièces attendues uniquement après validation de l'objet de domaine.

`list_cases()` charge les en-têtes et les pièces par ensembles afin d'éviter un N+1 par dossier.

Le repository ne décide jamais qu'un dossier est conforme ou accepté. Les transitions restent celles de `HrCase` : un statut technique d'échange réussi ne vaut pas acceptation métier.

## Journal append-only

`append_event()` effectue uniquement un `INSERT` d'événement puis de ses champs. Il n'existe aucune opération `update`, `delete` ou `remove` publique sur le journal.

Une collision d'identifiant déclenche `DuplicateTeamworksHrAuditEventError` au lieu d'écraser l'événement existant.

Les filtres de lecture peuvent cibler la nature et la référence d'une cible, ce qui préparera l'historique d'un dossier dans le futur cockpit.

## Sécurité et sobriété

Ce lot ne stocke :

- aucun mot de passe, token, cookie, certificat ou clé privée ;
- aucun payload réseau ;
- aucun document lui-même ;
- aucune donnée médicale ajoutée par ce chantier.

Les `HrAuditField` continuent d'appliquer les garde-fous CRH-04 contre les clés manifestement secrètes ou médicales.

## Tests

Les tests couvrent :

- schéma idempotent et versionné ;
- round-trip d'un dossier et de ses pièces ;
- modification sans duplication ;
- isolation multi-structures ;
- journal append-only ;
- collision d'identifiant sans écrasement ;
- filtres par cible ;
- contrat SQLite/MySQL ;
- absence de SQL spécifique SQLite, réseau, wxPython et clés étrangères historiques.

## Suite

Une fois ce lot qualifié, le prochain incrément pourra construire un service de projection et un **cockpit des démarches RH** de structure : à faire, échéances, anomalies, régularisations et retours, sans introduire d'automatisation de portail non officielle.
