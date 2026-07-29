# TW-117 — Stabilisation des parcours essentiels

## Objectif

Valider la version Windows intermédiaire sur les parcours métier indispensables avant tout travail de thème sombre.

## Périmètre prioritaire

1. démarrage de l'application et affichage de l'accueil ;
2. ouverture d'une base Teamworks existante ;
3. ouverture et consultation d'une fiche salarié ;
4. affichage des contrats et classifications ;
5. exécution des contrôles CCNS principaux ;
6. ouverture des dossiers incomplets ;
7. génération des exports essentiels ;
8. fermeture propre de l'application.

## Méthode

- utiliser le paquet Windows portable produit par la CI ;
- tester d'abord sur une copie de base réelle ;
- consigner pour chaque parcours : résultat, erreur, journal et capture utile ;
- corriger dans des lots ciblés sans refonte large de l'interface ;
- reconstruire et relancer le smoke test Windows après chaque correction bloquante.

## Critères de sortie

- aucun crash bloquant sur les huit parcours ;
- aucune altération de la base de test ;
- erreurs résiduelles explicitement documentées ;
- paquet Windows reproductible et CI verte ;
- thème sombre maintenu après cette phase.
