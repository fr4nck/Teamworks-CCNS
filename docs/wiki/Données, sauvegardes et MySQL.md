# Données, sauvegardes et MySQL

<a id="donnees-locales"></a>
## Données locales

Un dossier local utilise des fichiers du répertoire de données, notamment `<nom>_TDATA.dat`. Les sauvegardes savent aussi inclure les catégories photos (`TPHOTOS`) et documents numérisés (`TDOCUMENTS`) lorsqu’elles existent.

Utilisez les commandes Teamworks pour créer, ouvrir, sauvegarder et convertir un dossier plutôt que de déplacer manuellement ses fichiers.

<a id="donnees-reseau"></a>
## Réseau / MySQL

Un dossier réseau est identifié par le marqueur `[RESEAU]` et des paramètres de connexion. Teamworks sait choisir l’interface MySQL disponible (`MySQLdb` ou `mysql.connector`) et mémorise ce choix.

Le menu **Fichier** contient **Convertir en fichier réseau** et **Convertir en fichier local**. Leur activation dépend du type de dossier ouvert.

### Conversion local ↔ réseau

Ces commandes sont réellement présentes et les routines de conversion existent. Parce qu’elles changent le support de stockage, faites une sauvegarde et notez le nom du dossier ainsi que les paramètres réseau avant de commencer.

**À confirmer en recette fonctionnelle :** parcours complet d’une conversion aller/retour sur la RC documentée et comportement en cas d’interruption réseau.

<a id="performance-mysql"></a>
## Performance et latence MySQL

Un serveur distant ajoute un temps aller-retour à chaque requête. Pour distinguer latence réseau et lenteur applicative, notez :

- l’action exacte : liste Individus, ouverture de fiche, changement d’onglet, fermeture/rafraîchissement ;
- l’heure ;
- le mode local ou réseau ;
- si possible le même parcours sur une connexion plus proche.

Ne publiez jamais le mot de passe ni une chaîne de connexion complète dans un rapport public.

## Sauvegarder et restaurer

Les commandes **Fichier > Créer une sauvegarde**, **Restaurer une sauvegarde** et **Sauvegardes automatiques** couvrent les données locales et réseau selon les paramètres disponibles. Pour MySQL, la sauvegarde réseau passe par `mysqldump` et nécessite que les outils MySQL soient accessibles sur le poste qui effectue l’opération.

Voir [[Sauvegardes et restauration]] pour le parcours pratique.

## Compatibilité de base

À l’ouverture, Teamworks vérifie/adapte la structure de données prévue par la version. Une migration de schéma n’est pas une raison de supprimer l’ancienne sauvegarde : conservez une copie antérieure tant que la nouvelle version n’est pas validée sur vos données.

## Diagnostic réseau

Pour un problème MySQL, réunissez : version Teamworks, local/réseau, hôte et port **sans mot de passe**, action exacte, heure, message d’erreur, reproductibilité et rapport de crash éventuel. Voir [[Diagnostic et rapports de crash]].

## Liens associés

[[Sauvegardes et restauration]] · [[Versions et mises à jour wx]] · [[Problèmes fréquents]] · [[Diagnostic et rapports de crash]]
