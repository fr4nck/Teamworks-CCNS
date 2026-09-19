# Organisation du dépôt

Vue d'ensemble à l'usage des développeurs et des agents IA travaillant sur le dépôt. Pour les concepts métier, voir [Architecture — vue d'ensemble](../architecture/vue-ensemble.md).

## Dossiers racine

| Dossier | Rôle réel observé |
|---|---|
| `teamworks/` | application historique wxPython (fork Noethys/Teamworks) : `Dlg/` (dialogues), `Ctrl/` (contrôleurs/panneaux), `Utils/` (utilitaires, dont crash/sauvegarde/thème), `Ol/` (listes ObjectListView), `CcnsCore/` (moteur métier CCNS du fork), `GestionDB.py`/`UpgradeDB.py` (accès et migration de schéma), `Teamworks_core.py`/`Teamworks.py` (point d'entrée et fenêtre principale). Contient aussi des fichiers `.bak-phoenix`/`.bak-*` résiduels de la migration Python 2→3, à ne pas traiter comme du code actif. |
| `domain/` | modèle métier pur, sans dépendance wx ni base de données : `access/`, `security/` (habilitations, expérimental — voir [Utilisateurs et habilitations](../administration/utilisateurs.md)), `contracts/`, `convention/` (grilles CCNS/SMIC), `employment/`, `engine/`, `missions/`, `people/`, `planning/` (non branché à l'UI — voir [Présences et planning](../utilisation/presences-planning.md)), `qualifications/`, `regulatory/`, `documents/`, `repositories/` (interfaces/DTO). |
| `application/` | cas d'usage et services qui orchestrent `domain/` : `bootstrap/`, `control/` (contrôle salarial CCNS/CEE), `presentation/`, `security/`, `services/`. |
| `infrastructure/` | implémentations concrètes des interfaces de `domain/repositories` (lecture SQL, ex. `CcnsDataReader`), encore appuyées sur `GestionDB` — voir `docs/40-couche-acces-donnees.md`. |
| `migrations/` | scripts SQL numérotés pour le schéma moderne CCNS, distinct du schéma historique Teamworks. |
| `packaging/` | script Inno Setup (`windows/Teamworks-CCNS.iss`) réellement utilisé par la CI pour l'installateur Windows. |
| `tests/` | plusieurs centaines de fichiers `test_*.py`, très centrés sur le moteur CCNS (contrats, salaires, audit, grilles), avec un socle secondaire pour la fiche personne, le recrutement et le planning. |
| `tools/` | scripts d'audit/migration ponctuels et scripts de smoke-test appelés par la CI. |
| `requirements/` | dépendances Python applicatives (`python311-core.txt`, `python311-optional.txt`) et documentaires (`docs.txt`), séparées du `requirements.txt` racine utilisé par le build Windows. |

## Deux moteurs CCNS à ne pas confondre

- Un **aperçu en temps réel** dans l'assistant de création de contrat (`application/control/ccns_contract_compliance.py`), basé sur une grille salariale figée dans le code.
- Un **moteur d'audit en lot** (`teamworks/CcnsCore/audit_contracts_ccns.py`), qui relit toutes les grilles stockées en base et peut donc différer légèrement de l'aperçu du premier.

Voir [Contrats, CCNS et CEE](../utilisation/contrats-ccns-cee.md) pour la description utilisateur, et le code cité pour le détail technique.

## Voir aussi

[Démarrer en développement](demarrer-dev.md) · [Tests et CI](tests-ci.md) · [Architecture — vue d'ensemble](../architecture/vue-ensemble.md)
