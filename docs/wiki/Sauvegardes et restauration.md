# Sauvegardes et restauration

<a id="sauvegarde-manuelle"></a>
## À quoi ça sert ?

Les sauvegardes protègent le dossier avant une mise à jour, une migration, une conversion réseau ou une modification importante. Teamworks sait sauvegarder les données locales et, avec les outils nécessaires, les bases réseau/MySQL.

## Où les trouver ?

Menu **Fichier** :

- **Créer une sauvegarde** ;
- **Restaurer une sauvegarde** ;
- **Sauvegardes automatiques**.

## Créer une sauvegarde manuelle

1. Ouvrez le dossier à protéger.
2. Choisissez **Fichier > Créer une sauvegarde**.
3. Vérifiez les catégories de données et la destination proposées.
4. Selon les options, incluez aussi modèles et éditions si vous voulez les conserver avec la sauvegarde.
5. Contrôlez qu’un fichier a réellement été créé avant une opération risquée.

Le moteur crée une archive `.twd` non chiffrée ou `.twc` lorsqu’un mot de passe de sauvegarde est utilisé.

### Dossier réseau/MySQL

La sauvegarde MySQL utilise `mysqldump` puis intègre le fichier SQL à l’archive. Si Teamworks ne localise pas MySQL ou si l’export échoue, la sauvegarde réseau est signalée en échec.

<a id="sauvegardes-auto"></a>
## Sauvegardes automatiques

Une procédure automatique peut définir : destination, nom, fichiers locaux/réseau, modèles/éditions, envoi email et conditions d’exécution. Le moteur sait notamment conditionner l’exécution selon jours scolaires/vacances, plage horaire, poste, ancienneté de la dernière sauvegarde et utilisateur, puis supprimer les anciennes archives selon une durée configurée.

Teamworks lance la vérification des sauvegardes automatiques lors de la fermeture lorsque cette fonction est active.

<a id="restauration"></a>
## Restaurer

1. Conservez une copie intacte de l’archive d’origine.
2. Fermez les écrans qui modifient encore le dossier.
3. Choisissez **Fichier > Restaurer une sauvegarde**.
4. Identifiez précisément la sauvegarde et sa date.
5. Confirmez l’écrasement seulement après avoir vérifié le dossier cible.
6. Après restauration, ouvrez quelques fiches, contrats, présences et documents pour contrôler le résultat.

Le moteur demande confirmation avant de remplacer des fichiers locaux déjà présents. Les restaurations réseau nécessitent les paramètres/outils MySQL adaptés.

<a id="avant-mise-a-jour"></a>
## Avant une mise à jour

Checklist courte :

- [ ] faire une sauvegarde ;
- [ ] noter la version actuellement utilisée ;
- [ ] fermer Teamworks proprement ;
- [ ] conserver le paquet/installateur précédent si nécessaire ;
- [ ] après mise à jour, vérifier le dossier sur quelques parcours avant de supprimer l’ancienne sauvegarde.

## Précautions

- Une archive de sauvegarde peut contenir des données personnelles : protégez son emplacement.
- Ne testez pas une restauration destructive sur l’unique copie de production.
- Une base ouverte par une version plus récente peut recevoir des adaptations de schéma ; conservez une sauvegarde faite avant l’ouverture.
- Le succès d’une sauvegarde automatisée mérite d’être vérifié périodiquement par une restauration sur copie.

## Problèmes fréquents

Si le répertoire n’existe plus, si `mysqldump` est introuvable ou si la restauration échoue, ne multipliez pas les essais destructifs : conservez l’archive, notez la version et consultez [[Problèmes fréquents]] / [[Diagnostic et rapports de crash]].

## Liens associés

[[Données, sauvegardes et MySQL]] · [[Versions et mises à jour wx]] · [[Problèmes fréquents]]
