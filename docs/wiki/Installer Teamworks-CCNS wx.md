# Installer Teamworks-CCNS wx

Cette page concerne la **Vanilla wx**, pas la migration Qt.

## Quelle édition utiliser ?

Le projet est distribué sous forme d’installation Windows et, selon la livraison, sous forme portable. L’installateur intègre Teamworks dans un emplacement d’application Windows ; l’édition portable conserve l’application dans le dossier décompressé et se prête mieux aux essais ou à une exécution sans installation classique.

Avant de remplacer une installation utilisée en production, faites une [[sauvegarde|Sauvegardes et restauration]] du dossier métier / de la base concernée et notez la version actuellement utilisée.

## Vérifier la version

La branche documentée contient `VERSION = 0.9.2-rc3`. `rc` signifie **release candidate** : une version destinée à validation avant stabilisation, et non une version finale déclarée stable.

Dans l’application wx, la barre de titre est construite sous la forme `Teamworks v<version>` et affiche aussi le dossier ouvert. Pour un diagnostic, recopiez cette version exactement.

### À propos de `BUILD.txt`

Le fichier `VERSION` est présent dans le dépôt et constitue la source de version de l’application. Aucun `BUILD.txt` racine n’est présent dans l’arbre source de la branche auditée. Certaines constructions distribuées peuvent ajouter des métadonnées de build : si un `BUILD.txt` accompagne votre paquet, joignez-le au diagnostic, mais ne le supposez pas présent sur toutes les installations.

## Installation Windows

1. Fermez Teamworks-CCNS si une version est déjà ouverte.
2. Sauvegardez les données utilisées en production.
3. Lancez l’installateur fourni avec la version que vous avez décidé de déployer.
4. Conservez le chemin proposé sauf contrainte locale connue.
5. Lancez Teamworks et vérifiez la version dans le titre de fenêtre avant d’ouvrir/mettre à niveau un dossier important.

Le manuel ne publie volontairement **aucun ancien lien de téléchargement** : utilisez les livrables de la version actuellement validée par le projet.

## Version portable

1. Décompressez l’archive dans un dossier où vous avez le droit d’écrire.
2. Ne lancez pas directement l’exécutable depuis une archive compressée.
3. Évitez de mélanger les fichiers de deux versions dans le même répertoire : décompressez une nouvelle version dans un nouveau dossier.
4. Ouvrez vos données depuis Teamworks après avoir vérifié la version affichée.

## Premier lancement

Teamworks peut afficher l’**Assistant Démarrage**. Le menu **Fichier** permet aussi de créer un nouveau fichier ou d’ouvrir un fichier existant. L’application mémorise une liste de fichiers récemment ouverts.

Un dossier local est représenté par les données Teamworks dans le répertoire `Data`; le code wx reconnaît notamment le fichier `<nom>_TDATA.dat`. Un dossier réseau/MySQL utilise un identifiant `[RESEAU]` et des paramètres de connexion distincts. Ne renommez pas manuellement ces éléments pour « réparer » un dossier.

## Mise à jour

- sauvegardez avant toute mise à jour ;
- ne remplacez pas votre seule copie fonctionnelle d’une RC par une autre sans retour arrière ;
- ouvrez d’abord un dossier de test représentatif ;
- contrôlez Individus, contrats, présences et un publipostage réel ;
- en cas de migration de schéma proposée par l’application, ne l’interrompez pas.

## Désinstallation

Désinstaller l’application n’est pas une stratégie de sauvegarde des données. Avant toute suppression, identifiez le dossier métier et sa sauvegarde. Pour une édition portable, supprimer le dossier de programme n’efface pas nécessairement les données réseau/MySQL, mais peut supprimer des fichiers locaux si vous les avez volontairement placés à l’intérieur : vérifiez avant suppression.

## En cas de problème

Notez la version, le type d’installation (installateur/portable), le type de dossier (local/réseau), le message affiché et l’action exacte qui l’a provoqué. Voir [[Aide, discussions et signalement de bugs]].
