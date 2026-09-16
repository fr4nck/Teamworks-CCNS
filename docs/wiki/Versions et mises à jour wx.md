# Versions et mises à jour wx

<a id="version-lire"></a>
## Comprendre les identifiants

| Terme | Signification |
|---|---|
| **VERSION** | fichier canonique lu par la Vanilla wx pour afficher l’identité du logiciel |
| **RC** | *release candidate* : version candidate en validation, pas une stable finale par simple déduction |
| **Commit / SHA** | identifiant Git exact d’un état du code |
| **BUILD.txt** | métadonnée de build utilisée par certains paquets/rapports si le fichier existe |
| **Release GitHub** | paquet/version publié dans l’espace Releases du dépôt |
| **Vanilla wx** | rail wxPython historique/de production documenté par ce wiki |
| **Qt** | migration séparée, non couverte par les procédures wx de cette page |

<a id="version-documentee"></a>
## Version documentée

La branche documentaire auditée porte `VERSION = 0.9.2-rc3`. Il s’agit d’une **RC**. Le commit de départ de cette passe documentaire était `cf24b659cdcfa3e51db09c55e26c47f4898c2a35`.

Les Releases GitHub publiées peuvent être antérieures à cette RC : une branche de validation n’est pas automatiquement une release stable distribuée.

<a id="releases-github"></a>
## Releases GitHub

Pour installer une version publiée, utilisez l’espace **Releases** du dépôt et contrôlez le numéro, le type de paquet et, lorsqu’il est fourni, le fichier de sommes de contrôle. Une RC de branche n’est pas à présenter comme stable tant qu’elle n’a pas été publiée/qualifiée comme telle.

<a id="mise-a-jour-wx"></a>
## Mise à jour dans l’application

Le menu wx contient **Outils > Rechercher une mise à jour du logiciel**, et le cœur appelle une recherche de mise à jour au démarrage. Cela prouve la présence du mécanisme historique, **pas qu’un updater complet et fiable est livré pour la RC actuelle**.

**À confirmer en recette fonctionnelle :** découverte, téléchargement et application d’une mise à jour depuis un paquet Vanilla wx actuel.

Le mécanisme décrit ici concerne **la wx uniquement**. Il ne doit pas être utilisé pour déduire un processus de mise à jour Qt.

<a id="avant-maj-version"></a>
## Avant une mise à jour

1. suivre la checklist [[Sauvegardes et restauration#avant-mise-a-jour]] ;
2. noter la version actuellement affichée ;
3. identifier la release/RC cible ;
4. fermer Teamworks proprement ;
5. conserver l’ancien paquet le temps de valider les données avec la nouvelle version.

## BUILD.txt et VERSION

Les rapports de crash cherchent les deux fichiers lorsqu’ils existent. Dans le dépôt source audité, `VERSION` est la référence sûre ; ne supposez pas la présence systématique de `BUILD.txt` dans tous les environnements.

## Liens associés

[[Installer Teamworks-CCNS wx]] · [[Sauvegardes et restauration]] · [[Diagnostic et rapports de crash]] · [[Historique, versions et héritage]]
