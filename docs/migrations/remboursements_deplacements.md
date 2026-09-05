# Migration de cohérence — remboursements et déplacements

## Objectif

Cette migration applique la décision d'architecture des audits #372/#373 :

- `deplacements.IDremboursement` est la source canonique du rattachement ;
- `remboursements.listeIDdeplacement` reste une projection de compatibilité ;
- aucun changement de schéma n'est réalisé.

L'outil est dédié aux fichiers SQLite Teamworks existants. Il n'importe ni wxPython ni `GestionDB`.

## Principes de sécurité

1. `plan` ouvre la base en `mode=ro` et produit uniquement un dry-run.
2. `apply` ouvre une base **existante** en `mode=rw`, prend un verrou `BEGIN IMMEDIATE`, relit l'état, recalcule le plan, crée un snapshot externe immuable puis applique toutes les écritures dans une transaction unique.
3. Toute référence enfant orpheline, valeur `IDremboursement` enfant invalide, incohérence/non-vérifiabilité de personne ou projection canonique dépassant les 300 caractères historiques bloque l'ensemble de la migration.
4. Les corruptions limitées à `listeIDdeplacement` (ordre, doublons, token invalide, ID de déplacement absent, revendication d'un enfant qui pointe ailleurs) sont réparables : la projection est régénérée depuis les clés enfants.
5. Après les écritures, l'outil relit l'état dans la même transaction et vérifie son empreinte ainsi que l'absence d'écart résiduel avant le `COMMIT`.
6. `rollback` refuse d'écraser une base dont les relations ont changé depuis l'application de la migration.

## Mode strict par défaut

Le mode par défaut ne modifie **aucun** `deplacements.IDremboursement` valide ou libre. Un enfant à `0`/`NULL` reste libre, même si une ancienne projection parent le revendique. Les listes parent sont simplement régénérées depuis cet état canonique.

```bash
python tools/migrer_remboursements_deplacements.py plan /chemin/Teamworks.dat
python tools/migrer_remboursements_deplacements.py apply /chemin/Teamworks.dat
```

`apply` crée automatiquement un fichier voisin du type :

`Teamworks.dat.remboursements-YYYYMMDDTHHMMSSZ.snapshot.json`

Un chemin explicite peut être imposé avec `--snapshot` ; il doit ne pas déjà exister.

## Récupération parent unique — option explicite

La politique de l'audit #372 permet, après validation, de récupérer un enfant libre lorsqu'**une seule** projection parent existante, de la même personne, le revendique.

Cette récupération est désactivée par défaut et doit être demandée explicitement :

```bash
python tools/migrer_remboursements_deplacements.py plan /chemin/Teamworks.dat --recuperer-parent-unique
python tools/migrer_remboursements_deplacements.py apply /chemin/Teamworks.dat --recuperer-parent-unique
```

Si plusieurs parents revendiquent l'enfant libre, si la personne ne correspond pas ou si la revendication est autrement ambiguë, la clé enfant libre reste canonique et les revendications parent sont supprimées de la projection.

## Snapshot et rollback

Le snapshot contient, sans normalisation :

- `IDdeplacement`, `IDpersonne`, `IDremboursement` pour chaque déplacement ;
- `IDremboursement`, `IDpersonne`, `listeIDdeplacement` pour chaque remboursement ;
- les types SQLite bruts (`NULL`, entier, réel, texte, blob) ;
- l'empreinte SHA-256 de l'état avant ;
- l'empreinte SHA-256 de l'état attendu après ;
- le plan exact appliqué ;
- un checksum SHA-256 du snapshot lui-même.

Rollback :

```bash
python tools/migrer_remboursements_deplacements.py rollback /chemin/Teamworks.dat /chemin/snapshot.json
```

Le rollback restaure uniquement les deux représentations du rattachement. Il n'insère ni ne supprime aucune ligne. Il est refusé si l'état relationnel courant n'est plus exactement celui obtenu par la migration, afin de ne pas écraser des modifications ultérieures.

## Procédure opérateur recommandée

Avant toute application sur une base réelle :

1. arrêter Teamworks et toute écriture concurrente ;
2. travailler d'abord sur une copie de la base réelle ;
3. exécuter `plan` et conserver son rapport ;
4. arbitrer tout blocage côté source canonique ;
5. décider explicitement si la récupération parent unique est autorisée ;
6. exécuter `apply` et archiver le snapshot hors du répertoire de travail ;
7. relancer le diagnostic #373 ;
8. valider les écrans Déplacements, Remboursements et impression sur la copie ;
9. seulement ensuite planifier l'opération sur la base réelle.

Cet outil n'est pas une modification automatique du schéma et ne remplace pas une sauvegarde complète de la base Teamworks.
