# CRH-21 — projection du cockpit des démarches RH

**Date : 1er septembre 2026**  
**Statut : développement satellite, UI et persistance de production non incluses**

## Objet

CRH-21 prépare le **cockpit structure des démarches RH** sans raccorder encore les dossiers CRH-03 à la base Teamworks active. Le lot fournit une projection applicative stable, testable avec n'importe quel repository compatible, afin de figer les informations utiles à l'interface avant d'ajouter une migration ou un nouvel écran.

Il matérialise le besoin de tableau de bord prévu dans la trajectoire Connexions RH : tâches en cours, échéances, anomalies, régularisations, échecs techniques et organismes devenus orphelins.

## Séparation métier / technique

Le cockpit conserve deux axes distincts :

- **statut métier** : à faire, préparé, transmis, accepté, anomalie, régularisation, annulé ;
- **statut technique** : non applicable, non démarré, prêt, en cours, réussi, échoué.

Un échange technique réussi ne vaut jamais acceptation par l'organisme. Un échec technique ne transforme pas non plus automatiquement un dossier en anomalie métier.

## Projection

`HrCaseDashboardService` construit, pour une structure et une date de référence explicites :

- le nombre total et le nombre de dossiers ouverts ;
- les compteurs par statut métier ;
- les dossiers échus non clos ;
- les anomalies et régularisations ;
- les échecs techniques d'échange ;
- les références à un organisme qui n'est plus configuré ;
- le nombre de pièces attendues et de pièces déclarées obligatoires par dossier.

Le service **ne calcule pas** de pièces manquantes : CRH-03 décrit les pièces attendues mais ne porte pas encore un état fiable de présence/validation des documents. Le cockpit refuse donc d'inventer cette information.

Les lignes nécessitant une attention sont triées en premier, puis par échéance. Les compteurs restent descriptifs et ne portent aucune conclusion automatique de conformité juridique.

## Frontières

Le service dépend seulement de deux ports de lecture :

1. un repository capable de lister les `HrCase` d'une structure ;
2. le port existant `ConnectionProfileRepository` pour résoudre les libellés d'organismes.

CRH-21 ne dépend ni de wxPython, ni de SQLite, ni de `GestionDB`, ni d'un transport réseau.

## Suite prévue

Une étape distincte devra raccorder les dossiers et événements append-only à la base Teamworks active avec une migration additive compatible SQLite/MySQL. L'écran wxPython du cockpit viendra ensuite consommer **cette projection**, sans porter lui-même de requêtes SQL ni de logique de workflow.

Cette séparation évite de coupler la conception du tableau de bord à une migration de production encore non qualifiée.
