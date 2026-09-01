# CRH-25 — workflow contrôlé des démarches RH

**Date : 1er septembre 2026**

## Objet

CRH-25 prépare les futures actions du cockpit sans les raccorder encore à wxPython. Le lot fournit une frontière applicative dédiée aux transitions de statut métier des démarches RH et garantit que la projection courante et le journal d'audit sont persistés dans une seule transaction.

## Machine d'états

Le service `HrCaseWorkflowService` ne redéfinit aucune règle de transition. Il interroge `HrCase.can_transition_to()` et applique `HrCase.transition_to()` ; la machine d'états reste donc dans le domaine CRH-03.

Le service expose :

- les transitions actuellement autorisées pour un dossier ;
- l'application d'une transition avec résultat/commentaire éventuels ;
- la création d'un événement `CASE_STATUS_CHANGED` contenant `from_status` et `to_status`.

## Audit

Chaque transition produit un `HrAuditEvent` horodaté avec fuseau. L'identifiant d'événement et l'horloge sont injectables pour les tests et générés automatiquement en production.

Le journal reste append-only : aucun update ou delete d'événement n'est introduit.

## Atomicité et concurrence

`TeamworksHrCaseWorkflowRepository` réutilise le schéma CRH-22 sans nouvelle table ni migration.

La transition est écrite avec un contrôle optimiste sur :

- le statut métier attendu ;
- le statut technique d'échange lu avec le dossier.

Si le dossier a changé entre lecture et validation, l'écriture est refusée avec `StaleTeamworksHrCaseTransitionError` et aucun événement n'est ajouté. De même, une collision d'identifiant d'événement refuse l'ensemble de la transaction.

Cette règle évite qu'un écran resté ouvert écrase silencieusement une modification concurrente.

## Runtime

`HrCaseWorkflowRuntimeFactory` compose :

- l'identité stable de la structure ;
- la transaction de workflow ;
- le service applicatif.

L'interface future n'a donc ni `structure_ref`, ni repository, ni `GestionDB` à manipuler.

## Frontières

CRH-25 n'ajoute :

- aucun bouton wxPython ;
- aucune création automatique de dossier ;
- aucune règle réglementaire nouvelle ;
- aucun changement de statut technique d'échange ;
- aucun réseau, navigateur ou scraping ;
- aucun secret ou contenu médical.

Le sous-lot suivant pourra raccorder des actions explicites du cockpit à ce runtime, avec confirmation utilisateur et rafraîchissement après transition.
