# Données, sauvegardes et MySQL

Teamworks-CCNS wx sait travailler avec des données locales et avec un dossier réseau/MySQL. Cette page explique ce que l’utilisateur doit retenir sans transformer le wiki en documentation d’administration SQL.

## Dossier local

Le code wx reconnaît les fichiers locaux dans le répertoire Data, notamment `<nom>_TDATA.dat`. Le nom du dossier choisi dans Teamworks est plus important que la manipulation manuelle de ce fichier : utilisez les commandes de l’application pour créer, ouvrir, sauvegarder ou convertir.

## Dossier réseau / MySQL

Un identifiant de dossier réseau contient le marqueur `[RESEAU]` et les paramètres nécessaires à la connexion. L’application peut utiliser une interface MySQL disponible (`MySQLdb` ou `mysql.connector` selon l’environnement) et mémorise le choix dans sa configuration.

Le menu Fichier comporte **Convertir en fichier réseau** et **Convertir en fichier local**. Ces actions sont activées/désactivées en fonction du type de dossier actuellement ouvert.

## Latence réseau

Un serveur MySQL distant peut rendre visibles les temps aller-retour. Distinguez un temps réseau normal d’un blocage applicatif : notez l’action exacte (ouvrir la liste Individus, ouvrir une fiche, changer d’onglet, fermer la fiche) et comparez si possible avec le même parcours sur une liaison plus proche.

## Sauvegardes

Utilisez les commandes Teamworks plutôt qu’une copie improvisée : voir [[Sauvegardes et restauration]]. Les sauvegardes automatiques peuvent être exécutées à la fermeture selon la configuration.

## Mot de passe de dossier

Un dossier peut contenir un mot de passe dans ses données de configuration. Teamworks le demande à l’ouverture et refuse le dossier si la saisie est incorrecte. Ce mot de passe d’ouverture n’est pas la même chose qu’un compte MySQL.

## Version de la base

À l’ouverture, Teamworks vérifie la version du fichier/dossier et peut appliquer les adaptations prévues par l’application. Avant toute montée de version, sauvegardez le dossier dans son état antérieur.

## Diagnostic réseau

Pour un signalement, fournir : version Teamworks, local ou réseau, hôte/port sans mot de passe, action lente, heure du test, message d’erreur et si le problème est reproductible. Ne publiez jamais de mot de passe ou de chaîne de connexion complète.
