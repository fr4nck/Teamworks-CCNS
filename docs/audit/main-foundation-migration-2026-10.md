# Migration vers trois branches permanentes — préparation du futur `main` (2026-10-01)

Statut : **audit non destructif, qualification locale complète ; qualification GitHub : voir §8.8**. Aucune branche permanente (`master`, `wx/master`, `qt/master`,
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

Branche : `integration/main-foundation-2026-10` (poussée, sans amont sur les branches permanentes).

- HEAD de départ de la passe de correction : `1f97e18c11bcf082acb15f295e165a1483c01010`.
- Commit de correction #473 : `e1a0b44999df35cab72878c49737889df48dd823` (sommet de code qualifié
  localement, §8).
- HEAD final : le commit qui contient ce rapport (un fichier ne peut pas contenir le SHA de son
  propre commit) ; il est communiqué dans la réponse finale. Depuis `e1a0b449`, seul ce rapport change.

Pile de commits au-dessus de #492 (`4ec619b3`) :

| Commit | Contenu |
|---|---|
| `7918bb59` | merge `--no-ff` de #473 (moteur commun de recherche de personnes) |
| `06e2a1ea` | #474 — **parties communes seulement** (checkout sélectif) |
| `c1287d7f` | merge `--no-ff` de #454 (migration historique, inventaire, pilote Frais) |
| `7cbe7ee9` | test de garde : aucun wx/PySide6/ObjectListView dans domain/application/infrastructure |
| `245abc72` | `xfail(strict)` provisoire sur #473 (première passe) |
| `1f97e18c` | rapport de première passe (HEAD de départ de la passe de correction) |
| `e1a0b449` | #473 : contrat de saisie abrégée fixé, `xfail` supprimés (§3.3) |
| (HEAD final) | ce rapport mis à jour |

Écart code candidat ↔ #492 : **42 fichiers, tous ajoutés (A), 0 modifié, 0 supprimé** (domain 12,
infrastructure 5, application 2, tests 19, docs 3, tools 1), auxquels s'ajoutent ce rapport et la
correction de `tests/test_people_search.py`. Aucun fichier de #492 n'est écrasé.

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
| #473 recherche Personnes (`domain/people/search.py`) | merge `--no-ff`, sommet `782f14b8` ancêtre | ancestry | oui ; contrat de recherche fixé en §3.3, tests verts sans `xfail` |
| #474 suppression/résumé Personnes — parties communes | checkout sélectif de `application/services/person_{delete,summary}.py`, `infrastructure/repositories/person_{delete,summary}_repository.py` + 4 tests | blobs identiques à la branche source | **non** : pas d'ascendance Git ; la partie wx reste à porter |
| #454 migration historique | merge `--no-ff` (`c1287d7f`) | ancestry ; docs 66-68, `domain/migration/*`, 3 adaptateurs d'inventaire, `tools/inventory_legacy_database.py`, 14 tests | oui |

### 3.3 #473 — contrat de recherche Personnes (résolu)

- **Algorithme inchangé** (`domain/people/search.py` identique au sommet `782f14b8` de #473).
- **Contrat retenu** : « une saisie abrégée par préfixe (tous les tokens de la saisie ≤ 4 caractères)
  retourne tous les candidats dont les tokens commencent littéralement par les préfixes saisis ».
  Une saisie complète (`dupont marie`) reste exacte : `DUPOND Marie` n'est pas une correspondance
  certaine.
- **Modification exacte** (`tests/test_people_search.py`, commit `e1a0b449`) : suppression de
  `CONTRACT_CONFLICT_473` et des `xfail(strict)` ; l'attendu de `dupo mar` devient
  `{P01, P02, P03, P04, P05}` (`DUPOND Marie` = P04 inclus : `dupond` commence par `dupo`, `marie` par
  `mar`) dans `test_certain_matching` et `test_short_prefix_still_supports_abbreviated_entry` ; le contrat
  est documenté par un commentaire de 3 lignes. Le garde `dupont marie` sans P04 est conservé.
- Résultat : `tests/test_people_search.py` **63 passed**, 0 xfail, 0 skip.

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
| #376 audit de sortie du portail, #485 audit d'absorption | outillage commun mais hors socle métier → différé |
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
  **2 548 passed, 3 failed** (simulation faite avant la correction #473).
  - 2 × `test_people_search` : le défaut de #473, corrigé depuis (§3.3), pas lié à `rc3`.
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
  d'interface non exécutables) : **2 754 passed, 12 skipped, 6 failed** (avant la correction #473 ; les 2 échecs de recherche n'existent plus).
  - 2 × `test_people_search` : défaut de #473, corrigé depuis (§3.3) ; simulation faite avant la correction.
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

## 8. Qualification exécutée sur le sommet de code `e1a0b449`

Environnement : Windows 11, Python 3.11, wxPython 4.3.1, Docker Desktop 29.6.2, MariaDB 10.11.14.
Worktree propre détaché sur `e1a0b44999df35cab72878c49737889df48dd823`. La suite a été fragmentée en
6 parties (une première exécution monolithique avait été tuée par manque de mémoire ; ce n'est pas un
échec de test, tous les fragments équivalents sont exécutés).

### 8.1 Statique
| Contrôle | Résultat |
|---|---|
| `python -m compileall -q domain application infrastructure migrations tools tests scripts teamworks` | OK |
| `python scripts/check_utf8.py` | OK |
| `python scripts/check_essential_runtime.py` | OK (8 modules, 4 ressources) |
| `scripts/audit_runtime_risks.py` | informatif (continue-on-error en CI), code `teamworks/` wx historique |

### 8.2 Garde d'imports — 2 passed
`tests/test_common_layers_no_ui_imports.py` (analyse AST) : aucun `wx`, `PySide6`, `PyQt5/6`,
`ObjectListView` dans `domain/`, `application/`, `infrastructure/`. Exceptions historiques, minimales
et explicitement listées (import de `teamworks.Utils.UTILS_Diagnostic_performance`, sans dépendance UI) :
`infrastructure/persistence/ccns_data_reader.py`, `infrastructure/persistence/person_reader.py`. Aucune
exception ajoutée dans cette passe.

### 8.3 Groupes ciblés
| Groupe | Fichiers | Résultat |
|---|---|---|
| Recherche Personnes | `tests/test_people_search.py` | 63 passed |
| Profils / autorisations | `test_profile_permissions`, `test_portail_permission_alignment` et `test_*permission*/security*/access*/profil*` | 49 passed |
| Suppression/résumé Personnes (commun) | `test_person_delete*`, `test_person_summary*` hors wx | 23 passed |
| Migration / inventaire | `test_*migration*`, `test_*inventory*` | 120 passed |
| DPAE hors SQL | `test_dpae*` hors `test_dpae_mysql_*` | 58 passed, 25 subtests |
| Sorties hors SQL | `test_termination*` hors fichiers MariaDB | 42 passed |
| DPAE + Sorties MariaDB | voir §8.4 | 102 passed |

### 8.4 Tests MariaDB — décompte exact et écart 102 / 117

Commande reproductible (depuis la racine du dépôt ; Docker requis, `mariadb:10.11.14` démarré par
`tests/conftest.py` et `tests/termination_mysql_support.py` uniquement si `GITHUB_ACTIONS=true`) :

```
GITHUB_ACTIONS=true python -m pytest -q -rs \
  tests/test_dpae_mysql_*.py \
  tests/test_termination_mysql_concurrency.py tests/test_termination_mysql_repository.py \
  tests/test_termination_transmission_concurrency.py tests/test_termination_transmission_mysql.py
```
→ **102 collectés, 102 exécutés, 102 passed, 0 skipped.**

| Fichiers | Tests |
|---|---|
| 11 × `test_dpae_mysql_*.py` (dont `schema_contract` : 3, lecture de fichier sans SQL) | 36 |
| `test_termination_mysql_concurrency.py` | 9 |
| `test_termination_mysql_repository.py` | 20 |
| `test_termination_transmission_concurrency.py` | 11 |
| `test_termination_transmission_mysql.py` | 26 |
| **Total** | **102** |

**Les « 117 tests critiques » (corps de #492 : DPAE SQL, erreurs structurées, service v2, Sorties,
Profils) = ces 102 + 15 tests non-SQL** (tests en mémoire, sans connexion MariaDB, sans dépendance aux
variables `*_MYSQL_*`) :

| Fichier | Tests | Détail |
|---|---|---|
| `tests/test_dpae_service_v2.py` | 4 | snapshot H1 immuable après changement de source vers H2 ; rejeu sans resolver ni nouveau snapshot ; nouvelle préparation H1→H2 crée S2 sans muter S1 ; retry de soumission réutilise S1 |
| `tests/test_dpae_structured_errors.py` | 3 | resolver manquant : code stable ; contrat resolver violé : code stable sans fuite de payload ; compatibilité legacy RuntimeError/ValueError |
| `tests/test_profile_permissions.py` | 5 | catalogue complet ; vue profil ; libellés français centraux ; profils par défaut ; retrait de permission sans toucher l'historique |
| `tests/test_portail_permission_alignment.py` | 3 | utilisateur inactif sans permission ; union de profils multiples ; libellé de profil sans permission implicite |
| **Total** | **15** | |

Vérification : la commande ci-dessus, complétée de
`tests/test_dpae_service_v2.py tests/test_dpae_structured_errors.py tests/test_profile_permissions.py tests/test_portail_permission_alignment.py`,
donne **117 collectés, 117 exécutés, 117 passed, 0 skipped**. L'écart n'est donc ni un test perdu, ni
renommé, ni déplacé : c'est un périmètre différent (102 = tests touchant une base MariaDB réelle ;
117 = ces 102 + 15 tests applicatifs/sécurité). Il n'existe pas de test SQL de Profils.

**Sans `GITHUB_ACTIONS=true`** (poste local sans base) : seuls 69 des 102 tests sont collectés ; les
33 tests de 10 modules `test_dpae_mysql_*` sont écartés par un `pytest.skip(allow_module_level=True)`
(1 skip par module, « base MySQL DPAE (de recette) non configurée », visibles avec `-rs`) et les 59 tests
Sorties sont skippés (« base MySQL/MariaDB termination non configurée »). Un run local sans la variable
**n'est pas une qualification SQL** ; le décompte 102 n'est reproductible qu'avec `GITHUB_ACTIONS=true`.

### 8.5 Suite générale complète (hors fichiers MariaDB, 6 fragments, `GITHUB_ACTIONS` non positionné)
| Fragment | Résultat |
|---|---|
| 00 | 345 passed |
| 01 | 376 passed, 10 skipped (modules DPAE MySQL, voir §8.4), 25 subtests |
| 02 | 456 passed |
| 03 | 557 passed, **1 failed** (§8.6) |
| 04 | 316 passed |
| 05 | 326 passed |
| **Total** | **2 376 passed, 10 skipped, 1 failed** |

À ajouter : les 102 tests MariaDB du §8.4 (**102 passed**, `GITHUB_ACTIONS=true`). Aucun `xfail` ni
nouveau `skip` dans le candidat.

### 8.6 Unique échec : test de fenêtre réelle wx (préexistant, hors périmètre)
test de fenêtre réelle `…::test_*_run_in_real_windows_application` (fichier d'UAT « contrats 21h ») :
timeout de la fenêtre wx réelle (`return_code=124`) en local. Reproduit à l'identique sur
`origin/master` (`1673248c`) lors de la passe précédente : échec d'environnement local, non causé par
le candidat. En CI il est couvert par le job « Parcours critiques Windows ». **Il n'est pas masqué : le
candidat n'est donc pas déclaré « 100 % vert en local ».**

### 8.7 Simulations wx et Qt
Résultats en §6 et §7 (exécutées avant la correction #473, avec `--noconftest`, sans le test de fenêtre
réelle). Non rejouées : les branches wx et Qt ne sont pas touchées.

### 8.8 GitHub Actions
**Déclenchement.** `.github/workflows/ci.yml` (seul workflow) se déclenche sur `pull_request` vers
`master`, `push` sur `master` / tags `v*`, et `workflow_dispatch`. Un `push` sur
`integration/main-foundation-2026-10` ne déclenche donc **aucun** workflow (explication de l'absence de
run sur `1f97e18c`). La CI n'a pas été modifiée. Déclencheur sûr prévu par le dépôt retenu :
`workflow_dispatch` sur la branche, avec les entrées par défaut (`cleanup_actions=none`,
`build_windows=false`, `build_docs=false`) : jobs « Tests et règles du socle » et « Parcours critiques
Windows ». Aucune PR n'a été ouverte, rien n'est fusionné.

Résultat : voir ci-dessous (renseigné après exécution).

## 9. Stop-gates restants

Levés dans cette passe : contrat #473 (§3.3), écart 102/117 (§8.4), `xfail`.

Ouverts :
1. #474 non fermable comme absorbée (checkout sélectif, pas d'ascendance) ; sa partie wx doit être portée.
2. `ci.yml` : conflit `master` ↔ `wx/*` / `qt/*`, à résoudre par branche, jamais au niveau commun.
3. Raccords **wx** non traités : `ci.yml` ; contrat de packaging RC3 (`test_windows_installer_contract`,
   à garder en version `rc3` côté wx) ; `conftest.py` racine de `rc3` et son instrumentation de fenêtre
   réelle (session-autouse, timeout 1 200 s) ; câblage wx de #474, #475, #476.
4. Raccords **Qt** non traités : résolution de `ci.yml` ; dette des imports de diagnostic
   (`teamworks.Utils.UTILS_Diagnostic_performance` dans 2 lecteurs de `qt/master` : étendre les exceptions
   ou extraire vers un module neutre) ; 3 tests de contrat de workflow déjà rouges sur `qt/master` ;
   qualification réelle PySide6 dans un environnement approprié (PySide6 absent ici).
5. Test de fenêtre réelle wx rouge en local (§8.6), à valider par le job Windows de la CI.
6. Qualification GitHub du SHA final : voir §8.8.
7. Nommage permanent (`master`/`wx/master`/`qt/master` vs `main`/`wx`/`qt`) : non décidé, non exécuté.
8. Aucune écriture dans une base réelle ; tests SQL sur conteneurs jetables uniquement.

Le candidat **n'est pas déclaré « qualifié »** tant que les points 3 à 6 restent ouverts ; en l'état il
est « qualifié localement sur les couches communes, hors wx/Qt ».

## 10. Ordre recommandé pour la suite

1. (Fait) contrat de recherche #473 fixé, `xfail` retirés.
2. Revue du candidat (`integration/main-foundation-2026-10`) et validation de sa CI sur GitHub.
3. Résoudre `ci.yml` branche par branche ; fixer le test de contrat installateur côté wx.
4. wx : fusionner le candidat dans une branche d'intégration dérivée de `wx/master` (0 conflit), puis
   porter #474-wx, #475, #476 sur le socle commun.
5. Qt : fusionner dans une branche dérivée de `qt/master` ; étendre les exceptions d'import ;
   traiter les 3 contrats de workflow déjà rouges.
6. Instruire #452, #390, #386 (REVIEW) fichier par fichier.
7. Décider du renommage des branches permanentes (#487) seulement après les points 3 à 5.
8. Optionnel : #376 / #485 (outillage d'audit) une fois le socle stabilisé.

## 11. Contrôle des occurrences à ne plus faire apparaître

Ce rapport ne contient plus de nom de base de production, de nom de portail tiers ni de nom de test
issu d'un périmètre à exclure. Contrôle effectué sur l'arbre courant (`git grep`) et sur le diff ajouté
depuis #492 (`git diff 4ec619b3 HEAD`), pas sur l'historique Git. La liste exacte des termes interdits
n'étant pas consignée dans le dépôt, le contrôle a porté sur les termes présents dans l'ancienne version
de ce rapport. Restent dans le diff ajouté uniquement les occurrences de contenu fonctionnel de #454
(documentation 66 et inventaire de la base historique, qui nomment le système migré), fusionnées telles
quelles et non réécrites ici.
