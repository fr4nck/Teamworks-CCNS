# CRH-18 — Actions contrôlées de protection sociale salarié

## Statut

Lot empilé sur **CRH-17B**. Il prépare l'écriture depuis le futur onglet salarié sans encore ajouter de bouton ni de formulaire wxPython.

La validation manuelle Windows de **0.9.1b** reste le verrou de qualification de la release. Ce lot est un développement satellite : il reste isolé sur sa branche/PR et ne doit pas être confondu avec le build déjà qualifié. S'il est fusionné jusqu'à `master`, un futur build issu de ce nouveau `master` devra être reconstruit et requalifié.

## Objectif

Introduire une frontière d'écriture plus stricte que le repository générique afin que l'interface ne puisse pas modifier librement les données de protection sociale.

CRH-18 couvre deux actions :

- **enregistrer** un nouveau suivi salarié à partir d'un organisme déjà configuré ;
- **clôturer** un suivi actif en fixant sa date de fin.

Les natures déjà définies par CRH-11 restent disponibles : affiliation, dispense, enregistrement et suivi administratif, dans les familles d'organismes autorisées par le domaine.

## Contrat de création

`EmployeeProtectionCreateRequest` contient uniquement les données métier saisissables. La structure, le salarié et l'identifiant technique ne sont pas fournis par le formulaire.

`EmployeeProtectionActionService.register()` :

1. reçoit la structure et le salarié depuis le contexte applicatif ;
2. génère un identifiant opaque ;
3. refuse une collision d'identifiant au lieu d'écraser un enregistrement existant ;
4. construit un `EmployeeProtectionRecord` afin de réutiliser tous les invariants CRH-11 ;
5. passe par `EmployeeProtectionService`, qui exige que l'organisme soit configuré pour la même structure et que sa famille soit cohérente.

Aucune activation n'est déduite automatiquement : le statut et les dates sont explicitement fournis par le cas d'usage. Une dispense conserve notamment l'obligation d'un motif codifié.

## Contrat de clôture

`EmployeeProtectionActionService.end()` n'est pas une édition libre. Il :

- exige un suivi existant et appartenant au salarié demandé ;
- n'accepte qu'un suivi `ACTIVE` ;
- conserve l'identifiant, l'organisme, la nature du lien, le régime, l'option, le profil de cotisation, les références et la provenance ;
- passe le statut à `ENDED` ;
- conserve la date d'effet et fixe uniquement la date de fin ;
- refuse une date antérieure à la date d'effet ;
- refuse de prolonger une date de fin déjà enregistrée.

Il n'existe volontairement aucune opération publique `edit`, `update`, `delete` ou `remove` dans cette frontière.

## Historisation

CRH-18 évite l'écrasement métier par défaut. Une modification future de régime, option, profil de cotisation, organisme ou nature du lien devra être traitée comme une **nouvelle période** avec un nouvel identifiant, après clôture de la période précédente.

L'opération atomique « clôturer puis créer la période successeure » n'est pas introduite dans ce lot : elle devra disposer d'une frontière transactionnelle explicite avant d'être exposée à l'interface.

## Composition sur la base active

`EmployeeProtectionActionsRuntimeFactory` reprend la composition CRH-17A :

- identité opaque de la structure stockée dans la base Teamworks active ;
- `TeamworksHrConnectionsRepository` via `GestionDB` ;
- `EmployeeProtectionService` ;
- `EmployeeProtectionActionService`.

La façade runtime verrouille `structure_ref`. Le futur panneau ne fournira que `employee_ref` et la demande métier.

## Garde-fous

Ce lot n'ajoute :

- aucun SQL ni schéma supplémentaire ;
- aucune suppression de donnée ;
- aucun calcul de cotisation, brut/net ou conformité juridique ;
- aucune donnée médicale ;
- aucun secret, mot de passe, token ou certificat ;
- aucun appel réseau, navigateur ou API externe ;
- aucun raccordement de bouton wxPython.

Les tests couvrent les créations, collisions d'identifiants, organismes manquants, dispenses, clôtures, isolement salarié et composition réelle sur une base Teamworks SQLite simulant le contrat `GestionDB`.

## Suite proposée

Le prochain lot peut ajouter l'opération transactionnelle de **succession de période** puis seulement les dialogues wxPython de création/clôture. Cela maintient la règle : on ne remplace pas l'historique par une valeur courante mutable.
