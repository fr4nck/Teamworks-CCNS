# CRH-20 — Actions wxPython de protection sociale salarié

## Statut

Lot empilé sur **CRH-19**. CRH-20 raccorde à l'onglet salarié les actions métier
déjà contrôlées et transactionnelles sans créer de nouvelle règle de paie ou de
conformité juridique.

La validation manuelle Windows de **0.9.1b** reste le verrou de qualification de
la release déjà construite. CRH-20 reste un développement satellite : s'il est
ultérieurement fusionné jusqu'à `master`, un nouveau build de pré-release devra
être reconstruit et requalifié.

## Objectif

L'onglet **Protection sociale** n'est plus seulement descriptif. Il expose trois
intentions explicites :

- **Ajouter** un suivi ;
- **Clôturer** la période active sélectionnée ;
- **Nouvelle période** pour remplacer atomiquement une période active par sa
  successeure.

Il n'existe toujours aucune édition libre ni suppression d'historique.

## Frontière de présentation

`CTRL_Page_protection_sociale.Panel` reste indépendant de la persistance. Il :

- rend la synthèse CRH-14 ;
- mémorise uniquement la correspondance entre ligne visible et `record_id` ;
- active `Clôturer` et `Nouvelle période` uniquement pour une ligne `ACTIVE` ;
- émet les trois intentions via des handlers surchargeables ;
- n'importe ni repository, ni `GestionDB`, ni transport externe.

Les boutons utilisent le composant Teamworks `CTRL_Bouton_image` et les métriques
du design system existant.

## Chargement différé

Le raccordement CRH-17B reste défensif :

1. l'ouverture de la fiche salarié ne charge pas le runtime Connexions RH ;
2. l'ouverture de l'onglet charge seulement la synthèse ;
3. `EmployeeProtectionActionsRuntimeFactory` et le dialogue d'action ne sont
   importés qu'au premier clic sur une action ;
4. une erreur d'écriture affiche un message local sans fermer ni rendre
   inutilisable la fiche salarié.

## Dialogue de création et succession

`DLG_Protection_sociale_action.Dialog` reçoit uniquement :

- les organismes configurés proposés par le runtime ;
- éventuellement la période courante pour préremplir une succession.

Le dialogue ne reçoit ni `structure_ref`, ni identifiant technique à fabriquer,
ni repository. Il construit un `EmployeeProtectionCreateRequest` puis laisse les
services CRH-18/19 appliquer les invariants métier.

Les familles proposées sont limitées à la mutuelle, la prévoyance, la retraite
complémentaire et le SPST. Les natures de lien proposées reflètent les invariants
du domaine :

- mutuelle : affiliation, dispense, enregistrement ;
- prévoyance / retraite complémentaire : affiliation, enregistrement ;
- SPST : enregistrement, suivi administratif.

Une succession est toujours créée `ACTIVE` et exige une date d'effet. Le dialogue
préremplit les métadonnées de la période sélectionnée, mais l'opération finale
reste la transaction CRH-19 : ancienne période terminée la veille, nouvelle
période insérée, rollback intégral en cas d'échec.

## Clôture

`ClotureDialog` ne permet de saisir que la date de fin. L'action applicative
refuse toujours :

- un suivi non actif ;
- un suivi appartenant à un autre salarié ;
- une date antérieure à la date d'effet ;
- l'allongement d'une date de fin déjà enregistrée.

## Organismes et détails

`EmployeeProtectionActionsRuntime` expose deux lectures UI-agnostiques
supplémentaires :

- `available_organizations()` : organismes configurés compatibles avec le suivi
  salarié ;
- `get_record()` : relecture du suivi sélectionné avec contrôle du salarié.

Ces lectures évitent que le code wxPython connaisse ou instancie directement le
repository de production.

## Garde-fous

CRH-20 n'ajoute :

- aucune table ou migration ;
- aucune suppression de ligne ;
- aucune édition libre de l'historique ;
- aucun mot de passe, token ou certificat ;
- aucune donnée médicale ;
- aucun appel réseau, navigateur ou API ;
- aucun calcul de cotisation, brut/net ou bulletin ;
- aucune conclusion automatique de conformité juridique.

Les tests couvrent le filtrage des organismes, la frontière salarié lors de la
relecture, le chargement différé du runtime d'écriture, l'absence de persistance
dans la vue/dialogue et l'absence d'action libre `edit/delete/remove/update`.
