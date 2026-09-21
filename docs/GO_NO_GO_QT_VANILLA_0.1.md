# Qt Vanilla 0.1 — critères GO / NO-GO

Ce document fixe la décision de release de la Qt Vanilla 0.1.

Le SHA candidat doit être unique du build à la recette terrain.

## 1. Conditions GO obligatoires

La release est **GO** uniquement si toutes les conditions suivantes sont vraies.

### A. Identité de la candidate

- le SHA de la RC est celui indiqué dans le procès-verbal ;
- Linux, Windows natif et Packaging ont été exécutés sur ce même SHA ;
- le portable et le setup proviennent de ce même SHA ;
- les SHA-256 des artefacts sont conservés dans les preuves.

### B. MySQL exploitation

- `SELECT VERSION()` correspond exactement à la version réellement utilisée en exploitation ;
- la recette est exécutée sur une base dédiée `*_qt_vanilla_recette` ;
- la copie a passé l'audit d'anonymisation ;
- aucun test n'est exécuté sur l'unique base de production.

### C. Compatibilité

- tous les tests bloquants C-* de la matrice sont PASS ;
- création/modification/suppression Contrats fonctionne ;
- Signature et DUE persistent après redémarrage ;
- Frais create/update/delete + rattachement/détachement fonctionne ;
- Documents RH s'ouvrent sans déclencher de génération Office ;
- Unicode, NULL, chaînes vides, dates et décimaux sont relus correctement.

### D. Intégrité

- `automatic_schema_gate=true` ;
- aucune table, colonne ou index inattendu n'a changé ;
- tous les deltas de comptage sont expliqués ;
- aucun enregistrement orphelin n'est détecté ;
- tous les cas de rollback provoqués reviennent à l'état précédent ;
- aucune écriture partielle n'est constatée ;
- aucune connexion MySQL ne fuit après fermeture ;
- aucun `QThread destroyed while running`.

### E. Performance

- Performance = PASS dans le PV ;
- p50/p95 respectent les seuils documentés ;
- aucun parcours Qt/wx ne dépasse le ratio bloquant sans dérogation explicite ;
- aucune dérive d'endurance > 50 % ;
- aucune croissance mémoire non stabilisée au-delà du seuil bloquant ;
- la volumétrie de qualification est suffisante.

### F. Utilisabilité minimale

Sur un poste Windows réel, le parcours suivant doit être réalisable sans retour à wx :

1. rechercher un salarié ;
2. ouvrir Généralités ;
3. consulter Contrats ;
4. créer/modifier un contrat de recette ;
5. gérer Signature/DUE ;
6. consulter Présences/Scénarios ;
7. gérer Frais ;
8. ouvrir Documents RH ;
9. fermer puis relancer l'application.

## 2. NO-GO immédiat

Un seul des cas suivants suffit à déclarer **NO-GO** :

- SHA différent entre CI, artefact et recette ;
- version MySQL différente de l'exploitation ;
- test sur une base non dédiée ;
- donnée personnelle réelle détectée dans la copie de recette ;
- corruption, perte ou écriture partielle ;
- rollback incomplet ;
- relation orpheline créée ;
- mutation de schéma inattendue ;
- erreur MySQL reproductible sur un parcours du périmètre 0.1 ;
- fermeture laissant des threads ou connexions bloqués ;
- performance classée FAIL ;
- parcours critique nécessitant de repasser dans wx alors qu'il est déclaré inclus en 0.1.

## 3. Cas NON QUALIFIÉ

La candidate est **NON QUALIFIÉE** plutôt que FAIL lorsque la preuve manque sans qu'un défaut soit démontré.

Exemples :

- MySQL d'exploitation non accessible ;
- copie représentative non disponible ;
- volumétrie < 80 % pour la performance ;
- moins de 10 mesures P-01 à P-11 ;
- artefact testé différent de celui publié ;
- PV incomplet.

NON QUALIFIÉE interdit le tag stable.

## 4. Dérogations

Une dérogation n'est possible que pour un défaut de performance non critique ou une différence UX mineure.

Aucune dérogation n'est autorisée pour :

- corruption/perte de données ;
- erreur transactionnelle ;
- incompatibilité MySQL ;
- mutation de schéma ;
- fuite de connexion ;
- fuite de données personnelles ;
- divergence de SHA.

Toute dérogation doit préciser :

- référence du test ;
- mesure constatée ;
- risque ;
- justification ;
- décision explicite ;
- responsable de la décision.

## 5. Décision finale

Le PV doit conclure par exactement l'un des états :

```text
GO
NO-GO
NON QUALIFIEE
```

Règle de décision :

```text
si preuve obligatoire manquante -> NON QUALIFIEE
sinon si un bloqueur existe       -> NO-GO
sinon                             -> GO
```

Un **GO** autorise la préparation du tag `qt-v0.1.0`.

Il n'autorise pas un merge ou un tag automatique : la décision finale de merge reste manuelle.
