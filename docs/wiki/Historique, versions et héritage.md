# Historique, versions et héritage

## Origine

Teamworks-CCNS dérive du projet historique **Teamworks**, développé dans l'écosystème Noethys.

Le fork poursuit désormais son propre développement.

## Pourquoi ce fork ?

Les objectifs principaux sont notamment :

- maintenir Teamworks utilisable sur les environnements Python/wxPython actuels ;
- corriger les régressions et crashs ;
- améliorer les performances ;
- améliorer l'ergonomie ;
- moderniser progressivement l'architecture ;
- développer les fonctions liées à la CCNS et aux CEE.

## Vanilla wx

La branche wx constitue aujourd'hui la base opérationnelle utilisée pour la stabilisation et les recettes réelles.

Elle conserve une part importante du code historique tout en intégrant progressivement les corrections Teamworks-CCNS.

## Qt

Une évolution Qt existe parallèlement.

Elle ne doit pas être considérée comme identique à la Vanilla wx ni utiliser automatiquement son mécanisme de mise à jour.

## Versions

Les versions peuvent comporter des préversions :

```text
0.9.2-rc1
0.9.2-rc2
0.9.2-rc3
```

Une RC est une candidate à une version stable, pas une version finale.

## Historique upstream

L'historique ancien de Teamworks peut être conservé séparément afin de ne pas encombrer le changelog courant Teamworks-CCNS.

Le changelog principal doit décrire les modifications réellement apportées par le fork.
