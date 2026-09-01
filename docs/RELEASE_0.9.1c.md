# Teamworks-CCNS 0.9.1c

## Nature de la version

`0.9.1c` est une révision corrective et de qualification de `0.9.1b`.

Elle n'introduit **aucune nouvelle fonctionnalité métier**. Son objectif est de publier un paquet Windows correspondant au `master` actuellement qualifié côté machine, après les corrections et consolidations postérieures à la précédente release `v0.9.1b`.

## Référence avant incrément

Le build de référence immédiatement antérieur à cette publication est la qualification machine CI #789 du commit `4a226af71facf4fe201e022086e6dd00a46ecbf0` :

- 1 893 tests pytest réussis, 3 ignorés ;
- 332/332 fichiers Python compilables ;
- 0/0 chemin SQLite binaire ;
- parcours critiques Windows réussis ;
- portable et installateur construits ;
- démarrage automatisé de l'exécutable réussi ;
- manifeste d'intégrité validé.

La PR documentaire #315 a ensuite été fusionnée dans `master` sans modification runtime ni métier.

## Portée 0.9.1c

- incrément de version `0.9.1b` → `0.9.1c` ;
- reconstruction des paquets Windows depuis le `master` courant ;
- publication sous un nouveau tag, sans réécrire la release `v0.9.1b` existante ;
- aucune fonction nouvelle ;
- aucune modification volontaire du schéma métier ;
- aucune qualification bêta/RC implicite.

Le build Windows final doit être déclenché depuis le `master` fusionné au moyen du mécanisme contrôlé `[windows]` déjà prévu par le workflow unique.

## Validation restante

La publication de `0.9.1c` ne remplace pas la recette utilisateur sur copie de base réelle. La qualification bêta / RC / stable reste conditionnée au parcours de validation décrit dans `docs/VALIDATION_WINDOWS_0.9.1b.md` (applicable à `0.9.1c` tant qu'aucun changement fonctionnel n'est introduit).
