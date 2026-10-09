# DPAE — contrat de tests de concurrence

Ce document transforme les invariants de corrélation DPAE en scénarios de recette automatisable. Il complète le contrat PMSL-Arch sans supposer encore un ORM ou un moteur SQL particulier dans Teamworks.

## Invariants bloquants

- `DPAE-C1` : au plus un `DpaeReturn` logique pour un même retour externe/replay exact.
- `DPAE-C2` : au plus une corrélation courante par `DpaeReturn`.
- `DPAE-C3` : au plus un effet de chaque type par `DpaeReturn`.
- `DPAE-C4` : aucun effet métier depuis un retour dont la corrélation n'est pas `CONFIRMED`.
- `DPAE-C5` : une course se termine par succès, succès idempotent ou conflit explicite ; jamais par écrasement silencieux.
- `DPAE-C6` : l'historique de corrélation reste append-only.
- `DPAE-C7` : un BIS ne crée jamais automatiquement une nouvelle DPAE.
- `DPAE-C8` : un replay après commit ne reproduit aucun effet métier.

`C2`, `C4` et `C8` sont bloquants pour la première mise en production.

## Synchronisation des tests

Les tests de course utilisent deux connexions/transactions réellement indépendantes et des barrières déterministes. Ne pas utiliser deux appels partageant la même session ORM.

Hooks de test recommandés :

- `AFTER_RETURN_READ`
- `AFTER_CANDIDATE_RESOLUTION`
- `BEFORE_CORRELATION_COMMIT`
- `AFTER_BUSINESS_COMMIT`
- `BEFORE_MESSAGE_ACK`

Le harness doit pouvoir suspendre les deux acteurs au même hook puis les libérer ensemble.

## CONC-01 — deux workers, même retour, même candidat

Précondition : `R42=UNMATCHED`, `version=7`; `S12` est le candidat fort unique.

Les deux workers lisent la version 7 puis tentent `R42 -> S12` simultanément.

Attendu : une mutation gagne. Le second recharge le retour et constate que l'état demandé existe déjà : résultat `ALREADY_CORRELATED`, pas erreur métier. Une seule corrélation courante et aucun effet dupliqué.

## CONC-02 — deux workers, candidats différents

Précondition : `R42=UNMATCHED`, `version=7`. Le harness force A à proposer `S12` et B `S19`.

Attendu : un seul compare-and-swap/version check gagne. Le perdant reçoit `CONCURRENT_CORRELATION_CONFLICT`; il lui est interdit de relire puis d'écraser le gagnant. La base doit garantir `count(current correlation for R42) <= 1`.

## CONC-03 — worker automatique contre opérateur

Le worker trouve une clé forte pendant qu'un opérateur confirme un candidat depuis la file de revue.

Attendu : une seule décision courante. Si les deux visent le même candidat, le perdant obtient un succès idempotent. S'ils visent des candidats différents, conflit explicite et rechargement obligatoire.

## CONC-04 — deux opérateurs, même candidat

Alice et Bob ouvrent `R42 version=7` et choisissent tous deux `S12`.

Attendu : une seule décision effective. Le second compare sa version attendue, recharge et reçoit `ALREADY_CONFIRMED`. Aucun doublon d'audit métier.

## CONC-05 — deux opérateurs, candidats différents

Alice choisit `S12`, Bob `S19` depuis la même version.

Attendu : le premier commit gagne ; le second reçoit `DPAE_CORRELATION_STALE` / `CONCURRENT_CORRELATION_CONFLICT`. Aucun bouton/chemin de force overwrite. Une correction ultérieure passe par `INVALIDATE_MATCH` puis une nouvelle `CONFIRM_MATCH` append-only.

## CONC-06 — invalidation contre confirmation

Un opérateur invalide une corrélation pendant qu'un autre confirme depuis une vue obsolète.

Attendu : optimistic locking. La commande fondée sur une version périmée est refusée ; aucune décision historique n'est réécrite.

## REPLAY-01 — réception simultanée du même retour

Deux workers ingèrent le même retour brut et calculent la même identité de déduplication.

Attendu : une seule ligne logique `DpaeReturn`. Le perdant de l'INSERT récupère l'objet existant. Aucun doublon de document brut, corrélation, alerte ou effet.

## REPLAY-02 — replay après corrélation et traitement

`R42` est déjà `CONFIRMED` et résolu. Le même retour est reçu à nouveau.

Attendu : replay technique détecté, aucune nouvelle décision, transition Case/Submission, notification ou action métier.

## REPLAY-03 — crash après commit avant ACK

Injecter un crash après le commit contenant corrélation + clé d'effet + transition métier, mais avant l'acquittement du message. Rejouer ensuite le message.

Attendu : le retour, la corrélation et l'effet existent déjà ; le worker n'effectue aucune nouvelle mutation métier puis acquitte le message. C'est le test principal de `DPAE-C8`.

## REPLAY-04 — même identifiant externe, contenu différent

Un retour existant possède `external_return_id=EXT42`, `raw_hash=AAA`; un nouveau message annonce `EXT42`, `raw_hash=BBB`.

Attendu : `RETURN_INTEGRITY_CONFLICT`. Ne jamais traiter ce cas comme replay et ne jamais remplacer silencieusement le contenu précédent.

## EFFECT-01 — retour 41 traité par deux workers

Les deux workers tentent l'effet `MARK_DPAE_REGISTERED` pour le même retour 41.

Attendu : une clé unique logique `(return_id, effect_type)` autorise exactement un effet. Le Case termine dans l'état attendu, sans double transition ni double notification.

## EFFECT-02 — BIS traité par deux workers

Les deux workers traitent le même BIS confirmé.

Attendu : une seule action `RESOLVE_IDENTITY_DIVERGENCE` ouverte. Aucun worker ne crée de nouvelle `DpaeSubmission` du seul fait du BIS.

## Contraintes de persistance attendues

Le futur adaptateur SQL doit fournir l'équivalent de :

```sql
UNIQUE current correlation per return
UNIQUE (return_id, effect_type)
UNIQUE external return identity when available
optimistic version on DpaeReturn/correlation projection
```

La syntaxe exacte dépendra du moteur réellement retenu. Les tests métier ne doivent pas dépendre d'un index partiel PostgreSQL si Teamworks doit encore supporter un autre moteur.

## Assertions communes

Après chaque scénario, vérifier systématiquement :

```text
logical_return_count <= 1
current_correlation_count <= 1
effect_count(return_id, effect_type) <= 1
unconfirmed_return_business_effect_count == 0
history_is_append_only == true
```

Puis les assertions spécifiques BIS/41.

## Exigence sur le moteur de test

Les tests unitaires purs peuvent tester la machine d'état, mais les courses de transactions doivent également être exécutées sur le moteur SQL réellement ciblé par l'implémentation. SQLite en mémoire ne constitue pas une preuve suffisante du comportement des verrous, de l'isolation ou des contraintes concurrentes.
