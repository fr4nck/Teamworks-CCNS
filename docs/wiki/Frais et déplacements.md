# Frais et déplacements

<a id="frais-entrees"></a>
## À quoi ça sert ?

Teamworks-CCNS wx enregistre des **déplacements** et des **remboursements** associés à une personne. Le module calcule un montant kilométrique à partir de la distance et du tarif saisis.

## Où les trouver ?

- **Individus > fiche > Frais** : deux blocs **Déplacements** et **Remboursements** pour la personne ;
- **Outils > Gestion des frais de déplacements** : voie globale prévue par l’application.

## Déplacements

Le dialogue de saisie contient :

- date ;
- personne/utilisateur ;
- objet du déplacement ;
- ville/code postal de départ ;
- ville/code postal d’arrivée ;
- distance en kilomètres ;
- option aller/retour ;
- tarif du kilomètre ;
- montant calculé ;
- remboursement associé, s’il existe.

Lorsque Teamworks connaît déjà une distance entre deux villes, il peut la reprendre. Le nouvel enregistrement peut aussi reprendre le dernier tarif kilométrique utilisé. Cocher **aller/retour** ajuste la distance et recalcule le montant.

## Remboursements

Un remboursement contient une date, une personne et un montant. Le dialogue présente les déplacements rattachables et permet d’associer les déplacements concernés au remboursement.

Dans la fiche individuelle, les deux listes proposent **Ajouter**, **Modifier** et **Supprimer**. Les déplacements proposent également **Imprimer**.

<a id="frais-calcul"></a>
## Ce que Teamworks calcule

Le montant kilométrique du déplacement est calculé à partir de :

```text
distance × tarif du kilomètre
```

Le calcul tient compte de la distance affichée après application éventuelle de l’aller/retour. Le code valide que distance, tarif et montant sont des nombres utilisables.

<a id="frais-verifier"></a>
## Ce que l’utilisateur doit encore vérifier

- que la distance utilisée correspond bien au trajet réel ;
- que l’aller/retour est correctement indiqué ;
- que le tarif kilométrique saisi est celui que votre organisation souhaite appliquer ;
- que le montant de remboursement saisi correspond aux déplacements rattachés ;
- les justificatifs et règles comptables/URSSAF applicables hors de Teamworks.

Le code audité ne montre pas de workflow de justificatif comptable ni de déclaration URSSAF automatique. Le wiki n’en invente donc pas.

## Exports et documents

L’impression des déplacements est confirmée. Aucun contexte générique `frais` ou `deplacement` n’existe dans le moteur de publipostage audité ; ne supposez pas l’existence de balises de frais.

**À confirmer en recette fonctionnelle :** forme exacte de l’impression globale et comportement des rattachements complexes de remboursements.

## Problèmes fréquents

- **Montant nul/inattendu :** vérifier distance, aller/retour et tarif.
- **Distance non préremplie :** le couple départ/arrivée peut ne pas exister dans les distances connues ; saisir et vérifier manuellement.
- **Remboursement sans déplacement attendu :** vérifier la personne et les déplacements déjà rattachés.

## Liens associés

[[Individus et fiches]] · [[Problèmes fréquents]] · [[Sauvegardes et restauration]]
