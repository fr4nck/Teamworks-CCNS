# CRH-27 — historique des démarches RH

**Date : 1er septembre 2026**

## Objet

CRH-27 rend exploitable le journal append-only CRH-04/22 pour reconstituer l'historique descriptif d'une démarche RH. Le lot reste entièrement en lecture : il ne crée, ne modifie et ne supprime aucun événement.

## Projection applicative

`HrCaseHistoryService` lit uniquement les événements dont :

- la cible est `HrEventTargetKind.CASE` ;
- `target_ref` correspond au dossier demandé.

La projection expose :

- identifiant d'événement ;
- type d'événement ;
- horodatage avec fuseau ;
- acteur éventuel ;
- source éventuelle ;
- métadonnées d'audit non secrètes ;
- nombre total d'événements ;
- nombre de changements de statut ;
- horodatage du dernier événement.

Les événements sont présentés du plus récent au plus ancien.

## Runtime de production

`HrCaseHistoryRuntimeFactory` compose :

1. l'identité stable de la base active ;
2. `TeamworksHrCasesRepository` ;
3. `HrCaseHistoryService`.

La façade publique n'expose que `build(case_id=...)`. L'identité logique de structure et la persistance restent internes.

## Composant wxPython

`DLG_Demarches_rh_historique.py` fournit un dialogue de consultation prêt à être raccordé au cockpit. Il affiche :

- date et fuseau ;
- nature de l'événement ;
- acteur ;
- source ;
- détails des métadonnées d'audit.

Les valeurs `from_status` et `to_status` sont présentées avec les libellés métier connus, sans transformer ou réinterpréter l'événement enregistré.

Le raccord du bouton **Historique** au cockpit principal est volontairement conservé pour un sous-lot distinct afin de pouvoir qualifier séparément le nouveau composant avant de modifier à nouveau l'écran CRH-26.

## Garde-fous

Le lot interdit dans le composant UI :

- accès direct à `GestionDB` ou SQLite ;
- appel aux repositories ;
- ajout ou suppression d'événement ;
- transition de dossier ;
- modification du statut technique ;
- réseau, navigateur ou scraping.

Le service applicatif reste indépendant de wxPython et de la persistance de production.

## Limites

CRH-27 ne prétend pas que tous les actes historiques antérieurs à l'activation du journal sont présents. Il affiche uniquement les événements effectivement persistés. Il ne reconstitue pas artificiellement un historique absent et ne déduit aucune conformité juridique.
