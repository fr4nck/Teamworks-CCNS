# Qt Vanilla 0.1 — matrice de validation MySQL exploitation

SHA de référence initial : `d016c82d423b8b3be485c30ecd26bb8c71ea6da4`.

Cette matrice doit être exécutée sur :

- un poste Windows réel ;
- la version MySQL **exactement utilisée en exploitation** ;
- une copie représentative anonymisée ayant passé `ANONYMISATION_COPIE_RECETTE_QT.md` ;
- les artefacts Windows produits depuis le même SHA que la RC testée.

Le verdict global est **FAIL** si un test bloquant de compatibilité ou d'intégrité échoue.

## A. Préparation et identité de l'environnement

| ID | Contrôle | Action / preuve attendue | Criticité |
|---|---|---|---|
| ENV-01 | SHA Qt | relever le SHA de la RC et le comparer au SHA des artefacts | Bloquant |
| ENV-02 | Version MySQL | `SELECT VERSION();` | Bloquant |
| ENV-03 | SQL mode | relever `sql_mode` | Bloquant |
| ENV-04 | Encodage serveur | relever `character_set_server` et `collation_server` | Bloquant |
| ENV-05 | Moteurs | relever ENGINE et TABLE_COLLATION de toutes les tables | Bloquant |
| ENV-06 | Base cible | vérifier le suffixe `_qt_vanilla_recette` | Bloquant |
| ENV-07 | Anonymisation | rapport final sans `audit_issues` | Bloquant |
| ENV-08 | Coexistence | Vanilla wx installée séparément et non modifiée | Important |

SQL de relevé :

```sql
SELECT VERSION();

SHOW VARIABLES
WHERE Variable_name IN (
  'sql_mode',
  'character_set_server',
  'collation_server',
  'lower_case_table_names',
  'max_allowed_packet',
  'autocommit',
  'tx_isolation'
);

SELECT TABLE_NAME, ENGINE, TABLE_COLLATION
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = '<base>_qt_vanilla_recette'
  AND TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;
```

## B. Compatibilité

### B1. Connexion et lecture

| ID | Cas | Action | Résultat attendu | Criticité |
|---|---|---|---|---|
| C-01 | Connexion | démarrer Qt sur la copie | connexion sans fallback ni erreur MySQL | Bloquant |
| C-02 | Individus | charger la liste complète | données visibles, aucun mélange de dossiers | Bloquant |
| C-03 | Recherche | rechercher nom/prénom synthétique | résultat exact | Important |
| C-04 | Généralités | ouvrir dossiers complets/incomplets | `NULL`, vide et zéro correctement distingués | Bloquant |
| C-05 | Unicode | lire noms avec accents/apostrophes/tirets | affichage identique aux valeurs MySQL | Bloquant |
| C-06 | Contrats | afficher 0, 1 puis plusieurs contrats | aucune erreur de jointure ou conversion | Bloquant |
| C-07 | Présences | personne avec/sans présence | état vide distinct d'une erreur | Important |
| C-08 | Scénarios | personne avec/sans scénario | lecture correcte | Important |
| C-09 | Frais | afficher déplacements/remboursements | relations correctes | Bloquant |
| C-10 | Documents RH | ouvrir depuis un contrat | modèles/états affichés sans écriture DB | Bloquant |

### B2. Écritures Contrats

| ID | Cas | Action | Résultat attendu | Criticité |
|---|---|---|---|---|
| C-11 | Création valide | créer CDI/CDD CCNS de recette | commit + relecture identique | Bloquant |
| C-12 | Création invalide | saisir un cas rejeté métier | 0 écriture | Bloquant |
| C-13 | Modification | modifier un contrat de recette | commit unique + relecture | Bloquant |
| C-14 | Signature | basculer état | valeur persistée après redémarrage | Bloquant |
| C-15 | DUE | basculer état | valeur persistée après redémarrage | Bloquant |
| C-16 | Suppression annulée | annuler la confirmation | 0 modification | Bloquant |
| C-17 | Suppression confirmée | supprimer contrat de recette | ligne supprimée, aucune relation inattendue | Bloquant |

### B3. Écritures Frais

| ID | Cas | Action | Résultat attendu | Criticité |
|---|---|---|---|---|
| C-18 | Déplacement create | créer un déplacement | commit + relecture | Bloquant |
| C-19 | Déplacement update | modifier ce déplacement | valeurs persistées | Bloquant |
| C-20 | Remboursement | créer remboursement | parent persisté | Bloquant |
| C-21 | Rattachement multiple | rattacher plusieurs déplacements | toutes relations cohérentes | Bloquant |
| C-22 | Conflit rattachement | tenter de voler un déplacement | refus + rollback intégral | Bloquant |
| C-23 | Détachement | détacher selon parcours qualifié | relation supprimée proprement | Bloquant |
| C-24 | Suppression remboursement | supprimer cas de recette | aucun déplacement orphelin | Bloquant |

### B4. Compatibilité des types MySQL

| ID | Type | Données à couvrir | PASS |
|---|---|---|---|
| C-25 | `NULL` | dates de fin, rupture, coordonnées absentes | aucune conversion invalide |
| C-26 | chaîne vide | champs historiques vides | comportement métier conservé |
| C-27 | entier/zéro | flags et valeurs historiques | aucune confusion avec `NULL` |
| C-28 | DECIMAL/FLOAT | salaires, distances, remboursements | relecture sans dérive métier |
| C-29 | DATE/DATETIME | anciennes et nouvelles dates | pas de date zéro/interprétation incorrecte |
| C-30 | UTF-8 | é, è, ç, œ, apostrophes, tirets | aller-retour identique |

## C. Intégrité

### C1. Snapshot de schéma

Avant puis après la recette :

```sql
SELECT TABLE_NAME, ENGINE, TABLE_COLLATION
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = '<base>'
ORDER BY TABLE_NAME;

SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = '<base>'
ORDER BY TABLE_NAME, ORDINAL_POSITION;

SELECT TABLE_NAME, INDEX_NAME, NON_UNIQUE, COLUMN_NAME, SEQ_IN_INDEX
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = '<base>'
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;
```

| ID | Contrôle | PASS | Criticité |
|---|---|---|---|
| I-01 | Tables | aucune table inattendue créée/supprimée | Bloquant |
| I-02 | Colonnes | aucune colonne inattendue créée/modifiée | Bloquant |
| I-03 | Index | aucune divergence inattendue | Bloquant |
| I-04 | Moteurs/collations | aucune mutation automatique | Bloquant |

### C2. Comptages

Avant et après chaque séquence d'écriture :

```sql
SELECT COUNT(*) FROM personnes;
SELECT COUNT(*) FROM contrats;
SELECT COUNT(*) FROM presences;
SELECT COUNT(*) FROM scenarios;
SELECT COUNT(*) FROM deplacements;
SELECT COUNT(*) FROM remboursements;
```

| ID | Contrôle | PASS | Criticité |
|---|---|---|---|
| I-05 | Tables hors parcours | compteur inchangé | Bloquant |
| I-06 | Création | delta exactement attendu | Bloquant |
| I-07 | Suppression | retour au compteur attendu | Bloquant |

### C3. Relations

| ID | Relation | Vérification | PASS |
|---|---|---|---|
| I-08 | personne → contrat | aucun contrat de recette sans personne | 0 orphelin |
| I-09 | personne → déplacement | aucun déplacement de recette sans personne | 0 orphelin |
| I-10 | personne → remboursement | aucun remboursement de recette sans personne | 0 orphelin |
| I-11 | déplacement → remboursement | jointure cohérente | 0 orphelin |
| I-12 | ID historiques | IDs utilisés par Qt correspondent aux lignes réellement modifiées | aucune ambiguïté |

Contrôle Frais :

```sql
SELECT d.IDdeplacement
FROM deplacements d
LEFT JOIN remboursements r
  ON r.IDremboursement = d.IDremboursement
WHERE d.IDremboursement IS NOT NULL
  AND r.IDremboursement IS NULL;
```

Résultat : **0 ligne**.

### C4. Rollback

| ID | Faute provoquée | PASS | Criticité |
|---|---|---|---|
| I-13 | contrat invalide | aucune demi-écriture | Bloquant |
| I-14 | rattachement Frais refusé | parent/enfants inchangés | Bloquant |
| I-15 | annulation utilisateur | aucune écriture | Bloquant |
| I-16 | erreur transactionnelle contrôlée | état DB identique au snapshot avant opération | Bloquant |

### C5. Persistance / fermeture

| ID | Contrôle | PASS |
|---|---|---|
| I-17 | Redémarrage | toutes les écritures validées sont retrouvées |
| I-18 | Fermeture | aucun `QThread destroyed while running` |
| I-19 | Connexions MySQL | aucune accumulation de sessions après fermeture |
| I-20 | Documents RH | consultation ne modifie ni schéma ni lignes métier |

## D. Performance

Les tests P-* utilisent les seuils définis dans `SEUILS_PERFORMANCE_QT_VANILLA_0.1.md`.

Chaque mesure est répétée au minimum 10 fois après un premier passage de chauffe.

| ID | Parcours | Mesure |
|---|---|---|
| P-01 | démarrage | lancement → fenêtre utilisable |
| P-02 | liste Individus | ouverture/rafraîchissement |
| P-03 | recherche | frappe → résultat visible |
| P-04 | changement individu | clic → Généralités stabilisées |
| P-05 | Contrats | sélection → liste affichée |
| P-06 | Présences | sélection → données affichées |
| P-07 | Scénarios | sélection → données affichées |
| P-08 | Frais | sélection → données affichées |
| P-09 | création/modif Contrat | validation → relecture affichée |
| P-10 | cycle Remboursement | validation → relecture affichée |
| P-11 | Documents RH | clic → modèles/état affichés |
| P-12 | endurance | 50 changements successifs d'individu |
| P-13 | connexions | sessions MySQL avant/pendant/après |
| P-14 | mémoire | évolution sur le test d'endurance |

## E. Verdict

Le procès-verbal doit produire trois résultats séparés :

```text
COMPATIBILITE MYSQL : PASS / FAIL
INTEGRITE DONNEES   : PASS / FAIL
PERFORMANCE         : PASS / FAIL
```

Règles :

- un seul test **Bloquant** en échec dans C-* ou I-* => RC **FAIL** ;
- performance => appliquer les seuils du document dédié ;
- aucune dérogation implicite ;
- toute dérogation éventuelle doit être écrite dans le PV avec justification et décision explicite avant release.
