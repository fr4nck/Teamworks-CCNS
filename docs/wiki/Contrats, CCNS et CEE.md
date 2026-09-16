# Contrats, CCNS et CEE

Cette page sépare la **gestion du contrat** dans Teamworks des **contrôles métier CCNS/CEE** calculés autour de la rémunération.

## Gestion d’un contrat dans Teamworks

### Où le trouver ?

Ouvrez **Individus**, ouvrez la fiche de la personne puis l’onglet **Contrats**. La liste globale des contrats et les dialogues de création existent également dans l’application wx, mais la fiche individuelle reste le point d’entrée le plus naturel pour garantir que le contrat est rattaché à la bonne personne.

### Données de contrat exposées aux documents

Le moteur actuel lit notamment : personne, classification historique, type de contrat, valeur du point historique, dates, essai, qualification CEE, code de convention, groupe CCNS, durée hebdomadaire et salaire brut mensuel.

Les contrats modernes n’ont plus besoin de renseigner une classification ou une valeur du point historique pour alimenter les nouveaux contrôles ; les anciennes données restent lues pour préserver les modèles historiques.

## Contrôles métier CCNS

Lorsque `CONVENTION` vaut `CCNS`, qu’un groupe est renseigné et que la date de début permet de choisir le barème, Teamworks peut calculer : minimum CCNS, minimum SMIC, minimum retenu et résultat de conformité.

Pour un groupe à minimum annuel, le moteur indique un minimum « annuel » et le statut **Contrôle annuel requis** au lieu de transformer ce cas en contrôle mensuel artificiel.

## CEE

Un contrat est reconnu comme CEE lorsqu’il correspond au type/à l’intitulé CEE géré par le moteur. Si la qualification et la date de référence sont exploitables, Teamworks calcule le minimum journalier légal et recherche le barème CEE applicable. Le résultat de conformité est ensuite exposé aux documents quand le calcul est possible.

## Compatibilité avec les anciens modèles

- [`{BRUTMENS}`](Mots-clés-de-publipostage#publipostage-brutmens) contient la même valeur que [`{SALAIREBRUTMENSUEL}`](Mots-clés-de-publipostage#publipostage-salairebrutmensuel) ; préférez `{SALAIREBRUTMENSUEL}` dans les nouveaux modèles.
- `{CLASSIFICATION}` reste alimenté : classification historique si elle existe, sinon groupe CCNS, sinon qualification CEE.
- `{VALEURPOINT}` reste prévu pour les contrats historiques qui référencent une valeur du point.

## Mots-clés de publipostage liés aux contrats

Un document de contrat reçoit **les données de l’individu associé**, puis les données du contrat. Vous pouvez donc utiliser à la fois `{NOM}` et `{DATEDEBUT}`.

Principales balises :

- [`{DATEDEBUT}`](Mots-clés-de-publipostage#publipostage-datedebut)
- [`{DATEFIN}`](Mots-clés-de-publipostage#publipostage-datefin)
- [`{TYPECONTRAT}`](Mots-clés-de-publipostage#publipostage-typecontrat)
- [`{CONVENTION}`](Mots-clés-de-publipostage#publipostage-convention)
- [`{GROUPECCNS}`](Mots-clés-de-publipostage#publipostage-groupeccns)
- [`{QUALIFICATIONCEE}`](Mots-clés-de-publipostage#publipostage-qualificationcee)
- [`{DUREEHEBDO}`](Mots-clés-de-publipostage#publipostage-dureehebdo)
- [`{SALAIREBRUTMENSUEL}`](Mots-clés-de-publipostage#publipostage-salairebrutmensuel)
- [`{MINIMUMRETENU}`](Mots-clés-de-publipostage#publipostage-minimumretenu)
- [`{CONFORMITEREMUNERATION}`](Mots-clés-de-publipostage#publipostage-conformiteremuneration)

Voir [[Mots-clés de publipostage]] pour les 18 balises Contrat, les 18 balises Individu héritées, les champs personnalisés et les règles de calcul.

## Documents de contrat

L’assistant de publipostage peut travailler avec Teamword, Word ou Writer, puis sauvegarder, imprimer et prévisualiser selon les options choisies. Voir [[Publipostage et documents]] et [[Éditeur interne et documents]].

## Points d’attention

- Une balise calculée vide ne signifie pas forcément un bug : vérifiez la convention, le groupe/qualification, les heures, le salaire et la date de début.
- N’utilisez pas un ancien modèle avec `{BRUTMENS}` comme preuve que ce nom est le nom moderne recommandé.
- Les champs personnalisés de contrat sont définis par le dossier et ne peuvent pas être listés de façon universelle dans ce wiki.
