# TW-139 — Audit global des motifs de fragilité runtime

## Principe

Chaque erreur runtime identifiée déclenche une recherche du même motif dans l'ensemble du dépôt. Les corrections sont regroupées par famille et ne sont pas limitées au seul écran ayant produit le traceback.

## Périmètre du premier passage

- 345 fichiers Python analysés ;
- compilation statique de `teamworks`, `application`, `domain`, `infrastructure`, `scripts` et `tests` ;
- lancement de la suite `pytest` jusqu'au premier défaut de collecte ;
- inventaire des résultats SQL indexés directement, sélections vides, indexations après appel, largeurs de colonnes wxPython et exceptions silencieuses.

## Résultats bruts

| Famille | Occurrences | Risque principal |
|---|---:|---|
| `DB.ResultatReq()[0]` | 47 | `IndexError` sur résultat SQL vide |
| premier élément d'une sélection | 86 | `IndexError` sans ligne sélectionnée |
| appel immédiatement indexé par `[0]` | 228 | retour `None` ou séquence vide |
| `SetColumnWidth(...)` | 164 | `TypeError` avec largeur flottante sous wxPython récent |
| `except:` sans type | 207 | capture excessive, défauts masqués |
| exception suivie de `pass` | 155 | panne silencieuse et état incohérent |
| `Recherche_Pays(...)` | 4 | référence absente ou identifiant supprimé |

Ces nombres sont des candidats à examiner, pas des erreurs certaines. Chaque occurrence doit être classée selon les garanties du contexte avant modification.

## Défauts confirmés

### Pays absent

`CTRL_Page_generalites.Panel_general.__init__` indexait directement le retour de `Recherche_Pays("France")`. La fonction retourne `None` lorsqu'aucune ligne n'est trouvée. Le correctif protège désormais ce cas.

Les méthodes `SetPaysNaiss` et `SetNationalite` utilisent encore le même retour sans garde. Elles doivent être corrigées ensemble avec un comportement visuel de repli explicite.

### Collecte des tests impossible

La suite locale s'arrête pendant la collecte :

```text
ModuleNotFoundError: No module named 'teamworks.CcnsCore.audit_person_summary'
```

`tests/test_incomplete_files_ccns.py` importe indirectement ce module via `incomplete_files_ccns.py`. L'intégrité de la suite de tests doit être restaurée avant de considérer l'audit runtime comme validé.

### Avertissements Python

- séquence d'échappement invalide dans `DLG_Saisie_utilisateur_reseau.py` ;
- séquence `\s` non brute dans `UTILS_Html2text.py` ;
- comparaisons de chaînes avec `is` / `is not` dans `UTILS_Html2text.py`.

## Ordre de traitement

1. restaurer la collecte complète des tests ;
2. sécuriser toute la famille `Recherche_Pays` ;
3. classer et corriger les 47 résultats SQL directement indexés ;
4. sécuriser les sélections utilisées sans contrôle préalable ;
5. normaliser les largeurs ObjectListView/wxPython en entiers ;
6. traiter les dates et valeurs historiques absentes ;
7. réduire les exceptions silencieuses uniquement dans les parcours audités ;
8. exécuter la matrice Windows et consigner chaque résultat.

## Discipline

- aucun nouveau workflow GitHub Actions ;
- un seul audit reproductible via `scripts/audit_runtime_patterns.py` ;
- pas de `try/except` générique ajouté pour cacher un défaut ;
- chaque correction doit définir un comportement de repli ;
- chaque traceback futur doit être rapproché d'une famille et recherché dans tout le dépôt.
