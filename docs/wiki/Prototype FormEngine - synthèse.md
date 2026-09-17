# Prototype FormEngine — synthèse

> **Statut : prototype demandé, qualification distante en attente.** Cette page décrit l'architecture et les règles retenues pour la première preuve de faisabilité du FormEngine. Au moment de cette mise à jour, aucun commit/branche distant contenant le prototype `FormEngine` n'est encore visible dans `fr4nck/Teamworks-CCNS`. Les commandes et résultats de tests exacts ne sont donc pas inventés : ils seront renseignés dès que Claude Code aura poussé le prototype.

## Objectif

Le prototype doit démontrer qu'un formulaire métier Teamworks peut être défini, évalué et validé **sans wx, sans Qt et sans accès SQL direct**.

Le cas pilote est la **demande de congé / absence**.

Le moteur n'a pas vocation à remplacer le métier RH, le calcul des congés ou le workflow d'approbation. Il évalue une définition de formulaire à partir de réponses et d'un contexte métier neutre.

## Architecture

```text
Teamworks métier
      ↓
adaptateur
      ↓
FormDefinition
+ FormResponse
+ FormContext
      ↓
   FormEngine
      ↓
EvaluationResult
├── état des champs
├── erreurs
├── avertissements
└── niveau de validation éventuel
```

Le cœur doit rester importable et testable indépendamment de l'interface graphique.

### Concepts minimaux

Les noms exacts peuvent évoluer avec le prototype, mais la séparation attendue est la suivante :

- `FormDefinition` : définition du formulaire ;
- `FormField` : définition d'un champ ;
- `FieldType` : type de valeur attendu ;
- `FormResponse` : réponses saisies par l'utilisateur ;
- `FormContext` : données métier fournies par Teamworks, non saisies dans le formulaire ;
- `Condition` : comparaison élémentaire ;
- `ConditionGroup` : combinaison logique `ALL` / `ANY` correspondant à ET / OU ;
- `Rule` : condition(s) + action(s) ;
- `Action` : effet déclaratif sur l'état du formulaire ;
- `EvaluationResult` / `ValidationResult` : résultat neutre consommable par une future UI Qt ou un autre client.

## Types de champs visés en V1

Le prototype doit couvrir au minimum :

- texte court ;
- texte long ;
- entier ;
- décimal ;
- date ;
- booléen ;
- choix unique ;
- choix multiple ;
- référence neutre vers un document/pièce jointe.

Le moteur historique Noethys contient davantage de contrôles, mais les éléments sans usage RH immédiat — RFID, code-barres, couleur, réglette — ne sont pas prioritaires.

## Conditions et opérateurs

Le moteur doit au minimum permettre :

- égal / différent ;
- supérieur / supérieur ou égal ;
- inférieur / inférieur ou égal ;
- contient / ne contient pas ;
- vide / non vide ;
- appartient à / n'appartient pas à.

Les conditions doivent pouvoir être combinées simplement :

```text
ALL = ET
ANY = OU
```

Le moteur doit retourner un résultat maîtrisé lorsqu'une donnée est absente ou invalide ; une condition incorrecte ne doit pas provoquer une exception UI incontrôlée.

## Actions déclaratives visées

Première version :

- afficher un champ ;
- masquer un champ ;
- rendre obligatoire ;
- rendre facultatif ;
- activer ;
- désactiver ;
- définir une valeur par défaut ;
- produire un avertissement ;
- produire une erreur bloquante.

Un éventuel niveau de validation peut être retourné comme une donnée, mais le FormEngine ne doit pas orchestrer lui-même les notifications, changements de statut ou circuits d'approbation.

## Formulaire pilote : congés / absences

### Champs de base

```text
type_absence
date_debut
date_fin
demi_journee
commentaire
```

Types fictifs utilisés pour le prototype :

```text
CONGE_PAYE
RECUPERATION
EVENEMENT_FAMILIAL
ABSENCE_EXCEPTIONNELLE
```

Ces valeurs servent à la preuve de faisabilité et ne constituent pas encore le référentiel métier définitif de production.

### Règle 1 — dates obligatoires

Pour toute absence :

```text
date_debut : obligatoire
date_fin   : obligatoire
```

### Règle 2 — événement familial

Si :

```text
type_absence == EVENEMENT_FAMILIAL
```

alors afficher :

```text
type_evenement
date_evenement
justificatif
```

et rendre obligatoires :

```text
type_evenement
date_evenement
```

### Règle 3 — récupération

Si :

```text
type_absence == RECUPERATION
```

alors afficher :

```text
solde_recuperation
quantite_demandee
unite_recuperation
```

`solde_recuperation` doit provenir de `FormContext`. Le FormEngine ne calcule pas lui-même la banque de récupération et ne la modifie pas.

### Règle 4 — dépassement du solde

Si :

```text
quantite_demandee > solde_recuperation
```

alors produire une erreur bloquante :

```text
La quantité demandée dépasse le solde disponible.
```

### Règle 5 — absence exceptionnelle

Si :

```text
type_absence == ABSENCE_EXCEPTIONNELLE
```

alors afficher et rendre obligatoire :

```text
motif
```

et produire l'avertissement :

```text
Cette demande nécessite une validation spécifique.
```

## Exemple d'évaluation attendu

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

Le résultat doit permettre à l'interface de déterminer au minimum :

```text
date_debut             visible / required
date_fin               visible / required
solde_recuperation     visible / readonly
quantite_demandee      visible / required
unite_recuperation     visible
type_evenement         hidden
justificatif           hidden

valid = True
errors = []
```

Avec une quantité demandée de `4` pour un solde de `3`, le résultat attendu est :

```text
valid = False
errors = [
    "La quantité demandée dépasse le solde disponible."
]
```

## Commandes de test

### État actuellement vérifiable

Au moment de la rédaction de cette page, le prototype Claude Code n'est **pas encore visible sur une branche ou un commit distant** du dépôt GitHub. Il n'est donc pas possible de publier honnêtement une commande de test exacte liée à des fichiers qui ne sont pas encore présents sur le dépôt.

Les commandes seront renseignées ici à partir du commit réel, et non déduites du cahier des charges.

La qualification devra inclure au minimum :

```text
- commande exacte de la suite unitaire FormEngine ;
- commande exacte des tests du formulaire congés/absences ;
- commande exacte de la démonstration headless ;
- version Python utilisée ;
- SHA du commit testé.
```

## Résultats exacts

**État au 16 septembre 2026 : non disponibles sur le dépôt distant.**

Aucun résultat du type :

```text
X passed
Y failed
```

n'est publié ici tant qu'il n'a pas été obtenu à partir du prototype réellement poussé et de commandes réellement exécutées.

Cette absence de résultat est volontaire : le wiki ne doit pas transformer une spécification en preuve de fonctionnement.

## Scénarios de tests exigés

La qualification du prototype devra couvrir au minimum :

- types texte, entier, décimal, date, booléen et choix ;
- opérateurs `==`, `!=`, `>`, `>=`, `<`, `<=`, contient, vide, non vide et appartenance ;
- groupes ET / OU ;
- actions afficher/masquer, obligatoire/facultatif, activer/désactiver, warning et error ;
- congé payé : champs spécifiques masqués ;
- événement familial : champs spécifiques visibles et obligatoires ;
- événement familial incomplet : validation invalide ;
- récupération valide : demande inférieure ou égale au solde ;
- récupération excessive : erreur bloquante ;
- absence exceptionnelle : motif obligatoire + avertissement ;
- champ inconnu ;
- valeur absente ou `None` ;
- mauvais type ;
- date invalide ;
- choix inconnu ;
- groupe vide ;
- règle sans action.

## Limites de la première itération

Le prototype ne doit pas encore :

- être intégré aux écrans wx de production ;
- créer l'écran Qt complet de congés ;
- calculer les droits ou compteurs légaux ;
- débiter réellement une banque de récupération ;
- modifier un planning ;
- gérer un workflow complet d'approbation ;
- envoyer des notifications ou emails ;
- stocker les pièces jointes binaires ;
- exposer une API REST ;
- devenir un moteur BPM ;
- intégrer un langage de formules utilisateur ;
- dépendre du futur moteur documentaire.

## Critère de réussite

Le prototype sera considéré comme techniquement démontré lorsque :

1. le core fonctionne sans wx ni Qt ;
2. une définition de formulaire est sérialisable avec des structures simples ;
3. les règles congés/absences sont évaluées de manière déterministe ;
4. les tests unitaires couvrent conditions, groupes, actions et cas limites ;
5. une démonstration headless est exécutable ;
6. les commandes et résultats exacts sont enregistrés ici avec le SHA testé.

## Relation avec les autres chantiers

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

Le FormEngine et le futur moteur documentaire restent deux composants indépendants.

## Liens associés

[[Questionnaires et formulaires conditionnels]] · [[Architecture fonctionnelle]] · [[Évolution documentaire Qt]] · [[Contrats, CCNS et CEE]]
