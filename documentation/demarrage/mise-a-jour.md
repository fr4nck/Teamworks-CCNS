# Mises à jour

## Comprendre les identifiants

| Terme | Signification |
|---|---|
| **VERSION** | fichier canonique à la racine du dépôt, lu par la Vanilla wx pour afficher l'identité du logiciel. Son contenu varie selon la branche/le paquet installé — ne pas supposer un numéro fixe. |
| **RC** (release candidate) | version candidate en validation, pas une stable finale par simple déduction |
| **Commit / SHA** | identifiant Git exact d'un état du code |
| **BUILD.txt** | métadonnée de build utilisée par certains paquets/rapports, si le fichier existe |
| **Release GitHub** | paquet/version publié dans l'espace Releases du dépôt |
| **Vanilla wx** | rail wxPython historique/de production, seul rail disponible aujourd'hui |
| **Qt** | trajectoire à l'étude, sans code livré — voir [Trajectoire Qt](../architecture/qt.md) |

!!! info "Vérifier la version installée"
    La référence de version d'une copie donnée est toujours son propre fichier `VERSION` — ne vous fiez pas à un numéro cité dans une documentation générale, y compris celle-ci.

## Releases GitHub

Pour installer une version publiée, utilisez l'espace **Releases** du dépôt et contrôlez le numéro, le type de paquet et, lorsqu'il est fourni, le fichier de sommes de contrôle (SHA-256). Une RC de branche n'est pas à présenter comme stable tant qu'elle n'a pas été publiée/qualifiée comme telle.

## Mise à jour dans l'application

Le menu wx contient **Outils > Rechercher une mise à jour du logiciel**, et le cœur appelle une recherche de mise à jour au démarrage. Cela prouve la présence du mécanisme historique, **pas qu'un updater complet et fiable est livré pour la version courante**.

!!! warning "À confirmer en recette fonctionnelle"
    Découverte, téléchargement et application d'une mise à jour depuis un paquet Vanilla wx actuel.

Ce mécanisme concerne **la wx uniquement** ; il ne doit pas être utilisé pour déduire un processus de mise à jour Qt (inexistant à ce jour).

## Avant une mise à jour

1. Suivre la checklist [Sauvegardes et restauration — avant une mise à jour](../administration/donnees-sauvegardes.md#avant-mise-a-jour).
2. Noter la version actuellement affichée.
3. Identifier la release/RC cible.
4. Fermer Teamworks proprement.
5. Conserver l'ancien paquet le temps de valider les données avec la nouvelle version.

## BUILD.txt et VERSION

Les rapports de crash cherchent les deux fichiers lorsqu'ils existent. `VERSION` est la référence sûre ; ne supposez pas la présence systématique de `BUILD.txt` dans tous les environnements.

## Voir aussi

[Installation](installation.md) · [Données, sauvegardes et MySQL](../administration/donnees-sauvegardes.md) · [Diagnostic et rapports de crash](../administration/diagnostic.md) · [Historique du projet](../historique/origine-et-wiki.md)
