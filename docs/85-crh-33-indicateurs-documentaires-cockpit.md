# CRH-33 — indicateurs documentaires du cockpit Démarches RH

## Objet

CRH-33 enrichit la projection du cockpit **Démarches RH** avec l'état administratif réel des pièces suivi depuis CRH-31/32, sans déplacer la logique documentaire dans wxPython.

## Projection

Pour chaque démarche, la projection distingue désormais :

- nombre de pièces attendues ;
- nombre de pièces explicitement obligatoires ;
- nombre de pièces actuellement marquées reçues ;
- nombre de pièces attendues sans réception active ;
- nombre de pièces obligatoires sans réception active ;
- éventuelle réception rattachée à un code qui n'est plus attendu par la démarche.

Une pièce retirée est donc à nouveau considérée comme non reçue. La propriété de complétude porte exclusivement sur la **réception administrative des pièces marquées obligatoires**.

Elle ne signifie jamais que les documents sont authentiques, valides, suffisants ou juridiquement conformes.

## Attention documentaire

Sur une démarche ouverte, une pièce explicitement obligatoire mais non reçue devient un motif d'attention documentaire distinct des axes déjà existants :

- attention métier ;
- échec technique d'échange ;
- organisme à configurer ;
- échéance dépassée.

Un dossier accepté ou annulé conserve ses compteurs documentaires dans l'historique, mais une pièce manquante n'y crée plus une action à traiter.

Une réception portant sur un code qui n'est plus déclaré comme pièce attendue est exposée séparément comme incohérence documentaire. Elle n'est pas comptée comme pièce reçue valide pour la checklist.

## Lecture groupée

`TeamworksHrCaseDashboardDocumentRepository` lit toutes les réceptions de la structure en une seule requête ordonnée par démarche et code de pièce.

Le cockpit évite ainsi une requête par dossier. L'adaptateur est strictement en lecture seule et réutilise le schéma additif CRH-31 ; il ne crée aucune nouvelle table métier et n'écrit aucun événement.

## Compatibilité

`HrCaseDashboardService` accepte encore l'absence de repository documentaire. Dans ce cas, la présence des pièces reste explicitement **inconnue** (`None`) au lieu d'être assimilée à zéro réception. Cette compatibilité évite d'inventer des pièces manquantes lorsqu'un appelant ne dispose pas encore du suivi CRH-31.

Le runtime de production Teamworks compose en revanche systématiquement la projection documentaire groupée.

## Garde-fous

CRH-33 n'ajoute :

- aucun fichier binaire ou chemin local ;
- aucune suppression physique ;
- aucun calcul de conformité juridique ;
- aucune décision d'authenticité ou de validité ;
- aucune transmission, API, navigateur ou scraping ;
- aucune modification du statut technique d'échange ;
- aucune requête SQL dans wxPython.

## Suite

Le raccord visuel de ces nouveaux compteurs à la colonne **Pièces** et aux motifs d'attention du cockpit peut rester un sous-lot UI très court : la projection de production est désormais disponible sans N+1 et sans modifier la frontière d'écriture CRH-31/32.
