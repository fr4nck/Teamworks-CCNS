# CRH-24 — cockpit wxPython des démarches RH

**Date : 1er septembre 2026**

## Objet

CRH-24 rend visible dans Teamworks la projection CRH-21, désormais composée sur la persistance de production par CRH-22/23.

L'écran **Démarches RH** reste volontairement en lecture seule. Il sert de cockpit structure pour repérer les dossiers ouverts, échéances dépassées, anomalies métier, échecs techniques d'échange et références à des organismes non configurés.

## Accès

Le point d'entrée est injecté dans la coque moderne `Teamworks.py`, sans modifier `Teamworks_core.py`.

L'ouverture reste explicite et n'est possible que lorsqu'un fichier Teamworks est actif. Le dialogue `DLG_Demarches_rh.py` est importé uniquement au clic afin qu'une indisponibilité du sous-système Connexions RH ne casse pas le démarrage historique.

## Projection affichée

Le cockpit présente :

- nombre de dossiers ouverts ;
- nombre de dossiers demandant une attention ;
- dossiers en retard ;
- anomalies et régularisations ;
- échecs techniques ;
- organismes à configurer ;
- liste triée des démarches avec sujet, organisme, échéance, statut métier, statut technique, nombre de pièces attendues et motifs d'attention.

Un double-clic ou **Voir le détail** ouvre une fiche descriptive contenant le résultat et le commentaire déjà projetés, sans opération d'écriture.

## Séparation métier / technique

L'interface conserve deux colonnes et deux indicateurs distincts pour :

- le statut administratif de la démarche ;
- l'état technique d'un éventuel échange.

Un échange réussi ne vaut donc jamais acceptation métier, conformément aux invariants CRH-03/21.

## Frontières

Le dialogue dépend uniquement de `HrCaseDashboardRuntimeFactory` et des objets de domaine nécessaires aux libellés. Il ne connaît ni `GestionDB`, ni les repositories, ni `structure_ref`.

Le lot ne contient :

- aucune création ou transition de dossier ;
- aucune écriture d'événement ;
- aucune suppression ;
- aucun secret ;
- aucun réseau, navigateur ou scraping ;
- aucune conclusion automatique de conformité ou de paie.

Les futures actions de workflow seront développées dans un sous-lot séparé afin de conserver une frontière claire entre consultation et mutation.
