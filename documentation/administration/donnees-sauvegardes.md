# Données, sauvegardes et MySQL

## Données locales

Un dossier local utilise des fichiers du répertoire de données, notamment `<nom>_TDATA.dat`. Les sauvegardes savent aussi inclure les catégories photos (`TPHOTOS`) et documents numérisés (`TDOCUMENTS`) lorsqu'elles existent.

Utilisez les commandes Teamworks pour créer, ouvrir, sauvegarder et convertir un dossier plutôt que de déplacer manuellement ses fichiers.

## Réseau / MySQL

Un dossier réseau est identifié par le marqueur `[RESEAU]` et des paramètres de connexion. Teamworks gère à la fois SQLite (stockage local) et MySQL, via deux interfaces interchangeables (`MySQLdb` ou `mysql.connector`) dont il mémorise le choix.

Le menu **Fichier** contient **Convertir en fichier réseau** et **Convertir en fichier local**. Leur activation dépend du type de dossier ouvert.

### Conversion local ↔ réseau

Ces commandes et leurs routines de conversion sont réellement présentes dans le code. Parce qu'elles changent le support de stockage, faites une sauvegarde et notez le nom du dossier ainsi que les paramètres réseau avant de commencer.

!!! warning "À confirmer en recette fonctionnelle"
    Parcours complet d'une conversion aller/retour, et comportement en cas d'interruption réseau.

## Performance et latence MySQL

Un serveur distant ajoute un temps aller-retour à chaque requête. Pour distinguer latence réseau et lenteur applicative, notez :

- l'action exacte : liste Individus, ouverture de fiche, changement d'onglet, fermeture/rafraîchissement ;
- l'heure ;
- le mode local ou réseau ;
- si possible, le même parcours sur une connexion plus proche.

Ne publiez jamais le mot de passe ni une chaîne de connexion complète dans un rapport public.

## Sauvegarder

Menu **Fichier** :

- **Créer une sauvegarde** ;
- **Restaurer une sauvegarde** ;
- **Sauvegardes automatiques**.

### Créer une sauvegarde manuelle

1. Ouvrez le dossier à protéger.
2. Choisissez **Fichier > Créer une sauvegarde**.
3. Vérifiez les catégories de données et la destination proposées.
4. Selon les options, incluez aussi modèles et éditions si vous voulez les conserver avec la sauvegarde.
5. Contrôlez qu'un fichier a réellement été créé avant une opération risquée.

Le moteur crée une archive `.twd` non chiffrée, ou `.twc` lorsqu'un mot de passe de sauvegarde est utilisé.

### Dossier réseau/MySQL

La sauvegarde MySQL utilise `mysqldump` puis intègre le fichier SQL à l'archive, et nécessite que les outils MySQL soient accessibles sur le poste qui effectue l'opération. Si Teamworks ne localise pas MySQL ou si l'export échoue, la sauvegarde réseau est signalée en échec.

## Sauvegardes automatiques

Une procédure automatique peut définir : destination, nom, fichiers locaux/réseau, modèles/éditions, envoi email et conditions d'exécution. Le moteur sait conditionner l'exécution selon jours scolaires/vacances, plage horaire, poste, ancienneté de la dernière sauvegarde et utilisateur, puis supprimer les anciennes archives selon une durée configurée.

Teamworks lance la vérification des sauvegardes automatiques à la fermeture lorsque cette fonction est active.

## Restaurer {#restauration}

1. Conservez une copie intacte de l'archive d'origine.
2. Fermez les écrans qui modifient encore le dossier.
3. Choisissez **Fichier > Restaurer une sauvegarde**.
4. Identifiez précisément la sauvegarde et sa date.
5. Confirmez l'écrasement seulement après avoir vérifié le dossier cible.
6. Après restauration, ouvrez quelques fiches, contrats, présences et documents pour contrôler le résultat.

Le moteur demande confirmation avant de remplacer des fichiers locaux déjà présents. Les restaurations réseau nécessitent les paramètres/outils MySQL adaptés.

## Avant une mise à jour {#avant-mise-a-jour}

Checklist courte :

- [ ] faire une sauvegarde ;
- [ ] noter la version actuellement utilisée ;
- [ ] fermer Teamworks proprement ;
- [ ] conserver le paquet/installateur précédent si nécessaire ;
- [ ] après mise à jour, vérifier le dossier sur quelques parcours avant de supprimer l'ancienne sauvegarde.

## Compatibilité de base

À l'ouverture, Teamworks vérifie/adapte la structure de données prévue par la version (mécanisme de migration de schéma hérité). Une migration de schéma n'est pas une raison de supprimer l'ancienne sauvegarde : conservez une copie antérieure tant que la nouvelle version n'est pas validée sur vos données.

## Précautions

- Une archive de sauvegarde peut contenir des données personnelles : protégez son emplacement.
- Ne testez pas une restauration destructive sur l'unique copie de production.
- Une base ouverte par une version plus récente peut recevoir des adaptations de schéma ; conservez une sauvegarde faite avant l'ouverture.
- Le succès d'une sauvegarde automatisée mérite d'être vérifié périodiquement par une restauration sur copie.

## Diagnostic réseau

Pour un problème MySQL, réunissez : version Teamworks, local/réseau, hôte et port **sans mot de passe**, action exacte, heure, message d'erreur, reproductibilité et rapport de crash éventuel. Voir [Diagnostic et rapports de crash](diagnostic.md).

## Problèmes fréquents

Si le répertoire n'existe plus, si `mysqldump` est introuvable ou si la restauration échoue, ne multipliez pas les essais destructifs : conservez l'archive, notez la version et consultez [Problèmes fréquents](../reference/problemes-frequents.md) / [Diagnostic et rapports de crash](diagnostic.md).

## Voir aussi

[Mises à jour](../demarrage/mise-a-jour.md) · [Problèmes fréquents](../reference/problemes-frequents.md) · [Diagnostic et rapports de crash](diagnostic.md)
