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

Le package `domain.access` contient désormais `Account`, qui représente un utilisateur métier Teamworks indépendamment de toute authentification. Il porte un UUID, une identité civile minimale, un email normalisé, un état actif, des rôles directs et des délégations éventuelles.

`Account` reste volontairement limité au domaine : il ne contient ni mot de passe, ni session, ni écran wxPython, ni accès base de données, ni persistance. Les responsabilités effectives sont évaluées via `can(responsibility)`, `has_workspace(workspace)` et `has_role(code)`. Un compte désactivé ne porte aucun droit effectif jusqu'à réactivation.
