# Teamworks-CCNS 0.9.1f

Corrective de recette de la 0.9.1e centrée sur les régressions d'interface observées sous Windows.

## Corrections

- Préférences : fenêtre redimensionnable, contenu vertical défilable et pied `Valider / Annuler` maintenu hors de la zone défilante afin que les actions restent accessibles sur écran réduit, Snap Windows ou zoom élevé.
- Apparence : le changement clair/sombre n'est plus réappliqué partiellement pendant la fermeture du dialogue. L'apparence native complète est stabilisée au redémarrage de Teamworks-CCNS.
- Premier affichage : thème, métriques et bitmaps sont rafraîchis explicitement afin d'éviter les icônes qui n'apparaissaient qu'après survol ou clic et les surfaces recolorées tardivement.
- Listes : propagation du thème aux contrôles de liste/ObjectListView pour éviter une grille blanche dans une interface sombre.
- Fiche individuelle / Généralités : la page réellement utilisée par la fiche est désormais scrollable et son layout 1/2 colonnes est calculé avant le premier affichage.
- Adresse postale : CP et ville de résidence sont saisissables librement ; la base française de villes reste une assistance via `Rechercher` et ne doit plus bloquer ou remplacer une saisie valide.
- International : maintien de la saisie libre du lieu de naissance hors France et de la règle NIR `99` pour une naissance à l'étranger.

## Validation

Avant versionnage, la CI a validé les tests du socle et les parcours critiques Windows sur `master`, incluant la fiche personne et les contrats. Les tests de contrat UI ont été adaptés au nouveau comportement attendu plutôt que de réintroduire les hypothèses de la 0.9.1e.

Cette version remplace la 0.9.1e pour la recette des contrats.
