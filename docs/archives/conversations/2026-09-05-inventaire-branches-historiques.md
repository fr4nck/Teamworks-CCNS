# Archive — inventaire de branches historiques avant nettoyage

Date de capture : 2026-09-05

> Cette liste sert uniquement à préserver la mémoire du nettoyage Git. L'état live du dépôt prévaut. Une branche listée ici comme supprimable ne doit pas être supprimée à l'aveugle à une date ultérieure sans revalidation.

## 1. Noyau durable

- `wx/master`
- `qt/master`
- `master` — temporaire pour compatibilité

## 2. Travaux actifs ou à conserver au moment de la capture

- `docs/architecture-vanilla-reference` — PR #374
- `crh-36-lifecycle-template-management` — PR #357
- `audit/caracterisation-scenarios-frais` — PR #369
- `fix/operation-heures-signe-negatif` — PR #371
- `feat/diagnostic-coherence-remboursements` — PR #373
- `feat/migration-coherence-remboursements` — PR #375
- `ui/dialog-geometry-batch-1` — PR #363
- `dev-db-docker` — PR #270
- `feature/hr-document-selector-2026-08-29` — PR #383
- `audit/sortie-connecthys`

Branches encore à comparer avant décision définitive :

- `fix/frais-integrite-remboursements`
- `fix/frais-decimal-remboursement`
- `release/0.9.1c-build`

## 3. Pile CRH intermédiaire — branches historiques

Le sommet à conserver était `crh-36-lifecycle-template-management`.

Branches intermédiaires devenues candidates à suppression après consolidation :

- `crh-01-02-domain-registry`
- `crh-03-cases-workflow`
- `crh-04-event-journal`
- `crh-05-file-exchange-boundary`
- `crh-06-secret-store-contract`
- `crh-07-manual-portal-connector`
- `crh-08-reference-manual-connectors`
- `crh-09-additive-persistence`
- `crh-10-structure-configuration-service`
- `crh-10b-wx-structure-connections`
- `crh-11-employee-protection-model`
- `crh-12-employee-protection-service`
- `crh-13-employee-protection-persistence`
- `crh-14-employee-protection-summary`
- `crh-15-wx-employee-protection-panel`
- `crh-16-teamworks-production-persistence`
- `crh-17a-employee-protection-composition`
- `crh-17b-wx-employee-protection-wiring`
- `crh-18-employee-protection-actions`
- `crh-19-employee-protection-succession`
- `crh-20-wx-employee-protection-actions`
- `crh-21-case-dashboard-projection`
- `crh-21-structure-hr-connections-ui`
- `crh-21a-structure-hr-connections-dialog`
- `crh-22-teamworks-cases-persistence`
- `crh-22-teamworks-hr-cases-persistence`
- `crh-23-case-dashboard-runtime`
- `crh-24-wx-case-dashboard`
- `crh-25-case-workflow-service`
- `crh-26-wx-case-workflow-actions`
- `crh-27-case-audit-history`
- `crh-28-wire-case-history`
- `crh-29-case-creation-service`
- `crh-30-new-case-dialog`
- `crh-31-case-document-tracking`
- `crh-32-wx-case-document-checklist`
- `crh-33-dashboard-document-state`
- `crh-33-dashboard-document-status`
- `crh-34-lifecycle-planning`
- `crh-35-lifecycle-template-persistence`

## 4. Qt POC / convergence — branches historiques devenues obsolètes

- `PMSL35/qt-blocking-thread-lifecycle`
- `PMSL35/qt-convergence-377-378-380`
- `PMSL35/qt-final-gates-contract-clear`
- `PMSL35/qt-windows-qualification`
- `poc/qt-theme-isole`

Le contenu qualifié de ce dernier a été matérialisé dans `qt/master` ; il ne doit plus être traité comme le rail durable.

## 5. Anciennes branches UI / docs / release devenues candidates à suppression

- `audit/coherence-remboursements-deplacements`
- `audit/coherence-remboursements-deplacements-scan`
- `docs/fondations-rh-paie-ready`
- `feature/home-calendar-hr-foundation`
- `feature/hr-document-catalog-2026-08-29`
- `docs/documents-rh-structure-publipostage`
- `ui/form-standards-coordinates`
- `ui/recruitment-contract-flow`
- `release/0.9.1c`
- `release-0.9.1b-2026-08-28`

## 6. Branches observées lors du ratissage initial

La capture initiale comptait environ 88 branches. Parmi elles figuraient aussi :

- `audit/caracterisation-scenarios-frais`
- `audit/coherence-remboursements-deplacements`
- `audit/coherence-remboursements-deplacements-scan`
- `audit/scenarios-frais-caracterisation`
- `audit/sortie-connecthys`
- `ccns/session-actual-hr-current`
- `ccns/session-actual-hr-inbox`
- `dev-db-docker`
- `docs/architecture-vanilla-reference`
- `docs/documents-rh-structure-publipostage`
- `docs/fondations-rh-paie-ready`
- `docs/roadmap-ci789-qualification-machine`
- `feat/diagnostic-coherence-remboursements`
- `feat/migration-coherence-remboursements`
- `feature/home-calendar-hr-foundation`
- `feature/hr-document-catalog-2026-08-29`
- `feature/hr-document-selector-2026-08-29`
- `fix/coords-toggle-hotfix`
- `fix/frais-decimal-remboursement`
- `fix/frais-integrite-remboursements`
- `fix/individual-form-core-regression-test`
- `fix/operation-heures-signe-negatif`
- `fix/0.9.1e-generalites-addresses`
- `fix/0.9.1f-render-lifecycle`
- `fix/0.9.1f-ui-runtime-regressions`
- `fix/0.9.1g-render-transaction`
- `fix/0.9.1g-ui-rendering`
- `fix-dashboard-dark-navigation-2026-08-27`
- `fix-preferences-appearance-scope-2026-08-27`
- `fix-windows-icon-build-2026-08-28`
- `hardening-post-091b-2026-08-28`
- `release/0.9.1c-build`
- `ui/dialog-geometry-audit`
- `ui/dialog-geometry-batch-1`
- `ui/form-standards-coordinates`
- `ui/recruitment-contract-flow`
- `vanilla-bugfix`

Cette liste n'implique ni conservation ni suppression automatique ; elle documente simplement l'état foisonnant qui a motivé la consolidation.

## 7. Règle de suppression

Une branche peut être supprimée lorsque son contenu est démontré comme :

- mergé dans un rail durable ;
- inclus dans une branche de consolidation conservée ;
- superseded par une autre branche/PR qui porte l'intégralité du delta utile ;
- ou explicitement abandonné après décision fonctionnelle.

À défaut, conserver et comparer.
