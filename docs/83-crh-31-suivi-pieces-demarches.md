# CRH-31 — suivi administratif des pièces des démarches RH

## Objet

CRH-31 complète la création CRH-29/30 par un suivi explicite des **pièces attendues déjà déclarées dans une démarche RH**.

Le lot répond à une distinction importante : une démarche peut déclarer qu'une pièce est attendue sans que Teamworks prétende qu'elle a réellement été reçue. CRH-31 introduit donc une projection administrative séparée pour enregistrer la réception puis, si nécessaire, le retrait d'une pièce du suivi.

## Portée sémantique

L'état **reçue** signifie uniquement qu'un utilisateur ou un futur flux a enregistré une réception dans Teamworks.

Il ne signifie pas :

- que le document est authentique ;
- qu'il est juridiquement valable ;
- qu'il satisfait l'organisme destinataire ;
- qu'il suffit à rendre la démarche conforme ;
- qu'il a été transmis à l'extérieur.

Le retrait signifie qu'une réception précédemment enregistrée n'est plus considérée comme présente dans le suivi courant. La ligne n'est pas supprimée : son état devient `WITHDRAWN` et le journal conserve les événements antérieurs.

## Domaine

`HrCaseDocumentReceipt` porte uniquement :

- `case_id` ;
- `document_code` ;
- état `RECEIVED` ou `WITHDRAWN` ;
- date de réception ;
- date de retrait lorsqu'il existe ;
- `artifact_ref` facultatif et opaque ;
- source facultative.

Aucun contenu binaire, chemin local ou fichier n'est stocké dans ce modèle.

`HrCaseDocumentChecklist` rapproche les pièces explicitement attendues du dossier avec leur projection de réception. Il fournit des compteurs descriptifs : attendues, obligatoires, reçues et obligatoires manquantes. `complete_administratively` signifie uniquement que toutes les pièces marquées `required=True` dans le dossier ont un état courant `RECEIVED`.

## Cas d'usage

`HrCaseDocumentTrackingService` expose :

- `build_checklist()` en lecture ;
- `record_received()` pour enregistrer une réception ;
- `withdraw_received()` pour retirer administrativement une réception.

Le service refuse :

- une pièce absente de `expected_documents` ;
- une seconde réception alors que la pièce est déjà reçue ;
- le retrait d'une pièce qui n'est pas actuellement reçue ;
- toute modification de pièces sur une démarche `ACCEPTED` ou `CANCELLED`.

Les démarches closes restent lisibles.

## Persistance

`TeamworksHrCaseDocumentRepository` utilise une table additive dédiée :

`tw_hr_case_document_receipts`

La clé logique est `(structure_ref, case_id, document_code)`. Le composant dispose de sa propre version de schéma `hr_case_documents_runtime = 1` dans `tw_hr_schema_versions`.

Le repository :

- conserve la compatibilité SQLite/MySQL via les helpers de paramètres existants ;
- ne modifie aucune table historique Teamworks ;
- ne crée aucune clé étrangère vers salariés ou contrats ;
- ne supprime pas la projection lors d'un retrait ;
- vérifie dans la transaction que le dossier existe, qu'il n'est pas clos et que le code appartient encore aux pièces attendues ;
- applique un contrôle optimiste sur l'état courant de la pièce.

## Audit

Chaque réception crée un événement `DOCUMENT_ADDED` et chaque retrait un événement `DOCUMENT_REMOVED`.

Ces événements ciblent volontairement la **démarche** (`HrEventTargetKind.CASE`) et portent `document_code` dans leurs métadonnées. Ils deviennent donc immédiatement visibles dans l'historique CRH-27/28, qui sait déjà présenter ces deux types d'événements.

La projection et l'événement sont persistés dans la même transaction. Une collision, une modification concurrente, une fermeture du dossier ou une pièce devenue inconnue entraîne un rollback complet.

La référence documentaire opaque n'est pas recopiée dans le journal d'audit afin de limiter la duplication de métadonnées potentiellement sensibles.

## Runtime

`HrCaseDocumentTrackingRuntimeFactory` compose :

- l'identité stable de la structure active ;
- le repository de production CRH-31 ;
- le service applicatif.

L'appelant manipule uniquement `case_id`, `document_code`, dates et éventuelle `artifact_ref`. Il ne connaît ni `structure_ref`, ni `GestionDB`, ni la persistance.

## Interface

CRH-31 ne modifie volontairement pas encore le cockpit wxPython. Il fournit le moteur, la persistance et le runtime nécessaires à un lot d'interface séparé afin de conserver un périmètre qualifiable et réversible.

Le futur raccord pourra afficher une checklist par démarche et proposer **Marquer reçue** / **Retirer du suivi**, sans téléchargement, validation juridique ou transmission externe implicite.

## Tests

- `tests/test_hr_case_documents.py` : invariants domaine, checklist, réception/retrait, dossiers clos et événements ;
- `tests/test_teamworks_hr_case_document_repository.py` : schéma, idempotence, transaction, rollback, concurrence, dossiers clos et intégration au journal ;
- `tests/test_hr_case_document_tracking_runtime_factory.py` : composition sur une base Teamworks simulée et visibilité dans l'historique ;
- `tests/test_hr_case_document_tracking_policy.py` : frontières architecturales, absence de binaire, de suppression et de transport.

Aucune fusion automatique n'est autorisée.
