# Qt Vanilla 0.1 — recette MySQL réelle

## Objectif

La CI moderne valide le rail Frais contre MySQL 8.0.46. La sortie Qt Vanilla 0.1 exige en plus une recette sur le serveur réellement déployé par Teamworks.

Le code historique `UTILS_MySQL.ConstruireOptionsConnexion()` conserve explicitement le mode Python pur du connecteur pour rester compatible avec le serveur MySQL 5.5 de production. Tant que la production reste sur cette version, **MySQL 5.5 est le gate réel de sortie**.

Cette recette ne doit jamais être exécutée directement sur l'unique base de production.

## Documents normatifs de la recette

La qualification MySQL de la Qt Vanilla 0.1 repose sur trois documents complémentaires :

- `docs/MATRICE_VALIDATION_QT_VANILLA_0.1_MYSQL.md` : cas de test Compatibilité / Intégrité / Performance ;
- `docs/SEUILS_PERFORMANCE_QT_VANILLA_0.1.md` : seuils chiffrés et règles de mesure ;
- `docs/PV_RECETTE_QT_VANILLA_0.1_MYSQL.md` : procès-verbal à remplir et signer ;
- `docs/COLLECTE_PREUVES_QT_VANILLA_0.1_MYSQL.md` : snapshots, comparaison de schéma et synthèse p50/p95 automatisés.

Le verdict final doit être produit à partir de ces trois documents. Une simple impression de bon fonctionnement ne vaut pas qualification.

## Préconditions

- poste Windows réel ;
- candidate Qt Vanilla issue du SHA à qualifier ;
- accès au serveur MySQL de production ou à un serveur de recette de **même version** ;
- compte MySQL capable de créer/supprimer une base de recette dédiée pour le test automatisé Frais ;
- copie représentative de la base Teamworks pour la recette fonctionnelle ;
- Vanilla wx conservée comme référence de lecture, sans faire d'écriture concurrente pendant les tests.

## 1. Relever la version serveur

Depuis le serveur de recette :

```sql
SELECT VERSION();
```

Consigner la valeur exacte dans le procès-verbal de recette.

Si la version n'est pas identique à la production, la recette ne vaut pas qualification production.

## 2. Test automatisé Frais sur le serveur réel

Le test `tests/test_mysql_expense_roundtrip.py` crée et détruit uniquement la base jetable `teamworks_frais_ci`.

Dans PowerShell :

```powershell
$env:TEAMWORKS_MYSQL_INTEGRATION = "1"
$env:TEAMWORKS_MYSQL_HOST = "<serveur>"
$env:TEAMWORKS_MYSQL_PORT = "<port>"
$env:TEAMWORKS_MYSQL_USER = "<compte-recette>"
$env:TEAMWORKS_MYSQL_PASSWORD = "<mot-de-passe>"

python -m pytest -q tests/test_mysql_expense_roundtrip.py
```

Attendus :

- création/modification/suppression Déplacement : PASS ;
- création Remboursement + rattachement multi-déplacements : PASS ;
- impossibilité de voler un déplacement déjà rattaché : PASS ;
- rollback du parent en cas d'échec de rattachement : PASS ;
- rollback des détachements si la suppression du remboursement échoue : PASS ;
- la base `teamworks_frais_ci` est supprimée à la fin.

Un échec de connexion, de placeholder, de transaction ou de rollback bloque la RC.

## 3. Préparer la copie représentative Teamworks

La procédure complète d'anonymisation est décrite dans
`docs/ANONYMISATION_COPIE_RECETTE_QT.md`.

La base utilisée pour cette recette doit avoir passé l'audit final de cet outil avant tout parcours fonctionnel Qt.



Dupliquer la base de travail dans un nom explicitement de recette, par exemple :

`<base>_qt_vanilla_recette`

La copie doit contenir au minimum :

- plusieurs individus ;
- un individu sans contrat et un avec plusieurs contrats ;
- CDI et CDD CCNS ;
- présences ;
- scénarios ;
- déplacements et remboursements ;
- modèles/métadonnées Documents si utilisés dans la base réelle.

Ne jamais modifier les identifiants historiques pour les besoins de la recette.

## 4. Pointer Qt Vanilla vers la copie

Configurer `Config.json`/la connexion Teamworks pour que la Qt Vanilla ouvre **uniquement la copie de recette**.

Avant toute écriture, vérifier dans l'application et côté serveur que le nom de base actif correspond bien à la copie.

## 5. Individus / Généralités

- charger la liste ;
- rechercher au moins trois individus ;
- sélectionner rapidement plusieurs lignes ;
- ouvrir une personne avec et sans coordonnées.

Attendus :

- aucune erreur de connexion ;
- données identiques à la wx en lecture ;
- accents et Unicode corrects ;
- pas de mélange entre individus lors des chargements asynchrones.

## 6. Contrats

Sur un individu de recette :

1. créer un CDI ou CDD CCNS valide ;
2. tenter une création invalide ;
3. modifier un contrat ;
4. basculer Signature ;
5. basculer DUE ;
6. annuler une suppression ;
7. supprimer un contrat de test confirmé ;
8. fermer puis relancer Qt.

Contrôler les lignes SQL résultantes depuis un client MySQL ou la wx en lecture.

Attendus :

- cas invalide : aucune écriture ;
- cas valide : commit unique ;
- relecture après commit cohérente ;
- annulation : aucune modification ;
- persistance après redémarrage.

## 7. Frais via l'UI Qt

Sur un individu de recette :

1. créer un déplacement ;
2. modifier le déplacement ;
3. créer un remboursement ;
4. rattacher plusieurs déplacements ;
5. tenter de rattacher un déplacement appartenant déjà à un autre remboursement ;
6. supprimer/détacher selon le parcours autorisé ;
7. relancer l'application.

Attendus :

- mêmes garanties que le test automatisé ;
- aucune relation orpheline ;
- aucun ID de remboursement perdu après redémarrage.

## 8. Documents RH

Depuis un contrat réel de la copie :

- ouvrir Documents RH ;
- parcourir les types ;
- vérifier les modèles compatibles ;
- vérifier les états prêt / bloqué / préparation externe ;
- tester un contrat avec données incomplètes.

Attendus :

- lecture des métadonnées MySQL sans création de table ;
- aucune migration de schéma déclenchée par la consultation ;
- Word/LibreOffice ne sont pas lancés dans la 0.1 ;
- aucun fichier n'est présenté comme généré.

## 9. Contrôle de schéma

Avant et après la recette, comparer la liste des tables et colonnes de la copie.

La simple consultation Qt ne doit créer aucune table ni colonne.

Les seules modifications attendues sont les lignes métier explicitement créées/modifiées par la recette.

## 10. Fermeture

Après plusieurs chargements d'individus :

- fermer Qt ;
- vérifier l'absence de `QThread destroyed while running` ;
- vérifier qu'aucune connexion MySQL Teamworks ne reste bloquée côté serveur.

## Verdict

**PASS MySQL réel** uniquement si :

- version serveur identique à la production ;
- test automatisé Frais vert ;
- Individus/Généralités conformes en lecture ;
- Contrats CRUD borné vert ;
- Frais UI vert ;
- Documents RH lecture/préparation verte ;
- aucune mutation de schéma inattendue ;
- aucune perte ou corruption de données ;
- fermeture propre.

Le résultat doit mentionner : date, SHA Qt Vanilla, version Windows, version MySQL exacte, nom de la base de recette et verdict.
