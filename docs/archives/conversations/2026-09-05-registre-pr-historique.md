# Archive — registre des PR historiques du nettoyage Teamworks

Date de capture : 2026-09-05

> Registre historique destiné à comprendre pourquoi certaines PR ont été fermées, consolidées ou conservées. L'état live de GitHub prévaut pour toute action future.

## 1. Qualification Qt et convergence

### #366 — POC isolé — couche UI Qt thémable

- qualification technique menée à terme ;
- HEAD qualifié : `dad51c0f6aafeb77dd541b3873872fb2bebffa7c` ;
- fermée sans merge vers `master` ;
- son HEAD a servi de point de départ à `qt/master`.

### #377

Qualification runtime Qt Windows / clears / stale guards / parcours A→B/A→B→C.

- fermée sans merge comme superseded ;
- contenu convergé via #381 puis matérialisé dans `qt/master`.

### #378

Clear Contrats avant lecture du salarié suivant.

- fermée sans merge comme superseded ;
- comportement conservé dans la convergence Qt.

### #380

Lifecycle des QThread bloquants.

- fermée sans merge comme superseded ;
- politique de fermeture sûre conservée dans la convergence.

### #381 — convergence Qt

- mergée dans l'ancien POC Qt ;
- merge commit : `216b264f51c6a090e6a5fc52991c67023dadd2cd` ;
- réunissait les apports qualifiés des #377/#378/#380.

### #382 — réaligner le POC sur master

- mergée dans l'ancien POC Qt ;
- commit final : `dad51c0f6aafeb77dd541b3873872fb2bebffa7c` ;
- synchronisation master → POC sans refonte manuelle des zones Frais.

### CI de qualification associée

Run historique :

- workflow `Validation et publication` ;
- run `33960215727` / #1244 ;
- HEAD `dad51c0f...` ;
- Linux : succès ;
- Windows général : succès ;
- Linux : `2123 passed, 5 skipped` ;
- packaging Windows : skipped sur ce run.

Le smoke qwindows natif spécialisé provenait de #381 et avait validé notamment PySide6, plugin `windows`, vraie event loop, lifecycle, clears et stale rejection.

## 2. Architecture et nettoyage UI wx

### #374 — Architecture : officialiser les rails wx/master et qt/master

- ouverte au moment de la capture ;
- base `wx/master` ;
- head `docs/architecture-vanilla-reference` ;
- documentation de l'architecture à deux rails ;
- aucune fusion automatique.

### #359 — normaliser le dialogue Coordonnées

- ancienne refonte UI wx ;
- fermée sans merge après validation de la trajectoire Qt.

### #360 — parcours de création de contrats

- ancienne refonte UI wx ;
- fermée sans merge après validation de la trajectoire Qt.

### #361 — Accueil RH : anniversaires

- nouvelle UI structurée wx ;
- fermée sans merge ;
- l'idée métier peut être reprise ultérieurement dans l'UI cible appropriée.

### #363 — UI géométrie : premier lot de dialogues compacts

- conservée ;
- retargetée sur `wx/master` ;
- correction wx ciblée, compatible avec la stratégie de maintenance du rail de production.

## 3. CRH / paie-ready

### #316 — Docs — cadrer la trajectoire RH paie-ready

- fermée sans merge ;
- documentation devenue superseded par l'architecture à deux rails et la consolidation CRH.

### #357 — consolidation CRH-01 → CRH-36

- conservée ouverte en draft ;
- base `wx/master` ;
- head `crh-36-lifecycle-template-management` ;
- rôle : branche de récupération du sommet de pile, pas merge direct.

PR intermédiaires de la pile fermées sans merge après consolidation :

- #317 — CRH-01/02
- #318 — CRH-03
- #319 — CRH-04
- #320 — CRH-05
- #321 — CRH-06
- #322 — CRH-07
- #323 — CRH-08
- #324 — CRH-09
- #325 — CRH-10
- #328 — CRH-11
- #329 — CRH-12
- #330 — CRH-13
- #331 — CRH-14
- #332 — CRH-15
- #333 — CRH-16
- #334 — CRH-17A
- #335 — CRH-17B
- #336 — CRH-18
- #337 — CRH-19
- #338 — CRH-20
- #340 — CRH-10B
- #341 — CRH-21
- #342 — CRH-22
- #343 — CRH-23
- #344 — CRH-24
- #345 — CRH-25
- #346 — CRH-26
- #347 — CRH-27
- #348 — CRH-28
- #349 — CRH-29
- #350 — CRH-30
- #351 — CRH-31
- #352 — CRH-32
- #353 — CRH-33
- #355 — CRH-34
- #356 — CRH-35

#339 était déjà une duplication obsolète, superseded par #340.

## 4. Documents RH

### #312

Documentation / structure du publipostage RH.

- mergée historiquement ;
- branche correspondante devenue supprimable après vérification.

### #313

Catalogue de documents RH.

- mergée historiquement ;
- branche catalogue devenue supprimable après vérification.

### #383

`Documents RH — récupérer le sélecteur et le publipostage restant`

- ouverte en draft ;
- base `wx/master` ;
- head `feature/hr-document-selector-2026-08-29` ;
- point de récupération des éléments encore absents du rail wx courant.

## 5. Scénarios / Frais

### #369

Audit de caractérisation Scénarios/Frais.

- base `wx/master` ;
- draft ;
- racine de la pile de caractérisation.

### #371

Correction de conservation du signe des durées négatives.

- empilée directement sur #369 ;
- draft.

### #372

Audit cohérence remboursements/déplacements.

- fermée sans merge ;
- contenu absorbé dans la pile #373 ;
- branche intermédiaire devenue inutile comme base.

### #373

Diagnostic read-only de cohérence remboursements/déplacements.

- base directe sur la branche #369 après retarget ;
- draft ;
- conserve l'audit de #372 et ajoute le diagnostic.

### #375

Migration transactionnelle/réversible remboursements/déplacements.

- empilée sur #373 ;
- draft ;
- ne doit pas être mergée automatiquement.

### #379

`Frais : garantir l’intégrité remboursements / déplacements`

- historiquement mergée ;
- commit `860204ddbf297b4308dac7bef5e5f2b0e6e2bf2a` ;
- corrigeait l'intégrité courante mais ne remplaçait pas l'outillage de diagnostic/migration #373/#375.

## 6. Connecthys

### #376 — audit sortie Connecthys

Conclusion récupérée :

- environ **1 255 fichiers texte** inspectés ;
- **3 références explicites** à Connecthys relevées ;
- **0 dépendance exécutable bloquante confirmée** dans ce périmètre ;
- verdict : **CONNECTHYS : NON DÉMONTRÉ** comme dépendance bloquante.

Ce verdict ne remplaçait pas la qualification terrain : bases réelles, postes Windows, tâches planifiées/services, Noethys, trafic, liens, exports/restauration, contraintes contractuelles et RGPD restaient à vérifier.

## 7. Dev legacy

### #270

`Dev legacy — profil MySQL 5.5 reproductible et anonymisation`

- conservée ouverte ;
- retargetée sur `wx/master` ;
- profil de reproduction legacy propre à Teamworks ;
- ne doit pas redéfinir le DevKit transverse moderne.

## 8. Ancien contexte RH courant

### #368

Ancien merge de travail RH courant :

- merge commit `440e0e9d98abb48262c5a910c3c99d7dd0d7b8e1` ;
- titre historique : `Merge pull request #368 from fr4nck/ccns/session-actual-hr-current`.

Cette référence est conservée uniquement pour retracer les lignées de commits ; elle n'établit aucune règle d'architecture future.

## 9. Lecture de ce registre

Les notions « ouverte », « fermée », « mergée », « mergeable » et les bases/heads sont des états datés. Pour toute action, reconsulter GitHub.

En revanche, les motifs de consolidation et les règles de gouvernance doivent être comparés aux décisions courantes dans `docs/decisions/` avant de rouvrir un ancien chantier.
