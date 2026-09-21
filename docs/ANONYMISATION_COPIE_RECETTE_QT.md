# Copie représentative anonymisée — Qt Vanilla 0.1

## But

Construire une base de recette suffisamment proche de la base Teamworks réelle pour qualifier la RC Qt Vanilla 0.1, sans conserver les identités, coordonnées, secrets, textes libres, photos ou documents personnels.

L'outil agit **uniquement sur une copie déjà créée**. Il ne sait pas cloner la production et ne doit jamais être pointé directement vers la base de travail.

## Principe

La copie finale suit quatre règles :

1. relations métier conservées ;
2. identités racines remappées ;
3. valeurs personnelles remplacées par des données synthétiques ;
4. aucune table de correspondance original → synthétique conservée.

Le remappage est donc temporairement réversible uniquement en mémoire pendant l'exécution du script. Une fois le processus terminé, la copie ne contient pas ce mapping.

## Nom de base obligatoire

La cible doit se terminer exactement par :

`_qt_vanilla_recette`

Exemple :

`teamworks_ccns_2026_qt_vanilla_recette`

Le script exige en plus une seconde saisie identique via `--confirm-database`.

Une base appelée `teamworks`, `production`, `ccns` ou toute autre cible sans suffixe est refusée avant connexion.

## Préparation

1. faire une sauvegarde normale de la base de travail ;
2. restaurer cette sauvegarde dans une **nouvelle base de recette** ;
3. contrôler que Teamworks de production continue de pointer vers sa base habituelle ;
4. donner au compte d'anonymisation uniquement les droits nécessaires sur la copie et sur `information_schema` ;
5. ne jamais transmettre le mot de passe en argument de ligne de commande.

Le mot de passe est lu uniquement depuis :

`TEAMWORKS_MYSQL_PASSWORD`

## Dry-run obligatoire

Avant toute modification :

```powershell
$env:TEAMWORKS_MYSQL_HOST = "<serveur>"
$env:TEAMWORKS_MYSQL_PORT = "3306"
$env:TEAMWORKS_MYSQL_USER = "<compte-recette>"
$env:TEAMWORKS_MYSQL_PASSWORD = "<mot-de-passe>"

python tools/anonymize_qt_vanilla_recipe_db.py `
  --database "teamworks_ccns_2026_qt_vanilla_recette" `
  --confirm-database "teamworks_ccns_2026_qt_vanilla_recette" `
  --report "anonymisation-dry-run.json"
```

Sans `--apply`, aucun `UPDATE` ni `DELETE` n'est exécuté.

Le rapport contient uniquement des comptes et des informations techniques. Il ne contient pas le mapping des identifiants.

## Application

Si le dry-run est cohérent :

```powershell
python tools/anonymize_qt_vanilla_recipe_db.py `
  --database "teamworks_ccns_2026_qt_vanilla_recette" `
  --confirm-database "teamworks_ccns_2026_qt_vanilla_recette" `
  --apply `
  --report "anonymisation-final.json"
```

Si la copie contient des tables MyISAM ou un autre moteur non transactionnel, l'outil refuse par défaut l'exécution.

Sur une copie jetable explicitement vérifiée, il faut ajouter :

`--acknowledge-nontransactional`

Cette option n'est jamais une autorisation d'exécuter le script sur la production.

## Transformations

### Personnes

- `IDpersonne` remappé vers une séquence synthétique ;
- toutes les colonnes `IDpersonne` et `IDindividu` correspondantes suivent le même mapping ;
- nom, nom de naissance, prénom, adresse, CP et ville remplacés ;
- date de naissance remplacée en conservant le groupe mineur/adulte et une tranche d'âge utile ;
- NIR supprimé ;
- mémo et références photo supprimés ;
- contacts remplacés par `example.test` et numéros factices.

### Candidats

Même principe avec un espace d'identifiants distinct.

### Socle CCNS moderne

- `IDtw_person` remappé ;
- code interne et nom affiché synthétiques ;
- naissance synthétique ;
- contrats `tw_contracts` conservent la relation.

### Dates métier

Les dates liées directement à une personne dans les tables de recette essentielles sont décalées d'un nombre entier de semaines déterministe par personne.

Cela conserve :

- jour de semaine ;
- durée entre dates d'un même dossier ;
- ordre chronologique interne.

Les heures ne sont pas modifiées.

### Rémunérations

Les champs dont le nom contient `salaire` ou `remuner` dans les contrats liés à une personne reçoivent des valeurs synthétiques indépendantes du montant d'origine.

### Frais

Les relations Déplacement/Remboursement et leurs identifiants métier sont conservés. Les lieux et objets de déplacement sont remplacés par des valeurs de recette.

### Textes libres

Sont neutralisés notamment :

- mémos ;
- remarques de candidature ;
- remarques d'entretien ;
- réponses libres de questionnaire ;
- valeurs libres de champs de contrat ;
- descriptions de scénarios ;
- contenus de modèles d'email présents en base.

### Secrets et paramètres

- mots de passe SMTP supprimés ;
- utilisateurs SMTP supprimés ;
- paramètres SMTP supprimés ;
- paramètres de profils vidés ;
- paramètres de sauvegarde sensibles vidés ;
- toute colonne texte dont le nom contient `password`, `motdepasse`, `token`, `secret`, `apikey` ou `api_key` est vidée.

### Photos et documents

Les lignes des tables `photos` et `documents` sont supprimées.

Les modèles génériques statiques de Teamworks ne sont pas concernés : ils appartiennent au code, pas à la copie de données.

## Audit final bloquant

Avant commit, l'outil recherche notamment :

- BLOBs personnels restant dans `photos` ou `documents` ;
- NIR, mémos et références photos non neutralisés ;
- secrets dans les colonnes sensibles ;
- adresses contenant `@` hors du domaine réservé `example.test`.

Si un contrôle échoue :

- l'outil retourne une erreur ;
- la transaction InnoDB est annulée ;
- la copie n'est pas déclarée utilisable.

Pour les moteurs non transactionnels explicitement autorisés, la copie doit être considérée jetable et recréée depuis la sauvegarde si l'audit échoue.

## Vérification manuelle minimale

Après anonymisation :

1. ouvrir 10 individus aléatoires ;
2. vérifier qu'aucun nom/adresse/contact réel n'est reconnaissable ;
3. contrôler plusieurs relations Personne → Contrats ;
4. contrôler Présences ;
5. contrôler Scénarios ;
6. contrôler Déplacements/Remboursements ;
7. contrôler Documents RH ;
8. faire une recherche globale ciblée sur quelques noms/emails réels connus des personnes autorisées à préparer la copie ;
9. ne conserver aucun fichier de correspondance ou dump intermédiaire.

La recherche manuelle sur des valeurs réelles doit se faire localement par la personne autorisée ; ces valeurs ne doivent pas être ajoutées au dépôt ni au rapport de recette.

## Conservation

La copie anonymisée peut devenir le jeu de recette durable si l'audit est vert.

À supprimer après fabrication :

- dump brut intermédiaire ;
- copie non anonymisée ;
- fichiers temporaires ;
- éventuels journaux contenant des valeurs originales.

Le dépôt Git ne doit recevoir que :

- le code d'anonymisation ;
- les tests synthétiques ;
- la procédure ;
- les rapports de recette ne contenant aucune donnée personnelle.
