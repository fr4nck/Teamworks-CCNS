# Archive — état GitHub et travaux connus avant suppression des conversations

Date de capture : 2026-09-05

> **Archive datée, non normative pour l'état courant.**
>
> Ce document sauvegarde les branches, PR et chantiers connus au moment du nettoyage des conversations. Après cette date, l'état réel de GitHub prévaut toujours.

## 1. Architecture de branches

Branches durables validées :

- `wx/master` : production / référence wxPython ;
- `qt/master` : migration Qt ;
- `master` : conservé temporairement pour compatibilité.

Création historique :

- `wx/master` créé depuis `master@860204ddbf297b4308dac7bef5e5f2b0e6e2bf2a` ;
- `qt/master` créé depuis le HEAD Qt qualifié `dad51c0f6aafeb77dd541b3873872fb2bebffa7c`.

## 2. Qualification Qt historique

Ancienne PR #366 `POC isolé — couche UI Qt thémable` : fermée sans merge après qualification. Son HEAD qualifié a été matérialisé comme `qt/master`.

PR techniques satellites fermées comme superseded :

- #377 — qualification/runtime Qt Windows ;
- #378 — clear Contrats au changement de salarié ;
- #380 — lifecycle des QThread bloquants.

Convergence historique :

- #381 mergée dans l'ancien POC Qt ;
- merge commit `216b264f51c6a090e6a5fc52991c67023dadd2cd` ;
- #382 réalignement du POC sur master ;
- merge commit / HEAD final `dad51c0f6aafeb77dd541b3873872fb2bebffa7c`.

Qualification archivée séparément sur `qt/master` dans :

`docs/qualifications/qt/2026-09-05-qualification-initiale-qt-master.md`

## 3. PR d'architecture

### #374

Titre au moment de la capture :

`Architecture : officialiser les rails wx/master et qt/master`

- base : `wx/master` ;
- head : `docs/architecture-vanilla-reference` ;
- ouverte ;
- non mergée ;
- objectif : formaliser les deux rails, le sens wx → Qt et le rôle temporaire de `master`.

Cette PR ne doit pas être mergée automatiquement.

## 4. Consolidation CRH

La pile historique CRH-01 → CRH-36 a été consolidée dans une seule PR de récupération :

### #357

`CRH — consolidation Connexions RH / protection sociale / démarches (CRH-01 → CRH-36)`

- base : `wx/master` ;
- head : `crh-36-lifecycle-template-management` ;
- draft ;
- très divergée au moment de la capture ;
- rôle : conserver le sommet de la pile comme référence de récupération, pas comme demande de merge immédiat.

Les PR intermédiaires CRH ont été fermées sans merge après vérification que leur contenu était inclus dans la branche de sommet. La prochaine étape n'est pas de merger #357 telle quelle, mais d'extraire les composants utiles, séparer métier commun et raccordements wx, réaligner sur `wx/master` puis requalifier.

### Branches CRH intermédiaires considérées supprimables

Toutes les branches `crh-*` intermédiaires pouvaient être supprimées physiquement une fois la consolidation vérifiée, **sauf** :

`crh-36-lifecycle-template-management`

Le connecteur utilisé pendant les conversations ne permettait pas de supprimer les refs de branches ; aucune suppression physique n'était donc à considérer comme faite simplement parce qu'elle avait été recommandée.

## 5. Frais / Scénarios

Pile volontairement structurée :

### #369 — racine de caractérisation

`Audit — caractériser Scénarios et Frais avant Qt`

- base : `wx/master` ;
- head : `audit/caracterisation-scenarios-frais` ;
- draft ;
- caractérisation uniquement ;
- trois anomalies historiques exprimées en `xfail(strict=True)` : précision Decimal globale, remise à zéro du remboursement lors d'une modification de déplacement, perte du signe dans `OperationHeures`.

### #371 — signe des durées négatives

`Correction — conserver le signe des durées négatives`

- base : `audit/caracterisation-scenarios-frais` ;
- head : `fix/operation-heures-signe-negatif` ;
- draft ;
- correction isolée de `OperationHeures` dans `DLG_Scenario.py`.

### #372 — audit historique intermédiaire

`Audit — cohérence remboursements et déplacements`

- fermée sans merge ;
- ancienne branche : `audit/coherence-remboursements-deplacements` ;
- son contenu a été conservé dans la pile suivante.

### #373 — diagnostic

`feat/diagnostic-coherence-remboursements`

- base réalignée directement sur `audit/caracterisation-scenarios-frais` ;
- contient audit d'architecture + diagnostic read-only ;
- détecte notamment orphelins, projections parent obsolètes, rattachements multiples, NULL/0, incohérences de personne et projection canonique ;
- aucune écriture corrective.

### #375 — migration transactionnelle

`feat/migration-coherence-remboursements`

- base : `feat/diagnostic-coherence-remboursements` ;
- ajoute migration et CLI ;
- mode strict ;
- récupération optionnelle du parent unique ;
- blocage si état canonique invalide ;
- transaction `BEGIN IMMEDIATE` ;
- snapshot/checksum ;
- rollback exact.

Arbre voulu :

- #369 racine ;
  - #371 correction indépendante OperationHeures ;
  - #373 audit + diagnostic ;
    - #375 migration.

### #379 historique

PR historique déjà intégrée avant la séparation des rails :

`Frais : garantir l’intégrité remboursements / déplacements (#379)`

Commit associé : `860204ddbf297b4308dac7bef5e5f2b0e6e2bf2a`.

Elle avait corrigé la cohérence canonique `deplacements.IDremboursement`, la synchronisation de projection parent, la précision Decimal et plusieurs opérations create/edit/delete. Elle ne remplaçait pas à elle seule le diagnostic #373 ni la migration #375.

## 6. Documents RH

### #312

Fondations documentaires / structure de publipostage : PR historiquement mergée. La branche `docs/documents-rh-structure-publipostage` était donc considérée supprimable après vérification.

### #313

Catalogue documents RH : PR historiquement mergée. Branche `feature/hr-document-catalog-2026-08-29` considérée supprimable après vérification.

### #383

`Documents RH — récupérer le sélecteur et le publipostage restant`

- base : `wx/master` ;
- head : `feature/hr-document-selector-2026-08-29` ;
- draft ;
- branche ancienne et divergée ;
- rôle : point de récupération du sélecteur de documents RH et du publipostage encore absents de `wx/master`.

Avant toute intégration : comparer aux besoins actuels, extraire le utile, réaligner, qualifier sous Windows puis ne porter vers Qt que les frontières métier réutilisables.

## 7. Autres travaux encore suivis

### #363

`UI géométrie : borner le premier lot de dialogues compacts`

- base : `wx/master` ;
- head : `ui/dialog-geometry-batch-1` ;
- petit correctif wx ciblé, compatible avec la politique « corriger wx sans le redessiner ».

### #270

`Dev legacy — profil MySQL 5.5 reproductible et anonymisation`

- base : `wx/master` ;
- head : `dev-db-docker` ;
- profil legacy local de reproduction MySQL 5.5 ;
- ne doit pas être confondu avec le DevKit transverse moderne.

### `audit/sortie-connecthys`

Travail unique à conserver tant que la qualification terrain n'est pas achevée.

Conclusion d'audit historique : dépendance bloquante Connecthys **non démontrée** dans le code inspecté. Restent les vérifications terrain : bases réelles, postes Windows, tâches planifiées/services, Noethys, trafic, liens, exports/restauration, obligations contractuelles et RGPD.

## 8. Branches encore ambiguës au moment de la capture

À ne pas supprimer aveuglément sans comparaison finale :

- `fix/frais-integrite-remboursements` ;
- `fix/frais-decimal-remboursement` ;
- `release/0.9.1c-build`.

Motif : elles semblaient encore porter un delta par rapport à `wx/master`, même si une partie pouvait chevaucher des PR déjà intégrées.

## 9. Branches considérées supprimables après vérification

Liste historique de candidats sûrs ou fortement supportés :

- `PMSL35/qt-blocking-thread-lifecycle` ;
- `PMSL35/qt-convergence-377-378-380` ;
- `PMSL35/qt-final-gates-contract-clear` ;
- `PMSL35/qt-windows-qualification` ;
- `poc/qt-theme-isole` ;
- `audit/coherence-remboursements-deplacements` ;
- `audit/coherence-remboursements-deplacements-scan` ;
- `docs/fondations-rh-paie-ready` ;
- `feature/home-calendar-hr-foundation` ;
- `feature/hr-document-catalog-2026-08-29` ;
- `docs/documents-rh-structure-publipostage` ;
- `ui/form-standards-coordinates` ;
- `ui/recruitment-contract-flow` ;
- `release/0.9.1c` ;
- `release-0.9.1b-2026-08-28` ;
- toutes les branches CRH intermédiaires sauf `crh-36-lifecycle-template-management`.

Cette liste est une **capture historique**, pas un ordre automatique de suppression après le 2026-09-05.

## 10. Règle opérationnelle à retenir

Avant toute future suppression de branche :

1. vérifier l'état live GitHub ;
2. comparer la branche à son rail de référence ;
3. confirmer que le contenu est mergé, superseded ou conservé ailleurs ;
4. seulement ensuite supprimer la ref.

Avant toute future fusion : décision explicite requise.
