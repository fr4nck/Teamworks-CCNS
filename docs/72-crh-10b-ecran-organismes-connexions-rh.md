# CRH-10B — écran « Organismes & connexions RH »

**Date : 1er septembre 2026**  
**Statut : développement satellite, à qualifier avant toute fusion dans `master`**

## Objet

CRH-10A avait isolé le service applicatif de configuration des organismes d'une structure. CRH-10B complète le périmètre fonctionnel initial de CRH-10 en fournissant le premier écran wxPython réellement exploitable depuis **Paramétrage → Organismes & connexions RH**.

Le lot est empilé après CRH-20 car il consomme la persistance de production CRH-16 et l'identité de structure CRH-17A déjà présentes dans cette pile. Cette position technique ne change pas le découpage fonctionnel : CRH-10B reste le sous-lot UI du rattachement à la structure.

## Fonctionnement

L'écran permet de créer et modifier les profils non secrets d'organismes de la base Teamworks active :

- code stable et libellé ;
- famille d'organisme ;
- période d'effet éventuelle ;
- références administratives non secrètes ;
- un ou plusieurs portails HTTP/HTTPS ;
- état descriptif du connecteur manuel de référence.

Le code stable et la famille deviennent non modifiables après création afin d'éviter de réinterpréter silencieusement les historiques salarié qui référencent déjà cet organisme. Le lot ne propose pas de suppression de profil.

Les références sont validées par le domaine CRH-01, qui refuse les types manifestement secrets. Les liens de portail restent de simples références : CRH-10B n'ouvre aucun navigateur et n'effectue aucun échange réseau.

## Frontière applicative

`StructureConnectionProfileRequest` porte seulement les données saisissables. Il ne contient ni `structure_ref`, ni capacité de connecteur librement activable.

`StructureHrConnectionsRuntimeFactory` compose :

1. l'identité stable de la structure active ;
2. `TeamworksHrConnectionsRepository` au-dessus de `GestionDB` ;
3. le registre des connecteurs manuels de référence CRH-08 ;
4. `StructureHrConnectionsService` de CRH-10A.

Lors d'une modification, les capacités déjà persistées sont conservées mais l'écran n'en invente aucune. Une capacité `API`, `SUBMISSION` ou `STATUS_SYNC` ne peut donc pas apparaître parce qu'un utilisateur a simplement coché une option dans l'interface.

## Raccordement à Teamworks

Le menu est injecté depuis la coque moderne `Teamworks.py` après construction du menu historique. Le gros `Teamworks_core.py` n'est pas modifié pour ce seul point d'entrée.

Le dialogue CRH-10B est importé uniquement au clic sur le menu. Sans fichier Teamworks ouvert, l'action est refusée avant toute composition du runtime Connexions RH.

Ce choix préserve le démarrage historique et garde la fonctionnalité isolable. La même technique de composition est déjà employée par la coque moderne pour remplacer le `Toolbook` sans monkey-patcher wxPython.

## Garde-fous

- schéma existant CRH-16 réutilisé, aucune migration nouvelle ;
- aucune suppression de profil ;
- aucune modification du code ou de la famille d'un organisme existant ;
- aucun secret, mot de passe, jeton ou certificat ;
- aucune donnée médicale ;
- aucun réseau, navigateur ou scraping ;
- aucune activation déclarative d'API ou de dépôt ;
- aucun calcul de cotisation ou de paie ;
- aucune modification de `Teamworks_core.py`.

## Tests attendus

Les tests couvrent :

- enregistrement d'un profil via le runtime sur une base exposant le contrat `GestionDB` ;
- masquage de l'identité de structure dans la demande UI ;
- round-trip des références et portails ;
- état non configuré lorsqu'aucun portail n'existe ;
- conservation de capacités préexistantes lors d'une édition ;
- refus du changement de famille ;
- absence d'opération de suppression de profil ;
- import différé du dialogue depuis le menu ;
- absence de dépendance SQL/réseau/secrets dans le dialogue ;
- absence de wxPython dans la factory applicative.

## Qualification

Une CI verte de cette PR ne remplace pas la validation manuelle Windows de la 0.9.1b. Si la pile Connexions RH est fusionnée dans `master`, un nouveau build devra être reconstruit et requalifié sur Windows et sur copie de base réelle.
