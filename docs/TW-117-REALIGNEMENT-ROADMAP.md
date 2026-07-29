# TW-117 — Réalignement du registre après packaging Windows

## Constat

Les lots Windows ont été livrés plus vite que la consolidation de la feuille de route centrale :

- **TW-114** : paquet Windows portable reproductible, fusionné par la PR #177 (`786a5e69da4a4abab096330e9670f2d934e45f5b`) ;
- **TW-115** : smoke test de démarrage réel de l’exécutable, fusionné par la PR #180 (`6c204fcee85a900e7922d948eb588e1b0b4fe4f6`).

Le libellé historique « stabiliser les parcours essentiels » ne doit donc plus utiliser TW-115.

## Décision

Le prochain lot fonctionnel reçoit l’identifiant **TW-118 — Stabiliser les parcours essentiels de la version intermédiaire**.

Critère de sortie :

- ouverture d’une base SQLite existante ;
- affichage de l’accueil ;
- ouverture d’une fiche salarié ;
- exécution des contrôles CCNS prioritaires ;
- production des exports essentiels ;
- absence de crash bloquant sur ces parcours ;
- vérifications reproductibles documentées.

Le thème sombre reste **TW-116** et ne démarre qu’après TW-118.

## Consolidation attendue

Lors de la prochaine modification complète de `docs/FEUILLE_ROUTE_MAINTENANCE.md`, reporter :

- TW-114 : Terminé — PR #177 ;
- TW-115 : Terminé — PR #180 ;
- TW-116 : Prêt — thème sombre pragmatique ;
- TW-117 : Terminé — réalignement du registre ;
- TW-118 : Prêt — stabilisation des parcours essentiels.
