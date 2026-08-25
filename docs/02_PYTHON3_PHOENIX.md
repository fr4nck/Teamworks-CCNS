# Teamworks — suivi Python 3 / wxPython Phoenix

## Objectif

Ce fichier suit uniquement la **migration technique** depuis le socle historique vers Python 3 et wxPython Phoenix.

Il ne doit pas contenir :

- les bugs déjà présents dans Teamworks Vanilla ;
- la modernisation graphique en tant que telle ;
- les règles CCNS et fonctionnalités métier ajoutées.

## Périmètre

Entrent notamment ici :

- syntaxe et API Python 2 devenues incompatibles ;
- wxPython Classic -> Phoenix ;
- Unicode / encodages / bytes ;
- changements de comportement des contrôles wx ;
- compatibilité des bibliothèques ;
- adaptations de packaging et d'exécution nécessaires à Python 3 ;
- régressions introduites par cette migration.

## Règle de classement

Si un défaut existe déjà dans `Noethys/Teamworks`, il doit être suivi dans `01_VANILLA_BUGFIX.md`, même s'il a été découvert pendant la migration.

Si le code Vanilla fonctionne dans son environnement historique mais nécessite une adaptation pour fonctionner sous Python 3/Phoenix, l'élément appartient ici.

## État initial

Le dépôt contient déjà une migration très avancée et de nombreux garde-fous Windows/Linux. L'inventaire détaillé doit maintenant être reconstruit à partir de la roadmap, des commits historiques et des tests afin de distinguer :

- terminé et testé ;
- terminé mais à confirmer en recette Windows ;
- restant à migrer ;
- dette technique résiduelle.

## Pourcentage

**À recalculer après inventaire détaillé.**

Le pourcentage devra mesurer les lots de migration réellement validés, et non le simple nombre de fichiers modifiés.
