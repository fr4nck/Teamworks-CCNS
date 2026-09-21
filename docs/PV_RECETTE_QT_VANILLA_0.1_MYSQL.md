# Procès-verbal de recette — Qt Vanilla 0.1 / MySQL exploitation

> Ce document est un modèle. Dupliquer ce fichier pour chaque campagne de recette.
> Ne jamais y copier de donnée personnelle, secret, mot de passe ou identifiant sensible.

## 1. Identification

| Champ | Valeur |
|---|---|
| Date de recette | |
| Recetteur | |
| SHA Qt Vanilla | |
| Branche / PR | |
| Version affichée | |
| Artefact utilisé | Portable / Setup |
| SHA-256 artefact | |
| Version Windows | |
| Architecture | x64 |
| Nom machine de recette | |
| Version Python embarquée | |
| Version PySide6 | |

## 2. MySQL

| Champ | Valeur |
|---|---|
| Hôte de recette | |
| Port | |
| `SELECT VERSION()` | |
| Version identique à l'exploitation | OUI / NON |
| `sql_mode` | |
| `character_set_server` | |
| `collation_server` | |
| `lower_case_table_names` | |
| `max_allowed_packet` | |
| `autocommit` | |
| `tx_isolation` | |

Si la version MySQL n'est pas identique à l'exploitation : **VERDICT NON QUALIFIÉ**.

## 3. Copie représentative

| Champ | Valeur |
|---|---|
| Nom de base | |
| Suffixe `_qt_vanilla_recette` | OUI / NON |
| Date de fabrication | |
| Outil d'anonymisation | |
| Rapport d'anonymisation | |
| `audit_issues` | 0 attendu |
| Nb individus | |
| Nb contrats | |
| Nb présences | |
| Nb scénarios | |
| Nb déplacements | |
| Nb remboursements | |
| % volumétrie individus vs exploitation | |
| % volumétrie contrats vs exploitation | |
| % volumétrie présences vs exploitation | |
| % volumétrie frais vs exploitation | |

### Contrôle confidentialité

- [ ] aucun nom réel connu trouvé dans l'échantillon manuel ;
- [ ] aucun email réel hors `example.test` ;
- [ ] aucun téléphone réel ;
- [ ] aucun NIR ;
- [ ] aucun secret SMTP/API ;
- [ ] aucune photo personnelle ;
- [ ] aucun document personnel ;
- [ ] aucun mapping original → synthétique conservé.

## 4. Compatibilité MySQL

Référence : `MATRICE_VALIDATION_QT_VANILLA_0.1_MYSQL.md`.

| Test | Verdict | Preuve / observation |
|---|---|---|
| ENV-01 | PASS / FAIL | |
| ENV-02 | PASS / FAIL | |
| ENV-03 | PASS / FAIL | |
| ENV-04 | PASS / FAIL | |
| ENV-05 | PASS / FAIL | |
| ENV-06 | PASS / FAIL | |
| ENV-07 | PASS / FAIL | |
| ENV-08 | PASS / FAIL | |
| C-01 | PASS / FAIL | |
| C-02 | PASS / FAIL | |
| C-03 | PASS / FAIL | |
| C-04 | PASS / FAIL | |
| C-05 | PASS / FAIL | |
| C-06 | PASS / FAIL | |
| C-07 | PASS / FAIL | |
| C-08 | PASS / FAIL | |
| C-09 | PASS / FAIL | |
| C-10 | PASS / FAIL | |
| C-11 | PASS / FAIL | |
| C-12 | PASS / FAIL | |
| C-13 | PASS / FAIL | |
| C-14 | PASS / FAIL | |
| C-15 | PASS / FAIL | |
| C-16 | PASS / FAIL | |
| C-17 | PASS / FAIL | |
| C-18 | PASS / FAIL | |
| C-19 | PASS / FAIL | |
| C-20 | PASS / FAIL | |
| C-21 | PASS / FAIL | |
| C-22 | PASS / FAIL | |
| C-23 | PASS / FAIL | |
| C-24 | PASS / FAIL | |
| C-25 | PASS / FAIL | |
| C-26 | PASS / FAIL | |
| C-27 | PASS / FAIL | |
| C-28 | PASS / FAIL | |
| C-29 | PASS / FAIL | |
| C-30 | PASS / FAIL | |

### Verdict compatibilité

`COMPATIBILITE MYSQL : PASS / FAIL`

Commentaires :

## 5. Intégrité

### Snapshots

| Snapshot | Fichier / hash / preuve |
|---|---|
| Schéma avant | |
| Schéma après | |
| Comptages avant | |
| Comptages après | |
| Processlist avant | |
| Processlist après | |

| Test | Verdict | Preuve / observation |
|---|---|---|
| I-01 | PASS / FAIL | |
| I-02 | PASS / FAIL | |
| I-03 | PASS / FAIL | |
| I-04 | PASS / FAIL | |
| I-05 | PASS / FAIL | |
| I-06 | PASS / FAIL | |
| I-07 | PASS / FAIL | |
| I-08 | PASS / FAIL | |
| I-09 | PASS / FAIL | |
| I-10 | PASS / FAIL | |
| I-11 | PASS / FAIL | |
| I-12 | PASS / FAIL | |
| I-13 | PASS / FAIL | |
| I-14 | PASS / FAIL | |
| I-15 | PASS / FAIL | |
| I-16 | PASS / FAIL | |
| I-17 | PASS / FAIL | |
| I-18 | PASS / FAIL | |
| I-19 | PASS / FAIL | |
| I-20 | PASS / FAIL | |

### Écarts de comptage expliqués

| Table | Avant | Après | Delta attendu | Delta réel | Explication |
|---|---:|---:|---:|---:|---|
| personnes | | | 0 | | |
| contrats | | | | | |
| presences | | | 0 | | |
| scenarios | | | 0 | | |
| deplacements | | | | | |
| remboursements | | | | | |

### Verdict intégrité

`INTEGRITE DONNEES : PASS / FAIL`

Commentaires :

## 6. Performance

Référence : `SEUILS_PERFORMANCE_QT_VANILLA_0.1.md`.

### Conditions de mesure

| Champ | Valeur |
|---|---|
| Connexion réseau | |
| Charge serveur connue | |
| Antivirus / sauvegarde actifs | |
| Volumétrie suffisante (≥ 80 %) | OUI / NON |
| Nombre de mesures / parcours | 10 minimum |
| Mesure wx disponible | OUI / NON |

### Résultats

| ID | p50 Qt | p95 Qt | p50 wx | Ratio Qt/wx | Seuil respecté | Verdict |
|---|---:|---:|---:|---:|---|---|
| P-01 | | | | | OUI / NON | |
| P-02 | | | | | OUI / NON | |
| P-03 | | | | | OUI / NON | |
| P-04 | | | | | OUI / NON | |
| P-05 | | | | | OUI / NON | |
| P-06 | | | | | OUI / NON | |
| P-07 | | | | | OUI / NON | |
| P-08 | | | | | OUI / NON | |
| P-09 | | | | | OUI / NON | |
| P-10 | | | | | OUI / NON | |
| P-11 | | | | | OUI / NON | |

### Endurance P-12

| Mesure | Valeur |
|---|---:|
| p50 des 10 premiers changements | |
| p50 des 10 derniers changements | |
| dérive | |
| pire temps | |
| verdict | PASS / FAIL |

### Connexions P-13

| Mesure | Valeur |
|---|---:|
| connexions Teamworks avant lancement | |
| maximum pendant recette | |
| connexions 10 s après fermeture | |
| connexions 30 s après fermeture | |
| croissance monotone observée | OUI / NON |
| verdict | PASS / FAIL |

### Mémoire P-14

| Point | RSS |
|---|---:|
| fenêtre stabilisée | |
| après 10 changements | |
| après 50 changements | |
| après ouvertures répétées Contrats/Frais/Documents | |
| croissance absolue | |
| croissance relative | |
| verdict | PASS / FAIL |

### Requêtes lentes

| Parcours | Durée | Requête/service | EXPLAIN conservé | Décision |
|---|---:|---|---|---|
| | | | OUI / NON | |

### Verdict performance

`PERFORMANCE : PASS / FAIL / NON QUALIFIEE`

Commentaires :

## 7. Incidents et anomalies

| ID | Gravité | Domaine | Description | Reproductible | Correctif / issue / PR | Bloquant |
|---|---|---|---|---|---|---|
| | | | | OUI / NON | | OUI / NON |

Aucune donnée personnelle ne doit être copiée dans cette table.

## 8. Dérogations

| Référence | Motif | Risque | Décision | Approbateur |
|---|---|---|---|---|
| | | | | |

Aucune dérogation ne peut masquer :

- corruption ou perte de données ;
- transaction partielle ;
- incompatibilité MySQL ;
- fuite de connexion croissante ;
- mutation de schéma inattendue.

## 9. Verdict global

```text
QT VANILLA 0.1 — RECETTE MYSQL EXPLOITATION

SHA :
Windows :
MySQL :
Base de recette :

COMPATIBILITE MYSQL : PASS / FAIL
INTEGRITE DONNEES   : PASS / FAIL
PERFORMANCE         : PASS / FAIL / NON QUALIFIEE

VERDICT GLOBAL      : QUALIFIEE / BLOQUEE / NON QUALIFIEE
```

Règles :

- Compatibilité FAIL => **BLOQUÉE** ;
- Intégrité FAIL => **BLOQUÉE** ;
- Performance FAIL => **BLOQUÉE** sauf dérogation explicite avant release ;
- Performance NON QUALIFIÉE => la RC ne peut pas être déclarée stable ;
- MySQL différent de l'exploitation => **NON QUALIFIÉE** ;
- SHA différent entre EXE, CI, packaging et recette => **NON QUALIFIÉE**.

## 10. Signatures

| Rôle | Nom | Date | Verdict / signature |
|---|---|---|---|
| Recetteur | | | |
| Responsable release | | | |


## 11. Décision de release

Référence : `docs/GO_NO_GO_QT_VANILLA_0.1.md`.

Décision finale :

```text
GO / NO-GO / NON QUALIFIEE
```

Motif synthétique :

Responsable de la décision :

Date :
