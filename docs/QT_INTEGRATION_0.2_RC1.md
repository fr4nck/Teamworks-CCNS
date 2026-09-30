# Qt Integration 0.2 RC1

## Objet

Cette branche formalise une base Qt unique, installable et testable, sans ajouter de nouvelle fonctionnalité.

## Point de départ

- branche source : `qt/vanilla-0.1-rc`
- SHA de départ : `caed9650df74609f1b0e920fa4d946aa3456cfd8`
- PR source de référence : #467
- Validation Qt du SHA de départ : run `35651379116` — SUCCESS
- Packaging Qt Vanilla 0.1 du SHA de départ : run `35651379104` — SUCCESS

## Règle de branchement

Toute nouvelle branche Qt doit partir de la dernière branche d'intégration verte. Une ancienne PR ou branche empilée ne doit pas servir directement de base à un nouveau développement.

## Audit initial des lots

| Lot | PR | HEAD audité | Base historique | CI du HEAD | Verdict RC1 |
|---|---:|---|---|---|---|
| Contrats avancés / avenants | #486 | `81f8036851b9232a547b99ec9b1789f04516c056` | `qt/convergence-0.9.2-rc3` | Validation Qt `36579942884` — SUCCESS | ABSORBÉ PAR #467 |
| Présences / Planning | #450 | `de184614c4185c60b3c5526ca4921aa03c2117db` | `qt/convergence-0.9.2-rc3` | Validation Qt `35584073956` / `35584073896` — SUCCESS | ABSORBÉ PAR #467 |
| Scénarios | #446 | `46f2b07aed32edf5b034aeb1af708d20362e4a9b` | `qt/convergence-0.9.2-rc3` | Validation Qt `35571470082` / `35571457344` — SUCCESS | ABSORBÉ PAR #467 |
| Profils / autorisations | #472 | `35702a4a40b23bbb4ec77aa94bc896cdd166487e` | `qt/convergence-0.9.2-rc3` | Validation Qt `35680775760` — SUCCESS | ABSORBÉ PAR #467 |
| Personnes | #476 | `780b6bc7b953bd7e039332e093b6e6d4cb05d5ae` | pile Personnes | Validation et publication `36127657266` — FAILURE | À REQUALIFIER |
| DPAE | #482 | `77d012e8db33d54e3f1c8643b9a5645fb70a9d19` | pile DPAE | aucun run PR trouvé sur le HEAD | À REQUALIFIER |
| Sorties salarié | #484 | `7936bb4a3e55ac2e45fba2db32762d9bf559aaa6` | pile Sorties | aucun run PR trouvé sur le HEAD | À REQUALIFIER |
| CRH | #357 | `6a75377b1d799c4a710c1f6ecf268efd6955be43` | `wx/master` | hors qualification RC1 | À RÉCUPÉRER |
| Migration historique | #454 | `22fc042160cafbfeaf8466b99d1b9dfcf25915e0` | `master` | hors périmètre runtime Qt RC1 | À EXCLURE DE RC1 |

## Méthode de preuve d'absorption

Le graphe Git seul est trompeur parce que les branches historiques divergent depuis `qt/convergence-0.9.2-rc3`. L'audit a donc comparé les fichiers réellement portés par chaque lot avec le contenu de #467.

### Contrats avancés / avenants

- #486 contient bien dans son ascendance les HEAD de #448, #455, #457, #460, #462 et #464.
- 19 fichiers sur les 22 fichiers portés par #486 sont bit-à-bit identiques dans #467.
- Les trois fichiers partagés différents sont :
  - `.github/workflows/ci.yml`
  - `poc/qt-theme/pilot_generalities.py`
  - `poc/qt-theme/pilot_view.py`
- Sur ces trois fichiers, les changements de #486 sont déjà présents dans #467 ; #467 contient en plus les évolutions Vanilla ultérieures (Documents RH, Frais, Présences et qualification Windows/MySQL).

Conclusion : remérger #486 ferait perdre des évolutions plus récentes. Le lot est **ABSORBÉ PAR #467** sans nouveau merge.

### Présences / Planning

Les services, ports, adaptateurs, contrôleurs et tests propres de #450 sont identiques dans #467. Les fichiers partagés qui diffèrent (`data_adapter.py`, `individual_pages.py`, `launcher.py`, `pilot_generalities.py`, `production_read_adapter.py`) contiennent tous les apports de #450 ainsi que les évolutions Vanilla postérieures.

Conclusion : **ABSORBÉ PAR #467**.

### Scénarios

Les trois fichiers propres de #446 sont bit-à-bit identiques dans #467 :

- `application/services/scenario_write.py`
- `infrastructure/persistence/scenario_write_adapter.py`
- `tests/test_scenario_write_service.py`

Conclusion : **ABSORBÉ PAR #467**.

### Profils / autorisations

Les cinq fichiers portés par #472 sont bit-à-bit identiques dans #467 :

- `application/security/access_service.py`
- `domain/security/default_roles.py`
- `domain/security/permission.py`
- `tests/test_portail_permission_alignment.py`
- `tests/test_profile_permissions.py`

Conclusion : **ABSORBÉ PAR #467**.

## Lots volontairement hors RC1

- Personnes #473 à #476 : tête de pile rouge.
- DPAE #477, #478, #481, #482 : tête consolidée non qualifiée sur la future base d'intégration.
- Sorties salarié #479, #483, #484 : tête consolidée non qualifiée sur la future base d'intégration.
- CRH #357 : branche historique fortement divergente, récupération uniquement par lots rejoués.
- Migration #454 : chantier d'architecture/outillage séparé.

Aucune de ces branches ne doit servir de base à un nouveau développement Qt.

## Stop-gates

L'intégration du code ne lève aucun stop-gate fonctionnel.

En particulier :

- `advanced_contracts_enabled` conserve son état actuel ;
- `TEAMWORKS_RAIL_A_MYSQL_READY` reste réservé à la recette MySQL réelle ;
- une CI verte ne vaut pas recette MySQL d'exploitation.

## Qualification de la nouvelle branche

Branche : `qt/integration-0.2-rc1`

Premier commit documentaire : `e041f90e292de9f72226d7566966eaa070d8d627`

Validation de ce HEAD : run `36675114074` — SUCCESS.

La CI et le packaging sont configurés pour accepter les branches `qt/integration-*`. Le HEAD final de RC1 doit passer la Validation Qt et produire le packaging Windows depuis exactement le même SHA.

## Packaging final attendu

Depuis le HEAD final unique :

- installateur Windows x64 ;
- portable ZIP ;
- `SHA256SUMS.txt` ;
- SHA Git de référence ;
- artefacts provenant tous du même run / même HEAD.

## Anciennes PR potentiellement absorbées, sans fermeture

Sous réserve de l'audit final après packaging :

- #448
- #455
- #457
- #460
- #462
- #464
- #486
- #450
- #446
- #472

Elles restent ouvertes pendant cette passe.

## Base future

Une fois le HEAD final vert et le packaging validé :

> Toute nouvelle branche Qt doit partir de `qt/integration-0.2-rc1` ou de sa successeure verte.

Lorsqu'une nouvelle RC d'intégration la remplace, RC1 devient historique et la nouvelle RC devient l'unique base autorisée.
