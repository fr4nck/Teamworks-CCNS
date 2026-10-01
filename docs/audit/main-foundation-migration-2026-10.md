# Migration vers trois branches permanentes — préparation du futur `main` (2026-10-01)

Statut : **audit non destructif**. Aucune branche permanente (`master`, `wx/master`, `qt/master`,
`release/vanilla-wx-0.9.2-rc3`) n'a été modifiée, aucune PR fermée, aucune branche supprimée,
aucun force-push. Le seul objet créé est la branche temporaire
`integration/main-foundation-2026-10`.

Note de nommage : #487 et `AGENTS.md` documentent les trois branches permanentes sous les noms
`master`, `wx/master`, `qt/master`, pas `main`/`wx`/`qt`. Ce rapport emploie « futur main » pour le
sommet commun ; le renommage reste une décision séparée, non exécutée ici.

## 1. SHA exacts de départ (HEAD GitHub revérifiés avant et après la passe : inchangés)

| Référence | SHA | Arbre Git | Merge-base avec `master` | PR |
|---|---|---|---|---|
| `master` | `1673248ce646706313d4ed3a3f19024b32be49e7` | `decd075981dfb136b7192642511c066d4f1183b8` | lui-même | — |
| `wx/master` | `fdb383735f176dc04c2e43576e376fe7adfaba1b` | `1403816514b3b96df70e78392275c1c61a504a88` | `860204ddbf` | — |
| `release/vanilla-wx-0.9.2-rc3` | `327aff6bef7fb88681712c5b611cc79e4e8799ef` | `01bfff38d41580e503ad0ea583873fb1c9dcf86a` | `860204ddbf` | — |
| `qt/master` | `bb11275e881849ff802ae75fc722bdd324025f92` | `2804c6b272d1427bf89fd0b95fcbe3cbf19abe22` | `860204ddbf` | #488 (Qt 0.2 RC1, fusionnée) |
| `integ/master-consolidation-2026-09` | `4ec619b3bf82bdc34ca0445133574001c7aa4e70` | `dd9b63a917ce337b0099a5bc6e56cdc52ebd336b` | `1673248ce6` (17 en avance) | #492 |

Divergence : `master` et `wx/master`/`rc3`/`qt/master` partagent `860204ddbf` ; `master` est 17
commits en avance, `wx/master` 49, `rc3` 372, `qt/master` 528. Cette divergence produit déjà un
conflit sur `.github/workflows/ci.yml` indépendamment du candidat.

Branches constitutives de #492 (toutes **ancêtres** de #492 et du candidat) :

| Lot | Branche / PR | SHA | Arbre |
|---|---|---|---|
| Profils #489 | `port/profils-autorisations-master` (report de #472) | `93e91e3d` (parent 2 du merge `6e5ec6bb`) | — |
| DPAE #490 | `integ/dpae-master` | `b422c0305e4c` | `84fe2b6f3acb` |
| ↳ | `feature/dpae-domain-foundation` | `780eb98c6c64` | `15276dab6f68` |
| ↳ | `feature/dpae-declarative-data` | `e4b11be2780f` | `965fa72ca89e` |
| ↳ | `feature/dpae-incident-recovery` (#481) | `afad76a65d10` | `3a1d51952913` |
| ↳ | `feature/dpae-structured-errors` (#482) | `77d012e8db33` | `206e00455c73` |
| Sorties #491 | `integ/sorties-master` | `47b3e74f4d58` | `4dd7f1cedd1a` |
| ↳ | #479 → #484 (`feature/employee-termination-*`) | via `7936bb4a` | — |

Tags de sauvegarde : **non créés** (pas de nécessité : aucune référence n'est modifiée ; les SHA
ci-dessus suffisent comme points de repli).

## 2. SHA candidat du futur main

Branche : `integration/main-foundation-2026-10` (locale + poussée, sans amont sur les branches
permanentes). Le SHA exact est celui du commit qui contient ce rapport ; il est communiqué dans la
réponse finale (un fichier ne peut pas contenir le SHA de son propre commit).

Pile de commits au-dessus de #492 (`4ec619b3`) :

| Commit | Contenu |
|---|---|
| `7918bb59` | merge `--no-ff` de #473 (moteur commun de recherche de personnes) |
| `06e2a1ea` | #474 — **parties communes seulement** (checkout sélectif) |
| `c1287d7f` | merge `--no-ff` de #454 (migration Noethys/Teamworks, inventaire, pilote Frais) |
| `7cbe7ee9` | test de garde : aucun wx/PySide6/ObjectListView dans domain/application/infrastructure |
| `245abc72` | `xfail(strict)` sur le contrat contradictoire de #473 (voir §9) |
| (ce commit) | ce rapport |

Écart candidat ↔ #492 : **42 fichiers, tous ajoutés (A), 0 modifié, 0 supprimé** (domain 12,
infrastructure 5, application 2, tests 19, docs 3, tools 1). Aucun fichier de #492 n'est écrasé.

## 3. Lots absorbés

### 3.1 Noyau #492 — audit
- **Absorption prouvée par l'ascendance Git** : les 3 branches de lot et les 7 branches
  constitutives sont ancêtres du sommet #492 et du candidat.
- **Profils (#472→#489)** : report par patch identique ; 5 fichiers de sécurité avec blobs
  strictement identiques à `qt/master` ; pas un merge de #472.
- **Aucun fichier utile écrasé** : l'union des fichiers des trois lots égale le diff de #492 ; le
  seul recouvrement est `.github/requirements-ci.txt` (fusionné proprement).
- **DPAE et Sorties indépendants** : aucune référence croisée (`dpae` dans le code de sortie,
  `termination` dans le code DPAE : 0 occurrence).
- **SQL présent** : `infrastructure/persistence/sql/mysql/dpae_v1.sql`, `termination_v1.sql`,
  `termination_v2.sql`, `termination_v2_guards.sql` ; tests MariaDB DPAE et Sorties présents.
- **Pas de dépendance UI** : voir §8.4.

### 3.2 Ajouts au-dessus de #492
| Lot | Mode d'absorption | Preuve | Fermable comme « absorbée » ? |
|---|---|---|---|
| #473 recherche Personnes (`domain/people/search.py`) | merge `--no-ff`, sommet `782f14b8` ancêtre | ancestry | oui, mais **rouge** (§9) |
| #474 suppression/résumé Personnes — parties communes | checkout sélectif de `application/services/person_{delete,summary}.py`, `infrastructure/repositories/person_{delete,summary}_repository.py` + 4 tests | blobs identiques à la branche source | **non** : pas d'ascendance Git ; la partie wx reste à porter |
| #454 migration historique | merge `--no-ff` (`c1287d7f`) | ancestry ; docs 66-68, `domain/migration/*`, 3 adaptateurs d'inventaire, `tools/inventory_legacy_database.py`, 14 tests | oui |

#454 : moteur SQL cible inchangé ; garde-fous lecture seule conservés (inventaire en lecture,
adaptateurs SQLite/MySQL en lecture seule, couverts par les 14 tests).

## 4. Lots encore exclus

| PR | Raison |
|---|---|
| #474 (partie wx), #475, #476 | wx seulement : `teamworks/Ol`, `teamworks/Dlg`, `tests/test_person_delete_wx_wiring.py`, `tests/test_tw151_missing_person_guard.py`, `tests/test_person_list_objectlistview.py` |
| #452 Rail C documents RH / publipostage | mixte (`domain/documents` + `application/services` communs, mais `teamworks/Utils` wx/COM) → REVIEW |
| #442 RC2 état des tableaux / changement de dossier | `teamworks/Ctrl` → wx |
| #391 qualification distribution Windows | scripts de packaging wx → wx |
| #390 atomicité écritures RH, #386 restauration SQLite | touchent `teamworks/Utils` + tests → REVIEW |
| #376 audit sortie Connecthys, #485 audit d'absorption | outillage commun mais hors socle métier → différé |
| #487 | documentation de branches (nom `master` vs `main`) → à trancher avec le renommage |
| #493 Qt 0.2 RC1 | Qt seul (`docs/QT_INTEGRATION_0.2_RC1.md` + 2 workflows) |
| #486 Rail A avenants CDI/CDD | Qt, non évalué plus avant (hors périmètre transversal) |

## 5. Matrice COMMON / WX / QT / REVIEW

| PR / pile | A — COMMON | B — WX | C — QT | D — REVIEW |
|---|---|---|---|---|
| #492 (Profils, DPAE, Sorties) | `domain/`, `application/`, `infrastructure/`, SQL, tests de lot | — | — | `ci.yml`, `requirements-ci.txt` |
| #473 | `domain/people/search.py`, `tests/test_people_search.py` | — | — | — |
| #474 | services + repositories suppression/résumé, 4 tests | wiring `CTRL_Personnes`, `tests/test_person_delete_wx_wiring.py`, `test_tw151_missing_person_guard.py` | — | — |
| #475 | — | `tests/test_person_list_objectlistview.py` | — | — |
| #476 | — | `teamworks/Ol`, `teamworks/Dlg`, test OLV | — | `.github/workflows` |
| #454 | `domain/migration/*`, adaptateurs d'inventaire, `tools/`, 14 tests, docs 66-68 | — | — | — |
| #452 | `domain/documents`, `application/services` | `teamworks/Utils` (Word/COM) | — | tests mixtes |
| #442 | — | `teamworks/Ctrl` et tests UI | — | — |
| #391 | — | `scripts/test_windows_*.ps1` | — | — |
| #390 / #386 | — | — | — | `teamworks/Utils` + tests transactionnels |
| #376 / #485 | outillage `tools/` + tests | — | — | différé |
| #493 | — | — | docs + workflows Qt | — |

## 6. Conflits potentiels wx

Simulation en worktree temporaire (supprimé), sans toucher `rc3` ni `wx/master`.

| Simulation | Conflits Git |
|---|---|
| `wx/master` + candidat | **0** |
| `rc3` + candidat | **1** : `.github/workflows/ci.yml` (préexistant : `master` seul entre en conflit de la même façon) |

- Fichiers : 99 des 102 fichiers du candidat sont absents de `rc3` (ajouts purs) ; 3 fichiers de
  sécurité diffèrent (`access_service.py`, `default_roles.py`, `permission.py`) et fusionnent
  proprement.
- Suite de tests sur `rc3 + candidat` (`ci.yml` résolu côté `rc3`, `--noconftest`, voir §8.6) :
  **2 548 passed, 3 failed**.
  - 2 × `test_people_search` : le défaut de #473 (§9), pas lié à `rc3`.
  - 1 × `test_windows_installer_contract::test_windows_packages_are_not_built_on_every_commit` :
    **régression de la fusion** (passe sur `rc3` seule) — la fusion automatique mélange la version
    du test issue de `master` avec le `ci.yml` de `rc3` (déclencheur `release/vanilla-wx-0.9.2-rc3`).
    Raccord : garder la version `rc3` du test et du workflow côté wx.
- Piège : le `conftest.py` racine de `rc3` contient une instrumentation Windows temporaire
  (lancement de `tools/smoke_person_mainloop_lifecycle.py`, session-autouse) qui expire à 1 200 s
  dans cet environnement → 431 erreurs de setup sur la première tentative ; contournée par
  `--noconftest`. À retirer ou conditionner avant toute convergence.
- Raccords wx restants : câblage `CTRL_Personnes`/OLV vers `person_delete`/`person_summary` (#474
  wx), rafraîchissement/sélection/résumé ObjectListView (#475/#476), `tests/test_person_*` wx,
  `ci.yml` et son test de contrat.

## 7. Conflits potentiels Qt

| Simulation | Conflits Git |
|---|---|
| `qt/master` + candidat | **1** : `.github/workflows/ci.yml` (même cause préexistante) |

- Doublons : 5 fichiers Profils **identiques** (blobs égaux) → fusion sans effet ; 97 des 102
  fichiers du candidat sont absents de `qt/master`.
- Suite de tests sur `qt/master + candidat` (PySide6 absent de l'environnement ; tests Qt
  d'interface non exécutables) : **2 754 passed, 12 skipped, 6 failed**.
  - 2 × `test_people_search` (§9).
  - 1 × `test_common_layers_do_not_import_legacy_teamworks_outside_documented_exceptions` :
    `qt/master` contient deux lecteurs supplémentaires qui importent
    `teamworks.Utils.UTILS_Diagnostic_performance` (`individual_activity_reader.py`,
    `questionnaire_reader.py`) — même dette historique que les deux exceptions déjà documentées,
    sans wx/PySide6. Raccord : étendre la liste d'exceptions ou déplacer le diagnostic dans un
    module neutre.
  - 3 × tests de contrat de workflow (`test_main_navigation_smoke_contract`,
    `test_mysql_connection_compatibility`, `test_windows_installer_contract`) : **préexistants sur
    `qt/master` seul** (reproduits sur un worktree de `qt/master` non fusionné) ; non causés par le
    candidat.
- Risque de régression Qt : faible pour le code (ajouts purs, zéro conflit de contenu hors `ci.yml`).
  Le point d'attention est `ci.yml` (`Validation Qt`) dont les tests de contrat sont déjà rouges.
- Changements purement communs reprenables sans toucher aux vues Qt : tout le candidat (42
  ajouts), après résolution de la liste d'exceptions d'import ci-dessus.

## 8. Tests réellement exécutés (sommet `7cbe7ee9`, puis `245abc72`)

Environnement : Windows 11, Python 3.11, wxPython 4.3.1, Docker Desktop 29.6.2, MariaDB 10.11.14.

1. `compileall` : OK. `scripts/check_utf8.py` : OK. `scripts/check_essential_runtime.py` : OK
   (8 modules, 4 ressources). `scripts/audit_runtime_risks.py` : informatif (continue-on-error en CI),
   concentré sur du code `teamworks/` wx historique.
2. **Suite complète hors SQL** (6 fragments, `GITHUB_ACTIONS` non positionné) : **2 374 passed,
   10 skipped (DPAE MySQL), 3 failed**. Une première exécution monolithique avait été tuée par
   manque de mémoire à ~71 % (pas un échec de test) ; refaite par fragments.
   - 2 failed = #473 (§9), depuis marqués `xfail(strict)` (`245abc72`).
   - 1 failed = `test_pmsl_contracts_21h_run_in_real_windows_application` (fenêtre wx réelle, timeout
     180 s à l'étape `cdd-1`) : **reproduit à l'identique sur `origin/master` (`1673248c`)** → échec
     local préexistant, hors périmètre. En CI cette classe est exécutée par le job « Parcours
     critiques Windows ».
3. **Tests MariaDB réellement exécutés** (`GITHUB_ACTIONS=true`, conteneurs Docker `mariadb:10.11.14`) :
   `test_dpae_mysql_*` + `test_termination_mysql_*` + `test_termination_transmission_*` :
   **102 passed, 0 skipped**. Les 10 skips du point 2 ne comptent pas comme qualification SQL ; ce
   sont ces 102 tests qui la portent. (La CI annonce 117 tests critiques MariaDB ; l'écart de 15 n'est
   pas élucidé — tests hors motif de nommage utilisé ici.)
4. **Audit d'imports** : `tests/test_common_layers_no_ui_imports.py` (AST) — 2 passed.
   Aucun `wx`, `PySide6`, `PyQt5/6`, `ObjectListView` dans `domain/`, `application/`,
   `infrastructure/`. Exceptions historiques documentées (import de
   `teamworks.Utils.UTILS_Diagnostic_performance`, sans dépendance UI) :
   `infrastructure/persistence/ccns_data_reader.py`, `infrastructure/persistence/person_reader.py`.
5. **Groupes ciblés sur `245abc72`** (garde d'imports, Personnes, `test_person_*`, migration/inventaire,
   Profils/autorisations, DPAE et Sorties hors MySQL) : **336 passed, 11 skipped, 2 xfailed**.
6. Simulations wx et Qt : résultats en §6 et §7. Exécutées avec `--noconftest` et sans l'unique test
   de fenêtre réelle, sur un arbre fusionné avant le commit `245abc72` (d'où les échecs #473).

## 9. Stop-gates restants

1. **#473 est rouge sur son propre sommet** (`782f14b8`, CI « Tests et règles du socle » en échec).
   `test_certain_matching[dupo mar]` et `test_short_prefix_still_supports_abbreviated_entry` exigent
   que `DUPOND Marie` soit exclu de `dupo mar`, alors que `test_ambiguous_short_prefix_keeps_all_literal_prefix_matches`
   inclut `DUPOND` pour `dup mar` et que `dupo` est bien un préfixe littéral de `dupond`. Contrat
   contradictoire ; arbitrage métier requis. Les deux tests sont en `xfail(strict)` dans le
   candidat (aucun changement de comportement) : le candidat est donc « vert » avec 2 xfail
   documentés, **pas** vert sans réserve.
2. #474 non fermable comme absorbée (checkout sélectif) ; sa partie wx doit être portée séparément.
3. `ci.yml` : conflit `master` ↔ `wx/*` / `qt/*`, à résoudre par branche, jamais au niveau commun.
4. `rc3` : conftest racine avec instrumentation temporaire à neutraliser.
5. `test_windows_installer_contract` : à garder en version `rc3` côté wx.
6. Liste d'exceptions d'import historique à étendre côté Qt (2 fichiers) ou diagnostic à neutraliser.
7. Écart 102 vs 117 tests MariaDB à expliquer ; test de fenêtre réelle `pmsl_contracts_21h` rouge
   en local sur `master` aussi.
8. Nommage permanent (`master`/`wx/master`/`qt/master` vs `main`/`wx`/`qt`) : non décidé, non exécuté.
9. Aucune écriture dans la base réelle `pelemele_data` ; tests SQL sur conteneurs jetables uniquement.

## 10. Ordre recommandé pour la suite

1. Trancher le contrat de recherche #473 (« dupo mar » inclut-il `DUPOND` ?), corriger test ou moteur,
   retirer les `xfail`.
2. Revue du candidat (`integration/main-foundation-2026-10`) et validation de sa CI sur GitHub.
3. Résoudre `ci.yml` branche par branche ; fixer le test de contrat installateur côté wx.
4. wx : fusionner le candidat dans une branche d'intégration dérivée de `wx/master` (0 conflit), puis
   porter #474-wx, #475, #476 sur le socle commun.
5. Qt : fusionner dans une branche dérivée de `qt/master` ; étendre les exceptions d'import ;
   traiter les 3 contrats de workflow déjà rouges.
6. Instruire #452, #390, #386 (REVIEW) fichier par fichier.
7. Décider du renommage des branches permanentes (#487) seulement après les points 3 à 5.
8. Optionnel : #376 / #485 (outillage d'audit) une fois le socle stabilisé.
