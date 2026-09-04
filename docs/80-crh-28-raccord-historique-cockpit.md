# CRH-28 — raccord de l'historique au cockpit Démarches RH

**Date : 1er septembre 2026**

## Objet

CRH-28 raccorde au cockpit principal le composant d'historique qualifié en CRH-27, sans modifier sa frontière de lecture ni la frontière transactionnelle CRH-25/26.

## Parcours utilisateur

Lorsqu'une démarche est sélectionnée, le bouton **Historique** devient disponible, y compris pour un dossier accepté ou annulé. Un clic ouvre le journal du dossier sélectionné et transmet uniquement son `case_id` au composant CRH-27.

Le journal affiche exclusivement les événements réellement persistés. La fermeture du journal ramène au cockpit sans modifier la sélection, le dossier ou ses statuts.

## Chargement paresseux

`DLG_Demarches_rh_historique` n'est pas importé au chargement du cockpit. Le module est importé uniquement dans `OnHistory`, après une action explicite de l'utilisateur.

Cette règle évite d'introduire une nouvelle dépendance runtime dans l'ouverture du cockpit et maintient l'isolation déjà utilisée pour les autres extensions RH.

## Séparation des responsabilités

Le cockpit principal :

- choisit le dossier sélectionné ;
- ouvre le composant d'historique ;
- ne connaît ni `GestionDB`, ni repository, ni identité logique de structure ;
- ne construit aucun événement d'audit ;
- n'interprète pas le journal.

Le composant CRH-27 reste responsable de la projection et de l'affichage du journal.

## Garde-fous

Le raccord CRH-28 ne doit jamais :

- déclencher une transition ;
- écrire ou supprimer un événement ;
- modifier le statut technique ;
- transmettre autre chose que l'identifiant du dossier au dialogue d'historique ;
- importer le dialogue d'historique au niveau du module ;
- ajouter un accès réseau, navigateur ou scraping.

Le bouton **Faire évoluer** conserve ses règles CRH-26 et reste désactivé pour les dossiers clos ; le bouton **Historique**, lui, reste disponible dès qu'un dossier est sélectionné.
