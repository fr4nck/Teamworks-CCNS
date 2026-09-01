# CRH-26 — actions wxPython du cockpit Démarches RH

**Date : 1er septembre 2026**

## Objet

CRH-26 raccorde la frontière transactionnelle CRH-25 au cockpit wxPython CRH-24. Le cockpit devient actionnable pour les **transitions de statut métier uniquement**, sans exposer la persistance ni modifier l'état technique d'échange.

## Parcours utilisateur

À partir d'une démarche sélectionnée, le bouton **Faire évoluer** :

1. charge le runtime de workflow uniquement au premier clic ;
2. relit le dossier courant dans la base active ;
3. récupère les seules transitions autorisées par la machine d'états CRH-03 ;
4. propose le nouveau statut ainsi qu'un résultat/référence et un commentaire facultatifs ;
5. demande une confirmation explicite ;
6. applique la transition atomique CRH-25 ;
7. journalise automatiquement le changement de statut ;
8. recharge le cockpit et conserve la sélection du dossier.

Les dossiers `ACCEPTED` et `CANCELLED` n'exposent pas d'action, conformément à la machine d'états du domaine.

## Concurrence

Avant l'ouverture du dialogue d'action, CRH-26 compare le statut relu par le runtime avec celui affiché dans le cockpit. S'il a déjà changé, aucune action n'est proposée et la liste est actualisée.

Le contrôle transactionnel CRH-25 reste l'autorité finale : si le statut métier ou le statut technique a changé entre la lecture et l'enregistrement, la transaction est refusée. L'interface recharge alors le dossier et signale que la transition n'a pas été enregistrée.

## Séparation métier / technique

CRH-26 ne propose aucune commande de modification de `exchange_status`.

Le dialogue affiche l'état technique comme information **inchangée** et la confirmation rappelle que seule la progression administrative métier est modifiée. Les futurs échanges API, dépôts de fichiers ou synchronisations devront rester des lots distincts.

## Frontières d'architecture

`DLG_Demarches_rh.py` :

- continue d'utiliser `HrCaseDashboardRuntimeFactory` pour la lecture ;
- charge paresseusement `HrCaseWorkflowRuntimeFactory` uniquement lors d'une action ;
- ne connaît pas `GestionDB`, les repositories ni `structure_ref` ;
- n'appelle jamais `save_case`, `append_event`, `persist_case_transition`, `transition_to` ou `with_exchange_status` ;
- ne contient aucune table de transitions métier dupliquée.

Les transitions proposées viennent exclusivement de `available_transitions()`.

## Confirmation et audit

Une transition nécessite une confirmation `Oui / Non`, avec **Non** comme choix par défaut. La confirmation précise :

- le statut d'origine ;
- le statut cible ;
- la création d'une trace d'audit ;
- l'absence de modification de l'état technique d'échange.

L'événement d'audit est créé par le service CRH-25, pas par wxPython.

## Limites

CRH-26 n'ajoute pas :

- de création libre de démarche ;
- de suppression de dossier ;
- de changement manuel du statut technique ;
- de dépôt de fichier ;
- d'ouverture de navigateur ;
- d'appel réseau ;
- de conclusion automatique de conformité ;
- de calcul de paie ou de cotisation.

Le lot suivant pourra traiter la **création contrôlée de démarches** à partir de types et organismes configurés, séparément des transitions d'un dossier existant.
