# CRH-23 — runtime du cockpit des démarches RH

**Date : 1er septembre 2026**

## Objet

CRH-23 compose les briques déjà développées pour permettre au futur écran du cockpit RH de travailler sur la base Teamworks active sans connaître la persistance ni l'identité logique de la structure.

## Composition

`HrCaseDashboardRuntimeFactory` assemble :

1. `TeamworksStructureIdentityRepository` pour retrouver l'identité stable de la base active ;
2. `TeamworksHrCasesRepository` CRH-22 pour lire les démarches ;
3. `TeamworksHrConnectionsRepository` CRH-16 pour résoudre les organismes configurés ;
4. `HrCaseDashboardService` CRH-21 pour construire la projection métier.

Le résultat est une façade `HrCaseDashboardRuntime` dont l'unique opération publique métier est `build(as_of=...)`.

## Date de référence

Le runtime exige une date de référence explicite. Il n'appelle ni `date.today()` ni `datetime.now()` afin de rendre les résultats reproductibles et de ne pas cacher une dépendance temporelle dans le cockpit.

## Frontière UI

La future interface wxPython n'a pas besoin de connaître :

- `GestionDB` ;
- les repositories ;
- la fabrication de l'identité de structure ;
- les requêtes SQL ;
- les règles de calcul des compteurs.

L'identité de structure est conservée dans un attribut interne `_structure_ref` et n'est pas exposée comme donnée à saisir ou à afficher.

## Lecture seule

La composition CRH-23 est volontairement asymétrique : elle connaît les adaptateurs nécessaires à la lecture mais n'appelle aucune opération de création, transition ou journalisation. Cette frontière empêche le futur écran de cockpit de devenir par accident un second moteur de workflow.

Les actions sur les dossiers resteront donc un lot distinct, avec leurs propres règles de transition et d'audit.

## Limites

CRH-23 reste un lot de composition et de lecture :

- aucun nouvel écran wxPython ;
- aucune création ou transition de dossier ;
- aucun réseau ;
- aucune transmission à un organisme ;
- aucune conclusion juridique automatique.

Le lot suivant pourra raccorder un premier écran de cockpit en lecture seule, puis les actions de workflow dans un sous-lot séparé.
