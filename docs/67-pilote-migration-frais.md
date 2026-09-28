# Pilote de migration — Frais / remboursements

## 1. Périmètre source

Le pilote couvre uniquement les données nécessaires au domaine Frais :

- `personnes` : uniquement comme référentiel d'existence pour `IDpersonne` ;
- `deplacements` : source des trajets et source canonique du rattachement à un remboursement ;
- `remboursements` : parent financier et date de paiement ;
- `remboursements.listeIDdeplacement` : miroir historique à auditer, jamais source canonique si elle contredit `deplacements.IDremboursement`.

Le cache historique `distances` est hors périmètre. Il est recalculable et, s'il est rencontré dans un inventaire global, il devra être explicitement classé IGNORED avec une raison stable.

## 2. Champs source inclus

### deplacements

- IDdeplacement
- IDpersonne
- date
- objet
- cp_depart
- ville_depart
- cp_arrivee
- ville_arrivee
- distance
- aller_retour
- tarif_km
- IDremboursement

### remboursements

- IDremboursement
- IDpersonne
- date
- montant
- listeIDdeplacement

### personnes

- IDpersonne uniquement pour contrôler les références du pilote.

## 3. Normalisations admises

Les transformations suivantes sont prévues et doivent être journalisées :

- `IDremboursement` égal à 0 ou NULL devient absence de rattachement canonique ;
- dates texte valides deviennent un vrai type date ;
- `distance`, `tarif_km` et `montant` deviennent des décimaux canoniques ;
- `aller_retour` historique (`True`/`False`, 1/0 si rencontré) devient booléen ;
- codes postaux sont conservés comme texte pour préserver les zéros initiaux ;
- `listeIDdeplacement` est remplacée dans le nouveau modèle par une relation structurée calculée depuis `deplacements.IDremboursement`.

Aucune autre correction silencieuse n'est admise.

## 4. Hors périmètre du pilote

- géocodage et calcul automatique de distances ;
- cache `distances` ;
- UI wx ou Qt ;
- choix PostgreSQL/MariaDB ;
- conversion des autres domaines Noethys ;
- correction automatique d'une incohérence de personne entre déplacement et remboursement.

## 5. Vérité canonique du rattachement

Pour le pilote, la relation canonique est :

`deplacements.IDremboursement -> remboursements.IDremboursement`

Le champ `remboursements.listeIDdeplacement` est contrôlé contre cette relation.

Trois cas :

1. miroir identique à la relation canonique : MIGRATED ;
2. miroir différent mais relation canonique complète et non ambiguë : TRANSFORMED avec raison `LEGACY_TRIP_LIST_REBUILT_FROM_CANONICAL_ASSIGNMENTS` ;
3. contradiction impossible à résoudre sans interprétation humaine : REJECTED.

## 6. Contrôles structurels bloquants

- nombre de déplacements source = nombre de déplacements expliqués ;
- nombre de remboursements source = nombre de remboursements expliqués ;
- unicité de `IDdeplacement` ;
- unicité de `IDremboursement` ;
- toute `IDpersonne` utilisée par Frais existe dans `personnes` ;
- tout `IDremboursement` non nul/non zéro d'un déplacement existe ;
- aucune identité source n'est migrée deux fois.

## 7. Contrôles relationnels bloquants

- un déplacement appartient à une seule personne ;
- un remboursement appartient à une seule personne ;
- si un déplacement référence un remboursement, les deux `IDpersonne` doivent être identiques ;
- aucune relation destination ne doit pointer vers un objet absent ;
- un déplacement ne peut appartenir qu'à un seul remboursement destination.

## 8. Contrôles de valeur bloquants

Pour chaque déplacement :

- date identique après normalisation ;
- objet identique après normalisation autorisée ;
- code postal de départ identique comme texte ;
- ville de départ identique ;
- code postal d'arrivée identique comme texte ;
- ville d'arrivée identique ;
- distance numériquement identique ;
- aller/retour sémantiquement identique ;
- tarif kilométrique numériquement identique ;
- état libre/rattaché identique ;
- si rattaché, même remboursement logique.

Pour chaque remboursement :

- date identique ;
- montant exact au centime ;
- même personne ;
- même ensemble canonique de déplacements après reconstruction.

## 9. Agrégats obligatoires

Les métriques suivantes doivent être identiques source/destination :

- `TRIP_COUNT` ;
- `REIMBURSEMENT_COUNT` ;
- `FREE_TRIP_COUNT` ;
- `ATTACHED_TRIP_COUNT` ;
- `REIMBURSEMENT_TOTAL_CENTS` ;
- nombre de déplacements par personne ;
- nombre de remboursements par personne ;
- nombre de déplacements par remboursement ;
- date minimale/maximale des déplacements si la source n'est pas vide ;
- date minimale/maximale des remboursements si la source n'est pas vide.

La somme des remboursements est comparée en centimes entiers. Tolérance : zéro centime.

## 10. Contrôles du miroir listeIDdeplacement

Pour chaque remboursement, on compare :

- ensemble miroir = IDs parsés depuis `listeIDdeplacement` ;
- ensemble canonique = déplacements dont `IDremboursement` pointe vers le remboursement.

Le rapport doit compter :

- miroirs identiques ;
- IDs présents uniquement dans le miroir ;
- IDs présents uniquement dans la relation canonique ;
- IDs du miroir inexistants ;
- IDs du miroir appartenant à une autre personne.

Un écart n'est jamais effacé. Il devient une transformation documentée ou un rejet.

## 11. Cas explicitement testés par le pilote

- déplacement libre avec `IDremboursement = 0` ;
- déplacement libre avec `IDremboursement = NULL` ;
- déplacement rattaché ;
- code postal commençant par zéro ;
- remboursement sans déplacement ;
- remboursement avec plusieurs déplacements ;
- miroir historique vide ;
- miroir historique cohérent ;
- miroir historique divergent mais reconstructible ;
- remboursement orphelin ;
- déplacement pointant vers remboursement inexistant ;
- déplacement et remboursement de personnes différentes ;
- doublon d'identifiant source ;
- montant nul ;
- valeurs financières avec décimales.

## 12. Critère de succès du pilote

Le pilote est validé seulement si :

- zéro ligne Frais inexpliquée ;
- zéro REJECTED ;
- zéro relation orpheline ;
- zéro conflit de personne ;
- zéro centime d'écart sur le total des remboursements ;
- toutes les transformations du miroir historique sont journalisées ;
- un second import du même snapshot produit le même résultat sans doublon.

Le pilote ne prouve pas encore la migration complète de Noethys. Il prouve que la méthode de conversion, de traçabilité et de réconciliation est suffisamment solide pour être étendue domaine par domaine.