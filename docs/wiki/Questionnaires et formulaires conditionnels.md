# Questionnaires et formulaires conditionnels

> **Statut : étude / prototype.** Cette page décrit un chantier inspiré du moteur de questionnaires de Noethys. Il n'est pas encore intégré à la Vanilla wx actuelle.

## Pourquoi ce chantier ?

Noethys contient un système de questionnaires configurable qui distingue :

- les questions ;
- leur type de contrôle ;
- les choix possibles ;
- les réponses ;
- les filtres appliqués aux réponses.

Ce principe peut être utile à Teamworks-CCNS pour éviter de coder une fenêtre spécifique à chaque nouvelle demande métier.

Le cas d'usage pilote retenu est la **demande de congé / absence**.

## Ce que Noethys possède déjà

L'audit du moteur historique montre plusieurs types de contrôles :

- ligne de texte ;
- texte multiligne ;
- entier ;
- décimal ;
- montant ;
- liste déroulante ;
- liste à cocher ;
- case à cocher ;
- date ;
- réglette ;
- document ;
- code-barres ;
- RFID.

Les utilitaires de filtres savent notamment tester :

### Texte

- égal / différent ;
- contient / ne contient pas ;
- vide / non vide.

### Entiers et dates

- égal / différent ;
- supérieur / supérieur ou égal ;
- inférieur / inférieur ou égal ;
- compris entre deux valeurs.

### Cases à cocher

- cochée ;
- décochée.

### Choix

- présence d'une réponse parmi une liste de choix.

Ces filtres sont consommés dans plusieurs parties de Noethys, notamment les grilles, la tarification, les inscriptions, les locations ou le badgeage.

## Ce que Teamworks veut en conserver

L'objectif n'est pas de porter les écrans wx de Noethys.

Nous voulons conserver les concepts utiles :

```text
Définition du formulaire
        +
Réponses
        +
Contexte métier
        ↓
Conditions
        ↓
Actions déclaratives
        ↓
État du formulaire + validations
```

Le moteur doit fonctionner sans wx ni Qt.

## Exemple : demande de congé / absence

Formulaire de base :

```text
Type d'absence
Date de début
Date de fin
Demi-journée
Commentaire
```

Si le type choisi est **Événement familial** :

```text
Afficher :
- type d'événement
- date de l'événement
- justificatif éventuel

Rendre obligatoires :
- type d'événement
- date de l'événement
```

Si le type choisi est **Récupération** :

```text
Afficher :
- solde de récupération
- quantité demandée
- unité de récupération
```

Le solde doit être fourni par le métier Teamworks, pas recalculé par le moteur de formulaire.

Si la quantité demandée dépasse le solde disponible, le moteur peut produire une erreur bloquante.

## Conditions logiques

Le futur moteur doit pouvoir exprimer au minimum :

```text
A ET B
```

et :

```text
A OU B
```

Exemple :

```text
SI type_absence = EVENEMENT_FAMILIAL
ET duree_jours > 1
ALORS rendre le justificatif obligatoire
```

L'audit doit distinguer ce que Noethys sait réellement combiner de ce qui devra être ajouté proprement dans Teamworks.

## Actions envisagées

Un moteur de règles ne doit pas modifier directement des widgets. Il doit produire un état neutre.

Actions envisagées en première version :

- afficher / masquer un champ ;
- rendre obligatoire / facultatif ;
- activer / désactiver ;
- définir une valeur par défaut ;
- produire un avertissement ;
- produire une erreur bloquante.

À étudier ensuite seulement si nécessaire :

- valeur calculée ;
- demande de justificatif ;
- niveau de validation requis.

## Niveau de validation

L'organisation visée reste volontairement simple :

```text
animateur
   ↓
directrice adjointe
   ↓
directeur
```

Le moteur de formulaire pourra éventuellement retourner un niveau de validation requis, mais il ne doit pas devenir lui-même un moteur complet de workflow : pas d'envoi de notifications, de changement de statut ou d'orchestration globale.

## Architecture cible

Conceptuellement :

```text
Teamworks métier
      ↓
FormContext + réponses
      ↓
FormEngine
      ↓
état des champs
+ erreurs
+ avertissements
+ résultat de validation
```

Les interfaces wx, Qt ou un futur portail doivent rester de simples consommateurs.

## Concepts étudiés

Le prototype doit rester minimal. Les abstractions envisagées sont notamment :

- `FormDefinition` ;
- `FormField` ;
- `FieldType` ;
- `Condition` ;
- `ConditionGroup` ;
- `Rule` ;
- `Action` ;
- `FormContext` ;
- `ValidationResult`.

Ces noms ne sont pas un contrat définitif : ils doivent être validés par le prototype.

## Ce que le FormEngine ne doit pas faire

Le premier moteur ne doit pas devenir :

- un BPM généraliste ;
- un moteur de workflow d'entreprise ;
- un moteur de calcul légal des congés ;
- une nouvelle base RH ;
- un langage de programmation utilisateur ;
- une API réseau ;
- un moteur de documents.

Les calculs métier restent dans Teamworks et sont fournis au formulaire via son contexte.

## Relation avec le futur moteur documentaire

Les deux chantiers restent séparés :

```text
FormEngine
    ↓
données validées
    ↓
Teamworks métier
    ↓
MergeContext
    ↓
DocumentEngine
```

Un formulaire peut donc préparer ou valider des données utilisées ensuite dans un contrat, une attestation ou un courrier, sans créer de dépendance directe entre les deux moteurs.

## Prototype attendu

La première preuve de faisabilité doit fonctionner sans interface graphique :

```python
result = engine.evaluate(
    definition=absence_form,
    responses={
        "type_absence": "RECUPERATION",
        "quantite_demandee": 2,
    },
    context={
        "solde_recuperation": 3,
    },
)
```

Le résultat doit indiquer de manière déterministe :

- champs visibles ;
- champs obligatoires ;
- champs désactivés ou en lecture seule ;
- erreurs ;
- avertissements ;
- validité globale.

## Liens associés

[[Architecture fonctionnelle]] · [[Contrats, CCNS et CEE]] · [[Frais et déplacements]] · [[Évolution documentaire Qt]]
