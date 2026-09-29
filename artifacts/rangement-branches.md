# Rangement Git — inventaire et plan vers trois branches permanentes

Date : 2026-09-29. Références : audit général et audit CRH (commit a2b31844), intégration Qt locale (arbre 2804c6b2, script `artifacts/replay_qt_integration.sh`).

| Branche | PR | HEAD | Branche cible | Contenu propre (commits hors cible) | Absorbé ? / preuve | CI | Verdict |
|---|---|---|---|---|---|---|---|
| `PMSL35/qt-blocking-thread-lifecycle` | #380 fermée | `b91a522929c3` | master | 198 | aucun test propre permettant de prouver le comportement sur la cible | — | **À REVOIR** |
| `PMSL35/qt-convergence-377-378-380` | #381 fermée | `3827271d5fe7` | qt/master | 8 | absorption prouvée vers qt/master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `PMSL35/qt-final-gates-contract-clear` | #378 fermée | `bab7fe272ef1` | qt/master | 2 | absorption prouvée vers qt/master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `PMSL35/qt-windows-qualification` | #377 fermée | `ea5fc10cf092` | qt/master | 7 | résidu fonctionnel non absorbé: file-absent-from-target:poc/qt-theme/benchmark_windows.cmd, file-absent-from-target:poc/qt-theme/frugality.py, file-absent-from- | — | **CONSERVER TEMPORAIREMENT** |
| `architecture/migration-noethys-teamworks` | #454 | `22fc042160ca` | master | 23 | head de PR ouverte #454 | — | **CONSERVER TEMPORAIREMENT** |
| `architecture/person-delete-usecase` | #474 | `3f3519f265b6` | master (+ wx/master pour le raccord wx) | 16 | rejoué sans conflit sur master 1673248c ; qualification du sommet à refaire | — | **INTÉGRER MASTER + WX** |
| `architecture/person-refresh-contract` | #475 | `c1480c13d29e` | master (+ wx/master pour le raccord wx) | 18 | rejoué sans conflit sur master 1673248c ; qualification du sommet à refaire | — | **INTÉGRER MASTER + WX** |
| `architecture/person-refresh-wx` | #476 | `780b6bc7b953` | master (+ wx/master pour le raccord wx) | 39 | rejoué sans conflit sur master 1673248c ; qualification du sommet à refaire | socle ✔ Windows ✔ MkDocs ✘ (base avant 09ad795e) | **INTÉGRER MASTER + WX** |
| `architecture/profils-autorisations` | #472 | `35702a4a40b2` | qt/master | 83 | intégration locale arbre 2804c6b2 (2455 tests Linux verts) ; CI Linux+Windows verte sur le HEAD du lot | Linux ✔ Windows ✔ | **INTÉGRER QT** |
| `audit/0.9.2-stop-gate` | #396 | `2d7833c074cf` | wx/master | 6 | head de PR ouverte #396 | — | **CONSERVER TEMPORAIREMENT** |
| `audit/0.9.2-ux-stop-gate` | #405 | `6602f2f990e0` | wx/master | 15 | head de PR ouverte #405 | — | **CONSERVER TEMPORAIREMENT** |
| `audit/branch-absorption` | #485 | `0deff723584b` | master | 8 | head de PR ouverte #485 | — | **CONSERVER TEMPORAIREMENT** |
| `audit/caracterisation-scenarios-frais` | #369 | `ee152d12bc0e` | master | 1 | head de PR ouverte #369; base de PR ouverte #373, #371 | — | **CONSERVER TEMPORAIREMENT** |
| `audit/coherence-remboursements-deplacements` | #372 fermée | `67cc94a03955` | feat/diagnostic-coherence-remboursements | 0 | absorption prouvée et tests verts, mais la branche finale feat/diagnostic-coherence-remboursements n'est conservée que par une PR ouverte hors piles de référenc | — | **À REVOIR** |
| `audit/coherence-remboursements-deplacements-scan` | — | `ee152d12bc0e` | audit/caracterisation-scenarios-frais | 0 | absorption prouvée et tests verts, mais la branche finale audit/caracterisation-scenarios-frais n'est conservée que par une PR ouverte hors piles de référence : | — | **À REVOIR** |
| `audit/rangement-branches` | — | `6bf2c1fbff38` | — | — | branche de travail du rangement en cours | — | **CONSERVER TEMPORAIREMENT** |
| `audit/scenarios-frais-caracterisation` | — | `fd88dbf6025d` | master | 0 | aucun test propre permettant de prouver le comportement sur la cible | — | **À REVOIR** |
| `audit/sortie-connecthys` | #376 | `a0cc779a23c5` | master | 8 | head de PR ouverte #376 | — | **CONSERVER TEMPORAIREMENT** |
| `ccns/session-actual-hr-current` | #368 fermée | `0b8fb6f81bdb` | master | 0 | absorption prouvée vers master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `ccns/session-actual-hr-inbox` | #354 fermée | `3dadf2d0adc3` | master | 18 | résidu fonctionnel non absorbé: py:application/services/inter_domain_delivery_hr.py:_canonical_json, py:application/services/inter_domain_delivery_hr.py:_mappin | — | **CONSERVER TEMPORAIREMENT** |
| `ci/frugal-mkdocs` | #480 fermée | `a0b5b54b4c83` | master | 1 | aucun test propre permettant de prouver le comportement sur la cible | — | **À REVOIR** |
| `ci/update-windows-installer-contract` | #443 fermée | `9f875f825f85` | master | 1 | absorption prouvée vers master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `ci/wx-master-validation` | #385 fermée | `cc92ac8f3e30` | wx/master | 1 | aucun test propre permettant de prouver le comportement sur la cible | — | **À REVOIR** |
| `claude/pr-474-technical-review-agnk47` | — | `a2b3184479f4` | — | — | branche de travail du rangement en cours | — | **CONSERVER TEMPORAIREMENT** |
| `contract/duree-signee-commune` | #388 fermée | `bbeae37c119a` | wx/master | 0 | absorption prouvée vers wx/master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `crh-01-02-domain-registry` | #317 fermée | `5aa44f449589` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-03-cases-workflow` | #318 fermée | `19675cfa1792` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-04-event-journal` | #319 fermée | `f674c1edd640` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-05-file-exchange-boundary` | #320 fermée | `55254326bfd6` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-06-secret-store-contract` | #321 fermée | `3f4050a6ff5b` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-07-manual-portal-connector` | #322 fermée | `d6c5a072ea4e` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-08-reference-manual-connectors` | #323 fermée | `26a1eda5e4e1` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-09-additive-persistence` | #324 fermée | `b105a0bc620b` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-10-structure-configuration-service` | #325 fermée | `a5d3eae2817b` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-10b-wx-structure-connections` | #340 fermée | `86bc7af8ac9e` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-11-employee-protection-model` | #328 fermée | `85b30e89a790` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-12-employee-protection-service` | #329 fermée | `3ada7828bbe3` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-13-employee-protection-persistence` | #330 fermée | `07738eff58fe` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-14-employee-protection-summary` | #331 fermée | `6598caffc423` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-15-wx-employee-protection-panel` | #332 fermée | `2daa5faf893a` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-16-teamworks-production-persistence` | #333 fermée | `26bf05b5c633` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-17a-employee-protection-composition` | #334 fermée | `7e1c5cc7eea3` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-17b-wx-employee-protection-wiring` | #335 fermée | `17b550f858fb` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-18-employee-protection-actions` | #336 fermée | `1f39564ba616` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-19-employee-protection-succession` | #337 fermée | `06b9b237c593` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-20-wx-employee-protection-actions` | #338 fermée | `28f358658171` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-21-case-dashboard-projection` | #341 fermée | `7ad902139c27` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-21-structure-hr-connections-ui` | #339 fermée | `1e14e018e981` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-21a-structure-hr-connections-dialog` | — | `28f358658171` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-22-teamworks-cases-persistence` | #342 fermée | `1afba7640fee` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-22-teamworks-hr-cases-persistence` | — | `3f50b83b02ce` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-23-case-dashboard-runtime` | #343 fermée | `2ae8fdff989d` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-24-wx-case-dashboard` | #344 fermée | `de48bf0a4f5f` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-25-case-workflow-service` | #345 fermée | `71c44ddcbf17` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-26-wx-case-workflow-actions` | #346 fermée | `fecea89e1c68` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-27-case-audit-history` | #347 fermée | `2f78dc071cd4` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-28-wire-case-history` | #348 fermée | `55d2043cddd1` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-29-case-creation-service` | #349 fermée | `f670534034a0` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-30-new-case-dialog` | #350 fermée | `f004ca3e470b` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-31-case-document-tracking` | #351 fermée | `4a3390266115` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-32-wx-case-document-checklist` | #352 fermée | `9880e00d175e` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-33-dashboard-document-state` | — | `9880e00d175e` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-33-dashboard-document-status` | #353 fermée | `a0b18d8e44ea` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-34-lifecycle-planning` | #355 fermée | `477f2d3f30aa` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-35-lifecycle-template-persistence` | #356 fermée | `2a2f20aff8fc` | crh-36 (audit CRH) | — | audit CRH a2b31844 : patch-id + contenu + tests | — | **SUPPRESSION SÛRE** |
| `crh-36-lifecycle-template-management` | #357 | `6a75377b1d79` | master/wx/qt après rejeu | — | #357 : référence de récupération CRH | — | **CONSERVER TEMPORAIREMENT** |
| `dev-db-docker` | #270 | `8ce2a37dc11b` | master | 1447 | head de PR ouverte #270 | — | **CONSERVER TEMPORAIREMENT** |
| `docs/architecture-vanilla-reference` | #374 | `a9767d168948` | master | 7 | head de PR ouverte #374 | — | **CONSERVER TEMPORAIREMENT** |
| `docs/branches-permanentes` | — | `8e9140bc9ea4` | master | 1 | branche de travail du rangement en cours | — | **CONSERVER TEMPORAIREMENT** |
| `docs/documents-rh-structure-publipostage` | #312 fermée | `7f0139b246d9` | master | 1578 | aucun test propre permettant de prouver le comportement sur la cible | — | **À REVOIR** |
| `docs/fondations-rh-paie-ready` | #316 fermée | `e8b3df2dc0ec` | master | 1637 | résidu fonctionnel non absorbé: file-absent-from-target:docs/67-fondations-rh-paie-ready.md, file-absent-from-target:docs/68-plan-lots-connexions-rh.md, lines-m | — | **CONSERVER TEMPORAIREMENT** |
| `docs/mkdocs` | #441 fermée | `427e6fb1a9de` | master | 0 | aucun test propre permettant de prouver le comportement sur la cible | — | **À REVOIR** |
| `docs/mkdocs-pages` | #440 fermée | `7db56187b3d9` | master | 2 | résidu fonctionnel non absorbé: file-absent-from-target:docs/index.md, file-absent-from-target:docs/reference/mots-cles-publipostage.md, file-absent-from-target | — | **CONSERVER TEMPORAIREMENT** |
| `docs/roadmap-ci789-qualification-machine` | #315 fermée | `8dbf0b29ad1d` | master | 1631 | aucun test propre permettant de prouver le comportement sur la cible | — | **À REVOIR** |
| `docs/wiki-teamworks-ccns` | — | `2939fb74e74c` | master | 150 | aucun test propre permettant de prouver le comportement sur la cible | — | **À REVOIR** |
| `docs/wiki-teamworks-ccns-2` | — | `2939fb74e74c` | master | 150 | aucun test propre permettant de prouver le comportement sur la cible | — | **À REVOIR** |
| `docs/wiki-teamworks-ccns-content` | — | `2939fb74e74c` | master | 150 | aucun test propre permettant de prouver le comportement sur la cible | — | **À REVOIR** |
| `docs/wiki-teamworks-ccns-final` | — | `2939fb74e74c` | master | 150 | aucun test propre permettant de prouver le comportement sur la cible | — | **À REVOIR** |
| `docs/wiki-teamworks-ccns-ready` | #432 fermée | `536e319655e5` | master | 176 | résidu fonctionnel non absorbé: file-absent-from-target:.github/workflows/wiki-validation.yml, file-absent-from-target:docs/wiki/Aide, discussions et signalemen | — | **CONSERVER TEMPORAIREMENT** |
| `docs/wiki-teamworks-ccns-upload` | — | `2939fb74e74c` | master | 150 | aucun test propre permettant de prouver le comportement sur la cible | — | **À REVOIR** |
| `feat/diagnostic-coherence-remboursements` | #373 | `7795c06b9409` | master | 3 | head de PR ouverte #373; base de PR ouverte #375 | — | **CONSERVER TEMPORAIREMENT** |
| `feat/migration-coherence-remboursements` | #375 | `b2a8b75217c0` | master | 4 | head de PR ouverte #375 | — | **CONSERVER TEMPORAIREMENT** |
| `feature/dpae-declarative-data` | #478 | `e4b11be2780f` | master | 89 | rejoué sans conflit sur master 1673248c ; qualification du sommet à refaire | — | **INTÉGRER MASTER** |
| `feature/dpae-domain-foundation` | #477 | `780eb98c6c64` | master | 86 | rejoué sans conflit sur master 1673248c ; qualification du sommet à refaire | socle ✔ Windows ✔ | **INTÉGRER MASTER** |
| `feature/dpae-incident-recovery` | #481 | `afad76a65d10` | master | 92 | rejoué sans conflit sur master 1673248c ; qualification du sommet à refaire | — | **INTÉGRER MASTER** |
| `feature/dpae-structured-errors` | #482 | `77d012e8db33` | master | 95 | rejoué sans conflit sur master 1673248c ; qualification du sommet à refaire | aucune CI sur le HEAD | **INTÉGRER MASTER** |
| `feature/employee-termination-documents` | — | `f2eed1fab601` | master | 18 | résidu fonctionnel non absorbé: file-absent-from-target:domain/employment/termination.py, file-absent-from-target:domain/employment/termination_documents.py, fi | — | **CONSERVER TEMPORAIREMENT** |
| `feature/employee-termination-domain` | #479 | `3cd12d1426f3` | master | 3 | rejoué sans conflit sur master 1673248c ; qualification du sommet à refaire | socle ✔ Windows ✔ MkDocs ✘ | **INTÉGRER MASTER** |
| `feature/employee-termination-persistence` | #483 | `0903cfb26118` | master | 5 | rejoué sans conflit sur master 1673248c ; qualification du sommet à refaire | — | **INTÉGRER MASTER** |
| `feature/employee-termination-transmission` | #484 | `7936bb4a3e55` | master | 7 | rejoué sans conflit sur master 1673248c ; qualification du sommet à refaire | socle ✔ Windows ✔ MkDocs ✘ (base avant 09ad795e) | **INTÉGRER MASTER** |
| `feature/home-calendar-hr-foundation` | #361 fermée | `345d963dd5c7` | wx/master | 4 | résidu fonctionnel non absorbé: py:teamworks/Ctrl/CTRL_Calendrier_tw.py:CalendrierRh, py:teamworks/Ctrl/CTRL_Calendrier_tw.py:CalendrierRh.DrawCase, py:teamwork | — | **CONSERVER TEMPORAIREMENT** |
| `feature/hr-document-catalog-2026-08-29` | #313 fermée | `538e0f7a40f3` | crh-36-lifecycle-template-management | 0 | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence :  | — | **À REVOIR** |
| `feature/hr-document-selector-2026-08-29` | #383 | `b808c722d3df` | master | 1598 | head de PR ouverte #383 | — | **CONSERVER TEMPORAIREMENT** |
| `fix-dashboard-dark-navigation-2026-08-27` | #308 fermée | `c71a092544e6` | crh-36-lifecycle-template-management | 0 | historique absorbé dans crh-36-lifecycle-template-management mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | — | **À REVOIR** |
| `fix-preferences-appearance-scope-2026-08-27` | #306 fermée | `1562d88e3144` | crh-36-lifecycle-template-management | 1 | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence :  | — | **À REVOIR** |
| `fix-windows-icon-build-2026-08-28` | #309 fermée | `fcbef16dc6f2` | crh-36-lifecycle-template-management | 0 | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence :  | — | **À REVOIR** |
| `fix-wx-personnes-column-persistence` | #413 fermée,#417 fermée | `45876d28425b` | release/vanilla-wx-0.9.2-rc3 | 0 | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de release/vanilla-wx-0.9.2-rc3)** |
| `fix-wx-personnes-column-state` | #411 fermée | `2de3f9227b5c` | release/vanilla-wx-0.9.2-rc3 | 0 | historique absorbé dans release/vanilla-wx-0.9.2-rc3 mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | — | **À REVOIR** |
| `fix-wx-personnes-publipostage-id` | #412 fermée,#418 fermée | `3a5ccbbaccb0` | release/vanilla-wx-0.9.2-rc3 | 0 | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de release/vanilla-wx-0.9.2-rc3)** |
| `fix-wx-questionnaire-init-order` | #409 fermée,#421 fermée | `ba7d2b5b24c4` | release/vanilla-wx-0.9.2-rc3 | 0 | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de release/vanilla-wx-0.9.2-rc3)** |
| `fix/0.9.1e-generalites-addresses` | #364 fermée | `0d77d1d6fb94` | wx/master | 0 | aucun test propre permettant de prouver le comportement sur la cible | — | **À REVOIR** |
| `fix/0.9.1f-render-lifecycle` | #367 fermée | `691869e58ed3` | master | 2 | absorption prouvée vers master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `fix/0.9.1f-ui-runtime-regressions` | #365 fermée | `36949b033375` | master | 2 | absorption prouvée vers master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `fix/0.9.1g-render-transaction` | — | `fdbb42e7767a` | wx/master | 2 | résidu fonctionnel non absorbé: file-absent-from-target:teamworks/Utils/UTILS_RenderTransaction.py, lines-missing:teamworks/Teamworks.py:5/5 | — | **CONSERVER TEMPORAIREMENT** |
| `fix/0.9.1g-ui-rendering` | — | `3862ab7c9bc3` | wx/master | 0 | aucun test propre permettant de prouver le comportement sur la cible | — | **À REVOIR** |
| `fix/0.9.2-audit-ccns-productive-ui` | #397 fermée | `8dd66b0f3871` | wx/master | 0 | absorption prouvée vers wx/master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `fix/0.9.2-audit-user-errors` | #399 fermée | `4ac3c40cae85` | wx/master | 0 | absorption prouvée vers wx/master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `fix/0.9.2-ccns-initial-focus` | #401 fermée | `3193aefd3ea2` | wx/master | 0 | absorption prouvée vers wx/master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `fix/0.9.2-compact-dialog-geometry` | #392 fermée | `70505fa51999` | wx/master | 0 | absorption prouvée vers wx/master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `fix/0.9.2-confirm-appli-modele-worker-lifecycle` | — | `fdb383735f17` | wx/master | 0 | absorption prouvée vers wx/master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `fix/0.9.2-entretiens-password-ux` | #407 | `f34dbd86e9ea` | wx/master | 1 | head de PR ouverte #407 | — | **CONSERVER TEMPORAIREMENT** |
| `fix/0.9.2-final-wx-ux-cleanup` | #395 fermée | `19abeee2b65d` | wx/master | 0 | absorption prouvée vers wx/master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `fix/0.9.2-frais-integrite-impression-distance` | #402 | `5172536a5ef9` | wx/master | 23 | head de PR ouverte #402 | — | **CONSERVER TEMPORAIREMENT** |
| `fix/0.9.2-frais-integrite-moteur` | — | `1018bd4da1e8` | wx/master | 13 | résidu fonctionnel non absorbé: py:scripts/audit_dialog_geometry.py:_stretch_is_action_alignment, py:teamworks/Dlg/DLG_CCNS_audit_list.py:Dialog._apply_workspac | — | **CONSERVER TEMPORAIREMENT** |
| `fix/0.9.2-legacy-ccns-audit-ux` | #403 fermée | `2d1e14d05a87` | wx/master | 0 | absorption prouvée vers wx/master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `fix/0.9.2-minicamp-recuperation-bank` | #394 | `7149fe069d30` | wx/master | 7 | head de PR ouverte #394 | — | **CONSERVER TEMPORAIREMENT** |
| `fix/0.9.2-presences-moteur` | #406 | `bbd08d66ad58` | wx/master | 7 | head de PR ouverte #406 | — | **CONSERVER TEMPORAIREMENT** |
| `fix/0.9.2-salary-history-language` | #400 fermée | `a4ba31ed524f` | wx/master | 0 | absorption prouvée vers wx/master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `fix/0.9.2-salary-history-ux` | #393 fermée | `2c9f2ebfd384` | fix/0.9.2-scenario-atomicity | 5 | absorption prouvée et tests verts, mais la branche finale fix/0.9.2-scenario-atomicity n'est conservée que par une PR ouverte hors piles de référence : sûre tan | — | **À REVOIR** |
| `fix/0.9.2-scenario-atomicity` | #398 | `eb0ad8c071b0` | wx/master | 13 | head de PR ouverte #398 | — | **CONSERVER TEMPORAIREMENT** |
| `fix/0.9.2-scenario-presence-duration` | #404 | `8ae321076e6e` | wx/master | 5 | head de PR ouverte #404 | — | **CONSERVER TEMPORAIREMENT** |
| `fix/coords-toggle-hotfix` | #358 fermée | `363a79231b0f` | wx/master | 9 | résidu fonctionnel non absorbé: lines-missing:teamworks/Dlg/DLG_Saisie_coords.py:4/9 | — | **CONSERVER TEMPORAIREMENT** |
| `fix/frais-decimal-remboursement` | #370 fermée | `6a2e7f0ad204` | wx/master | 3 | résidu fonctionnel non absorbé: lines-missing:teamworks/Dlg/DLG_Saisie_deplacement.py:1/1 | — | **CONSERVER TEMPORAIREMENT** |
| `fix/frais-integrite-remboursements` | #379 fermée | `c885f55fe458` | master | 14 | absorption prouvée vers master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `fix/individual-form-core-regression-test` | #314 fermée | `c2d758327f63` | crh-36-lifecycle-template-management | 0 | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence :  | — | **À REVOIR** |
| `fix/operation-heures-signe-negatif` | #371 | `bfbdbc39fc69` | wx/master | 2 | head de PR ouverte #371 | — | **CONSERVER TEMPORAIREMENT** |
| `fix/rc1-dpae-due-20260908` | #424 fermée | `5cdd89d1a88d` | release/vanilla-wx-0.9.2-rc3 | 1 | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de release/vanilla-wx-0.9.2-rc3)** |
| `fix/rc1-publipostage-native-lifecycle` | #427 fermée | `067a6bb2e68b` | release/vanilla-wx-0.9.2-rc3 | 2 | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de release/vanilla-wx-0.9.2-rc3)** |
| `fix/rc1-publipostage-typeerror-null` | #426 fermée | `802458481b72` | wx/master | 50 | résidu fonctionnel non absorbé: py:teamworks/Dlg/DLG_Saisie_champs_publipostage.py:_nullable_db_text, lines-missing:teamworks/Dlg/DLG_Saisie_champs_publipostage | — | **CONSERVER TEMPORAIREMENT** |
| `fix/rc1-recette-bugs-20260908` | #423 fermée | `66a5091293a5` | release/vanilla-wx-0.9.2-rc3 | 0 | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de release/vanilla-wx-0.9.2-rc3)** |
| `fix/rc1-stdout-flush-20260908` | #425 fermée | `ab11e7b6198e` | release/vanilla-wx-0.9.2-rc3 | 2 | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de release/vanilla-wx-0.9.2-rc3)** |
| `fix/rc2-individual-form-lazy-test` | #429 fermée | `0b20d93ac692` | release/vanilla-wx-0.9.2-rc3 | 0 | historique absorbé dans release/vanilla-wx-0.9.2-rc3 mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | — | **À REVOIR** |
| `fix/rc2-ui-state-context-refresh-20260919` | #442 | `5712aa019c55` | wx/master | 6 | head de PR ouverte #442 | — | **CONSERVER TEMPORAIREMENT** |
| `fix/rc3-updater-prerelease` | #434 fermée,#433 fermée | `1b12eec383bc` | release/vanilla-wx-0.9.2-rc3 | 0 | historique absorbé dans release/vanilla-wx-0.9.2-rc3 mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | — | **À REVOIR** |
| `fix/scenario-report-cycles` | #387 fermée | `492cfdfa26a0` | wx/master | 6 | absorption prouvée vers wx/master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `fix/vanilla-wx-0.9.2-rc2-c-f` | — | `4dd3d25ecf7a` | wx/master | 69 | résidu fonctionnel non absorbé: py:scripts/audit_dialog_geometry.py:_stretch_is_action_alignment, py:teamworks/Ctrl/CTRL_Creation_contrat_p6.py:_database_ready, | — | **CONSERVER TEMPORAIREMENT** |
| `fix/wx-0.9.2-rc3-audit-cleanup-20260922` | — | `26f48cc21ed6` | release/vanilla-wx-0.9.2-rc3 | 0 | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de release/vanilla-wx-0.9.2-rc3)** |
| `fix/wx-0.9.2-rc3-final-stabilisation-20260921` | — | `674df21375a0` | wx/master | 357 | résidu fonctionnel non absorbé: py:scripts/audit_dialog_geometry.py:_stretch_is_action_alignment, py:teamworks/Ctrl/CTRL_Bouton_image.py:Compact, py:teamworks/C | — | **CONSERVER TEMPORAIREMENT** |
| `fix/wx-customize-encoding` | #439 fermée | `2f6ba3817e04` | wx/master | 105 | résidu fonctionnel non absorbé: lines-missing:docs/02_PYTHON3_PHOENIX.md:1/21, lines-missing:teamworks/Teamworks.py:6/107, lines-missing:teamworks/Utils/UTILS_A | — | **CONSERVER TEMPORAIREMENT** |
| `fix/wx-dialog-root-panel-sizers` | #416 fermée,#420 fermée | `f5552dc60420` | release/vanilla-wx-0.9.2-rc3 | 0 | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de release/vanilla-wx-0.9.2-rc3)** |
| `fix/wx-scenario-negative-duration` | #384 fermée | `c5f80bad95ac` | wx/master | 5 | absorption prouvée vers wx/master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `fix/wx-window-work-area` | #415 fermée,#419 fermée | `18cbef2cb29c` | release/vanilla-wx-0.9.2-rc3 | 0 | absorption prouvée vers release/vanilla-wx-0.9.2-rc3 et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de release/vanilla-wx-0.9.2-rc3)** |
| `hardening-post-091b-2026-08-28` | #311 fermée | `3006a785c268` | crh-36-lifecycle-template-management | 6 | absorption prouvée et tests verts, mais la branche finale crh-36-lifecycle-template-management n'est conservée que par une PR ouverte hors piles de référence :  | — | **À REVOIR** |
| `master` | #382 fermée,#267 fermée,#266 fermée,#264 fermée,#263 fermée,#261 fermée,#260 fermée,#258 fermée,#251 fermée | `1673248ce646` | — | — |  | ✔ run 1832 sur 1673248c | **PERMANENTE** |
| `perf-wx-personnes-latency` | #408 fermée | `377dd2089130` | release/vanilla-wx-0.9.2-rc3 | 0 | historique absorbé dans release/vanilla-wx-0.9.2-rc3 mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | — | **À REVOIR** |
| `perf-wx-presences-latency` | #410 fermée | `f2a7438ad5d2` | release/vanilla-wx-0.9.2-rc3 | 0 | historique absorbé dans release/vanilla-wx-0.9.2-rc3 mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | — | **À REVOIR** |
| `poc/qt-theme-isole` | #366 fermée | `dad51c0f6aaf` | qt/master | 0 | absorption prouvée vers qt/master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `qt/contracts-amendment-foundation` | — | `81f8036851b9` | qt/master | 134 | intégration locale arbre 2804c6b2 (2455 tests Linux verts) ; CI Linux+Windows verte sur le HEAD du lot | Linux ✔ Windows ✔ (#1850) | **INTÉGRER QT** |
| `qt/contracts-cee-create` | #448,#449 fermée | `3ceaad829ff7` | qt/master | 90 | intégration locale arbre 2804c6b2 (2455 tests Linux verts) ; CI Linux+Windows verte sur le HEAD du lot | — | **INTÉGRER QT** |
| `qt/contracts-classification-prep` | #457,#458 fermée | `7f64cb099f01` | qt/master | 102 | intégration locale arbre 2804c6b2 (2455 tests Linux verts) ; CI Linux+Windows verte sur le HEAD du lot | — | **INTÉGRER QT** |
| `qt/contracts-probation-prep` | #460,#461 fermée | `72b663e3eba0` | qt/master | 108 | intégration locale arbre 2804c6b2 (2455 tests Linux verts) ; CI Linux+Windows verte sur le HEAD du lot | — | **INTÉGRER QT** |
| `qt/contracts-renewal-prep` | #455,#456 fermée | `bc58c7618a2c` | qt/master | 95 | intégration locale arbre 2804c6b2 (2455 tests Linux verts) ; CI Linux+Windows verte sur le HEAD du lot | — | **INTÉGRER QT** |
| `qt/contracts-ui-gate` | #465 fermée,#464 | `e4ea900c6402` | qt/master | 116 | intégration locale arbre 2804c6b2 (2455 tests Linux verts) ; CI Linux+Windows verte sur le HEAD du lot | — | **INTÉGRER QT** |
| `qt/contracts-ui-prep` | #462,#463 fermée | `ec243bb027b9` | qt/master | 112 | intégration locale arbre 2804c6b2 (2455 tests Linux verts) ; CI Linux+Windows verte sur le HEAD du lot | — | **INTÉGRER QT** |
| `qt/convergence-0.9.2-rc3` | #431 fermée | `d40c78669873` | qt/master | 74 | intégration locale arbre 2804c6b2 (2455 tests Linux verts) ; CI Linux+Windows verte sur le HEAD du lot | — | **INTÉGRER QT** |
| `qt/document-core-iteration-1` | — | `a87b9da4e9cb` | qt/master | 32 | résidu fonctionnel non absorbé: py:domain/documents/merge_context.py:MergeContext.from_mapping, py:domain/repositories/person_data.py:PersonCoordinateRecord, py | — | **CONSERVER TEMPORAIREMENT** |
| `qt/document-core-iteration-2` | #436 fermée,#435 fermée | `2ae9fe2ddf79` | qt/master | 33 | résidu fonctionnel non absorbé: py:domain/documents/merge_context.py:MergeContext.from_mapping, file-absent-from-target:docs/DOCUMENT_CORE_ITERATION_1.md, file- | — | **CONSERVER TEMPORAIREMENT** |
| `qt/document-core-iteration-3` | #438 fermée,#437 fermée | `5c8b5981dc56` | qt/master | 34 | résidu fonctionnel non absorbé: py:domain/documents/merge_context.py:MergeContext.from_mapping, file-absent-from-target:docs/DOCUMENT_CORE_ITERATION_1.md, file- | — | **CONSERVER TEMPORAIREMENT** |
| `qt/frais-transactions` | #444 fermée,#466 fermée,#445 fermée | `4d81b5850f41` | qt/vanilla-0.1-rc | 0 | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de qt/vanilla-0.1-rc)** |
| `qt/integration-0.2-rc1` | — | `caed9650df74` | qt/master | 202 | intégration locale arbre 2804c6b2 (2455 tests Linux verts) ; CI Linux+Windows verte sur le HEAD du lot | — | **INTÉGRER QT** |
| `qt/master` | — | `36db74ab70bb` | — | — |  | — | **PERMANENTE** |
| `qt/presence-transactions` | #451 fermée,#450 | `de184614c418` | qt/master | 115 | intégration locale arbre 2804c6b2 (2455 tests Linux verts) ; CI Linux+Windows verte sur le HEAD du lot | Linux ✔ Windows ✔ | **INTÉGRER QT** |
| `qt/rail-c-documents-rh` | #453 fermée | `49449e6f7b6d` | qt/vanilla-0.1-rc | 0 | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de qt/vanilla-0.1-rc)** |
| `qt/scenario-transactions` | #446,#447 fermée | `46f2b07aed32` | qt/master | 77 | intégration locale arbre 2804c6b2 (2455 tests Linux verts) ; CI Linux+Windows verte sur le HEAD du lot | Linux ✔ Windows ✔ | **INTÉGRER QT** |
| `qt/vanilla-0.1-anonymisation` | #468 fermée | `ea05126ca52e` | qt/vanilla-0.1-rc | 0 | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de qt/vanilla-0.1-rc)** |
| `qt/vanilla-0.1-go-no-go` | #471 fermée | `3cf725098b35` | qt/vanilla-0.1-rc | 0 | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de qt/vanilla-0.1-rc)** |
| `qt/vanilla-0.1-mysql-evidence` | #470 fermée | `20ee79a12c6a` | qt/vanilla-0.1-rc | 0 | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de qt/vanilla-0.1-rc)** |
| `qt/vanilla-0.1-mysql-validation` | #469 fermée | `d55bb45f98f1` | qt/vanilla-0.1-rc | 0 | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de qt/vanilla-0.1-rc)** |
| `qt/vanilla-0.1-packaging` | #459 fermée | `4d35c618f089` | qt/vanilla-0.1-rc | 0 | absorption prouvée vers qt/vanilla-0.1-rc et tests propres verts | — | **SUPPRESSION SÛRE (après intégration de qt/vanilla-0.1-rc)** |
| `qt/vanilla-0.1-rc` | #467 | `caed9650df74` | qt/master | 202 | intégration locale arbre 2804c6b2 (2455 tests Linux verts) ; CI Linux+Windows verte sur le HEAD du lot | Linux ✔ Windows ✔ Packaging ✔ | **INTÉGRER QT** |
| `rail-c/documents-rh-publipostage` | #452 | `8edfb4ded534` | wx/master | 42 | head de PR ouverte #452 | — | **CONSERVER TEMPORAIREMENT** |
| `refactor/0.9.2-modular-foundations` | #428 fermée | `0b20d93ac692` | release/vanilla-wx-0.9.2-rc3 | 0 | historique absorbé dans release/vanilla-wx-0.9.2-rc3 mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | — | **À REVOIR** |
| `release-0.9.1b-2026-08-28` | #310 fermée | `52231436173e` | wx/master | 1575 | aucun test propre permettant de prouver le comportement sur la cible | — | **À REVOIR** |
| `release/0.9.1c` | #326 fermée | `8048ceacaf69` | wx/master | 1634 | résidu fonctionnel non absorbé: file-absent-from-target:docs/RELEASE_0.9.1c.md, lines-missing:VERSION:1/1 | — | **CONSERVER TEMPORAIREMENT** |
| `release/0.9.1c-build` | #327 fermée | `14d2d20c8889` | wx/master | 1636 | résidu fonctionnel non absorbé: file-absent-from-target:docs/RELEASE_0.9.1c.md | — | **CONSERVER TEMPORAIREMENT** |
| `release/vanilla-wx-0.9.2-rc1` | #422 fermée | `748a36282718` | release/vanilla-wx-0.9.2-rc3 | 0 | historique absorbé dans release/vanilla-wx-0.9.2-rc3 mais tests propres en échec sur la cible : comportement modifié ensuite, à confirmer | — | **À REVOIR** |
| `release/vanilla-wx-0.9.2-rc2` | — | `dfa21c471b69` | wx/master | 67 | résidu fonctionnel non absorbé: py:scripts/audit_dialog_geometry.py:_stretch_is_action_alignment, py:teamworks/Ctrl/CTRL_Creation_contrat_p6.py:_database_ready, | — | **CONSERVER TEMPORAIREMENT** |
| `release/vanilla-wx-0.9.2-rc3` | #430 | `37755f8375ee` | wx/master | 299 | head de PR ouverte #430 | — | **CONSERVER TEMPORAIREMENT** |
| `test/0.9.2-recette-windows-interactive` | #414 | `71a75ecacd86` | wx/master | 19 | head de PR ouverte #414 | — | **CONSERVER TEMPORAIREMENT** |
| `test/0.9.2-scenario-integration` | — | `741fb8b19755` | wx/master | 1 | résidu fonctionnel non absorbé: py:scripts/audit_dialog_geometry.py:_stretch_is_action_alignment, py:teamworks/Dlg/DLG_CCNS_audit_list.py:Dialog._apply_workspac | — | **CONSERVER TEMPORAIREMENT** |
| `test/0.9.2-scenario-stacked` | — | `b1735b91371f` | wx/master | 16 | résidu fonctionnel non absorbé: py:scripts/audit_dialog_geometry.py:_stretch_is_action_alignment, py:teamworks/Dlg/DLG_CCNS_audit_list.py:Dialog._apply_workspac | — | **CONSERVER TEMPORAIREMENT** |
| `tw10-01-atomic-sqlite-restore` | #386 | `525e09b67aca` | wx/master | 7 | head de PR ouverte #386 | — | **CONSERVER TEMPORAIREMENT** |
| `tw10-03-rh-transaction-atomicity` | #390 | `4bb4c5bc6f0a` | wx/master | 1 | head de PR ouverte #390 | — | **CONSERVER TEMPORAIREMENT** |
| `tw10-04-dispatch-helper` | — | `860204ddbf29` | master | 0 | absorption prouvée vers master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `tw10-04-windows-release-qualification` | #391 | `adce8bd09a28` | wx/master | 1 | head de PR ouverte #391 | — | **CONSERVER TEMPORAIREMENT** |
| `ui/dialog-geometry-audit` | #362 fermée | `dce27c099eb0` | master | 5 | absorption prouvée vers master et tests propres verts | — | **SUPPRESSION SÛRE** |
| `ui/dialog-geometry-batch-1` | #363 fermée | `982de8c51399` | wx/master | 3 | tests propres en échec sur master | — | **CONSERVER TEMPORAIREMENT** |
| `ui/form-standards-coordinates` | #359 fermée | `ff110207f121` | wx/master | 24 | résidu fonctionnel non absorbé: py:teamworks/Dlg/DLG_Saisie_coords.py:Dialog._fit_to_content, lines-missing:teamworks/Ctrl/CTRL_Page_generalites.py:15/15, lines | — | **CONSERVER TEMPORAIREMENT** |
| `ui/recruitment-contract-flow` | #360 fermée | `a78a67f40999` | wx/master | 19 | résidu fonctionnel non absorbé: lines-missing:teamworks/Ctrl/CTRL_Creation_contrat_p1.py:44/44, lines-missing:teamworks/Ctrl/CTRL_Creation_contrat_p2.py:112/113 | — | **CONSERVER TEMPORAIREMENT** |
| `ux/person-search-contract` | #473 | `782f14b84fb3` | master | 7 | rejoué sans conflit sur master 1673248c ; qualification du sommet à refaire | socle ✘ | **INTÉGRER MASTER** |
| `vanilla-bugfix` | — | `bfd7b094cba5` | wx/master | 122 | résidu fonctionnel non absorbé: file-absent-from-target:CHANGELOG.md, lines-missing:teamworks/Ctrl/CTRL_Bouton_image.py:10/10, lines-missing:teamworks/Ctrl/CTRL | — | **CONSERVER TEMPORAIREMENT** |
| `wx/master` | — | `fdb383735f17` | — | — |  | — | **PERMANENTE** |
| `wx/raccord-operation-heures` | #389 | `c4621f8556f0` | wx/master | 3 | head de PR ouverte #389 | — | **CONSERVER TEMPORAIREMENT** |

## Suppressions immédiatement autorisées (61)

Suppression physique bloquée dans cette session (HTTP 403 sur `git push origin --delete`). À exécuter depuis une session autorisée ; le script vérifie chaque HEAD avant suppression et s'arrête sur tout écart.

```sh
set -e
check_and_delete() { cur=$(git ls-remote origin "refs/heads/$1" | cut -f1); if [ "$cur" = "$2" ]; then git push origin --delete "$1"; else echo "STOP $1 : HEAD $cur ≠ $2 — réauditer"; fi; }
check_and_delete PMSL35/qt-convergence-377-378-380 3827271d5fe79470ba14fc035a3a560b64d4fc9a
check_and_delete PMSL35/qt-final-gates-contract-clear bab7fe272ef1eaf4b1dec50630e70cd0887bdd4b
check_and_delete ccns/session-actual-hr-current 0b8fb6f81bdb780400e911f0df15444f5681eac0
check_and_delete ci/update-windows-installer-contract 9f875f825f852c163238e168d8a7695c4fd5b4c0
check_and_delete contract/duree-signee-commune bbeae37c119ae71363332ac965b9086a909f5ce9
check_and_delete crh-01-02-domain-registry 5aa44f449589099f61cb0443f4f8aac8e97401ae
check_and_delete crh-03-cases-workflow 19675cfa1792d972e9bc3a8a8d7d66f82605d9f4
check_and_delete crh-04-event-journal f674c1edd6404861359de693907e24781027af78
check_and_delete crh-05-file-exchange-boundary 55254326bfd6a60687b3f3ae4a6348d498e0890a
check_and_delete crh-06-secret-store-contract 3f4050a6ff5b5e8a1242f6de218aa7e059ce4ae9
check_and_delete crh-07-manual-portal-connector d6c5a072ea4ea51b910e2b4f1b534989adcedf34
check_and_delete crh-08-reference-manual-connectors 26a1eda5e4e10c259dc96801e566a14ae2c0ed0c
check_and_delete crh-09-additive-persistence b105a0bc620b7182d5296805958fabb57fec7e64
check_and_delete crh-10-structure-configuration-service a5d3eae2817bcd90b9966e9b19dd1b3dc0716917
check_and_delete crh-10b-wx-structure-connections 86bc7af8ac9e5cd35dd5607713916d0511fd69c2
check_and_delete crh-11-employee-protection-model 85b30e89a790cb3472942666ace2cd78c8eedef8
check_and_delete crh-12-employee-protection-service 3ada7828bbe380f72a274f23df7f05a45b406759
check_and_delete crh-13-employee-protection-persistence 07738eff58fef5d23eda0ab9944cfcf768c6f88c
check_and_delete crh-14-employee-protection-summary 6598caffc4234a6427b71d5612cb4c9a63b5fcf8
check_and_delete crh-15-wx-employee-protection-panel 2daa5faf893a98832f76685a8d67bab0772dbac9
check_and_delete crh-16-teamworks-production-persistence 26bf05b5c6333c7297d92de9d2b0da3f2d58ce56
check_and_delete crh-17a-employee-protection-composition 7e1c5cc7eea3df96c537ba390559a954390f3344
check_and_delete crh-17b-wx-employee-protection-wiring 17b550f858fbd15c73da0cf35ed06e7c578f8513
check_and_delete crh-18-employee-protection-actions 1f39564ba616eecd0e9a7364356e93dfa48238c0
check_and_delete crh-19-employee-protection-succession 06b9b237c5933000b61daad64db28d5aad561c63
check_and_delete crh-20-wx-employee-protection-actions 28f3586581718f14789c6deee858895cec7764a7
check_and_delete crh-21-case-dashboard-projection 7ad902139c276ecfbe9727c4b6e16d8483d72235
check_and_delete crh-21-structure-hr-connections-ui 1e14e018e98161b27e460cad0e40dbe29b74cede
check_and_delete crh-21a-structure-hr-connections-dialog 28f3586581718f14789c6deee858895cec7764a7
check_and_delete crh-22-teamworks-cases-persistence 1afba7640fee2f6c927ff6b9acc44f57d578fc5e
check_and_delete crh-22-teamworks-hr-cases-persistence 3f50b83b02ce5b93a3e449f4db6c66aed33ce1b9
check_and_delete crh-23-case-dashboard-runtime 2ae8fdff989d7d1efa665e500677fa7713e98db8
check_and_delete crh-24-wx-case-dashboard de48bf0a4f5fae65a551ab1add10497c6854949d
check_and_delete crh-25-case-workflow-service 71c44ddcbf17f911c5af853757eb719778a5b976
check_and_delete crh-26-wx-case-workflow-actions fecea89e1c68463ecd26d923eab1ee48f477e13f
check_and_delete crh-27-case-audit-history 2f78dc071cd47f698885d97ecd4d12d78dccad38
check_and_delete crh-28-wire-case-history 55d2043cddd1e43cebaa5d6adfde15be88c2c5bd
check_and_delete crh-29-case-creation-service f670534034a03e341d0ceb0fa921231f297e0048
check_and_delete crh-30-new-case-dialog f004ca3e470b6b58845ff90a299ad95f7448983b
check_and_delete crh-31-case-document-tracking 4a339026611556f145decdf6f265fc1b5a7ad0d9
check_and_delete crh-32-wx-case-document-checklist 9880e00d175e60df81abd6922338b7f145b01fc3
check_and_delete crh-33-dashboard-document-state 9880e00d175e60df81abd6922338b7f145b01fc3
check_and_delete crh-33-dashboard-document-status a0b18d8e44ea11e0a4e37731ca79e0f4ea70fccc
check_and_delete crh-34-lifecycle-planning 477f2d3f30aa3568bc94cc5c9182efc18d6ae3f4
check_and_delete crh-35-lifecycle-template-persistence 2a2f20aff8fc1696e095d8b1186178bfe6bb9cf3
check_and_delete fix/0.9.1f-render-lifecycle 691869e58ed35fef03eadb21af719d3ffc07617e
check_and_delete fix/0.9.1f-ui-runtime-regressions 36949b033375e26a977105ebf58981497377fc1c
check_and_delete fix/0.9.2-audit-ccns-productive-ui 8dd66b0f387158d5fe8ca3355dc24095dd210eb0
check_and_delete fix/0.9.2-audit-user-errors 4ac3c40cae85c7ecf25f8331f0e2bb33324891ab
check_and_delete fix/0.9.2-ccns-initial-focus 3193aefd3ea2280b1d21df208757dfe407bfe17a
check_and_delete fix/0.9.2-compact-dialog-geometry 70505fa51999af588b3ff0fc9995936461af6534
check_and_delete fix/0.9.2-confirm-appli-modele-worker-lifecycle fdb383735f176dc04c2e43576e376fe7adfaba1b
check_and_delete fix/0.9.2-final-wx-ux-cleanup 19abeee2b65dcf2bfe9e4d6d8ffe890246096c6b
check_and_delete fix/0.9.2-legacy-ccns-audit-ux 2d1e14d05a871e898272779e214e3e96ec390225
check_and_delete fix/0.9.2-salary-history-language a4ba31ed524f958ec4217100acedb03da8499091
check_and_delete fix/frais-integrite-remboursements c885f55fe45855420b4e7d79f5496624a67ef1cb
check_and_delete fix/scenario-report-cycles 492cfdfa26a010bca110852caa56fcfcea29379a
check_and_delete fix/wx-scenario-negative-duration c5f80bad95ac1fbfd206c4b300ebd8fc5e52389f
check_and_delete poc/qt-theme-isole dad51c0f6aafeb77dd541b3873872fb2bebffa7c
check_and_delete tw10-04-dispatch-helper 860204ddbf297b4308dac7bef5e5f2b0e6e2bf2a
check_and_delete ui/dialog-geometry-audit dce27c099eb06d26483ee5e9b7fee6526f3b6554
```
