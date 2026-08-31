# Fondations RH « paie-ready »

**Décision du 31 août 2026**

## Objet

Teamworks-CCNS doit d'abord exécuter correctement et durablement son périmètre RH actuel. Le projet **ne lance pas à ce stade un moteur de paie**, ne produit pas de bulletin natif et ne génère pas de DSN.

En revanche, chaque évolution RH doit éviter de perdre une information qui pourrait devenir utile, plus tard, à la préparation ou au calcul d'un bulletin de paie.

Cette orientation est une **règle d'architecture et de modélisation**, pas une nouvelle roadmap concurrente. `ROADMAP.md` reste la seule roadmap d'exécution et la validation réelle de la version 0.9.1b reste prioritaire sur tout nouveau développement fonctionnel majeur.

## Principe directeur

Lorsqu'une donnée RH est ajoutée ou modifiée, se demander :

> Cette information pourrait-elle être nécessaire pour expliquer, préparer, contrôler ou recalculer une rémunération future ?

Si oui, la donnée doit être conservée de façon suffisamment structurée, datée et traçable pour pouvoir être réutilisée ultérieurement sans reconstruction manuelle de l'historique.

Le but est de rendre Teamworks progressivement **paie-ready**, sans lui imposer aujourd'hui la complexité réglementaire et déclarative d'un logiciel de paie.

## Données à préserver progressivement

### Contrat et situation d'emploi

- nature et régime du contrat ;
- dates de début, fin, renouvellement et avenants ;
- durée contractuelle et organisation du temps ;
- classification, groupe, emploi et positionnement CCNS ;
- période d'essai ;
- ancienneté utile ;
- statut cadre/non-cadre lorsqu'il est nécessaire ;
- conditions particulières ayant un effet possible sur la rémunération.

### Rémunération contractuelle

- salaire ou taux contractuel ;
- unité de référence ;
- date d'effet ;
- primes régulières ;
- éléments forfaitaires ;
- avantages en nature ;
- indemnités prévues au contrat ou par une règle applicable ;
- historique des changements et motif lorsqu'il est connu.

Une valeur de rémunération qui doit être historisée ne doit pas être modélisée uniquement comme un champ courant écrasant la valeur précédente.

### Temps et activité

- temps contractuel ;
- temps réellement réalisé lorsqu'il est disponible ;
- heures complémentaires et supplémentaires ;
- travail les jours particuliers ;
- temps de préparation ;
- déplacements et trajets professionnels lorsque leur qualification est pertinente ;
- repos et récupérations ;
- modulation, intermittence et compteurs individuels ;
- affectations lorsque celles-ci déterminent la nature ou la valorisation du temps.

### Congés et absences

Les absences doivent être qualifiées plutôt que stockées comme de simples journées indisponibles :

- congés payés ;
- maladie ;
- accident du travail / maladie professionnelle ;
- maternité, paternité, adoption ;
- congé sans solde ;
- événement familial ;
- formation ;
- absence autorisée ;
- autres natures nécessitant une distinction métier.

Lorsque pertinent, conserver dates, durée, unité, justificatif, statut de traitement et origine de l'information.

### Protection sociale et organismes

Teamworks doit pouvoir conserver progressivement, lorsqu'elles sont utiles au fonctionnement RH :

- affiliation ou dispense de mutuelle ;
- régime de prévoyance ;
- caisse ou organisme de retraite complémentaire ;
- service de prévention et de santé au travail ;
- OPCO ;
- organisme ou portail social concerné ;
- références de contrat ou d'adhésion ;
- dates d'effet et de fin ;
- justificatifs ;
- statut d'une démarche ou d'une affiliation.

Ces informations doivent rester multi-structures et ne contenir aucune donnée PMSL codée en dur.

## Connexions RH externes

La future couche « Connexions RH » doit être conçue comme un registre générique de connecteurs et non comme une série d'automatismes spécifiques dispersés dans les écrans.

Organismes potentiellement concernés :

- URSSAF ;
- Net-entreprises ;
- mutuelle ;
- prévoyance ;
- retraite complémentaire ;
- OPCO ;
- service de prévention et de santé au travail ;
- France Travail ;
- autres organismes selon les besoins des structures utilisatrices.

Un connecteur peut offrir différents niveaux de capacité sans supposer qu'une API existe :

1. référentiel, échéance et lien vers le portail ;
2. import/export de fichiers ;
3. échange par API officielle ;
4. synchronisation de statuts et retours lorsque le service le permet.

Les mots de passe, secrets, jetons et certificats ne doivent jamais être enregistrés en clair dans les données métier.

## Éléments variables de rémunération

Teamworks pourra, lorsque les besoins RH le justifieront, introduire un objet générique d'**élément variable de rémunération** sans pour autant calculer une paie.

Le concept devra pouvoir porter au minimum :

- salarié ;
- période ;
- type ;
- quantité ;
- unité ;
- montant ou taux éventuel ;
- date d'effet ;
- source ;
- justificatif éventuel ;
- commentaire ;
- statut de validation.

Exemples possibles : heures complémentaires, prime exceptionnelle, indemnité, frais kilométriques, avantage en nature ou absence ayant un impact sur la préparation de paie.

**Aucune table ou abstraction ne doit être ajoutée uniquement pour anticiper la paie** : on introduit ces objets lorsqu'un besoin RH réel les rend utiles, en veillant simplement à ce que leur forme soit réutilisable plus tard.

## Traçabilité minimale

Pour les données susceptibles d'avoir un effet sur la rémunération, privilégier selon le besoin :

- date d'effet ;
- date de fin ;
- source ;
- auteur ou origine technique ;
- date de création/modification ;
- justificatif associé ;
- état ou statut ;
- historique des modifications sensibles.

Une donnée calculée doit rester distinguable de la donnée saisie ou importée qui lui sert de source.

## Règles réglementaires

Les taux, seuils et règles susceptibles d'évoluer ne doivent pas être codés en dur dans les interfaces.

Lorsqu'une règle métier est ajoutée, conserver autant que possible :

- identifiant stable ;
- source ;
- date d'effet ;
- population concernée ;
- paramètres ;
- version ;
- tests associés.

Cette discipline est déjà cohérente avec le moteur CCNS et doit être maintenue pour toute donnée qui pourrait un jour alimenter un calcul de paie.

## Ce qui n'est pas lancé maintenant

Cette orientation **n'autorise pas**, à elle seule :

- un moteur de calcul du brut au net ;
- le calcul natif des cotisations sociales ;
- la production d'un bulletin de paie Teamworks ;
- la génération d'une DSN ;
- le dépôt automatisé sur Net-entreprises ;
- le remplacement du tiers ou logiciel de paie actuel.

Ces sujets feront l'objet d'une décision ultérieure distincte.

## Conditions avant une éventuelle paie native

Une décision de construire la paie native ne devra être envisagée qu'après :

1. stabilisation et usage réel satisfaisant des fonctions RH existantes ;
2. validation de la qualité et de l'historisation des données nécessaires ;
3. couverture suffisante des règles CCNS pertinentes ;
4. capacité à exporter ou comparer les variables avec la paie de référence ;
5. essais parallèles sur plusieurs périodes et plusieurs profils de salariés ;
6. absence d'écarts inexpliqués sur les montants et bases comparés ;
7. étude spécifique du déclaratif social, de la DSN et de la maintenance réglementaire.

Jusqu'à cette décision, Teamworks reste un **logiciel RH qui se prépare correctement à une éventuelle paie**, et non un logiciel de paie inachevé.
