# Présences et planning

L’espace **Présences** est un onglet principal de Teamworks-CCNS wx et la fiche individuelle possède aussi un onglet **Présences**.

## Deux niveaux d’utilisation

- **Présences globales** : utilisez l’onglet principal Présences pour travailler à l’échelle du dossier.
- **Présences d’une personne** : ouvrez la fiche Individu puis l’onglet Présences pour rester centré sur cette personne.

La liste Individus peut également rechercher les personnes **présentes sur une période donnée** : utilisez le bouton de recherche par période, choisissez les deux dates puis revenez à **Afficher tout** pour supprimer ce filtre.

## Planning et périodes

Les écrans de présences/planning utilisent les données déjà enregistrées pour la personne. Avant de corriger un résultat de planning, vérifiez le contrat et la période concernés afin d’éviter de compenser un problème de données par une saisie incohérente.

## Impression

Le dépôt contient un moteur d’impression graphique des présences (`UTILS_Impression_presences_graph.py`). Les détails d’impression dépendent de l’écran qui l’appelle ; si une option précise n’apparaît pas dans votre version, ne la déduisez pas de ce module seul.

## Mots-clés de publipostage liés aux présences et au planning

Le moteur générique audité **ne déclare pas de catégorie `presence`** dans `UTILS_Publipostage_donnees.py`. Il n’existe donc pas, dans ce parcours générique, de liste vérifiée de balises propres aux présences à recopier dans un modèle.

Les balises Individu restent documentées pour les parcours Individu/Contrat où elles sont réellement exposées : voir [[Mots-clés de publipostage]]. Ne supposez pas qu’elles sont disponibles depuis un écran Présences tant que celui-ci ne lance pas l’assistant avec un contexte pris en charge.

## À documenter après validation fonctionnelle

Le détail exhaustif des actions de planning (création de plages, duplication, suppression et impressions selon écran) doit encore être confirmé par une recette interactive Windows avant d’être présenté comme procédure utilisateur stable.
