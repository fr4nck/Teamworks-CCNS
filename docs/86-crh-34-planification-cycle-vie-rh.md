# CRH-34 — planification explicite du cycle de vie RH

## Objet

CRH-34 prépare les futurs déclencheurs liés au cycle de vie salarié sans transformer Teamworks en moteur réglementaire implicite.

Le lot distingue deux notions :

- un **événement de cycle de vie** décrit un fait de gestion connu de Teamworks ;
- un **modèle de cycle de vie** est une règle locale explicitement configurée qui peut faire naître une suggestion de démarche.

Aucune démarche n'est créée par CRH-34.

## Événements génériques

Le domaine introduit trois faits volontairement génériques :

- début d'emploi ;
- fin d'emploi ;
- modification de contrat.

Ils portent uniquement un identifiant d'événement, une référence salarié, une date d'effet et une éventuelle référence source opaque.

Le lot n'introduit pas d'événement médical ou d'absence afin de ne pas faire transiter des données sensibles dans cette nouvelle frontière.

## Modèles explicitement configurés

Un `HrLifecycleTemplate` peut décrire :

- le type d'événement auquel il répond ;
- un organisme ;
- un type de démarche interne ;
- un décalage de date facultatif ;
- des pièces attendues facultatives ;
- son état actif/inactif.

Il n'existe **aucun catalogue fourni par défaut**. Le code ne décide donc pas qu'un début d'emploi implique telle déclaration, tel organisme, tel délai ou telle pièce.

Le décalage d'échéance n'est utilisé que s'il est renseigné explicitement dans le modèle. Sans décalage, la suggestion ne possède pas d'échéance.

## Service de planification

`HrLifecyclePlanningService` lit les modèles configurés pour la structure et produit un `HrLifecyclePlan` contenant des suggestions descriptives.

Chaque suggestion possède une clé SHA-256 déterministe construite à partir de la structure, de l'événement et du modèle. Cette clé prépare une future déduplication sans créer de dossier ni écrire dans la base.

Les organismes sont lus en groupe depuis les profils existants. Un organisme absent n'est ni créé ni remplacé : la suggestion est simplement signalée comme rattachée à un organisme non configuré.

## Séparation avec les démarches RH

CRH-34 n'appelle pas `HrCaseCreationService` et n'écrit aucun `HrCase`.

Cette séparation est volontaire : un futur lot pourra proposer à l'utilisateur les suggestions issues d'un événement, puis matérialiser seulement celles qu'il confirme explicitement via la frontière de création contrôlée déjà qualifiée.

Ainsi :

**fait RH → suggestion locale → confirmation humaine → création contrôlée**

reste distinct de :

**fait RH → démarche automatique**, qui n'est pas introduit.

## Garde-fous

CRH-34 n'ajoute :

- aucune DPAE, DSN ou démarche France Travail automatique ;
- aucune échéance réglementaire codée en dur ;
- aucune pièce obligatoire implicite ;
- aucune donnée médicale ;
- aucune persistance ou migration ;
- aucune modification du statut technique d'échange ;
- aucun réseau, navigateur, API ou scraping ;
- aucun code wxPython.

## Suite

Après qualification de cette frontière, les lots suivants pourront traiter séparément :

1. la persistance additive des modèles locaux et leur configuration par la structure ;
2. la détection contrôlée d'un événement depuis les données Teamworks ;
3. la présentation des suggestions à l'utilisateur ;
4. la matérialisation explicite d'une suggestion en démarche RH via CRH-29.

Chaque étape restera auditable et pourra être qualifiée sans activer prématurément une automatisation réglementaire.
