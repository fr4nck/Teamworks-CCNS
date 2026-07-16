# Habilitations et historique sensible

Cette étape ajoute le socle des habilitations et de l'historique sensible.

## Ce qui est ajouté

- permissions
- rôles par défaut
- utilisateurs
- périmètres d'accès
- événements sensibles
- services simples d'accès et d'historique

## Ce que ça couvre déjà

- accès total pour direction, RH et comptabilité
- accès plus limité pour direction adjointe
- accès planning pour coordination
- accès lecture contrôle pour bénévole dirigeant
- plafond de groupe
- journalisation simple des actions sensibles

## Ce qui n'est pas encore fait

- persistance branchée
- interface graphique
- filtrage fin par site, domaine et type de donnée dans les écrans
- historique détaillé avant/après

## Account métier

Le package `domain.access` contient désormais `Account`, qui représente un utilisateur métier Teamworks indépendamment de toute authentification. Il porte un UUID, une identité civile minimale, un email normalisé, un état actif, des habilitations directes (`AccessGrant`) et des délégations éventuelles.

Une habilitation lie obligatoirement un `Role` et un `Scope` explicite. Une délégation porte elle aussi ce couple, ainsi que son état d'activité. `AuthorizationService.authorize(...)` est l'unique point d'entrée : il autorise une demande seulement lorsqu'une même habilitation active porte à la fois la responsabilité et un périmètre couvrant la demande. Les rôles et les scopes de plusieurs habilitations ne sont jamais combinés. Aucun scope global implicite n'est créé : un accès global doit être déclaré avec `Scope.global_scope()`.

`Account` reste volontairement limité au domaine : il ne contient ni mot de passe, ni session, ni écran wxPython, ni accès base de données, ni persistance. Un compte désactivé ne porte aucun droit effectif jusqu'à réactivation.
