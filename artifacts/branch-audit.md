# Audit d'absorption des branches

> Rapport non destructif : aucune branche supprimée, aucune PR fermée, aucun merge, aucun workflow GitHub Actions déclenché.

- Total audité : **188**
- CONSERVER : **81**
- SUPPRESSION SÛRE : **38**
- À REVOIR : **69**

> **Surcharge CRH (arbitrage final)** : pour les 41 branches `crh-*`, les verdicts ci-dessous sont remplacés par `artifacts/crh-branch-audit.md` : 40 SUPPRESSION SÛRE, 0 À REVOIR, 1 À CONSERVER (`crh-36-lifecycle-template-management`).

## Contexte d'exécution

- généré_le : `2026-09-28T22:12:37Z`
- origin/master : `1673248ce646706313d4ed3a3f19024b32be49e7`
- origin/wx/master : `fdb383735f176dc04c2e43576e376fe7adfaba1b`
- origin/qt/master : `36db74ab70bbe9953852b24d6ff507b7544b121c`
- outil : `tools/audit_branch_absorption.py (v2 locale, base origin/audit/branch-absorption 0deff723)`
- fetch : `git fetch --all --prune --no-tags (+ refs/pull/* en lecture)`
- PR : `API REST GitHub (lecture seule), 485 PR dont 48 ouvertes — aucune minute GitHub Actions`
- tests : `pytest local, python 3.11.15 ; tests propres réinjectés dans un worktree de la cible seule, après exécution de référence sur la branche`
- cibles : `ancres conservées uniquement : master, wx/master, qt/master, têtes et bases des 48 PR ouvertes`
- ancres fortes : `architecture/migration-noethys-teamworks, architecture/person-delete-usecase, architecture/person-refresh-contract, architecture/person-refresh-wx, architecture/profils-autorisations, feature/dpae-declarative-data, feature/dpae-domain-foundation, feature/dpae-incident-recovery, feature/dpae-structured-errors, feature/employee-termination-domain, feature/employee-termination-persistence, feature/employee-termination-transmission, master, qt/contracts-cee-create, qt/contracts-classification-prep, qt/contracts-probation-prep, qt/contracts-renewal-prep, qt/contracts-ui-gate, qt/contracts-ui-prep, qt/convergence-0.9.2-rc3, qt/master, qt/presence-transactions, qt/scenario-transactions, qt/vanilla-0.1-rc, rail-c/documents-rh-publipostage, release/vanilla-wx-0.9.2-rc3, ux/person-search-contract, wx/master`

## 1. CONSERVER (81)

| Branche | SHA | Dernière activité | PR | Justification | Confiance |
|---|---|---|---|---|---|
| `PMSL35/qt-windows-qualification` | `ea5fc10cf092` | 2026-09-05 | #377 (closed) | résidu fonctionnel non absorbé: file-absent-from-target:poc/qt-theme/benchmark_windows.cmd, file-absent-from-target:poc/qt-theme/frugality.py, file-absent-from-target:poc/qt-theme/launcher.py | high |
| `architecture/migration-noethys-teamworks` | `22fc042160ca` | 2026-09-21 | #454 (open) | head de PR ouverte #454 | high |
| `architecture/person-delete-usecase` | `3f3519f265b6` | 2026-09-25 | #474 (open) | head de PR ouverte #474; base de PR ouverte #475 | high |
| `architecture/person-refresh-contract` | `c1480c13d29e` | 2026-09-25 | #475 (open) | head de PR ouverte #475; base de PR ouverte #476 | high |
| `architecture/person-refresh-wx` | `780b6bc7b953` | 2026-09-25 | #476 (open) | head de PR ouverte #476 | high |
| `architecture/profils-autorisations` | `35702a4a40b2` | 2026-09-22 | #472 (open) | head de PR ouverte #472 | high |
| `audit/0.9.2-stop-gate` | `2d7833c074cf` | 2026-09-07 | #396 (open) | head de PR ouverte #396 | high |
| `audit/0.9.2-ux-stop-gate` | `6602f2f990e0` | 2026-09-07 | #405 (open) | head de PR ouverte #405 | high |
| `audit/branch-absorption` | `0deff723584b` | 2026-09-28 | #485 (open) | head de PR ouverte #485 | high |
| `audit/caracterisation-scenarios-frais` | `ee152d12bc0e` | 2026-09-04 | #369 (open) | head de PR ouverte #369; base de PR ouverte #373, #371 | high |
| `audit/sortie-connecthys` | `a0cc779a23c5` | 2026-09-05 | #376 (open) | head de PR ouverte #376 | high |
| `ccns/session-actual-hr-inbox` | `3dadf2d0adc3` | 2026-09-02 | #354 (closed) | résidu fonctionnel non absorbé: py:application/services/inter_domain_delivery_hr.py:_canonical_json, py:application/services/inter_domain_delivery_hr.py:_mapping_copy, py:infrastructure/persistence/session_actual_hr_repository.py:SessionActualHrRepository._required_key, lines-missing:application/services/inter_domain_delivery_hr.py:42/165, lines-missing:application/services/session_actual_hr.py:1/26, lines-missing:docs/04_CCNS_EXTENSIONS.md:24/24 | high |
| `crh-21-structure-hr-connections-ui` | `1e14e018e981` | 2026-09-01 | #339 (closed) | résidu fonctionnel non absorbé: py:teamworks/Ctrl/CTRL_Page_protection_sociale.py:Panel.OnOrganismes, py:teamworks/Ctrl/CTRL_Page_protection_sociale_runtime.py:Panel.OnOrganismes, file-absent-from-target:application/bootstrap/structure_hr_connections_factory.py, file-absent-from-target:docs/72-crh-21-configuration-organismes-rh.md, file-absent-from-target:teamworks/Dlg/DLG_Connexions_RH.py | high |
| `crh-22-teamworks-hr-cases-persistence` | `3f50b83b02ce` | 2026-09-01 | — | résidu fonctionnel non absorbé: py:infrastructure/persistence/teamworks_hr_cases_repository.py:_adapt_placeholders, py:infrastructure/persistence/teamworks_hr_cases_repository.py:_case_from_rows, py:infrastructure/persistence/teamworks_hr_cases_repository.py:_close, file-absent-from-target:application/bootstrap/structure_hr_connections_factory.py, file-absent-from-target:docs/72-crh-21-configuration-organismes-rh.md, file-absent-from-target:docs/73-crh-22-persistence-demarches-rh.md | high |
| `crh-36-lifecycle-template-management` | `6a75377b1d79` | 2026-09-02 | #357 (open) | head de PR ouverte #357 | high |
| `dev-db-docker` | `8ce2a37dc11b` | 2026-08-25 | #270 (open) | head de PR ouverte #270 | high |
| `docs/architecture-vanilla-reference` | `a9767d168948` | 2026-09-05 | #374 (open) | head de PR ouverte #374 | high |
| `docs/fondations-rh-paie-ready` | `e8b3df2dc0ec` | 2026-09-01 | #316 (closed) | résidu fonctionnel non absorbé: file-absent-from-target:docs/67-fondations-rh-paie-ready.md, file-absent-from-target:docs/68-plan-lots-connexions-rh.md, lines-missing:docs/00-architecture-cible.md:6/7 | high |
| `docs/mkdocs-pages` | `7db56187b3d9` | 2026-09-18 | #440 (closed) | résidu fonctionnel non absorbé: file-absent-from-target:docs/index.md, file-absent-from-target:docs/reference/mots-cles-publipostage.md, file-absent-from-target:docs/utilisateur/index.md | high |
| `docs/wiki-teamworks-ccns-ready` | `536e319655e5` | 2026-09-17 | #432 (closed) | résidu fonctionnel non absorbé: file-absent-from-target:.github/workflows/wiki-validation.yml, file-absent-from-target:docs/wiki/Aide, discussions et signalement de bugs.md, file-absent-from-target:docs/wiki/Architecture fonctionnelle.md | high |
| `feat/diagnostic-coherence-remboursements` | `7795c06b9409` | 2026-09-04 | #373 (open) | head de PR ouverte #373; base de PR ouverte #375 | high |
| `feat/migration-coherence-remboursements` | `b2a8b75217c0` | 2026-09-05 | #375 (open) | head de PR ouverte #375 | high |
| `feature/dpae-declarative-data` | `e4b11be2780f` | 2026-09-27 | #478 (open) | head de PR ouverte #478; base de PR ouverte #481 | high |
| `feature/dpae-domain-foundation` | `780eb98c6c64` | 2026-09-27 | #477 (open) | head de PR ouverte #477; base de PR ouverte #478 | high |
| `feature/dpae-incident-recovery` | `afad76a65d10` | 2026-09-27 | #481 (open) | head de PR ouverte #481; base de PR ouverte #482 | high |
| `feature/dpae-structured-errors` | `77d012e8db33` | 2026-09-27 | #482 (open) | head de PR ouverte #482 | high |
| `feature/employee-termination-documents` | `f2eed1fab601` | 2026-09-28 | — | résidu fonctionnel non absorbé: file-absent-from-target:domain/employment/termination.py, file-absent-from-target:domain/employment/termination_documents.py, file-absent-from-target:domain/employment/termination_repository.py | high |
| `feature/employee-termination-domain` | `3cd12d1426f3` | 2026-09-27 | #479 (open) | head de PR ouverte #479; base de PR ouverte #483 | high |
| `feature/employee-termination-persistence` | `0903cfb26118` | 2026-09-27 | #483 (open) | head de PR ouverte #483; base de PR ouverte #484 | high |
| `feature/employee-termination-transmission` | `7936bb4a3e55` | 2026-09-28 | #484 (open) | head de PR ouverte #484 | high |
| `feature/home-calendar-hr-foundation` | `345d963dd5c7` | 2026-09-02 | #361 (closed) | résidu fonctionnel non absorbé: py:teamworks/Ctrl/CTRL_Calendrier_tw.py:CalendrierRh, py:teamworks/Ctrl/CTRL_Calendrier_tw.py:CalendrierRh.DrawCase, py:teamworks/Ctrl/CTRL_Calendrier_tw.py:CalendrierRh.MAJpanel, file-absent-from-target:teamworks/CcnsCore/calendar_hr.py, lines-missing:teamworks/Ctrl/CTRL_Calendrier_tw.py:80/82 | high |
| `feature/hr-document-selector-2026-08-29` | `b808c722d3df` | 2026-08-29 | #383 (open) | head de PR ouverte #383 | high |
| `fix/0.9.1g-render-transaction` | `fdbb42e7767a` | 2026-09-03 | — | résidu fonctionnel non absorbé: file-absent-from-target:teamworks/Utils/UTILS_RenderTransaction.py, lines-missing:teamworks/Teamworks.py:5/5 | high |
| `fix/0.9.2-entretiens-password-ux` | `f34dbd86e9ea` | 2026-09-07 | #407 (open) | head de PR ouverte #407 | high |
| `fix/0.9.2-frais-integrite-impression-distance` | `5172536a5ef9` | 2026-09-07 | #402 (open) | head de PR ouverte #402 | high |
| `fix/0.9.2-frais-integrite-moteur` | `1018bd4da1e8` | 2026-09-07 | — | résidu fonctionnel non absorbé: py:scripts/audit_dialog_geometry.py:_stretch_is_action_alignment, py:teamworks/Dlg/DLG_CCNS_audit_list.py:Dialog._apply_workspace_profile, py:teamworks/Dlg/DLG_CCNS_salary_control_history.py:Dialog._apply_workspace_profile, file-absent-from-target:docs/archives/conversations/2026-09-05-contexte-fonctionnel-et-migration-qt.md, file-absent-from-target:docs/archives/conversations/2026-09-05-etat-github-et-travaux.md, file-absent-from-target:docs/archives/conversations/2026-09-05-inventaire-branches-historiques.md | high |
| `fix/0.9.2-minicamp-recuperation-bank` | `7149fe069d30` | 2026-09-07 | #394 (open) | head de PR ouverte #394 | high |
| `fix/0.9.2-presences-moteur` | `bbd08d66ad58` | 2026-09-07 | #406 (open) | head de PR ouverte #406 | high |
| `fix/0.9.2-scenario-atomicity` | `eb0ad8c071b0` | 2026-09-07 | #398 (open) | head de PR ouverte #398 | high |
| `fix/0.9.2-scenario-presence-duration` | `8ae321076e6e` | 2026-09-07 | #404 (open) | head de PR ouverte #404 | high |
| `fix/coords-toggle-hotfix` | `363a79231b0f` | 2026-09-02 | #358 (closed) | résidu fonctionnel non absorbé: lines-missing:teamworks/Dlg/DLG_Saisie_coords.py:4/9 | high |
| `fix/frais-decimal-remboursement` | `6a2e7f0ad204` | 2026-09-04 | #370 (closed) | résidu fonctionnel non absorbé: lines-missing:teamworks/Dlg/DLG_Saisie_deplacement.py:1/1 | high |
| `fix/operation-heures-signe-negatif` | `bfbdbc39fc69` | 2026-09-04 | #371 (open) | head de PR ouverte #371 | high |
| `fix/rc1-publipostage-typeerror-null` | `802458481b72` | 2026-09-09 | #426 (closed) | résidu fonctionnel non absorbé: py:teamworks/Dlg/DLG_Saisie_champs_publipostage.py:_nullable_db_text, lines-missing:teamworks/Dlg/DLG_Saisie_champs_publipostage.py:9/9 | high |
| `fix/rc2-ui-state-context-refresh-20260919` | `5712aa019c55` | 2026-09-19 | #442 (open) | head de PR ouverte #442 | high |
| `fix/vanilla-wx-0.9.2-rc2-c-f` | `4dd3d25ecf7a` | 2026-09-11 | — | résidu fonctionnel non absorbé: py:scripts/audit_dialog_geometry.py:_stretch_is_action_alignment, py:teamworks/Ctrl/CTRL_Creation_contrat_p6.py:_database_ready, py:teamworks/Ctrl/CTRL_Page_contrats_core.py:_database_ready, file-absent-from-target:docs/PERF_WX_PERSONNES_2026-09-07.md, file-absent-from-target:docs/PERF_WX_PRESENCES_2026-09-07.md, file-absent-from-target:docs/PERF_WX_PRESENCES_AFTER_410.md | high |
| `fix/wx-0.9.2-rc3-final-stabilisation-20260921` | `674df21375a0` | 2026-09-22 | — | résidu fonctionnel non absorbé: py:scripts/audit_dialog_geometry.py:_stretch_is_action_alignment, py:teamworks/Ctrl/CTRL_Bouton_image.py:Compact, py:teamworks/Ctrl/CTRL_Bouton_image.py:Compact.MAJ, file-absent-from-target:CHANGELOG.md, file-absent-from-target:docs/PERF_WX_PERSONNES_2026-09-07.md, file-absent-from-target:docs/PERF_WX_PRESENCES_2026-09-07.md | high |
| `fix/wx-customize-encoding` | `2f6ba3817e04` | 2026-09-18 | #439 (closed) | résidu fonctionnel non absorbé: lines-missing:docs/02_PYTHON3_PHOENIX.md:1/21, lines-missing:teamworks/Teamworks.py:6/107, lines-missing:teamworks/Utils/UTILS_Aide.py:19/24 | high |
| `master` | `1673248ce646` | 2026-09-28 | #382 (closed), #267 (closed), #266 (closed), #264 (closed) | branche structurante protégée | high |
| `qt/contracts-cee-create` | `3ceaad829ff7` | 2026-09-21 | #448 (open), #449 (closed) | head de PR ouverte #448; base de PR ouverte #455 | high |
| `qt/contracts-classification-prep` | `7f64cb099f01` | 2026-09-21 | #457 (open), #458 (closed) | head de PR ouverte #457; base de PR ouverte #460 | high |
| `qt/contracts-probation-prep` | `72b663e3eba0` | 2026-09-21 | #460 (open), #461 (closed) | head de PR ouverte #460; base de PR ouverte #462 | high |
| `qt/contracts-renewal-prep` | `bc58c7618a2c` | 2026-09-21 | #455 (open), #456 (closed) | head de PR ouverte #455; base de PR ouverte #457 | high |
| `qt/contracts-ui-gate` | `e4ea900c6402` | 2026-09-21 | #465 (closed), #464 (open) | head de PR ouverte #464 | high |
| `qt/contracts-ui-prep` | `ec243bb027b9` | 2026-09-21 | #462 (open), #463 (closed) | head de PR ouverte #462; base de PR ouverte #464 | high |
| `qt/convergence-0.9.2-rc3` | `d40c78669873` | 2026-09-21 | #431 (closed) | base de PR ouverte #472, #448, #450, #446 | high |
| `qt/document-core-iteration-1` | `a87b9da4e9cb` | 2026-09-16 | — | résidu fonctionnel non absorbé: py:domain/documents/merge_context.py:MergeContext.from_mapping, py:domain/repositories/person_data.py:PersonCoordinateRecord, py:domain/repositories/person_data.py:PersonGeneralitiesRecord, file-absent-from-target:application/control/contract_classification.py, file-absent-from-target:docs/DOCUMENT_CORE_ITERATION_1.md, file-absent-from-target:docs/DOCUMENT_FORMAT_V1.md | high |
| `qt/document-core-iteration-2` | `2ae9fe2ddf79` | 2026-09-16 | #436 (closed), #435 (closed) | résidu fonctionnel non absorbé: py:domain/documents/merge_context.py:MergeContext.from_mapping, file-absent-from-target:docs/DOCUMENT_CORE_ITERATION_1.md, file-absent-from-target:docs/DOCUMENT_FORMAT_V1.md, file-absent-from-target:docs/TWD_LEGACY_FORMAT_AUDIT.md | high |
| `qt/document-core-iteration-3` | `5c8b5981dc56` | 2026-09-16 | #438 (closed), #437 (closed) | résidu fonctionnel non absorbé: py:domain/documents/merge_context.py:MergeContext.from_mapping, file-absent-from-target:docs/DOCUMENT_CORE_ITERATION_1.md, file-absent-from-target:docs/DOCUMENT_FIELD_LEGACY_ALIASES.md, file-absent-from-target:docs/DOCUMENT_FORMAT_V1.md | high |
| `qt/master` | `36db74ab70bb` | 2026-09-05 | — | branche structurante protégée | high |
| `qt/presence-transactions` | `de184614c418` | 2026-09-21 | #451 (closed), #450 (open) | head de PR ouverte #450 | high |
| `qt/scenario-transactions` | `46f2b07aed32` | 2026-09-21 | #446 (open), #447 (closed) | head de PR ouverte #446 | high |
| `qt/vanilla-0.1-rc` | `caed9650df74` | 2026-09-21 | #467 (open) | head de PR ouverte #467 | high |
| `rail-c/documents-rh-publipostage` | `8edfb4ded534` | 2026-09-21 | #452 (open) | head de PR ouverte #452 | high |
| `release/0.9.1c` | `8048ceacaf69` | 2026-09-01 | #326 (closed) | résidu fonctionnel non absorbé: file-absent-from-target:docs/RELEASE_0.9.1c.md, lines-missing:VERSION:1/1 | high |
| `release/0.9.1c-build` | `14d2d20c8889` | 2026-09-01 | #327 (closed) | résidu fonctionnel non absorbé: file-absent-from-target:docs/RELEASE_0.9.1c.md | high |
| `release/vanilla-wx-0.9.2-rc2` | `dfa21c471b69` | 2026-09-08 | — | résidu fonctionnel non absorbé: py:scripts/audit_dialog_geometry.py:_stretch_is_action_alignment, py:teamworks/Ctrl/CTRL_Creation_contrat_p6.py:_database_ready, py:teamworks/Ctrl/CTRL_Page_contrats_core.py:_database_ready, file-absent-from-target:docs/PERF_WX_PERSONNES_2026-09-07.md, file-absent-from-target:docs/PERF_WX_PRESENCES_2026-09-07.md, file-absent-from-target:docs/PERF_WX_PRESENCES_AFTER_410.md | high |
| `release/vanilla-wx-0.9.2-rc3` | `37755f8375ee` | 2026-09-23 | #430 (open) | head de PR ouverte #430 | high |
| `test/0.9.2-recette-windows-interactive` | `71a75ecacd86` | 2026-09-07 | #414 (open) | head de PR ouverte #414 | high |
| `test/0.9.2-scenario-integration` | `741fb8b19755` | 2026-09-07 | — | résidu fonctionnel non absorbé: py:scripts/audit_dialog_geometry.py:_stretch_is_action_alignment, py:teamworks/Dlg/DLG_CCNS_audit_list.py:Dialog._apply_workspace_profile, py:teamworks/Dlg/DLG_CCNS_salary_control_history.py:Dialog._apply_workspace_profile, file-absent-from-target:.github/workflows/tmp-scenario-integration.yml, file-absent-from-target:docs/archives/conversations/2026-09-05-contexte-fonctionnel-et-migration-qt.md, file-absent-from-target:docs/archives/conversations/2026-09-05-etat-github-et-travaux.md | high |
| `test/0.9.2-scenario-stacked` | `b1735b91371f` | 2026-09-07 | — | résidu fonctionnel non absorbé: py:scripts/audit_dialog_geometry.py:_stretch_is_action_alignment, py:teamworks/Dlg/DLG_CCNS_audit_list.py:Dialog._apply_workspace_profile, py:teamworks/Dlg/DLG_CCNS_salary_control_history.py:Dialog._apply_workspace_profile, file-absent-from-target:.github/workflows/tmp-stack-scenario-presence.yml, file-absent-from-target:docs/archives/conversations/2026-09-05-contexte-fonctionnel-et-migration-qt.md, file-absent-from-target:docs/archives/conversations/2026-09-05-etat-github-et-travaux.md | high |
| `tw10-01-atomic-sqlite-restore` | `525e09b67aca` | 2026-09-06 | #386 (open) | head de PR ouverte #386 | high |
| `tw10-03-rh-transaction-atomicity` | `4bb4c5bc6f0a` | 2026-09-06 | #390 (open) | head de PR ouverte #390 | high |
| `tw10-04-windows-release-qualification` | `adce8bd09a28` | 2026-09-06 | #391 (open) | head de PR ouverte #391 | high |
| `ui/dialog-geometry-batch-1` | `982de8c51399` | 2026-09-02 | #363 (closed) | tests propres en échec sur master | high |
| `ui/form-standards-coordinates` | `ff110207f121` | 2026-09-02 | #359 (closed) | résidu fonctionnel non absorbé: py:teamworks/Dlg/DLG_Saisie_coords.py:Dialog._fit_to_content, lines-missing:teamworks/Ctrl/CTRL_Page_generalites.py:15/15, lines-missing:teamworks/Dlg/DLG_Saisie_coords.py:28/45, lines-missing:teamworks/Utils/UTILS_Styles.py:1/1 | high |
| `ui/recruitment-contract-flow` | `a78a67f40999` | 2026-09-02 | #360 (closed) | résidu fonctionnel non absorbé: lines-missing:teamworks/Ctrl/CTRL_Creation_contrat_p1.py:44/44, lines-missing:teamworks/Ctrl/CTRL_Creation_contrat_p2.py:112/113 | high |
| `ux/person-search-contract` | `782f14b84fb3` | 2026-09-25 | #473 (open) | head de PR ouverte #473 | high |
| `vanilla-bugfix` | `bfd7b094cba5` | 2026-09-02 | — | résidu fonctionnel non absorbé: file-absent-from-target:CHANGELOG.md, lines-missing:teamworks/Ctrl/CTRL_Bouton_image.py:10/10, lines-missing:teamworks/Ctrl/CTRL_Page_generalites.py:7/7 | high |
| `wx/master` | `fdb383735f17` | 2026-09-07 | — | branche structurante protégée | high |
| `wx/raccord-operation-heures` | `c4621f8556f0` | 2026-09-07 | #389 (open) | head de PR ouverte #389 | high |

## 2. SUPPRESSION SÛRE (38)

| Branche | SHA | Dernière activité | PR | Justification | Confiance |
|---|---|---|---|---|---|
| `PMSL35/qt-convergence-377-378-380` | `3827271d5fe7` | 2026-09-05 | #381 (closed) | absorption prouvée vers qt/master et tests propres verts | high |
| `PMSL35/qt-final-gates-contract-clear` | `bab7fe272ef1` | 2026-09-05 | #378 (closed) | absorption prouvée vers qt/master et tests propres verts | high |
| `ccns/session-actual-hr-current` | `0b8fb6f81bdb` | 2026-09-04 | #368 (closed) | absorption prouvée vers master et tests propres verts | high |
| `ci/update-windows-installer-contract` | `9f875f825f85` | 2026-09-19 | #443 (closed) | absorption prouvée vers master et tests propres verts | high |
| `contract/duree-signee-commune` | `bbeae37c119a` | 2026-09-06 | #388 (closed) | absorption prouvée vers wx/master et tests propres verts | high |
| `fix-wx-personnes-column-persistence` | `45876d28425b` | 2026-09-07 | #413 (closed), #417 (closed) | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | high |
| `fix-wx-personnes-publipostage-id` | `3a5ccbbaccb0` | 2026-09-07 | #412 (closed), #418 (closed) | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | high |
| `fix-wx-questionnaire-init-order` | `ba7d2b5b24c4` | 2026-09-07 | #409 (closed), #421 (closed) | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | high |
| `fix/0.9.1f-render-lifecycle` | `691869e58ed3` | 2026-09-03 | #367 (closed) | absorption prouvée vers master et tests propres verts | high |
| `fix/0.9.1f-ui-runtime-regressions` | `36949b033375` | 2026-09-03 | #365 (closed) | absorption prouvée vers master et tests propres verts | high |
| `fix/0.9.2-audit-ccns-productive-ui` | `8dd66b0f3871` | 2026-09-07 | #397 (closed) | absorption prouvée vers wx/master et tests propres verts | high |
| `fix/0.9.2-audit-user-errors` | `4ac3c40cae85` | 2026-09-07 | #399 (closed) | absorption prouvée vers wx/master et tests propres verts | high |
| `fix/0.9.2-ccns-initial-focus` | `3193aefd3ea2` | 2026-09-07 | #401 (closed) | absorption prouvée vers wx/master et tests propres verts | high |
| `fix/0.9.2-compact-dialog-geometry` | `70505fa51999` | 2026-09-07 | #392 (closed) | absorption prouvée vers wx/master et tests propres verts | high |
| `fix/0.9.2-confirm-appli-modele-worker-lifecycle` | `fdb383735f17` | 2026-09-07 | — | absorption prouvée vers wx/master et tests propres verts | high |
| `fix/0.9.2-final-wx-ux-cleanup` | `19abeee2b65d` | 2026-09-07 | #395 (closed) | absorption prouvée vers wx/master et tests propres verts | high |
| `fix/0.9.2-legacy-ccns-audit-ux` | `2d1e14d05a87` | 2026-09-07 | #403 (closed) | absorption prouvée vers wx/master et tests propres verts | high |
| `fix/0.9.2-salary-history-language` | `a4ba31ed524f` | 2026-09-07 | #400 (closed) | absorption prouvée vers wx/master et tests propres verts | high |
| `fix/frais-integrite-remboursements` | `c885f55fe458` | 2026-09-05 | #379 (closed) | absorption prouvée vers master et tests propres verts | high |
| `fix/rc1-dpae-due-20260908` | `5cdd89d1a88d` | 2026-09-08 | #424 (closed) | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | high |
| `fix/rc1-publipostage-native-lifecycle` | `067a6bb2e68b` | 2026-09-09 | #427 (closed) | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | high |
| `fix/rc1-recette-bugs-20260908` | `66a5091293a5` | 2026-09-08 | #423 (closed) | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | high |
| `fix/rc1-stdout-flush-20260908` | `ab11e7b6198e` | 2026-09-08 | #425 (closed) | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | high |
| `fix/scenario-report-cycles` | `492cfdfa26a0` | 2026-09-06 | #387 (closed) | absorption prouvée vers wx/master et tests propres verts | high |
| `fix/wx-0.9.2-rc3-audit-cleanup-20260922` | `26f48cc21ed6` | 2026-09-22 | — | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | high |
| `fix/wx-dialog-root-panel-sizers` | `f5552dc60420` | 2026-09-07 | #416 (closed), #420 (closed) | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | high |
| `fix/wx-scenario-negative-duration` | `c5f80bad95ac` | 2026-09-05 | #384 (closed) | absorption prouvée vers wx/master et tests propres verts | high |
| `fix/wx-window-work-area` | `18cbef2cb29c` | 2026-09-07 | #415 (closed), #419 (closed) | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | high |
| `poc/qt-theme-isole` | `dad51c0f6aaf` | 2026-09-05 | #366 (closed) | absorption prouvée vers qt/master et tests propres verts | high |
| `qt/frais-transactions` | `4d81b5850f41` | 2026-09-21 | #444 (closed), #466 (closed), #445 (closed) | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts | high |
| `qt/rail-c-documents-rh` | `49449e6f7b6d` | 2026-09-21 | #453 (closed) | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts | high |
| `qt/vanilla-0.1-anonymisation` | `ea05126ca52e` | 2026-09-21 | #468 (closed) | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts | high |
| `qt/vanilla-0.1-go-no-go` | `3cf725098b35` | 2026-09-21 | #471 (closed) | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts | high |
| `qt/vanilla-0.1-mysql-evidence` | `20ee79a12c6a` | 2026-09-21 | #470 (closed) | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts | high |
| `qt/vanilla-0.1-mysql-validation` | `d55bb45f98f1` | 2026-09-21 | #469 (closed) | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts | high |
| `qt/vanilla-0.1-packaging` | `4d35c618f089` | 2026-09-21 | #459 (closed) | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts | high |
| `tw10-04-dispatch-helper` | `860204ddbf29` | 2026-09-05 | — | absorption prouvée vers master et tests propres verts | high |
| `ui/dialog-geometry-audit` | `dce27c099eb0` | 2026-09-02 | #362 (closed) | absorption prouvée vers master et tests propres verts | high |

## 3. À REVOIR (69)

| Branche | SHA | Dernière activité | PR | Justification | Confiance |
|---|---|---|---|---|---|
| `PMSL35/qt-blocking-thread-lifecycle` | `b91a522929c3` | 2026-09-05 | #380 (closed) | aucun test propre permettant de prouver le comportement sur la cible | medium |
| `audit/coherence-remboursements-deplacements` | `67cc94a03955` | 2026-09-04 | #372 (closed) | absorption prouvée et tests verts, mais la branche finale feat/diagnostic-coherence-remboursements n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `audit/coherence-remboursements-deplacements-scan` | `ee152d12bc0e` | 2026-09-04 | — | absorption prouvée et tests verts, mais la branche finale audit/caracterisation-scenarios-frais n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `audit/scenarios-frais-caracterisation` | `fd88dbf6025d` | 2026-09-03 | — | aucun test propre permettant de prouver le comportement sur la cible | medium |
| `ci/frugal-mkdocs` | `a0b5b54b4c83` | 2026-09-27 | #480 (closed) | aucun test propre permettant de prouver le comportement sur la cible | medium |
| `ci/wx-master-validation` | `cc92ac8f3e30` | 2026-09-06 | #385 (closed) | aucun test propre permettant de prouver le comportement sur la cible | medium |
| `crh-01-02-domain-registry` | `5aa44f449589` | 2026-09-01 | #317 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-03-cases-workflow` | `19675cfa1792` | 2026-09-01 | #318 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-04-event-journal` | `f674c1edd640` | 2026-09-01 | #319 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-05-file-exchange-boundary` | `55254326bfd6` | 2026-09-01 | #320 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-06-secret-store-contract` | `3f4050a6ff5b` | 2026-09-01 | #321 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-07-manual-portal-connector` | `d6c5a072ea4e` | 2026-09-01 | #322 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-08-reference-manual-connectors` | `26a1eda5e4e1` | 2026-09-01 | #323 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-09-additive-persistence` | `b105a0bc620b` | 2026-09-01 | #324 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-10-structure-configuration-service` | `a5d3eae2817b` | 2026-09-01 | #325 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-10b-wx-structure-connections` | `86bc7af8ac9e` | 2026-09-01 | #340 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-11-employee-protection-model` | `85b30e89a790` | 2026-09-01 | #328 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-12-employee-protection-service` | `3ada7828bbe3` | 2026-09-01 | #329 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-13-employee-protection-persistence` | `07738eff58fe` | 2026-09-01 | #330 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-14-employee-protection-summary` | `6598caffc423` | 2026-09-01 | #331 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-15-wx-employee-protection-panel` | `2daa5faf893a` | 2026-09-01 | #332 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-16-teamworks-production-persistence` | `26bf05b5c633` | 2026-09-01 | #333 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-17a-employee-protection-composition` | `7e1c5cc7eea3` | 2026-09-01 | #334 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-17b-wx-employee-protection-wiring` | `17b550f858fb` | 2026-09-01 | #335 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-18-employee-protection-actions` | `1f39564ba616` | 2026-09-01 | #336 (closed) | historique absorbé dans crh-36-lifecycle-template-management mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | medium |
| `crh-19-employee-protection-succession` | `06b9b237c593` | 2026-09-01 | #337 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-20-wx-employee-protection-actions` | `28f358658171` | 2026-09-01 | #338 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-21-case-dashboard-projection` | `7ad902139c27` | 2026-09-01 | #341 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-21a-structure-hr-connections-dialog` | `28f358658171` | 2026-09-01 | — | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-22-teamworks-cases-persistence` | `1afba7640fee` | 2026-09-01 | #342 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-23-case-dashboard-runtime` | `2ae8fdff989d` | 2026-09-01 | #343 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-24-wx-case-dashboard` | `de48bf0a4f5f` | 2026-09-01 | #344 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-25-case-workflow-service` | `71c44ddcbf17` | 2026-09-01 | #345 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-26-wx-case-workflow-actions` | `fecea89e1c68` | 2026-09-01 | #346 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-27-case-audit-history` | `2f78dc071cd4` | 2026-09-01 | #347 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-28-wire-case-history` | `55d2043cddd1` | 2026-09-01 | #348 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-29-case-creation-service` | `f670534034a0` | 2026-09-01 | #349 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-30-new-case-dialog` | `f004ca3e470b` | 2026-09-02 | #350 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-31-case-document-tracking` | `4a3390266115` | 2026-09-02 | #351 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-32-wx-case-document-checklist` | `9880e00d175e` | 2026-09-02 | #352 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-33-dashboard-document-state` | `9880e00d175e` | 2026-09-02 | — | aucun test propre permettant de prouver le comportement sur la cible | medium |
| `crh-33-dashboard-document-status` | `a0b18d8e44ea` | 2026-09-02 | #353 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-34-lifecycle-planning` | `477f2d3f30aa` | 2026-09-02 | #355 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `crh-35-lifecycle-template-persistence` | `2a2f20aff8fc` | 2026-09-02 | #356 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `docs/documents-rh-structure-publipostage` | `7f0139b246d9` | 2026-08-28 | #312 (closed) | aucun test propre permettant de prouver le comportement sur la cible | medium |
| `docs/mkdocs` | `427e6fb1a9de` | 2026-09-19 | #441 (closed) | aucun test propre permettant de prouver le comportement sur la cible | medium |
| `docs/roadmap-ci789-qualification-machine` | `8dbf0b29ad1d` | 2026-08-31 | #315 (closed) | aucun test propre permettant de prouver le comportement sur la cible | medium |
| `docs/wiki-teamworks-ccns` | `2939fb74e74c` | 2026-09-15 | — | aucun test propre permettant de prouver le comportement sur la cible | medium |
| `docs/wiki-teamworks-ccns-2` | `2939fb74e74c` | 2026-09-15 | — | aucun test propre permettant de prouver le comportement sur la cible | medium |
| `docs/wiki-teamworks-ccns-content` | `2939fb74e74c` | 2026-09-15 | — | aucun test propre permettant de prouver le comportement sur la cible | medium |
| `docs/wiki-teamworks-ccns-final` | `2939fb74e74c` | 2026-09-15 | — | aucun test propre permettant de prouver le comportement sur la cible | medium |
| `docs/wiki-teamworks-ccns-upload` | `2939fb74e74c` | 2026-09-15 | — | aucun test propre permettant de prouver le comportement sur la cible | medium |
| `feature/hr-document-catalog-2026-08-29` | `538e0f7a40f3` | 2026-08-29 | #313 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `fix-dashboard-dark-navigation-2026-08-27` | `c71a092544e6` | 2026-08-27 | #308 (closed) | historique absorbé dans crh-36-lifecycle-template-management mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | medium |
| `fix-preferences-appearance-scope-2026-08-27` | `1562d88e3144` | 2026-08-27 | #306 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `fix-windows-icon-build-2026-08-28` | `fcbef16dc6f2` | 2026-08-28 | #309 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `fix-wx-personnes-column-state` | `2de3f9227b5c` | 2026-09-07 | #411 (closed) | historique absorbé dans release/vanilla-wx-0.9.2-rc3 mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | medium |
| `fix/0.9.1e-generalites-addresses` | `0d77d1d6fb94` | 2026-09-03 | #364 (closed) | aucun test propre permettant de prouver le comportement sur la cible | medium |
| `fix/0.9.1g-ui-rendering` | `3862ab7c9bc3` | 2026-09-03 | — | aucun test propre permettant de prouver le comportement sur la cible | medium |
| `fix/0.9.2-salary-history-ux` | `2c9f2ebfd384` | 2026-09-07 | #393 (closed) | absorption prouvée et tests verts, mais la branche finale fix/0.9.2-scenario-atomicity n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `fix/individual-form-core-regression-test` | `c2d758327f63` | 2026-08-31 | #314 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `fix/rc2-individual-form-lazy-test` | `0b20d93ac692` | 2026-09-10 | #429 (closed) | historique absorbé dans release/vanilla-wx-0.9.2-rc3 mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | medium |
| `fix/rc3-updater-prerelease` | `1b12eec383bc` | 2026-09-16 | #434 (closed), #433 (closed) | historique absorbé dans release/vanilla-wx-0.9.2-rc3 mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | medium |
| `hardening-post-091b-2026-08-28` | `3006a785c268` | 2026-08-28 | #311 (closed) | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine | medium |
| `perf-wx-personnes-latency` | `377dd2089130` | 2026-09-07 | #408 (closed) | historique absorbé dans release/vanilla-wx-0.9.2-rc3 mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | medium |
| `perf-wx-presences-latency` | `f2a7438ad5d2` | 2026-09-07 | #410 (closed) | historique absorbé dans release/vanilla-wx-0.9.2-rc3 mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | medium |
| `refactor/0.9.2-modular-foundations` | `0b20d93ac692` | 2026-09-10 | #428 (closed) | historique absorbé dans release/vanilla-wx-0.9.2-rc3 mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | medium |
| `release-0.9.1b-2026-08-28` | `52231436173e` | 2026-08-28 | #310 (closed) | aucun test propre permettant de prouver le comportement sur la cible | medium |
| `release/vanilla-wx-0.9.2-rc1` | `748a36282718` | 2026-09-08 | #422 (closed) | historique absorbé dans release/vanilla-wx-0.9.2-rc3 mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | medium |

## SUPPRESSION SÛRE — chaîne d'absorption

| Branche | Cible immédiate | Cible intermédiaire | Branche finale conservée | Preuve Git | Preuve patch/squash | Tests réinjectés | Résultat | Résidu | Confiance |
|---|---|---|---|---|---|---|---|---|---|
| `PMSL35/qt-convergence-377-378-380` | `poc/qt-theme-isole` | `—` | `qt/master` | merge-base ff8a8e10a57d | 0/8 patch-id | 2 | PASS (réf. branche : PASS) | aucun | high |
| `PMSL35/qt-final-gates-contract-clear` | `poc/qt-theme-isole` | `—` | `qt/master` | merge-base aebe502c2069 | 0/2 patch-id, lignes 2/2 | 1 | PASS (réf. branche : PASS) | aucun | high |
| `ccns/session-actual-hr-current` | `master` | `tw10-04-dispatch-helper` | `master` | ancêtre | 19/19 patch-id | 3 | PASS (réf. branche : PASS) | aucun | high |
| `ci/update-windows-installer-contract` | `master` | `—` | `master` | merge-base 5e2fa861ccc2 | 1/1 patch-id | 1 | PASS (réf. branche : PASS) | aucun | high |
| `contract/duree-signee-commune` | `wx/master` | `fix/0.9.2-compact-dialog-geometry` | `wx/master` | ancêtre | 5/5 patch-id | 2 | PASS (réf. branche : PASS) | aucun | high |
| `fix-wx-personnes-column-persistence` | `release/vanilla-wx-0.9.2-rc1` | `release/vanilla-wx-0.9.2-rc1` | `release/vanilla-wx-0.9.2-rc3` | ancêtre | 3/3 patch-id, lignes 60/66 | 1 | PASS (réf. branche : PASS) | aucun (1 expliqué(s) par l'historique cible) | high |
| `fix-wx-personnes-publipostage-id` | `release/vanilla-wx-0.9.2-rc1` | `release/vanilla-wx-0.9.2-rc1` | `release/vanilla-wx-0.9.2-rc3` | ancêtre | 4/4 patch-id, lignes 43/44 | 1 | PASS (réf. branche : PASS) | aucun (1 expliqué(s) par l'historique cible) | high |
| `fix-wx-questionnaire-init-order` | `release/vanilla-wx-0.9.2-rc1` | `release/vanilla-wx-0.9.2-rc1` | `release/vanilla-wx-0.9.2-rc3` | ancêtre | 3/3 patch-id, lignes 21/21 | 1 | PASS (réf. branche : PASS) | aucun | high |
| `fix/0.9.1f-render-lifecycle` | `master` | `—` | `master` | merge-base 3862ab7c9bc3 | 0/2 patch-id | 1 | PASS (réf. branche : PASS) | aucun | high |
| `fix/0.9.1f-ui-runtime-regressions` | `master` | `—` | `master` | merge-base f7ce3a4ce30f | 2/2 patch-id | 1 | PASS (réf. branche : PASS) | aucun | high |
| `fix/0.9.2-audit-ccns-productive-ui` | `wx/master` | `fix/0.9.2-audit-user-errors` | `wx/master` | ancêtre | 2/2 patch-id, lignes 35/35 | 1 | PASS (réf. branche : PASS) | aucun | high |
| `fix/0.9.2-audit-user-errors` | `wx/master` | `fix/0.9.2-salary-history-language` | `wx/master` | ancêtre | 3/3 patch-id | 1 | PASS (réf. branche : PASS) | aucun | high |
| `fix/0.9.2-ccns-initial-focus` | `wx/master` | `fix/0.9.2-legacy-ccns-audit-ux` | `wx/master` | ancêtre | 3/3 patch-id | 1 | PASS (réf. branche : PASS) | aucun | high |
| `fix/0.9.2-compact-dialog-geometry` | `wx/master` | `fix/0.9.2-audit-ccns-productive-ui` | `wx/master` | ancêtre | 1/1 patch-id | 1 | PASS (réf. branche : PASS) | aucun | high |
| `fix/0.9.2-confirm-appli-modele-worker-lifecycle` | `wx/master` | `—` | `wx/master` | ancêtre | 3/3 patch-id | 2 | PASS (réf. branche : PASS) | aucun | high |
| `fix/0.9.2-final-wx-ux-cleanup` | `wx/master` | `fix/0.9.2-audit-ccns-productive-ui` | `wx/master` | ancêtre | 6/6 patch-id, lignes 4/4 | 2 | PASS (réf. branche : PASS) | aucun | high |
| `fix/0.9.2-legacy-ccns-audit-ux` | `wx/master` | `fix/0.9.2-confirm-appli-modele-worker-lifecycle` | `wx/master` | ancêtre | 3/3 patch-id | 2 | PASS (réf. branche : PASS) | aucun | high |
| `fix/0.9.2-salary-history-language` | `wx/master` | `fix/0.9.2-ccns-initial-focus` | `wx/master` | ancêtre | 2/2 patch-id | 1 | PASS (réf. branche : PASS) | aucun | high |
| `fix/frais-integrite-remboursements` | `master` | `—` | `master` | merge-base 440e0e9d98ab | 0/14 patch-id | 3 | PASS (réf. branche : PASS) | aucun | high |
| `fix/rc1-dpae-due-20260908` | `release/vanilla-wx-0.9.2-rc1` | `—` | `release/vanilla-wx-0.9.2-rc3` | merge-base 748a36282718 | 0/1 patch-id, lignes 26/26 | 1 | PASS (réf. branche : PASS) | aucun | high |
| `fix/rc1-publipostage-native-lifecycle` | `release/vanilla-wx-0.9.2-rc1` | `—` | `release/vanilla-wx-0.9.2-rc3` | merge-base 748a36282718 | 0/2 patch-id | 1 | PASS (réf. branche : PASS) | aucun | high |
| `fix/rc1-recette-bugs-20260908` | `release/vanilla-wx-0.9.2-rc1` | `fix/rc2-individual-form-lazy-test` | `release/vanilla-wx-0.9.2-rc3` | ancêtre | 15/15 patch-id, lignes 34/35 | 2 | PASS (réf. branche : PASS) | aucun (1 expliqué(s) par l'historique cible) | high |
| `fix/rc1-stdout-flush-20260908` | `release/vanilla-wx-0.9.2-rc1` | `—` | `release/vanilla-wx-0.9.2-rc3` | merge-base 748a36282718 | 0/2 patch-id, lignes 5/5 | 1 | PASS (réf. branche : PASS) | aucun | high |
| `fix/scenario-report-cycles` | `wx/master` | `—` | `wx/master` | merge-base c619f1614aae | 0/6 patch-id | 1 | PASS (réf. branche : PASS) | aucun | high |
| `fix/wx-0.9.2-rc3-audit-cleanup-20260922` | `release/vanilla-wx-0.9.2-rc3` | `—` | `release/vanilla-wx-0.9.2-rc3` | ancêtre | 1/1 patch-id | 1 | PASS (réf. branche : PASS) | aucun | high |
| `fix/wx-dialog-root-panel-sizers` | `release/vanilla-wx-0.9.2-rc1` | `release/vanilla-wx-0.9.2-rc1` | `release/vanilla-wx-0.9.2-rc3` | ancêtre | 1/1 patch-id, lignes 12/12 | 1 | PASS (réf. branche : PASS) | aucun | high |
| `fix/wx-scenario-negative-duration` | `wx/master` | `—` | `wx/master` | merge-base 3be59e6701d0 | 0/5 patch-id, lignes 14/14 | 1 | PASS (réf. branche : PASS) | aucun | high |
| `fix/wx-window-work-area` | `release/vanilla-wx-0.9.2-rc1` | `release/vanilla-wx-0.9.2-rc1` | `release/vanilla-wx-0.9.2-rc3` | ancêtre | 1/1 patch-id | 1 | PASS (réf. branche : PASS) | aucun | high |
| `poc/qt-theme-isole` | `master` | `—` | `qt/master` | ancêtre | 207/207 patch-id | 21 | PASS (réf. branche : PASS) | aucun | high |
| `qt/frais-transactions` | `qt/vanilla-0.1-rc` | `qt/vanilla-0.1-anonymisation` | `qt/vanilla-0.1-rc` | ancêtre | 34/34 patch-id, lignes 159/159 | 5 | PASS (réf. branche : PASS) | aucun | high |
| `qt/rail-c-documents-rh` | `qt/convergence-0.9.2-rc3` | `qt/vanilla-0.1-packaging` | `qt/vanilla-0.1-rc` | ancêtre | 23/23 patch-id, lignes 65/69 | 6 | PASS (réf. branche : PASS) | aucun (1 expliqué(s) par l'historique cible) | high |
| `qt/vanilla-0.1-anonymisation` | `qt/vanilla-0.1-rc` | `qt/vanilla-0.1-mysql-validation` | `qt/vanilla-0.1-rc` | ancêtre | 9/9 patch-id, lignes 6/6 | 2 | PASS (réf. branche : PASS) | aucun | high |
| `qt/vanilla-0.1-go-no-go` | `qt/vanilla-0.1-rc` | `—` | `qt/vanilla-0.1-rc` | ancêtre | 5/5 patch-id | 1 | PASS (réf. branche : PASS) | aucun | high |
| `qt/vanilla-0.1-mysql-evidence` | `qt/vanilla-0.1-rc` | `qt/vanilla-0.1-go-no-go` | `qt/vanilla-0.1-rc` | ancêtre | 9/9 patch-id, lignes 1/2 | 2 | PASS (réf. branche : PASS) | aucun (1 expliqué(s) par l'historique cible) | high |
| `qt/vanilla-0.1-mysql-validation` | `qt/vanilla-0.1-rc` | `qt/vanilla-0.1-mysql-evidence` | `qt/vanilla-0.1-rc` | ancêtre | 6/6 patch-id, lignes 252/253 | 1 | PASS (réf. branche : PASS) | aucun (1 expliqué(s) par l'historique cible) | high |
| `qt/vanilla-0.1-packaging` | `qt/rail-c-documents-rh` | `qt/vanilla-0.1-anonymisation` | `qt/vanilla-0.1-rc` | ancêtre | 16/16 patch-id, lignes 129/129 | 1 | PASS (réf. branche : PASS) | aucun | high |
| `tw10-04-dispatch-helper` | `master` | `docs/mkdocs` | `master` | ancêtre | 1/1 patch-id | 3 | PASS (réf. branche : PASS) | aucun | high |
| `ui/dialog-geometry-audit` | `master` | `—` | `master` | merge-base d39b6e11120d | 0/5 patch-id | 1 | PASS (réf. branche : PASS) | aucun | high |

## 4. Limites de l'analyse

- Une branche sans test propre (tests/*.py ajoutés ou modifiés) ne peut pas être SUPPRESSION SÛRE : elle reste À REVOIR, même absorbée par l'historique.
- Une absorption vers une PR ouverte hors piles de référence (ancre faible) reste À REVOIR : sûre tant que cette PR et sa branche sont conservées.
- Les tests propres réinjectés dépendent de l'environnement local (sans wx, PySide6 ni MySQL) : une dépendance absente donne INFRA_ERROR (jamais SUPPRESSION SÛRE).
- Le contrôle de contenu est ligne à ligne sur les lignes ajoutées de plus de 3 caractères (espaces de bord ignorés) ; une réécriture équivalente mais textuellement différente apparaît comme résidu (conservateur).
- Un résidu est « expliqué » uniquement si la branche est déjà dans l'historique (ascendance ou patch-id) et qu'un commit ultérieur de la cible modifie le même fichier ; le commit est cité dans le JSON.
- Les branches d'ancien historique (avant réécriture de septembre) sont comparées aux PR ouvertes du même historique (#270, #357, #383) ; leur éventuelle présence dans le nouvel historique n'est pas démontrée.
- Les métadonnées GitHub (état des PR) sont celles de l'instant de l'audit.

## 5. Suppression paraissant sûre mais demandant une validation humaine finale

- `audit/coherence-remboursements-deplacements` : absorption prouvée et tests verts, mais la branche finale feat/diagnostic-coherence-remboursements n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `audit/coherence-remboursements-deplacements-scan` : absorption prouvée et tests verts, mais la branche finale audit/caracterisation-scenarios-frais n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-01-02-domain-registry` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-03-cases-workflow` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-04-event-journal` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-05-file-exchange-boundary` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-06-secret-store-contract` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-07-manual-portal-connector` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-08-reference-manual-connectors` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-09-additive-persistence` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-10-structure-configuration-service` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-10b-wx-structure-connections` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-11-employee-protection-model` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-12-employee-protection-service` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-13-employee-protection-persistence` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-14-employee-protection-summary` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-15-wx-employee-protection-panel` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-16-teamworks-production-persistence` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-17a-employee-protection-composition` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-17b-wx-employee-protection-wiring` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-19-employee-protection-succession` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-20-wx-employee-protection-actions` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-21-case-dashboard-projection` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-21a-structure-hr-connections-dialog` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-22-teamworks-cases-persistence` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-23-case-dashboard-runtime` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-24-wx-case-dashboard` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-25-case-workflow-service` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-26-wx-case-workflow-actions` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-27-case-audit-history` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-28-wire-case-history` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-29-case-creation-service` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-30-new-case-dialog` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-31-case-document-tracking` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-32-wx-case-document-checklist` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-33-dashboard-document-status` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-34-lifecycle-planning` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `crh-35-lifecycle-template-persistence` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `feature/hr-document-catalog-2026-08-29` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `fix-preferences-appearance-scope-2026-08-27` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `fix-windows-icon-build-2026-08-28` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `fix/0.9.2-salary-history-ux` : absorption prouvée et tests verts, mais la branche finale fix/0.9.2-scenario-atomicity n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `fix/individual-form-core-regression-test` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine
- `hardening-post-091b-2026-08-28` : absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine

## Anomalies du premier audit (rejeu local de l'outil v1)

Rejeu v1 sur le même état : {'CONSERVER': 155, 'SUPPRESSION SÛRE': 27, 'À REVOIR': 6, 'total': 188}.

| Branche | Verdict v1 | Verdict v2 | Motif v2 |
|---|---|---|---|
| `fix/0.9.2-salary-history-ux` | SUPPRESSION SÛRE | À REVOIR | absorption prouvée et tests verts, mais la branche finale fix/0.9.2-scenario-atomicity n'est conservée que par une PR ouverte hors piles de référence : sûre tant que celle-ci est conservée — validation humaine |
| `fix/rc1-dpae-due-20260908` | CONSERVER | SUPPRESSION SÛRE | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts |
| `fix/rc1-publipostage-native-lifecycle` | CONSERVER | SUPPRESSION SÛRE | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts |
| `fix/rc1-recette-bugs-20260908` | CONSERVER | SUPPRESSION SÛRE | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts |
| `fix/rc1-stdout-flush-20260908` | CONSERVER | SUPPRESSION SÛRE | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts |
| `fix/wx-0.9.2-rc3-audit-cleanup-20260922` | CONSERVER | SUPPRESSION SÛRE | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts |
| `fix/wx-scenario-negative-duration` | CONSERVER | SUPPRESSION SÛRE | absorption prouvée vers wx/master et tests propres verts |
| `qt/frais-transactions` | CONSERVER | SUPPRESSION SÛRE | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts |
| `qt/rail-c-documents-rh` | CONSERVER | SUPPRESSION SÛRE | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts |
| `qt/vanilla-0.1-anonymisation` | CONSERVER | SUPPRESSION SÛRE | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts |
| `qt/vanilla-0.1-mysql-evidence` | CONSERVER | SUPPRESSION SÛRE | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts |
| `qt/vanilla-0.1-mysql-validation` | CONSERVER | SUPPRESSION SÛRE | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts |
| `qt/vanilla-0.1-packaging` | CONSERVER | SUPPRESSION SÛRE | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts |
