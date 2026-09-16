# Présences et planning

<a id="presences-disponible"></a>
## À quoi ça sert ?

L’espace **Présences** sert à consulter et saisir les plages de présence du dossier. La même donnée est accessible depuis l’onglet **Présences** d’une fiche individuelle pour travailler sur une seule personne.

## Où la trouver ?

- onglet principal **Présences** pour la vue globale ;
- **Individus > ouvrir une fiche > Présences** pour une personne.

## Fonction disponible

### Navigation et affichage

La vue globale s’appuie sur un calendrier/planning wx et permet de changer la période affichée. Les présences sont associées à une personne, une date, des heures de début/fin et une catégorie de présence.

### Ajouter une présence

Le dialogue de saisie permet de choisir :

- une ou plusieurs personnes selon le point d’entrée ;
- une ou plusieurs dates ;
- heure de début et heure de fin ;
- catégorie de présence ;
- légende/complément lorsque l’écran le propose.

Le code vérifie qu’une plage ne chevauche pas une présence existante pour la même personne. Une saisie qui se superpose est refusée avec un message explicatif.

### Modifier et supprimer

Les listes de présences exposent **Ajouter**, **Modifier** et **Supprimer**. Dans la fiche individuelle, on trouve aussi **Imprimer**, **Statistiques** et l’application d’un **Modèle**.

### Modèles et répétition

Le contrôleur contient une voie de modèles de présence permettant de réutiliser une organisation enregistrée. Le détail clic par clic et les conséquences sur une période complète sont **À confirmer en recette fonctionnelle**.

### Impression et statistiques

Le dépôt contient le moteur d’impression graphique des présences et un dialogue de statistiques. Leur disponibilité est prouvée dans les contrôleurs ; le rendu exact doit être vérifié sur Windows avant d’en faire une référence visuelle.

## Données utilisées

- personne ;
- date ;
- début/fin ;
- catégorie ;
- informations de planning associées.

Les contrats et personnes constituent le contexte du dossier, mais une présence n’est pas un contrat : corrigez les données à leur source plutôt que de forcer une saisie de planning incohérente.

## Résultat attendu

Une présence validée apparaît dans le planning et dans l’onglet Présences de la personne concernée. Les modifications doivent se refléter lors du rafraîchissement de la liste/planning.

<a id="presences-controle-metier"></a>
## Contrôle métier encore à valider

La présence du moteur de contrats CCNS/CEE ne prouve pas que chaque règle de durée du travail, repos ou plafond est automatiquement contrôlée dans l’écran Présences.

**À confirmer en recette fonctionnelle :**

- règles conventionnelles de planning effectivement signalées dans cette page ;
- comportement des modèles sur des périodes complexes ;
- rendu et contenu exacts des statistiques/impressions ;
- interactions complètes entre rupture/fin de contrat et planning.

Le wiki ne présente donc pas ces contrôles comme une validation juridique ou conventionnelle du planning.

## Publipostage

Le moteur générique ne déclare pas de contexte `presence`. N’inventez pas de balise de présence dans Teamword/Word/Writer. Voir [[Mots-clés de publipostage]].

## Problèmes fréquents

- **La saisie est refusée :** vérifier les horaires et un éventuel chevauchement.
- **Une personne n’apparaît pas comme attendu :** contrôler sa fiche et la période affichée.
- **Le planning semble lent :** distinguer temps de chargement local et latence MySQL ; voir [[Problèmes fréquents]].

## Liens associés

[[Individus et fiches]] · [[Contrats, CCNS et CEE]] · [[Paramétrage]] · [[Problèmes fréquents]]
