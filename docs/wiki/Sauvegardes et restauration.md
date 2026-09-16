# Sauvegardes et restauration

Les fonctions de sauvegarde sont accessibles dans le menu **Fichier** : **Créer une sauvegarde**, **Restaurer une sauvegarde** et **Sauvegardes automatiques**.

## Créer une sauvegarde manuelle

1. Ouvrez le dossier à sauvegarder.
2. Choisissez **Fichier > Créer une sauvegarde**.
3. Choisissez/contrôlez la destination proposée.
4. Conservez la sauvegarde sur un emplacement distinct des données de travail.
5. Pour une opération risquée, vérifiez qu’un fichier a réellement été créé avant de continuer.

## Sauvegardes automatiques

Teamworks peut déclencher une sauvegarde automatique, notamment lors de la fermeture d’un dossier/application selon la configuration. Le code vérifie aussi que le répertoire de destination enregistré existe ; s’il a disparu, il peut revenir vers le dossier Documents de l’utilisateur.

Une sauvegarde automatique n’est utile que si sa destination est accessible et surveillée. Testez périodiquement la restauration sur une copie.

## Restaurer

1. Fermez les écrans qui modifient encore le dossier.
2. Identifiez précisément la sauvegarde et sa date.
3. Utilisez **Fichier > Restaurer une sauvegarde**.
4. Après restauration, contrôlez quelques individus, contrats, présences et documents avant de reprendre le travail.

## Avant une mise à jour

Toujours créer une sauvegarde avant d’ouvrir pour la première fois un dossier important avec une nouvelle RC/version. Une migration de structure de données peut être irréversible sans sauvegarde antérieure.

## Local et réseau/MySQL

Le mécanisme de stockage diffère entre dossier local et dossier réseau. Ne remplacez pas une sauvegarde MySQL par une simple copie approximative d’un fichier local. Voir [[Données, sauvegardes et MySQL]].

## En cas d’échec

Ne multipliez pas les tentatives de restauration sur l’unique copie. Conservez la sauvegarde d’origine, notez la version de Teamworks et le message d’erreur, puis consultez [[Aide, discussions et signalement de bugs]].
