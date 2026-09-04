# Audit d’architecture — cohérence Remboursements ↔ Déplacements

## Cadre

- Référence : branche `audit/caracterisation-scenarios-frais`, commit `ee152d12bc0e2387307c2d579fc62b93752b4345`.
- Sujet : cohérence entre `deplacements.IDremboursement` et `remboursements.listeIDdeplacement`.
- Nature du lot : audit, documentation et tests de caractérisation uniquement.
- Hors périmètre : aucun changement de production, aucun changement de schéma, aucune suppression de représentation, aucun refactoring des écritures, aucun changement sous `poc/qt-theme/`.

L’inventaire a été obtenu par balayage exhaustif du dépôt (`git grep`) puis vérification des fonctions concernées. Les bases SQLite livrées dans `teamworks/Static/Databases/Defaut.dat` et `teamworks/Static/Exemples/Exemple_TDATA.dat` ont également été comparées sans modification.

## Conclusion

Le système possède deux représentations persistées du même rattachement :

1. `deplacements.IDremboursement`, scalaire, porté par chaque déplacement ;
2. `remboursements.listeIDdeplacement`, chaîne d’identifiants séparés par `-`, portée par le remboursement.

Elles ne forment pas un invariant transactionnel. Elles sont écrites ensemble lors de la sauvegarde d’un remboursement, mais des lecteurs différents choisissent des sources différentes et d’autres flux modifient une seule représentation.

**La source opérationnelle dominante est `deplacements.IDremboursement`.** Elle pilote l’éligibilité et les cases de l’éditeur de remboursement, l’état « remboursé », les protections de suppression, les totaux de gestion et l’écran d’impression. `remboursements.listeIDdeplacement` est principalement une représentation d’affichage dans la liste des remboursements ; l’éditeur charge bien cette colonne avec l’en-tête du remboursement mais ne l’utilise pas pour reconstruire ses rattachements.

La divergence la plus directe est reproductible sans panne : sauvegarder la modification d’un déplacement déjà remboursé écrit `IDremboursement=0`, sans modifier `listeIDdeplacement`. Le même déplacement redevient alors disponible pour un autre remboursement, ce qui peut conduire deux listes parent à le revendiquer tandis que le déplacement pointe seulement le second remboursement.

## Inventaire des lecteurs et écrivains

Le balayage exhaustif ne trouve pas d’autre lecteur/écrivain applicatif de ces deux représentations en dehors des modules suivants :

- `teamworks/Data/DATA_Tables.py` : déclaration des deux colonnes ;
- `teamworks/Dlg/DLG_Gestion_frais.py` : agrégation des personnes selon `deplacements.IDremboursement` ;
- `teamworks/Ctrl/CTRL_Page_frais.py` : listes Déplacements/Remboursements, protections et suppressions ;
- `teamworks/Dlg/DLG_Saisie_deplacement.py` : affichage du remboursement et sauvegarde du déplacement ;
- `teamworks/Dlg/DLG_Saisie_remboursement.py` : lecture et double écriture du rattachement ;
- `teamworks/Dlg/DLG_Impression_frais.py` : sélection/impression depuis les déplacements ;
- `teamworks/Ol/OL_personnes.py` et `teamworks/Ol/OL_personnes_core.py` : gardes de suppression d’une personne par existence de lignes, sans arbitrage entre les deux représentations.

Les autres occurrences sont de la documentation, des tests/smokes ou les bases binaires livrées. La matrice détaillée est dans `docs/audits/coherence_remboursements_deplacements_matrice.md`.

## Source effective par écran ou traitement

### Gestion globale des frais

`DLG_Gestion_frais.ListCtrl_personnes` lit les déplacements et détermine les montants remboursés/non remboursés à partir de `deplacements.IDremboursement`. La liste sérialisée n’intervient pas.

**Source effective : `deplacements.IDremboursement`.**

### Page Frais — liste Déplacements

`CTRL_Page_frais.ListCtrl_deplacements` affiche le numéro de remboursement à partir du champ du déplacement.

**Source effective : `deplacements.IDremboursement`.**

### Page Frais — liste Remboursements

`CTRL_Page_frais.ListCtrl_remboursements` lit `listeIDdeplacement`, la découpe sur `-` et construit le libellé « Déplacements rattachés » à partir de cette chaîne.

**Source effective : `remboursements.listeIDdeplacement`.**

Cette ligne peut donc contredire immédiatement la liste Déplacements affichée dans le même écran.

### Saisie d’un déplacement

Le déplacement est chargé par `SELECT *`; son `IDremboursement` est utilisé pour afficher le remboursement. La date du remboursement est ensuite recherchée dans la table parent. Si la clé du déplacement pointe un remboursement absent, la recherche parent ne trouve rien et le libellé n’est pas renseigné, alors que les traitements qui testent uniquement la valeur non nulle/non zéro continuent de considérer le déplacement comme remboursé.

À la sauvegarde, création **et modification** écrivent `IDremboursement=0`.

**Source de lecture : `deplacements.IDremboursement`. Écriture : uniquement cette représentation, remise à zéro.**

### Saisie d’un remboursement

L’en-tête lit `listeIDdeplacement`, mais les déplacements proposés et cochés sont déterminés par `deplacements.IDremboursement` :

- création : `IDremboursement=0` ;
- modification : `IDremboursement=0 OR IDremboursement=<courant>` ;
- état coché : clé du déplacement non nulle/non zéro dans le résultat proposé.

La sauvegarde reconstruit `listeIDdeplacement` depuis les cases cochées, puis met à jour les clés des déplacements.

**Source de lecture métier : `deplacements.IDremboursement`. Écriture : les deux représentations.**

### Impression des frais

La sélection liste les déplacements et affiche leur rattachement à partir de `IDremboursement`. Le PDF est alimenté par une requête sur `deplacements`; `IDremboursement` est encore sélectionné mais n’est actuellement pas rendu dans le tableau imprimé. `listeIDdeplacement` n’est jamais consultée.

**Source effective : `deplacements` ; `listeIDdeplacement` n’intervient pas.**

### Suppression d’un déplacement

La suppression est interdite lorsque `deplacements.IDremboursement` est non nul/non zéro. Une divergence « liste parent contient l’ID, clé enfant à 0 » contourne donc la protection et permet la suppression, laissant un identifiant inexistant dans la chaîne parent.

**Source de garde : `deplacements.IDremboursement`.**

### Suppression d’un remboursement

Les déplacements associés sont recherchés via `WHERE deplacements.IDremboursement=<ID>`. Le remboursement est supprimé, puis ces déplacements sont remis à zéro. `listeIDdeplacement` n’est pas utilisée pour trouver les enfants à libérer.

**Source de rattachement pour la suppression : `deplacements.IDremboursement`.**

## Analyse transactionnelle

### Sémantique de `GestionDB`

Les primitives génériques `ReqInsert`, `ReqMAJ` et `ReqDEL` acceptent `commit=True` par défaut et committent donc leur écriture sauf appel explicite avec `commit=False`. Les `DB.Commit()` visibles dans les dialogues ne constituent pas, à eux seuls, une transaction multi-écritures : la plupart des modifications sont déjà validées individuellement.

### Création d’un remboursement

Ordre observé :

1. ouverture d’une première connexion ;
2. `ReqInsert("remboursements", ...)` contenant `listeIDdeplacement` — commit par défaut ;
3. `DB.Commit()` puis fermeture ;
4. ouverture d’une seconde connexion ;
5. boucle de `ReqMAJ("deplacements", IDremboursement=<nouvel ID>)` — chaque appel committe par défaut ;
6. boucle des déplacements décochés vers `0` — chaque appel committe par défaut ;
7. `DB.Commit()` puis fermeture.

Une panne après l’étape 2 laisse donc un remboursement et sa liste sérialisée persistés sans les clés enfants. Une panne au milieu des boucles produit un sous-ensemble mis à jour.

### Modification d’un remboursement

La séquence est identique, avec `ReqMAJ` du remboursement en première phase. La nouvelle liste parent est donc persistée avant la réconciliation des enfants. Une interruption peut laisser l’ancienne distribution des clés enfants face à la nouvelle liste parent, ou seulement une partie des clés réconciliées.

### Suppression d’un remboursement

Dans `CTRL_Page_frais`, les enfants sont d’abord lus depuis `deplacements.IDremboursement`. Puis :

1. `ReqDEL("remboursements", ...)` — commit par défaut ;
2. boucle de `ReqMAJ` sur les enfants lus pour mettre `IDremboursement=0` — commit par défaut à chaque ligne ;
3. commit explicite final.

Une interruption après le `DELETE` mais avant la fin de la boucle laisse des déplacements pointant un remboursement désormais absent. Une interruption en milieu de boucle laisse seulement une partie des clés libérées.

## Scénarios de divergence

| Scénario | État obtenu | Conséquence observable | Reproductibilité |
|---|---|---|---|
| Modifier/sauvegarder un déplacement remboursé | clé enfant `0`, liste parent contient encore l’ID | liste Remboursements dit « rattaché », éditeur et traitements le voient libre | Reproduit par test |
| Réaffecter ensuite ce déplacement à un autre remboursement | enfant → B, liste A contient ID, liste B contient ID | deux parents revendiquent le même enfant ; seuls les écrans basés sur la clé voient B | Reproduit par test |
| Panne entre enregistrement parent et phase enfants | nouvelle liste parent persistée, clés enfants inchangées | incohérence immédiate après reprise | Reproduit par panne injectée |
| Panne au milieu de la boucle enfants | liste parent complète, seulement une partie des enfants réconciliée | rattachement partiel | Déduit de commits ligne par ligne |
| Panne pendant suppression | parent absent, tout ou partie des enfants pointent l’ID supprimé | clés orphelines | Déduit de l’ordre et des commits |
| Supprimer un enfant dont la clé a été remise à 0 mais reste dans une liste parent | liste parent contient un ID inexistant | affichage d’un déplacement fantôme dans la liste Remboursements | Flux normal possible |
| Clé enfant vers remboursement inexistant | enfant traité comme remboursé par certains écrans ; fiche déplacement ne résout pas le parent | statut contradictoire/parent fantôme | Données possibles sans FK |
| Même ID dans plusieurs listes parent | plusieurs remboursements revendiquent le même déplacement | affichage contradictoire ; la clé enfant ne peut en représenter qu’un | Flux normal après détachement + réaffectation |
| ID de déplacement inexistant ou d’une autre personne dans une liste parent | chaîne valide syntaxiquement mais fausse métier | affichage trompeur ; aucune contrainte ne corrige | Données possibles |
| `IDremboursement IS NULL` | gestion/impression le traitent souvent comme non remboursé ; requête de création remboursement exige `=0` | déplacement non remboursé mais non proposé à l’éditeur | Reproductible par état legacy/importé |
| Liste mal formée, doublonnée ou dépassant le modèle `VARCHAR(300)` | projection parent non fiable | parsing/affichage fragile, intégrité non garantie | Données possibles sans contrainte |
| Deux fenêtres modifient le même remboursement | deux snapshots, écritures indépendantes | dernière liste parent et succession de clés enfants peuvent ne pas correspondre | Risque de concurrence sans verrou/version |

## Caractérisation ajoutée

`tests/characterisation/test_remboursements_deplacements_coherence.py` exécute les méthodes historiques extraites de leur AST avec une doublure SQLite minimale, sans importer wxPython. Les tests couvrent notamment :

- modification réelle d’un déplacement remboursé puis divergence clé/liste ;
- réaffectation à un second remboursement avec revendication par deux listes parent ;
- panne injectée entre la phase parent et la phase enfants ;
- lecteurs différents de la liste principale et de l’éditeur ;
- différence de traitement entre `NULL` et `0` ;
- commits par défaut des primitives `GestionDB` et ordre parent → enfants.

Ces tests figent le comportement actuel ; ils ne constituent pas une correction.

## État des données livrées

Les deux bases d’exemple présentes dans le dépôt ont été auditées en lecture seule :

- `teamworks/Static/Databases/Defaut.dat` : 4 déplacements, 1 remboursement, 0 divergence, 0 liste invalide ;
- `teamworks/Static/Exemples/Exemple_TDATA.dat` : 4 déplacements, 1 remboursement, 0 divergence, 0 liste invalide.

Ce résultat montre que les fixtures livrées sont propres ; il ne permet pas de conclure sur les bases utilisateurs existantes. Une future migration doit commencer par un inventaire/dry-run sur chaque base réelle.

## Source de vérité cible recommandée

**Recommandation : faire de `deplacements.IDremboursement` la source de vérité canonique du rattachement.**

Motifs :

1. la cardinalité naturelle est « plusieurs déplacements → un remboursement » et se représente directement par la clé portée par l’enfant ;
2. c’est déjà la source dominante des traitements opérationnels ;
3. elle permet des requêtes SQL directes, indexables et contrôlables ;
4. elle ne dépend pas d’un format de chaîne, d’une limite de longueur ou d’un parsing ;
5. elle est la représentation qui pourra, dans une migration ultérieure distincte, recevoir des contraintes d’intégrité.

`remboursements.listeIDdeplacement` doit rester présente pendant la migration de compatibilité, mais être considérée comme **projection dérivée/miroir historique**, non comme autorité concurrente.

## Plan de migration proposé — sans implémentation

### Phase 0 — inventaire et sauvegarde

Avant toute écriture :

- exporter pour chaque déplacement son `IDdeplacement`, `IDpersonne` et `IDremboursement` brut ;
- exporter pour chaque remboursement son `IDremboursement`, `IDpersonne` et `listeIDdeplacement` brute, sans normalisation ;
- horodater et signer/checksummer cet export ;
- exécuter un dry-run qui classe chaque relation.

Catégories minimales : exact, parent-only, enfant-only, clé enfant orpheline, ID parent inexistant, conflit enfant→B mais liste A, revendications multiples, incohérence de personne, liste invalide, `NULL`/`0`.

### Phase 1 — politique de réconciliation

Politique recommandée :

- une clé enfant non nulle/non zéro qui pointe un remboursement existant de la même personne est canonique ;
- si la clé enfant est libre (`0`/`NULL`) et qu’exactement une liste parent valide de la même personne revendique l’enfant, classer le cas comme récupération non ambiguë et le soumettre au mode choisi (automatique après validation ou revue) ;
- si plusieurs listes parent revendiquent un enfant, ou si la liste contredit une clé enfant valide, la clé enfant gagne et le conflit est consigné ;
- une clé enfant orpheline ne doit pas être effacée silencieusement : elle doit être reportée et traitée selon une décision de migration explicite ;
- toute donnée écartée doit rester récupérable depuis le snapshot brut.

### Phase 2 — projection de compatibilité

Une fois les clés enfants réconciliées, régénérer `listeIDdeplacement` depuis les enfants canoniques, de façon déterministe (IDs uniques triés, séparateur historique `-`). La colonne reste en place afin de préserver les lecteurs historiques et de permettre un rollback applicatif.

### Phase 3 — bascule progressive des lecteurs et écritures

Dans des PR de production ultérieures, séparées de cet audit :

- basculer tous les lecteurs métier vers la clé enfant ;
- maintenir temporairement la chaîne parent comme projection compatible ;
- regrouper les écritures d’un remboursement dans une transaction réelle unique (`commit=False` pour les primitives, commit final unique, rollback sur erreur) ;
- ajouter des contrôles de parité et métriques de divergence avant de retirer toute dépendance à la chaîne.

Aucune de ces modifications n’est réalisée dans cet audit.

### Phase 4 — durcissement éventuel du schéma

Seulement après stabilisation et dans une migration dédiée : convention `NULL`/`0`, index, clé étrangère, contraintes de cohérence ou remplacement de la projection sérialisée. Le présent audit ne modifie pas le schéma.

## Stratégie de rollback

Le rollback doit restaurer les **deux représentations originales**, et non recalculer l’une depuis l’autre :

1. conserver le snapshot immuable pré-migration des clés enfants et des chaînes parent brutes ;
2. exécuter la migration par lots identifiables avec journal externe ou artefact de migration, sans exiger de nouveau schéma ;
3. en cas de rollback, stopper les écritures concurrentes, restaurer d’abord les `deplacements.IDremboursement` originaux puis les `remboursements.listeIDdeplacement` brutes du même snapshot ;
4. vérifier les nombres de lignes, checksums et écarts par lot ;
5. conserver `listeIDdeplacement` durant toute la période de compatibilité, afin qu’un rollback de version applicative reste possible ;
6. ne supprimer aucune trace de conflit tant que la période d’observation n’est pas terminée.

Le point essentiel est de ne jamais utiliser l’état « normalisé » comme sauvegarde : le rollback doit pouvoir restituer exactement les données préexistantes, y compris les divergences historiques.

## Décision recommandée

Adopter `deplacements.IDremboursement` comme source de vérité cible, conserver `remboursements.listeIDdeplacement` comme projection de compatibilité, commencer toute migration par un rapport de réconciliation en lecture seule, puis migrer les écritures et lecteurs progressivement avec transaction atomique et rollback fondé sur un snapshot brut des deux représentations.
