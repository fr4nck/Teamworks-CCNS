# Présences et planning

## À quoi ça sert ?

L'espace **Présences** sert à consulter et saisir les plages de présence du dossier. La même donnée est accessible depuis l'onglet **Présences** d'une fiche individuelle pour travailler sur une seule personne.

## Où la trouver ?

- onglet principal **Présences** pour la vue globale ;
- **Individus > ouvrir une fiche > Présences** pour une personne.

## Fonction disponible

### Navigation et affichage

La vue globale s'appuie sur un calendrier/planning wx et permet de changer la période affichée. Les présences sont associées à une personne, une date, des heures de début/fin et une catégorie de présence.

### Ajouter une présence

Le dialogue de saisie permet de choisir une ou plusieurs personnes selon le point d'entrée, une ou plusieurs dates, l'heure de début et de fin, la catégorie de présence, et une légende/complément lorsque l'écran le propose.

Le code vérifie qu'une plage ne chevauche pas une présence existante pour la même personne, avec contrôle SQL direct sur les heures ; une saisie qui se superpose est refusée avec un message explicatif (y compris pour une saisie multi-personnes/dates, avec rapport des lignes rejetées).

### Modifier et supprimer

Les listes de présences exposent **Ajouter**, **Modifier** et **Supprimer**. Dans la fiche individuelle, on trouve aussi **Imprimer**, **Statistiques** et l'application d'un **Modèle**.

### Modèles et répétition

Le contrôleur contient une voie de modèles de présence permettant de réutiliser une organisation enregistrée. Le détail clic par clic et les conséquences sur une période complète restent **à confirmer en recette fonctionnelle**.

### Impression et statistiques

Le dépôt contient le moteur d'impression graphique des présences et un dialogue de statistiques. Leur disponibilité est prouvée dans les contrôleurs ; le rendu exact doit être vérifié sur Windows avant d'en faire une référence visuelle.

## Données utilisées

- personne ;
- date ;
- début/fin ;
- catégorie ;
- informations de planning associées.

Les contrats et personnes constituent le contexte du dossier, mais une présence n'est pas un contrat : corrigez les données à leur source plutôt que de forcer une saisie de planning incohérente.

## Résultat attendu

Une présence validée apparaît dans le planning et dans l'onglet Présences de la personne concernée. Les modifications doivent se refléter lors du rafraîchissement de la liste/planning.

!!! info "Un moteur de planning plus riche existe dans le code, mais n'est pas encore branché à l'écran"
    Le dépôt contient un moteur de domaine « Planning/Missions » (statuts de planning brouillon/validé/publié/archivé, occurrences de mission, affectations, disponibilités hebdomadaires, détection de conflits) nettement plus élaboré que l'écran Présences décrit ci-dessus. **Aucun écran de l'application ne l'utilise aujourd'hui** — il n'est référencé que par les tests automatisés. C'est une base de travail pour une future évolution, pas une fonctionnalité disponible : n'en déduisez pas de comportement pour l'écran Présences actuel.

## Contrôle métier encore à valider

La présence du moteur de contrats CCNS/CEE ne prouve pas que chaque règle de durée du travail, repos ou plafond est automatiquement contrôlée dans l'écran Présences.

!!! warning "À confirmer en recette fonctionnelle"
    - règles conventionnelles de planning effectivement signalées dans cet écran ;
    - comportement des modèles sur des périodes complexes ;
    - rendu et contenu exacts des statistiques/impressions ;
    - interactions complètes entre rupture/fin de contrat et planning.

## Publipostage

Le moteur générique ne déclare pas de contexte `presence`. N'inventez pas de balise de présence dans Teamword/Word/Writer. Voir la [référence des mots-clés](../publipostage/mots-cles.md).

## Problèmes fréquents

- **La saisie est refusée :** vérifier les horaires et un éventuel chevauchement.
- **Une personne n'apparaît pas comme attendu :** contrôler sa fiche et la période affichée.
- **Le planning semble lent :** distinguer temps de chargement local et latence MySQL ; voir [Problèmes fréquents](../reference/problemes-frequents.md).

## Voir aussi

[Individus et fiches](individus.md) · [Contrats, CCNS et CEE](contrats-ccns-cee.md) · [Paramétrage](../administration/parametrage.md) · [Problèmes fréquents](../reference/problemes-frequents.md)
