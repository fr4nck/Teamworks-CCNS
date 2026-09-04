# CRH-29 — création contrôlée des démarches RH

## Objectif

Permettre l'ouverture d'une nouvelle démarche RH depuis Teamworks sans introduire de catalogue juridique automatique, de transport externe implicite ou d'écriture partielle.

CRH-29 fournit la **frontière applicative et transactionnelle**. Le dialogue wxPython de création restera un sous-lot séparé.

## Principes

- le type de démarche, son libellé, le sujet, l'organisme, les dates et les pièces attendues sont fournis explicitement par le cas d'usage appelant ;
- aucun type DPAE/DSN/France Travail/etc. n'est imposé ou déduit par le service ;
- l'organisme doit déjà exister dans **Organismes & connexions RH** ;
- une nouvelle démarche démarre toujours avec le statut métier `TODO` et le statut technique `NOT_APPLICABLE`, via `HrCase.create()` ;
- la création du dossier et l'événement `CASE_CREATED` sont persistés dans une seule transaction ;
- l'événement d'audit conserve uniquement des métadonnées administratives non secrètes : type de démarche, nature du sujet et code organisme ;
- aucune transmission externe, ouverture de navigateur ou modification d'un statut technique n'est effectuée.

## Service applicatif

`HrCaseCreationService` reçoit un `HrCaseCreationRequest` et vérifie :

1. la validité des données explicites ;
2. l'existence du profil d'organisme dans la structure active ;
3. l'unicité de l'identifiant généré ;
4. la présence d'un horodatage avec fuseau ;
5. la création de l'événement `CASE_CREATED` ;
6. la persistance atomique dossier + pièces attendues + audit.

Le service reste indépendant de wxPython, `GestionDB`, SQLite/MySQL et des transports externes.

## Persistance de production

`TeamworksHrCaseCreationRepository` réutilise le schéma CRH-22 et n'ajoute aucune table ni version de schéma.

Il refuse :

- un identifiant de dossier déjà présent ;
- un identifiant d'événement déjà présent ;
- un dossier créé dans un statut autre que `TODO` ;
- un événement autre que `CASE_CREATED` ;
- un événement ne ciblant pas le dossier créé.

Toute erreur provoque un rollback intégral.

## Runtime

`HrCaseCreationRuntimeFactory` compose :

- l'identité stable de structure CRH-17A ;
- `TeamworksHrCaseCreationRepository` ;
- `TeamworksHrConnectionsRepository` pour vérifier l'organisme ;
- `HrCaseCreationService`.

L'appelant ne reçoit ni `structure_ref`, ni repository, ni objet `GestionDB`.

## Hors périmètre

CRH-29 n'ajoute pas encore :

- le bouton **Nouvelle démarche** du cockpit ;
- un sélecteur de salarié ;
- un catalogue réglementaire de démarches ;
- des règles automatiques d'échéance ou de pièces ;
- une transmission API/fichier/portail ;
- une décision de conformité juridique.

Ces comportements doivent rester des lots distincts et qualifiés séparément.
