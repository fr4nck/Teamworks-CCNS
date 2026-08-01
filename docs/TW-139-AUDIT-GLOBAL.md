# TW-139 — Audit global des motifs de fragilité runtime

## Principe

Chaque erreur runtime identifiée déclenche une recherche du même motif dans l'ensemble du dépôt. Les corrections sont regroupées par famille et ne sont pas limitées au seul écran ayant produit le traceback.

## Périmètre du premier passage

- 345 fichiers Python analysés ;
- compilation statique de `teamworks`, `application`, `domain`, `infrastructure`, `scripts` et `tests` ;
- lancement de la suite `pytest` jusqu'au premier défaut de collecte ;
- inventaire des résultats SQL indexés directement, sélections vides, indexations après appel, largeurs de colonnes wxPython et exceptions silencieuses.

## Résultats bruts

| Famille | Occurrences initiales | Après corrections TW-139 | Risque principal |
|---|---:|---:|---|
| `DB.ResultatReq()[0]` | 47 | 15 | `IndexError` sur résultat SQL vide |
| premier élément d'une sélection | 86 | 78 | `IndexError` sans ligne sélectionnée |
| appel immédiatement indexé par `[0]` | 228 | 226 | retour `None` ou séquence vide |
| `SetColumnWidth(...)` | 164 | 166 | `TypeError` avec largeur flottante sous wxPython récent |
| `except:` sans type | 207 | 203 | capture excessive, défauts masqués |
| exception suivie de `pass` | 155 | 157 | panne silencieuse et état incohérent |
| `Recherche_Pays(...)` | 4 | 4 | référence absente ou identifiant supprimé |

Ces nombres sont des candidats à examiner, pas des erreurs certaines. Chaque occurrence doit être classée selon les garanties du contexte avant modification.

## Défauts confirmés et corrigés

### Résultats SQL indexés sans garde — parcours principaux

Les fichiers suivants indexaient directement `DB.ResultatReq()[0]` dans un parcours principal exposé à une absence de ligne :

| Fichier | Méthode | Correction |
|---|---|---|
| `CTRL_Page_generalites.py` | `Panel_general.__init__` | garde `if pays_france is not None` |
| `CTRL_Page_generalites.py` | `SetPaysNaiss`, `SetNationalite` | garde `if not pays: return` |
| `CTRL_Page_generalites.py` | `Importation` | garde `if not resultats: return` |
| `CTRL_Personnes.py` | `OnSelectPersonne` | garde `if not resultats: return` |
| `CTRL_Recrutement.py` | `MAJidentite` | garde `if not resultats: return` |
| `DLG_Saisie_candidat.py` | `Importation` | garde + message utilisateur |
| `DLG_Saisie_coords.py` | `Importation` | garde + message + `EndModal(CANCEL)` |
| `DLG_Saisie_piece.py` | `Importation` | garde + message + `EndModal(CANCEL)` |
| `DLG_Saisie_presence.py` | `ImportDonneesModif` | garde + message + retour `None` |
| `DLG_Importation_vacances.py` | `ImportationZone` | garde + message utilisateur |
| `DLG_Parametres_calendrier.py` | `Importation`, `OnLeftLink` | gardes + `EndModal(CANCEL)` |

### Assertion wxWidgets — `wx.ALIGN_RIGHT` dans sizer horizontal

`DLG_Selection_periode.py` utilisait `wx.ALIGN_RIGHT` dans quatre appels `sizer.Add()` de sizers `StaticBoxSizer` horizontaux. wxWidgets 3.2+ lève une assertion fatale sur ce cas. Le drapeau a été retiré des appels `.Add()` uniquement ; les styles `wx.ALIGN_RIGHT` des `StaticText` sont conservés (ils sont valides).

### Résultats SQL indexés sans garde — lot 2 (01/08/2026)

| Fichier | Méthode | Correction |
|---|---|---|
| `DLG_Edition_DUE.py` | `Import_Donnees` | garde `if not resultats: DB.Close(); return` sur contrat et personne ; fallbacks inline pour classification, type, valeur_point, nationalité, pays_naiss |
| `OL_candidats.py` | `ConvertirFiche` | garde `if not resultats: return` après `DB.Close()` |
| `UTILS_Publipostage_donnees.py` | `Importation_contrat` | fallbacks `if resultats else ""` pour classification, type_contrat et valeur_point |

### Occurrences non dangereuses classées

- `CTRL_Page_presences.py:834` — `identite = DB.ResultatReq()[0]` : déjà enveloppé dans un `try/except` qui substitue un titre générique. Pas de crash possible.
- `DLG_Publiposteur.py:435-483` — lignes commentées (`##`). Inactives.
- `GestionDB.py:643` — ligne commentée (`##`). Inactive.
- `tests/test_tw139_runtime_guards.py` — occurrences dans des `assertNotIn`. Inoffensives.

### Collecte des tests (résolu)

`tests/test_incomplete_files_ccns.py` utilisait un import direct résolu par import différé. La suite `test_tw139_runtime_guards.py` est collectée et s'exécute sans dépendance externe.

### Avertissements Python (non bloquants)

- séquence d'échappement invalide dans `DLG_Saisie_utilisateur_reseau.py` ;
- séquence `\s` non brute dans `UTILS_Html2text.py` ;
- comparaisons de chaînes avec `is` / `is not` dans `UTILS_Html2text.py`.

## Risques restants non confirmés

| Famille | Fichiers restants | Priorité |
|---|---|---|
| `SetColumnWidth` avec valeur flottante | Tous les fichiers listés | Confirmé uniquement sous wxPython 4.3+ |
| Exceptions silencieuses | Nombreux fichiers | À traiter par famille, pas globalement |

> **`ResultatReq()[0]` non gardé** : aucune occurrence non protégée dans le périmètre audité.

## Ordre de traitement restant

1. ~~restaurer la collecte complète des tests~~ ✓ résolu ;
2. ~~sécuriser toute la famille `Recherche_Pays`~~ ✓ résolu ;
3. ~~classer et corriger les résultats SQL directement indexés dans les parcours principaux~~ ✓ résolu pour 10 occurrences ;
4. ~~classer et corriger `DLG_Edition_DUE.py`, `OL_candidats.py`, `UTILS_Publipostage_donnees.py`~~ ✓ résolu (lot 2) ;
5. normaliser les largeurs ObjectListView/wxPython en entiers si wxPython 4.3 est ciblé ;
6. réduire les exceptions silencieuses uniquement dans les parcours audités ;
7. exécuter la matrice Windows et consigner chaque résultat.

## Discipline

- aucun nouveau workflow GitHub Actions ;
- un seul audit reproductible via `scripts/audit_runtime_patterns.py` ;
- pas de `try/except` générique ajouté pour cacher un défaut ;
- chaque correction doit définir un comportement de repli ;
- chaque traceback futur doit être rapproché d'une famille et recherché dans tout le dépôt.
