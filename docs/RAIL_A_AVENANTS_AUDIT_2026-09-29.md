# Rail A — audit avenants CDI/CDD — 2026-09-29

## Verdict

La gestion des avenants ne doit pas créer un second modèle de contrats.

Le Rail A possède déjà :

- une frontière transactionnelle Contrats ;
- un éditeur du contrat courant par `IDcontrat` stable ;
- les opérations `NEW`, `CDD_RENEWAL`, `CDD_TO_CDI` ;
- `previous_contract_id` pour la chaîne CDD ;
- les règles de période d'essai ;
- la classification historique ;
- un raccord UI avancé derrière `advanced_contracts_enabled=False`.

Il manquait une trace append-only avant/après et une date d'effet propre aux
modifications de clauses qui restent sur le même contrat.

## PR et HEAD vérifiés

| PR | Branche | HEAD vérifié | État au 2026-09-29 | Rôle |
|---|---|---|---|---|
| #431 | `qt/convergence-0.9.2-rc3` | `d40c786698738288a2aa9ae1f2f7bdeff685d062` | fermée, non mergée | socle transactionnel Contrats repris par le Rail A |
| #448 | `qt/contracts-cee-create` | `3ceaad829ff70b0fe12c304d4121b706c8f2cdeb` | ouverte, draft | stop-gate Windows/MySQL + CEE |
| #455 | `qt/contracts-renewal-prep` | `bc58c7618a2cc90eae5285cf4691b83fc053dd0c` | ouverte, draft | `CDD_RENEWAL`, `CDD_TO_CDI`, lien précédent |
| #457 | `qt/contracts-classification-prep` | `7f64cb099f01a1c79115d8fd358a07c3875fbb93` | ouverte, draft | classification / valeur de point |
| #460 | `qt/contracts-probation-prep` | `72b663e3eba099c893fc4d604f582f82016e0ab5` | ouverte, draft | période d'essai complète |
| #462 | `qt/contracts-ui-prep` | `ec243bb027b9d6fa3425d968c7260f1fab7fae2a` | ouverte, draft | dialogues et câblage interne avancé |
| #464 | `qt/contracts-ui-gate` | `e4ea900c640217a24fa1a60259e3c2d2bf0ffea1` | ouverte, draft | feature gate UI, caché par défaut |

Le run GitHub Actions **Validation Qt #1656** du HEAD #464 est `SUCCESS`.

## Absorption par master

`master` était au SHA `1673248ce646706313d4ed3a3f19024b32be49e7`
lors de l'audit.

La comparaison GitHub `master...qt/contracts-ui-gate` donne :

- état : `diverged` ;
- Rail A : 325 commits en avance ;
- Rail A : 17 commits en retard ;
- merge-base : `860204ddbf297b4308dac7bef5e5f2b0e6e2bf2a`.

Les fichiers cœur `application/services/contract_write.py`,
`infrastructure/persistence/contract_write_adapter.py` et les widgets/tests Qt
du Rail A apparaissent encore comme ajouts par rapport à `master`.

Les recherches sur `master` de `CDD_RENEWAL`, `previous_contract_id`,
`operation_type` et `advanced_contracts_enabled` ne retrouvent pas le Rail A.

Conclusion : **le Rail A avancé n'est pas absorbé dans master**.

## Cartographie fonctionnelle

| Besoin | Existe ? | Preuve | État | Réutilisation / manque |
|---|---|---|---|---|
| Modification contrat | oui | `contract_write.update_contract()` | implémenté | réutilisé comme projection courante |
| Renouvellement CDD | oui | #455, `CDD_RENEWAL` | implémenté, UI non activée | ne pas dupliquer |
| CDD → CDI | oui | #455, `CDD_TO_CDI` | implémenté, UI non activée | ne pas dupliquer |
| Lien contrat précédent | oui | `previous_contract_id` | implémenté | réservé à la chaîne qui produit un nouveau contrat |
| Date d'effet d'un avenant | non avant ce lot | aucune branche/PR `avenant`/`amendment` | absent | ajoutée au journal d'avenants |
| Historique avant/après | non avant ce lot | `update_contract()` faisait un UPDATE destructif | absent | ajout append-only |
| Avenant rémunération | partiel avant ce lot | salaire modifiable par `update_contract()` | non historisé | V1 historisée |
| Avenant durée | partiel avant ce lot | `weekly_hours` modifiable | non historisé | V1 historisée |
| Avenant groupe CCNS | partiel avant ce lot | `ccns_group` modifiable | non historisé | V1 historisée |
| Avenant qualification CEE | partiel avant ce lot | `cee_qualification` modifiable | non historisé | V1 historisée |
| Avenant classification historique / point | moteur séparé existant | #457 | pas intégré V1 | lot ultérieur |
| Avenant fonctions / emploi | non démontré | pas de champ correspondant dans le snapshot Rail A | absent du modèle inspecté | ne pas inventer de stockage |
| Avenant lieu de travail | non démontré | pas de champ correspondant dans le snapshot Rail A | absent du modèle inspecté | ne pas inventer de stockage |
| Document avenant | non | moteur Documents RH séparé | absent du parcours | lot ultérieur après modèle stabilisé |

## Architecture minimale retenue

### Identité

Un avenant V1 conserve le même `IDcontrat`.

Il **ne crée pas** une seconde ligne CDI/CDD et ne touche pas à
`previous_contract_id`. Cette colonne reste la relation entre contrats lorsque
l'opération produit effectivement un nouveau contrat : renouvellement CDD ou
CDD → CDI.

### Projection courante

La table historique `contrats` reste la projection courante consommée par les
lecteurs legacy. L'écriture est toujours effectuée par le service Rail A
`update_contract()` et son adaptateur existant.

### Historique append-only

La table additive `tw_contract_amendment` conserve :

- `contract_id` ;
- date d'effet ;
- nature dominante ;
- clé d'idempotence ;
- hash de la requête ;
- liste des clauses modifiées ;
- hash avant/après ;
- payload canonique avant/après ;
- instant UTC d'enregistrement.

Le format SQL n'utilise volontairement ni JSON, ni colonne générée, ni CHECK
obligatoire afin de rester compatible avec MySQL 5.5+/MariaDB.

### Transaction

L'avenant :

1. contrôle l'idempotence ;
2. verrouille la ligne `contrats` avec `SELECT ... FOR UPDATE` sur MySQL ;
3. compare l'empreinte de l'état relu à celle chargée par l'opérateur ;
4. valide date d'effet et nature du changement ;
5. insère l'historique avec `commit=False` ;
6. réutilise `update_contract()` ;
7. le commit du Rail A valide ensemble historique et projection ;
8. la relecture après commit conserve la distinction `READBACK_ERROR`.

Le rollback retire donc également l'historique préparé si la validation ou
l'écriture du contrat échoue avant commit.

### Concurrence et replay

- `expected_before_hash` fournit l'optimistic locking applicatif ;
- `FOR UPDATE` ferme la course entre le contrôle et l'UPDATE sur MySQL ;
- `idempotency_key` est UNIQUE ;
- même clé + même requête = replay sans nouvelle écriture ;
- même clé + requête différente = refus ;
- une empreinte devenue obsolète = `CONCURRENT_MODIFICATION`.

### Date d'effet future

La V1 **refuse** volontairement une date d'effet future.

Mettre à jour immédiatement `contrats` avec une clause qui ne doit s'appliquer
que plus tard serait faux. Un lot ultérieur devra introduire explicitement la
projection différée / activation à date avant d'autoriser ces avenants.

### Bornes V1

La V1 historise uniquement les clauses déjà présentes dans l'éditeur Rail A :

- groupe CCNS ;
- qualification CEE ;
- durée hebdomadaire ;
- rémunération mensuelle ;
- rémunération annuelle.

Elle refuse les modifications de dates dans le parcours générique afin de ne
pas absorber silencieusement le renouvellement CDD existant.

La classification historique / valeur de point reste hors V1 : #457 possède
une commande et un parcours dédiés qui devront être raccordés proprement dans
un second lot.

## Stop-gate Windows/MySQL

La recette `tools/recipe_qt_contracts_mysql.py` vérifie réellement :

- Windows natif ;
- `GestionDB.DB().isNetwork == True` ;
- création CDD ;
- readback ;
- modification ;
- readback ;
- suppression/nettoyage ;
- émission de `TEAMWORKS_RAIL_A_MYSQL_READY` uniquement en cas de succès.

L'audit n'a trouvé :

- aucun commentaire sur #448 matérialisant un succès ;
- aucune occurrence de `TEAMWORKS_RAIL_A_MYSQL_READY` sur `master` ;
- aucune absorption du Rail A dans `master`.

Le stop-gate est donc **non prouvé comme levé**. Ce lot ne doit activer aucun
bouton d'avenant en production.

## Lot créé

Branche : `qt/contracts-amendment-foundation`, issue du HEAD #464
`e4ea900c640217a24fa1a60259e3c2d2bf0ffea1`.

Fichiers ajoutés :

- `domain/contracts/contract_amendment.py` ;
- `application/services/contract_amendment.py` ;
- `infrastructure/persistence/contract_amendment_adapter.py` ;
- `infrastructure/persistence/sql/contract_amendment_v1.sql` ;
- `tests/test_contract_amendment_service.py` ;
- `tests/test_contract_amendment_adapter_contract.py` ;
- ce document.

Aucun widget Qt/wx, aucun lanceur et aucun feature gate n'est activé dans ce lot.
