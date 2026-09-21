# Qt Vanilla 0.1 — collecte automatisée des preuves MySQL

L'outil :

`tools/collect_qt_vanilla_mysql_evidence.py`

complète la matrice et le procès-verbal de recette. Il ne remplace pas le jugement final du PV.

Il produit uniquement des métadonnées techniques de qualification :

- SHA de la RC ;
- version MySQL ;
- variables serveur utiles ;
- hash du schéma ;
- comptages par tables métier principales ;
- résumé non sensible des connexions ;
- SHA-256 des artefacts Windows fournis ;
- p50/p95 des mesures de performance.

Il ne stocke pas :

- mot de passe MySQL ;
- noms/prénoms ;
- contenu des lignes métier ;
- SQL en cours dans le processlist ;
- adresse réseau ou utilisateur MySQL dans le rapport.

## 1. Préparer l'environnement

```powershell
$env:TEAMWORKS_MYSQL_HOST = "<serveur>"
$env:TEAMWORKS_MYSQL_PORT = "3306"
$env:TEAMWORKS_MYSQL_USER = "<compte-recette>"
$env:TEAMWORKS_MYSQL_PASSWORD = "<mot-de-passe>"
```

Le mot de passe ne doit jamais être passé en argument.

La base cible doit déjà être anonymisée et se terminer par :

`_qt_vanilla_recette`

## 2. Snapshot avant recette

Exemple :

```powershell
python tools/collect_qt_vanilla_mysql_evidence.py snapshot `
  --database "teamworks_ccns_qt_vanilla_recette" `
  --sha "2c212403b0813100f2b0212fb32b24fb46aae05d" `
  --label before `
  --artifact ".\Teamworks-CCNS-Qt-0.1.0-windows-x64-portable.zip" `
  --artifact ".\Teamworks-CCNS-Qt-0.1.0-windows-x64-setup.exe" `
  --output ".\preuves\mysql-before.json"
```

Le snapshot contient :

- version MySQL exacte ;
- variables serveur ;
- liste structurée des tables/colonnes/index ;
- hash SHA-256 de chaque bloc de schéma ;
- compteurs `personnes`, `contrats`, `presences`, `scenarios`, `deplacements`, `remboursements` ;
- nombre de connexions sur la base et histogramme commande/état ;
- hashes des artefacts.

## 3. Exécuter la matrice de recette

Utiliser :

- `MATRICE_VALIDATION_QT_VANILLA_0.1_MYSQL.md`
- `SEUILS_PERFORMANCE_QT_VANILLA_0.1.md`
- `PV_RECETTE_QT_VANILLA_0.1_MYSQL.md`

Pendant cette phase, toute création/modification/suppression doit être explicitement prévue par la matrice.

## 4. Snapshot après recette

```powershell
python tools/collect_qt_vanilla_mysql_evidence.py snapshot `
  --database "teamworks_ccns_qt_vanilla_recette" `
  --sha "2c212403b0813100f2b0212fb32b24fb46aae05d" `
  --label after `
  --artifact ".\Teamworks-CCNS-Qt-0.1.0-windows-x64-portable.zip" `
  --artifact ".\Teamworks-CCNS-Qt-0.1.0-windows-x64-setup.exe" `
  --output ".\preuves\mysql-after.json"
```

## 5. Comparer avant / après

```powershell
python tools/collect_qt_vanilla_mysql_evidence.py compare `
  --before ".\preuves\mysql-before.json" `
  --after ".\preuves\mysql-after.json" `
  --output ".\preuves\mysql-compare.json"
```

Le comparateur vérifie automatiquement :

- même SHA ;
- même base ;
- même version MySQL ;
- tables identiques ;
- colonnes identiques ;
- index identiques.

Il affiche également les deltas de comptage.

Important :

> `automatic_schema_gate=true` ne signifie pas « intégrité complète validée ».

Les deltas métier doivent encore être comparés aux opérations prévues dans le PV. Une création de contrat peut par exemple expliquer `contrats: +1`, tandis que `personnes: +1` serait inattendu.

## 6. Relever les performances

Créer un CSV sans donnée personnelle :

```csv
test_id,qt_seconds,wx_seconds
P-01,2.41,2.80
P-01,2.35,2.76
P-02,0.84,0.91
...
```

Aucune colonne de commentaire libre n'est nécessaire.

Il faut au minimum 10 lignes pour chaque P-01 à P-11.

Puis :

```powershell
python tools/collect_qt_vanilla_mysql_evidence.py performance `
  --input ".\preuves\performance.csv" `
  --output ".\preuves\performance-summary.json"
```

Le rapport calcule :

- nombre de mesures ;
- p50 ;
- p95 ;
- seuil p50 ;
- seuil p95 ;
- p50 wx si disponible ;
- ratio Qt/wx ;
- verdict par test.

### Verdicts automatiques

- `PASS` : seuils absolus respectés et ratio ≤ 1,20 ;
- `ANALYSE` : ratio > 1,20 et ≤ 1,50 malgré seuils absolus verts ;
- `FAIL` : seuil absolu dépassé ou ratio > 1,50 ;
- `NON_QUALIFIE` : moins de 10 mesures.

Un seul `ANALYSE` empêche le gate automatique global de passer : il faut alors une décision explicite dans le PV.

## 7. P-12 / P-13 / P-14

Les tests :

- endurance ;
- fuite de connexions ;
- croissance mémoire ;

restent consignés dans le PV selon leurs règles spécifiques.

Le snapshot avant/après fournit une preuve supplémentaire pour les connexions MySQL mais ne remplace pas l'observation P-13 pendant la séquence.

## 8. Dossier de preuves attendu

Exemple :

```text
preuves/
  mysql-before.json
  mysql-after.json
  mysql-compare.json
  performance.csv
  performance-summary.json
  PV_RECETTE_QT_VANILLA_0.1_MYSQL-rempli.md
```

Ces fichiers ne doivent contenir aucune donnée personnelle.

## 9. Verdict de release

La RC ne devient qualifiée que si :

- `automatic_schema_gate=true` ;
- les deltas de comptage sont tous expliqués ;
- Compatibilité = PASS ;
- Intégrité = PASS ;
- Performance = PASS ;
- version MySQL identique à l'exploitation ;
- SHA identique entre RC, artefacts, snapshots et PV.

Le collecteur est une **preuve reproductible**, pas un raccourci pour éviter la recette métier.
