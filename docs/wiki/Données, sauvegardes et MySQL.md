# Données, sauvegardes et MySQL

Teamworks-CCNS peut fonctionner avec des données locales ou une base MySQL distante.

## Mode local

Les données sont stockées dans des fichiers locaux gérés par Teamworks.

Ce mode peut convenir notamment à une utilisation monoposte.

## Mode réseau

Le mode réseau permet de travailler avec une base MySQL partagée.

La qualité de la connexion réseau peut avoir un impact important sur les performances, notamment lors du chargement de listes importantes.

## Sauvegardes

Effectuer régulièrement des sauvegardes.

Avant :

- une mise à jour importante ;
- une migration ;
- une modification massive de données ;

une sauvegarde récente est fortement recommandée.

## Performance

Teamworks-CCNS comprend des outils de diagnostic permettant de distinguer notamment :

- temps de connexion ;
- temps SQL ;
- nombre de requêtes ;
- traitement Python/wx.

Ces diagnostics peuvent être utilisés lors d'une recette sans enregistrer le contenu des données utilisateur.
