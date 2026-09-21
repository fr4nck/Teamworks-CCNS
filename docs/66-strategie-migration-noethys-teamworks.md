# Stratégie de migration Noethys / Teamworks

## Objectif

Permettre à Teamworks de devenir autonome sans conversion destructive de la base historique.

Règle centrale : **aucune donnée source attendue ne peut disparaître silencieusement**.

## Règles non négociables

1. Aucune conversion en place : on migre depuis un snapshot/copie immuable.
2. L'import doit être reproductible et relançable depuis zéro.
3. Chaque ligne source doit avoir une issue explicite.
4. Les quatre issues autorisées sont MIGRATED, TRANSFORMED, IGNORED et REJECTED.
5. TRANSFORMED, IGNORED et REJECTED exigent un code de raison.
6. REJECTED bloque la bascule tant qu'une décision humaine formalisée ne l'a pas traité.
7. Les comptages de lignes ne suffisent pas : relations, montants et documents critiques sont réconciliés.
8. Les identifiants historiques restent traçables par source_system + source_table + source_id.
9. Après bascule, le schéma historique n'est plus une dépendance runtime.
10. L'ancienne base reste archivée et inchangée pendant la période de stabilisation.

## États d'une ligne source

- MIGRATED : transférée sans changement métier significatif.
- TRANSFORMED : transférée avec restructuration documentée, par exemple 0 vers NULL ou liste d'IDs vers table de relation.
- IGNORED : volontairement non portée, uniquement avec justification stable, par exemple un cache recalculable.
- REJECTED : aurait dû être migrée mais ne peut pas l'être de façon sûre.

## Provenance

Chaque objet issu d'un import conserve :
- le système source ;
- la table source ;
- l'identifiant source ;
- l'identifiant du run de migration.

Le nouveau moteur peut utiliser ses propres clés internes. Il ne doit pas perdre le lien vers l'ancien enregistrement.

## Pipeline

### A. Gel de la source
- snapshot ou copie ;
- horodatage ;
- moteur/version ;
- empreinte de l'archive ;
- comptage brut des lignes par table.

### B. Inventaire automatique
Pour chaque table : colonnes, types observés, NULL, chaînes vides, zéros pseudo-NULL, doublons, orphelins, plages de dates/nombres, blobs et valeurs atypiques.

### C. Cartographie
Chaque table/champ est classé : canonique, transformé, cache/recalculable, obsolète ou à expertiser. La cartographie décrit source, destination, transformation, règle de NULL, collision et contrôle de réconciliation.

### D. Import staging
Les données sont lues dans une zone de staging ou par un importeur dédié avant écriture canonique.

### E. Import canonique
L'import doit être idempotent : relancer le même snapshot ne crée pas de doublons. La provenance empêche les créations multiples.

### F. Réconciliation

Niveau structure : attendu = migré + transformé + ignoré + rejeté, et inexpliqué = 0.

Niveau relations : personnes/coordonnées, personnes/contrats, déplacements/remboursements, familles/individus, activités/inscriptions, factures/lignes, règlements/ventilations, documents/objets.

Niveau métier : sommes financières, soldes, nombres de présences, contrats, dates extrêmes, volumes par saison/exercice et empreintes documentaires.

Par défaut, la tolérance monétaire est de 0 centime.

## Journal de migration

Chaque ligne traitée enregistre au minimum : run_id, source_system, source_table, source_id, statut, type destination, id destination éventuel, reason_code, message et horodatage.

## Critères de validation

Un run n'est VALIDATED que si :
- aucune ligne source attendue n'est inexpliquée ;
- aucun rejet bloquant ne subsiste ;
- aucune identité source n'est traitée deux fois ;
- toutes les métriques bloquantes concordent ;
- les relations obligatoires concordent ;
- les valeurs financières critiques concordent ;
- les documents critiques attendus sont présents.

Sinon le run est FAILED ou REVIEW_REQUIRED.

## Bascule

1. recette sur copie ancienne ;
2. second import depuis zéro pour vérifier la répétabilité ;
3. recette sur copie récente ;
4. arrêt temporaire des écritures historiques ;
5. snapshot final ;
6. import final ;
7. réconciliation complète ;
8. bascule uniquement si le run est validé ;
9. ancienne base conservée en archive/lecture seule.

Aucune correction SQL manuelle non rejouable ne fait partie d'une migration valide.

## Ordre proposé

Référentiels -> personnes -> coordonnées/familles -> contrats/RH -> activités/saisons -> inscriptions/présences -> frais -> facturation -> règlements -> documents/blobs -> caches -> audit global.

## Premier pilote

Frais/remboursements est le pilote conseillé : il couvre IDs historiques, montants, relations, NULL/0, transactions multi-tables et invariants de concurrence déjà testés.

## Définition de zéro petit perdu

Pour chaque ligne source, le rapport doit répondre : qu'est-elle devenue, vers quel objet, avec quelle transformation ou quelle justification ?

Une migration n'est validée que si le nombre de lignes source non expliquées est exactement zéro.

## Hors décision

Cette stratégie ne fige pas encore le moteur cible, le format final des clés primaires ni l'outil SQL de migration. Ces choix peuvent évoluer sans remettre en cause les garanties ci-dessus.