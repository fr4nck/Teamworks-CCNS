# Recrutement

**Recrutement** est un onglet principal de Teamworks-CCNS wx. La fiche individuelle possède également un onglet Recrutement pour les candidatures reliées à une personne.

## Candidat et candidature : deux objets distincts

Le moteur de publipostage confirme deux contextes séparés :

- **candidat** — identité/coordonnées du candidat, qualifications et mémo ;
- **candidature** — dépôt, offre, disponibilités, fonctions, affectations, décision et réponse.

Une candidature peut être encore rattachée au candidat ou déjà rattachée à une personne Teamworks.

## Ce qui change après liaison à une personne

Pour un document **Candidature** :

- si `IDpersonne` est absent/0, Teamworks charge les données du candidat ;
- si une personne est liée, Teamworks charge les données de la personne à la place ;
- les 9 données propres à la candidature sont ensuite ajoutées dans les deux cas.

Conséquence : `{QUALIFICATIONS}` et `{MEMO}` du candidat ne sont pas automatiquement repris après liaison à une personne, tandis que les champs propres à la personne comme `{NUMSECU}` deviennent disponibles lorsqu’elle est liée.

## Mots-clés de publipostage liés au recrutement

Principales balises :

- [`{NOM}`](Mots-clés-de-publipostage#publipostage-nom)
- [`{PRENOM}`](Mots-clés-de-publipostage#publipostage-prenom)
- [`{QUALIFICATIONS}`](Mots-clés-de-publipostage#publipostage-qualifications)
- [`{MEMO}`](Mots-clés-de-publipostage#publipostage-memo)
- [`{DATEDEPOT}`](Mots-clés-de-publipostage#publipostage-datedepot)
- [`{TYPEDEPOT}`](Mots-clés-de-publipostage#publipostage-typedepot)
- [`{OFFREDEMPLOI}`](Mots-clés-de-publipostage#publipostage-offredemploi)
- [`{DISPONIBILITES}`](Mots-clés-de-publipostage#publipostage-disponibilites)
- [`{FONCTIONS}`](Mots-clés-de-publipostage#publipostage-fonctions)
- [`{DECISION}`](Mots-clés-de-publipostage#publipostage-decision)

Voir [[Mots-clés de publipostage]] pour le tableau exact Candidat/Candidature et les conditions de chaque balise.

## Disponibilités et décision

`{DISPONIBILITES}` assemble les périodes sous la forme « du … au … ». `{DECISION}` traduit la valeur enregistrée en **Décision non prise**, **Oui** ou **Non**. Les champs de réponse ne sont remplis que lorsqu’une réponse est effectivement enregistrée.

## Offre d’emploi

`{OFFREDEMPLOI}` contient l’intitulé de l’offre liée. Sans offre, la valeur devient **Candidature spontanée**.

Le moteur contient aussi une fonction auxiliaire qui sait lire le détail et les dates d’une offre, mais ces noms `OFFRE_*` ne sont pas ajoutés au contexte générique Candidature actuel : ils ne sont donc pas documentés comme balises disponibles.

## À documenter après validation fonctionnelle

Les dialogues de candidat, candidature, emploi et entretien existent dans le code. Le détail clic par clic de toutes les opérations de recrutement doit encore être confirmé par recette interactive avant d’être figé ici.
