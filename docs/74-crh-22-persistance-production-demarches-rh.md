# CRH-22 — persistance de production des démarches RH

**Date : 1er septembre 2026**

## Objet

CRH-22 raccorde les dossiers de démarches RH définis par CRH-03 et les événements d'audit CRH-04 à la base Teamworks active, sans encore créer l'écran wxPython du cockpit.

Le lot fournit `TeamworksHrCasesRepository`, compatible avec la frontière `GestionDB` déjà utilisée par Teamworks en local SQLite comme en réseau MySQL/MariaDB.

## Schéma additif

Le composant `hr_cases_runtime`, version 1, ajoute uniquement :

- `tw_hr_cases` ;
- `tw_hr_case_expected_documents` ;
- `tw_hr_audit_events` ;
- `tw_hr_audit_fields` ;
- des index ciblés sur statut/échéance, sujet, organisme et cible d'audit.

Le registre partagé `tw_hr_schema_versions` est créé si nécessaire et reste compatible avec les autres composants Connexions RH.

Aucune table historique de salariés ou contrats n'est modifiée et aucune clé étrangère n'est créée vers les données historiques.

## Dossiers RH

Les dossiers sont des projections courantes : `save_case()` crée ou actualise un dossier et remplace atomiquement la liste de pièces attendues décrite par le domaine.

La persistance conserve séparément :

- le statut métier ;
- le statut technique d'échange ;
- le sujet personne/structure ;
- l'organisme ;
- dates d'ouverture et d'échéance ;
- type de démarche ;
- source, résultat et commentaire ;
- pièces attendues et caractère obligatoire déclaré.

Le repository ne déduit aucune conformité ni pièce réellement manquante.

## Journal d'audit

Les événements sont append-only. `append_event()` refuse tout doublon de `event_id` dans une même structure logique et aucune API de mise à jour ou suppression d'événement n'est exposée.

Les garde-fous CRH-04 restent applicables : les champs d'audit sont construits par le domaine, qui refuse les clés manifestement secrètes ou médicales.

## Compatibilité et sécurité

Le lot :

- n'utilise pas `ON CONFLICT`, `INSERT OR REPLACE` ou DDL incompatible avec les chemins réseau historiques ;
- passe par les helpers SQL partagés de `TeamworksHrConnectionsRepository` pour l'adaptation `?` / `%s` ;
- n'importe pas `sqlite3` dans l'adaptateur de production ;
- ne stocke aucun credential, jeton, cookie ou contenu médical ;
- n'effectue aucun accès réseau, aucune ouverture de navigateur et aucun scraping.

## Suite

CRH-21 dispose désormais d'un port de lecture pouvant être satisfait par cet adaptateur. Le lot suivant pourra composer un runtime de cockpit avec :

1. identité stable de structure CRH-17A ;
2. `TeamworksHrCasesRepository` ;
3. `TeamworksHrConnectionsRepository` pour la résolution des organismes ;
4. `HrCaseDashboardService` CRH-21 ;
5. puis seulement un écran wxPython de consultation et d'action.

La qualification manuelle Windows de la release reste indépendante de ce chantier satellite. Aucune fusion automatique n'est prévue.
