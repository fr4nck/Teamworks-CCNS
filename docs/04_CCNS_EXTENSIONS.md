# Teamworks-CCNS — suivi CCNS et extensions

## Objectif

Ce fichier suit les **fonctionnalités ajoutées par notre fork** : règles CCNS, contrôles métier, nouveaux services, tableaux de bord, exports et extensions propres au produit.

## Périmètre

Entrent notamment ici :

- moteur de règles CCNS ;
- classifications et minima conventionnels ;
- contrôles salariaux ;
- contrats et régimes d'emploi enrichis ;
- historique, alertes et traçabilité réglementaire ;
- planning, disponibilités et contrôles ajoutés ;
- habilitations et sécurité ajoutées ;
- exports et tableaux de bord CCNS ;
- fonctionnalités propres aux besoins PMSL ou à l'évolution fonctionnelle du fork.

## Règle de classement

Un bug déjà présent dans Teamworks original appartient à `01_VANILLA_BUGFIX.md`.

Une adaptation imposée par Python 3/Phoenix appartient à `02_PYTHON3_PHOENIX.md`.

Une régression purement graphique appartient à `03_UI_UX_MODERNISATION.md`.

Tout comportement inexistant dans le Teamworks original et introduit par notre extension métier appartient ici.

## Références principales

- `ROADMAP.md`
- documentation `docs/40-*` à `docs/65-*`
- `docs/48-revue-architecture-ccns.md`
- `docs/50-scope-metier.md`
- `docs/60-scenario-utilisation-controle-salarial.md`

## État initial

Le socle métier CCNS est déjà conséquent : domaine, services de contrôle, règles conventionnelles, présentateurs, exports et documentation sont présents. L'inventaire détaillé devra distinguer implémentation, couverture de tests, raccordement réel à l'interface et recette utilisateur.

## Pourcentage

**À recalculer après inventaire détaillé.**

La progression doit être pondérée par lot fonctionnel et par niveau de validation : code, tests, intégration UI et recette réelle.
