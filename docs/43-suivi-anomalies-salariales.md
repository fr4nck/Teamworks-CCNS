# TW-057 — Suivi des anomalies salariales

Le suivi des anomalies salariales compare deux snapshots historisés de contrôle salarial CCNS afin d'identifier les anomalies nouvelles, persistantes et résolues dans le temps.

## Fonctionnement

Le suivi s'appuie exclusivement sur les lignes conservées dans les snapshots TW-055. Le service `TrackContractSalaryControlIssuesService` reçoit un snapshot précédent et un snapshot courant, extrait les anomalies historisées, puis produit un historique immuable.

Aucun contrôle salarial n'est recalculé : les montants, statuts, motifs et codes d'anomalie sont ceux déjà figés dans les snapshots.

## Identification stable

Une anomalie est identifiée par :

- `contract_id` ;
- `issue_code` ;
- `failure_reason` lorsque le motif de non-évaluation fait partie de l'identité métier.

Les libellés affichés (`issue_message`, `failure_message`) ne sont jamais utilisés comme identifiants métier. Ils servent uniquement à expliquer les changements de motif à l'utilisateur.

## Statuts

- `NEW` : anomalie présente dans le snapshot courant mais absente du précédent ;
- `ONGOING` : anomalie présente dans les deux snapshots ;
- `RESOLVED` : anomalie présente dans le snapshot précédent mais absente du courant ;
- `UNKNOWN` : statut réservé aux cas impossibles à classifier dans une évolution future.

## Évolutions suivies

Le détail indique notamment :

- anomalie nouvelle ;
- anomalie toujours présente ;
- anomalie corrigée ;
- anomalie remplacée par une autre anomalie du même contrat ;
- changement de gravité, matérialisé par l'évolution de l'écart salarial historisé ;
- changement de motif ;
- changement de statut salarial.

## Interface

Depuis l'historique des contrôles salariaux, l'action **Suivi des anomalies** compare deux snapshots sélectionnés. L'écran reste en lecture seule et expose :

- un résumé des nouvelles anomalies, anomalies résolues et anomalies persistantes ;
- une liste détaillée par contrat et salarié ;
- les dates des deux snapshots ;
- des filtres pour afficher toutes les anomalies, les nouvelles, les persistantes ou les résolues.

## Limites

Le suivi décrit une évolution entre deux contrôles uniquement. Il ne crée pas de workflow de traitement manuel, ne modifie pas les snapshots et ne corrige aucune donnée métier.

## Différence avec les alertes TW-058

TW-057 ne déclenche aucune alerte automatique, notification, seuil de délai ni règle de priorisation. Ces mécanismes relèvent de TW-058. Le suivi fournit seulement une lecture déterministe de l'évolution des anomalies déjà historisées.
