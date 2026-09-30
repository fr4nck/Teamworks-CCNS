# Qt Integration 0.2 RC1

## Objet

Cette branche consolide une base Qt unique, installable et testable, sans ajouter de nouvelle fonctionnalité.

## Point de départ

- Branche source : `qt/vanilla-0.1-rc`
- SHA de départ : `caed9650df74609f1b0e920fa4d946aa3456cfd8`
- PR source de référence : #467

## Règle de branchement

Toute nouvelle branche Qt doit partir de la dernière branche d'intégration verte. Une ancienne PR ou branche empilée ne doit pas servir directement de base à un nouveau développement.

## Audit initial

| Lot | PR | HEAD actuel | Base actuelle | CI HEAD | Relation avec #467 | Verdict initial |
|---|---:|---|---|---|---|---|
| Contrats avancés / avenants | #486 | `81f8036851b9232a547b99ec9b1789f04516c056` | `qt/convergence-0.9.2-rc3` | Validation Qt SUCCESS | diverge depuis `d40c786...`; 60 commits propres | INTÉGRABLE |
| Présences / Planning | #450 | `de184614c4185c60b3c5526ca4921aa03c2117db` | `qt/convergence-0.9.2-rc3` | Validation Qt SUCCESS | diverge depuis `d40c786...`; 41 commits propres | INTÉGRABLE |
| Scénarios | #446 | `46f2b07aed32edf5b034aeb1af708d20362e4a9b` | `qt/convergence-0.9.2-rc3` | Validation Qt SUCCESS | diverge depuis `d40c786...`; 3 commits propres | INTÉGRABLE |
| Profils / autorisations | #472 | `35702a4a40b23bbb4ec77aa94bc896cdd166487e` | `qt/convergence-0.9.2-rc3` | Validation Qt SUCCESS | diverge depuis `d40c786...`; 9 commits propres | INTÉGRABLE |
| Personnes | #476 | `780b6bc7b953bd7e039332e093b6e6d4cb05d5ae` | pile Personnes | Validation et publication FAILURE | pile hors base Qt | À REQUALIFIER |
| DPAE | #482 | `77d012e8db33d54e3f1c8643b9a5645fb70a9d19` | pile DPAE | aucun run PR trouvé sur le HEAD | pile hors base Qt | À REQUALIFIER |
| Sorties salarié | #484 | `7936bb4a3e55ac2e45fba2db32762d9bf559aaa6` | pile Sorties | aucun run PR trouvé sur le HEAD | pile hors base Qt | À REQUALIFIER |
| CRH | #357 | `6a75377b1d799c4a710c1f6ecf268efd6955be43` | `wx/master` | non qualifié pour RC1 | fortement divergente | À RÉCUPÉRER |
| Migration historique | #454 | `22fc042160cafbfeaf8466b99d1b9dfcf25915e0` | `master` | hors périmètre runtime Qt RC1 | chantier architecture séparé | À EXCLURE DE RC1 |

## Contrats : absorption de la pile historique

Le HEAD de #486 contient dans son ascendance les HEAD de #448, #455, #457, #460, #462 et #464. Ces PR ne seront donc pas rejouées individuellement dans RC1.

## Ordre d'intégration prévu

1. Contrats avancés / avenants (#486)
2. Présences / Planning (#450)
3. Scénarios (#446)
4. Profils / autorisations (#472), sous réserve de qualification après les trois étapes précédentes

Chaque étape doit être requalifiée sur le HEAD exact avant de passer à la suivante.

## Lots volontairement hors RC1 à ce stade

- Personnes #473 à #476
- DPAE #477, #478, #481, #482
- Sorties salarié #479, #483, #484
- CRH #357
- Migration historique #454

## Fichiers partagés à résoudre sémantiquement

- `.github/workflows/ci.yml`
- `application/services/contract_write.py`
- `application/services/service_result.py`
- `application/services/read_result.py`
- `infrastructure/persistence/contract_write_adapter.py`
- `poc/qt-theme/launcher.py`
- `poc/qt-theme/pilot_generalities.py`
- `poc/qt-theme/pilot_view.py`
- `poc/qt-theme/data_adapter.py`
- `poc/qt-theme/deferred_people.py`
- packaging Windows

Aucun choix automatique « ours » / « theirs » ne doit être appliqué à ces fichiers.

## Stop-gates

L'intégration du code ne lève aucun stop-gate fonctionnel. En particulier, `advanced_contracts_enabled` conserve son état tant que la recette MySQL réelle n'a pas produit la preuve attendue.

Le marqueur `TEAMWORKS_RAIL_A_MYSQL_READY` reste réservé à la recette réelle.

## État courant

- branche d'intégration créée : `qt/integration-0.2-rc1`
- SHA de départ confirmé : `caed9650df74609f1b0e920fa4d946aa3456cfd8`
- intégrations fonctionnelles : aucune à ce stade
- packaging final : non lancé
- HEAD final : à déterminer
