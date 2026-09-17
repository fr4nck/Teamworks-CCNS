# Publipostage et modèles de documents

Teamworks construit les données de publipostage en fonction du type d'objet sélectionné. Dans l'éditeur Teamword, un mot-clé est utilisé comme jeton entre accolades, par exemple `{NOM}`.

## Documents liés à une personne

Utiliser les [mots-clés personne](../reference/mots-cles-publipostage.md#mots-cles-personne).

Ils couvrent notamment l'identité, la naissance, les coordonnées et la situation du salarié.

## Documents liés à un contrat

Un document de catégorie `contrat` reçoit à la fois :

- les [mots-clés personne](../reference/mots-cles-publipostage.md#mots-cles-personne) ;
- les [mots-clés contrat](../reference/mots-cles-publipostage.md#mots-cles-contrat).

Les champs CCNS/CEE ajoutés au moteur actuel sont donc disponibles dans les modèles de contrat lorsqu'ils peuvent être calculés ou renseignés.

## Documents liés à un candidat

Utiliser les [mots-clés candidat](../reference/mots-cles-publipostage.md#mots-cles-candidat).

## Documents liés à une candidature

Une candidature reçoit les [mots-clés candidature](../reference/mots-cles-publipostage.md#mots-cles-candidature), auxquels Teamworks ajoute :

- les mots-clés de la personne si la candidature est déjà liée à une personne ;
- sinon les mots-clés du candidat.

Cette différence est importante pour les modèles utilisés avant et après l'intégration d'un candidat comme salarié.

## Champs personnalisés

Teamworks permet d'ajouter des [champs personnalisés](../reference/mots-cles-publipostage.md#champs-personnalises) par catégorie.

Un mot-clé personnalisé doit être unique et ne contenir que des lettres ou chiffres en majuscules. Les espaces, accents, symboles et doublons avec les mots-clés de base sont refusés par l'éditeur.

## Contrat cible moderne

La modernisation documentaire introduit aussi des espaces de noms canoniques `STRUCTURE_*`, `SALARIE_*` et `CONTRAT_*`. Le [catalogue canonique actuellement garanti](../reference/mots-cles-publipostage.md#mots-cles-canoniques-modernes) est distinct du catalogue historique et doit être étendu progressivement sans casser les anciens modèles.

La décision d'architecture complète est décrite dans [Documents RH, Structure et publipostage](../09_DOCUMENTS_RH_STRUCTURE_PUBLIPOSTAGE.md).
