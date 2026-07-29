# Politique CI Teamworks-CCNS

## Principe

La CI doit apporter une preuve utile sans multiplier les exécutions coûteuses.

## Tests automatiques

Les contrôles rapides de compilation, tests unitaires et audits statiques peuvent s'exécuter sur les pull requests lorsqu'ils couvrent directement les fichiers modifiés.

## Build Windows

Le build Windows complet n'est jamais déclenché automatiquement sur chaque pull request ou chaque push.

Il est lancé uniquement :

- manuellement lorsqu'un lot cohérent doit être testé sur Windows ;
- automatiquement lors de la création d'un tag de version.

Un seul workflow Windows produit l'exécutable, exécute le smoke test et crée le ZIP portable.

## Ressources

- aucun workflow redondant pour une même preuve ;
- annulation d'une exécution précédente du même build lorsqu'une nouvelle démarre ;
- conservation courte des artefacts intermédiaires ;
- aucun build pour une modification documentaire seule ;
- aucun statut bêta, RC ou stable sans validation Windows réelle.
