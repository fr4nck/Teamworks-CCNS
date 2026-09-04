# CRH-32 — checklist wx des pièces de démarches RH

## Objet

CRH-32 raccorde la frontière de suivi administratif CRH-31 au cockpit wxPython « Démarches RH » sans déplacer la logique métier, l'identité de structure ou la persistance dans l'interface.

## Accès depuis le cockpit

Un bouton **Pièces** devient disponible lorsqu'une démarche sélectionnée possède au moins une pièce explicitement attendue. Le dialogue `DLG_Demarches_rh_pieces` est importé uniquement au clic : l'ouverture normale du cockpit ne charge ni le runtime CRH-31 ni son adaptateur de production.

Les démarches `ACCEPTED` et `CANCELLED` restent consultables mais leur checklist est ouverte en lecture seule. La protection applicative et transactionnelle de CRH-31 reste néanmoins autoritaire en cas de modification concurrente.

## Checklist

Le dialogue affiche pour chaque `ExpectedDocument` :

- libellé ;
- caractère obligatoire ou facultatif défini lors de la création de la démarche ;
- état administratif `Non reçue`, `Reçue` ou `Retirée` ;
- date de réception ;
- date de retrait éventuelle ;
- référence documentaire opaque facultative.

La synthèse indique le nombre de pièces attendues, reçues et obligatoires manquantes. Ce compteur est strictement administratif.

## Actions

Deux écritures explicites sont disponibles sur une démarche ouverte :

- **Marquer reçue** : demande une date de réception et, facultativement, une référence documentaire ;
- **Retirer l'état reçue** : conserve la projection et produit un état historisé, sans suppression.

Chaque opération demande confirmation avant d'appeler le runtime CRH-31. Après écriture, la checklist est relue depuis la base afin de refléter l'état réellement persisté.

## Sémantique volontairement limitée

« Reçue » signifie uniquement qu'une réception administrative a été enregistrée dans Teamworks. CRH-32 ne conclut jamais :

- à l'authenticité d'un document ;
- à sa validité ;
- à sa conformité juridique ;
- à la satisfaction automatique d'une obligation réglementaire.

Aucune règle n'ajoute ou ne rend obligatoire une pièce : la checklist ne fait que refléter les `ExpectedDocument` déjà définis par la démarche.

## Stockage et documents

CRH-32 n'est pas un gestionnaire de fichiers. Le dialogue ne propose aucun `FileDialog`, n'ouvre et ne copie aucun fichier, et n'enregistre aucun chemin local. La seule donnée documentaire facultative est un identifiant opaque transmis à CRH-31.

L'intégration future avec le catalogue documentaire RH devra fournir ses propres références stables plutôt que faire entrer des chemins locaux ou des contenus binaires dans le suivi des démarches.

## Audit et concurrence

Les opérations CRH-32 utilisent exclusivement `record_received` et `withdraw_received` du runtime CRH-31. La persistance de la projection et des événements `DOCUMENT_ADDED` / `DOCUMENT_REMOVED` reste transactionnelle ; l'historique CRH-27/28 affiche donc les changements réellement persistés.

En cas d'état devenu obsolète ou de clôture concurrente de la démarche, l'écriture est refusée par le service/repository puis la checklist tente de se recharger.

## Hors périmètre

Ce lot n'ajoute :

- aucun upload ou stockage binaire ;
- aucune signature ou vérification de document ;
- aucune déduction juridique ;
- aucune communication réseau ;
- aucune modification du statut technique d'échange ;
- aucune suppression physique de document ou d'événement d'audit.

CRH-32 reste un lot satellite de Connexions RH. Sa qualification automatisée ne remplace pas la recette manuelle Windows de la version applicative en cours de qualification.
