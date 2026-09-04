# CRH-36 — gestion contrôlée des modèles de cycle de vie RH

## Objet

CRH-36 ajoute la frontière applicative de gestion des modèles locaux préparés en CRH-34 et persistés en CRH-35. Le but est de rendre cette configuration administrable sans introduire de catalogue réglementaire implicite.

## Principes

Un modèle reste une décision explicite de la structure. Il associe :

- un fait générique de cycle de vie (`employment_start`, `employment_end`, `contract_changed`) ;
- un organisme déjà configuré dans « Organismes & connexions RH » ;
- un code et un libellé internes de démarche ;
- un décalage d’échéance facultatif ;
- une liste facultative de pièces attendues, avec caractère obligatoire/facultatif explicitement saisi ;
- un état actif/inactif.

CRH-36 n’ajoute aucune DPAE, DSN, démarche France Travail, échéance légale ou pièce obligatoire par défaut.

## Service applicatif

`HrLifecycleTemplateManagementService` fournit trois opérations :

1. lister tous les modèles de la structure ;
2. enregistrer une configuration explicite après contrôle de l’existence de l’organisme ;
3. désactiver un modèle existant.

Aucune API de suppression n’est exposée. La désactivation reconstruit le modèle avec `enabled=False` et conserve son identifiant, son événement, son organisme, son type de démarche, son décalage et ses pièces.

## Lecture groupée

`TeamworksHrLifecycleTemplateRepository.list_all_templates()` lit tous les modèles de la structure puis toutes leurs pièces en groupe. Le futur écran de paramétrage n’aura donc pas à effectuer une requête documentaire par modèle.

## Runtime

`HrLifecycleTemplateManagementRuntimeFactory` compose :

- l’identité stable de la structure ;
- la persistance CRH-35 ;
- les profils d’organismes CRH-16 ;
- le service de gestion CRH-36.

La façade publique expose les modèles, les organismes configurés, l’enregistrement et la désactivation sans exposer `structure_ref`, `GestionDB` ou les repositories.

## Hors périmètre

CRH-36 ne réalise toujours pas :

- la détection d’un fait depuis un contrat Teamworks ;
- la création automatique d’une démarche RH ;
- la transmission vers un organisme ;
- une décision de conformité ;
- le stockage de secret ou de donnée médicale ;
- une interface wxPython.

Le raccordement wxPython du paramétrage restera un sous-lot distinct afin de conserver une frontière testable entre UI et persistance.
