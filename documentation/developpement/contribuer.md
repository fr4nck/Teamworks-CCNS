# Contribuer et documenter

Cette page complète `AGENTS.md` (à la racine du dépôt) pour ce qui concerne spécifiquement la documentation MkDocs.

## Principe

Cette documentation est construite à partir de l'état réel du code, jamais à partir de suppositions. Pour toute fonctionnalité décrite :

- vérifier le comportement dans le code actuel avant de documenter ;
- distinguer explicitement **disponible**, **partiel**, **expérimental**, **prévu** et **historique/obsolète** ;
- signaler un doute avec la mention **« à confirmer en recette fonctionnelle »** plutôt que d'affirmer un comportement non vérifié ;
- en cas de divergence entre cette documentation et le code, corriger la documentation pour refléter le comportement actuel, et non l'inverse.

## Quand mettre à jour la documentation

Lorsqu'une pull request modifie de façon significative une fonctionnalité utilisateur, un paramètre, une interface, un mot-clé de publipostage, un workflow ou un comportement métier, la documentation correspondante doit être vérifiée et mise à jour dans la même PR (ou signalée comme à mettre à jour si l'ampleur du sujet le justifie). Cette règle vise la cohérence, pas la bureaucratie : une correction mineure de code sans impact utilisateur n'exige pas de modification documentaire.

## Ajouter ou modifier une page

1. Éditer les fichiers dans `documentation/`.
2. Ajouter toute nouvelle page à la navigation (`nav:`) de `mkdocs.yml`.
3. Vérifier localement : voir [Démarrer en développement](demarrer-dev.md).
4. Lancer `mkdocs build --strict` avant de proposer la modification — un lien cassé ou une page orpheline doit être corrigé, pas ignoré.

## Où va quoi

- **`utilisation/`** : ce qu'un utilisateur final fait avec le logiciel.
- **`publipostage/`** : référence technique du moteur de mots-clés (source de vérité : le code du moteur, pas les modèles d'exemple).
- **`administration/`** : réglages et opérations réservés à un administrateur du dossier.
- **`architecture/`** et **`developpement/`** : lecture développeur/agent IA, sans dupliquer le contenu utilisateur.

Évitez de créer une nouvelle page pour un sujet qui tient en une section d'une page existante — préférez enrichir une page proche plutôt que multiplier les fichiers courts.

## Voir aussi

[Démarrer en développement](demarrer-dev.md) · [Organisation du dépôt](organisation-depot.md) · [Historique et migration du Wiki](../historique/origine-et-wiki.md)
