# FormEngine et questionnaires

## Ce qui est réellement disponible : le module Questionnaire wx

Teamworks-CCNS embarque un module de **questionnaires configurables** hérité de Noethys, fonctionnel et testé (`teamworks/Ctrl/CTRL_Questionnaire.py`, `CTRL_Page_questionnaire.py`, accessible aussi via **Paramétrage > Questionnaire**). Il gère des questions typées (ligne de texte, bloc de texte, entier, liste déroulante, liste à cocher, case à cocher, date, réglette, document) et leurs réponses par individu, affichées dans l'onglet **Questionnaire** de la fiche — voir [Individus et fiches](../utilisation/individus.md#onglets-fiche).

!!! info "Formulaire statique, pas conditionnel"
    Ce module affiche toujours les mêmes champs : il n'existe **aucune logique conditionnelle** (afficher/masquer/rendre obligatoire un champ selon une autre réponse) dans le code actuel.

## Le chantier à l'étude : formulaires conditionnels

!!! danger "Prévu / à l'étude — aucun code"
    Aucune trace de code n'existe pour un moteur de règles conditionnelles. Cette section décrit une réflexion de conception, pas un développement en cours.

L'idée est d'ajouter, au-dessus du module Questionnaire existant, un moteur capable d'évaluer des règles indépendamment de wx/Qt et sans accès SQL direct :

```text
Définition du formulaire + Réponses + Contexte métier
        ↓
   Conditions (ET / OU)
        ↓
   Actions déclaratives (afficher, masquer, rendre obligatoire, activer, désactiver,
                          valeur par défaut, avertissement, erreur bloquante)
        ↓
   État du formulaire + validations
```

Le cas d'usage pilote envisagé est la **demande de congé/absence** : des champs supplémentaires (justificatif, type d'événement, quantité demandée...) apparaîtraient et deviendraient obligatoires selon le type d'absence choisi, avec un contrôle simple (ex. quantité demandée ne dépassant pas un solde fourni par le contexte métier). Ce moteur n'aurait pas vocation à calculer les droits légaux, gérer un workflow d'approbation complet ou remplacer une base RH — les calculs métier resteraient dans Teamworks, fournis au formulaire via son contexte.

Concepts de conception évoqués (non figés, à valider par un prototype s'il démarre un jour) : `FormDefinition`, `FormField`, `FieldType`, `FormResponse`, `FormContext`, `Condition`, `ConditionGroup`, `Rule`, `Action`, `EvaluationResult`.

## FormEngine : nom donné à un prototype de preuve de faisabilité

!!! danger "Non démarré"
    Un document de cadrage nommé « FormEngine » décrit une première preuve de faisabilité technique pour ce moteur conditionnel. **Aucun commit ni branche contenant ce prototype n'existe dans ce dépôt** — recherche exhaustive négative pour toute trace de code (`FormEngine`, `FormDefinition`, `FormResponse`...). Ce cahier des charges détaille des types de champs visés, des opérateurs de condition, des actions déclaratives et un scénario de test complet pour le cas « congés/absences », mais **aucune ligne de code n'a été livrée** : ne présentez ce chantier ni comme disponible, ni comme expérimental, ni même comme un prototype en cours — c'est une spécification, rien de plus, à ce jour.

## Relation avec le futur moteur documentaire

Les deux chantiers (FormEngine et [trajectoire Qt](qt.md)/moteur documentaire) resteraient indépendants l'un de l'autre :

```text
FormEngine → données validées → Teamworks métier → MergeContext → moteur documentaire
```

Un formulaire pourrait ainsi préparer ou valider des données réutilisées ensuite dans un contrat, une attestation ou un courrier, sans dépendance directe entre les deux moteurs.

## Voir aussi

[Individus et fiches](../utilisation/individus.md) · [Trajectoire Qt](qt.md) · [Architecture — vue d'ensemble](vue-ensemble.md) · [Contrats, CCNS et CEE](../utilisation/contrats-ccns-cee.md)
