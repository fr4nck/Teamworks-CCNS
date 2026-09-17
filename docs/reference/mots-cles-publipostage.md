# Référence des mots-clés de publipostage

Cette page décrit le catalogue réellement exposé par le moteur actuel de Teamworks.

**Source de vérité du catalogue historique :** `teamworks/Utils/UTILS_Publipostage_donnees.py`.

Le moteur expose actuellement **46 mots-clés de base distincts**. Les champs personnalisés définis dans la base peuvent en ajouter d'autres.

Dans Teamword, les jetons sont insérés entre accolades, par exemple `{NOM}`.

## Matrice des contextes

| Catégorie de document | Données disponibles |
|---|---|
| `personne` | [mots-clés personne](#mots-cles-personne) |
| `contrat` | [mots-clés personne](#mots-cles-personne) + [mots-clés contrat](#mots-cles-contrat) |
| `candidat` | [mots-clés candidat](#mots-cles-candidat) |
| `candidature` | [mots-clés candidature](#mots-cles-candidature) + personne si liée, sinon candidat |

`candidature*` dans le tableau détaillé signifie donc « disponible dans une candidature selon que celle-ci est liée à une personne ou repose encore sur le candidat ».

## Catalogue détaillé

Chaque entrée possède une ancre stable de la forme `#mot-cle-nom`, afin qu'une autre page du manuel puisse pointer directement vers le mot-clé concerné.

| Mot-clé | Signification | Utilisable dans |
|---|---|---|
|<a id="mot-cle-adresseresid"></a>`ADRESSERESID`|Adresse de résidence|personne, contrat, candidature*, candidat|
|<a id="mot-cle-affectations"></a>`AFFECTATIONS`|Affectations|candidature|
|<a id="mot-cle-age"></a>`AGE`|Âge|personne, contrat, candidature*, candidat|
|<a id="mot-cle-baremecee"></a>`BAREMECEE`|Barème CEE|contrat|
|<a id="mot-cle-civilite"></a>`CIVILITE`|Civilité|personne, contrat, candidature*, candidat|
|<a id="mot-cle-classification"></a>`CLASSIFICATION`|Classification|contrat|
|<a id="mot-cle-conformiteremuneration"></a>`CONFORMITEREMUNERATION`|Résultat du contrôle de rémunération|contrat|
|<a id="mot-cle-convention"></a>`CONVENTION`|Convention collective|contrat|
|<a id="mot-cle-cpnaiss"></a>`CPNAISS`|Code postal de naissance|personne, contrat, candidature*|
|<a id="mot-cle-cpresid"></a>`CPRESID`|Code postal de résidence|personne, contrat, candidature*, candidat|
|<a id="mot-cle-datedebut"></a>`DATEDEBUT`|Date de début du contrat|contrat|
|<a id="mot-cle-datedepot"></a>`DATEDEPOT`|Date de dépôt de la candidature|candidature|
|<a id="mot-cle-datefin"></a>`DATEFIN`|Date de fin du contrat|contrat|
|<a id="mot-cle-datenaiss"></a>`DATENAISS`|Date de naissance|personne, contrat, candidature*, candidat|
|<a id="mot-cle-datereponse"></a>`DATEREPONSE`|Date de réponse|candidature|
|<a id="mot-cle-decision"></a>`DECISION`|Décision|candidature|
|<a id="mot-cle-disponibilites"></a>`DISPONIBILITES`|Disponibilités|candidature|
|<a id="mot-cle-dureehebdo"></a>`DUREEHEBDO`|Durée hebdomadaire|contrat|
|<a id="mot-cle-emails"></a>`EMAILS`|Adresses e-mail|personne, contrat, candidature*, candidat|
|<a id="mot-cle-essai"></a>`ESSAI`|Période d'essai|contrat|
|<a id="mot-cle-fax"></a>`FAX`|Fax|personne, contrat, candidature*, candidat|
|<a id="mot-cle-fonctions"></a>`FONCTIONS`|Fonctions|candidature|
|<a id="mot-cle-groupeccns"></a>`GROUPECCNS`|Groupe CCNS|contrat|
|<a id="mot-cle-memo"></a>`MEMO`|Mémo candidat|candidat, candidature*|
|<a id="mot-cle-minimumccns"></a>`MINIMUMCCNS`|Minimum conventionnel CCNS|contrat|
|<a id="mot-cle-minimumcee"></a>`MINIMUMCEE`|Minimum légal CEE|contrat|
|<a id="mot-cle-minimumretenu"></a>`MINIMUMRETENU`|Minimum finalement retenu|contrat|
|<a id="mot-cle-minimumsmic"></a>`MINIMUMSMIC`|Minimum issu du SMIC|contrat|
|<a id="mot-cle-nationalite"></a>`NATIONALITE`|Nationalité|personne, contrat, candidature*|
|<a id="mot-cle-nom"></a>`NOM`|Nom|personne, contrat, candidature*, candidat|
|<a id="mot-cle-nomjfille"></a>`NOMJFILLE`|Nom de naissance|personne, contrat, candidature*|
|<a id="mot-cle-numsecu"></a>`NUMSECU`|Numéro de sécurité sociale|personne, contrat, candidature*|
|<a id="mot-cle-offredemploi"></a>`OFFREDEMPLOI`|Offre d'emploi|candidature|
|<a id="mot-cle-paysnaiss"></a>`PAYSNAISS`|Pays de naissance|personne, contrat, candidature*|
|<a id="mot-cle-prenom"></a>`PRENOM`|Prénom|personne, contrat, candidature*, candidat|
|<a id="mot-cle-qualificationcee"></a>`QUALIFICATIONCEE`|Qualification CEE|contrat|
|<a id="mot-cle-qualifications"></a>`QUALIFICATIONS`|Qualifications du candidat|candidat, candidature*|
|<a id="mot-cle-salairebrutmensuel"></a>`SALAIREBRUTMENSUEL`|Salaire brut mensuel|contrat|
|<a id="mot-cle-situation"></a>`SITUATION`|Situation|personne, contrat, candidature*|
|<a id="mot-cle-telephones"></a>`TELEPHONES`|Téléphones|personne, contrat, candidature*, candidat|
|<a id="mot-cle-typecontrat"></a>`TYPECONTRAT`|Type de contrat|contrat|
|<a id="mot-cle-typedepot"></a>`TYPEDEPOT`|Type de dépôt|candidature|
|<a id="mot-cle-typereponse"></a>`TYPEREPONSE`|Type de réponse|candidature|
|<a id="mot-cle-valeurpoint"></a>`VALEURPOINT`|Valeur du point|contrat|
|<a id="mot-cle-villenaiss"></a>`VILLENAISS`|Ville de naissance|personne, contrat, candidature*|
|<a id="mot-cle-villeresid"></a>`VILLERESID`|Ville de résidence|personne, contrat, candidature*, candidat|

## Mots-clés personne

- [`CIVILITE`](#mot-cle-civilite)
- [`NOM`](#mot-cle-nom)
- [`NOMJFILLE`](#mot-cle-nomjfille)
- [`PRENOM`](#mot-cle-prenom)
- [`DATENAISS`](#mot-cle-datenaiss)
- [`AGE`](#mot-cle-age)
- [`CPNAISS`](#mot-cle-cpnaiss)
- [`VILLENAISS`](#mot-cle-villenaiss)
- [`NATIONALITE`](#mot-cle-nationalite)
- [`PAYSNAISS`](#mot-cle-paysnaiss)
- [`NUMSECU`](#mot-cle-numsecu)
- [`ADRESSERESID`](#mot-cle-adresseresid)
- [`CPRESID`](#mot-cle-cpresid)
- [`VILLERESID`](#mot-cle-villeresid)
- [`SITUATION`](#mot-cle-situation)
- [`TELEPHONES`](#mot-cle-telephones)
- [`FAX`](#mot-cle-fax)
- [`EMAILS`](#mot-cle-emails)

## Mots-clés contrat

Un document `contrat` reçoit aussi tous les [mots-clés personne](#mots-cles-personne).

- [`DATEDEBUT`](#mot-cle-datedebut)
- [`DATEFIN`](#mot-cle-datefin)
- [`ESSAI`](#mot-cle-essai)
- [`CLASSIFICATION`](#mot-cle-classification)
- [`TYPECONTRAT`](#mot-cle-typecontrat)
- [`VALEURPOINT`](#mot-cle-valeurpoint)
- [`CONVENTION`](#mot-cle-convention)
- [`GROUPECCNS`](#mot-cle-groupeccns)
- [`QUALIFICATIONCEE`](#mot-cle-qualificationcee)
- [`DUREEHEBDO`](#mot-cle-dureehebdo)
- [`SALAIREBRUTMENSUEL`](#mot-cle-salairebrutmensuel)
- [`MINIMUMCCNS`](#mot-cle-minimumccns)
- [`MINIMUMSMIC`](#mot-cle-minimumsmic)
- [`MINIMUMRETENU`](#mot-cle-minimumretenu)
- [`CONFORMITEREMUNERATION`](#mot-cle-conformiteremuneration)
- [`BAREMECEE`](#mot-cle-baremecee)
- [`MINIMUMCEE`](#mot-cle-minimumcee)

## Mots-clés candidat

- [`CIVILITE`](#mot-cle-civilite)
- [`NOM`](#mot-cle-nom)
- [`PRENOM`](#mot-cle-prenom)
- [`ADRESSERESID`](#mot-cle-adresseresid)
- [`VILLERESID`](#mot-cle-villeresid)
- [`MEMO`](#mot-cle-memo)
- [`CPRESID`](#mot-cle-cpresid)
- [`DATENAISS`](#mot-cle-datenaiss)
- [`AGE`](#mot-cle-age)
- [`QUALIFICATIONS`](#mot-cle-qualifications)
- [`TELEPHONES`](#mot-cle-telephones)
- [`FAX`](#mot-cle-fax)
- [`EMAILS`](#mot-cle-emails)

## Mots-clés candidature

Une candidature reçoit ces mots-clés propres, plus les données personne ou candidat selon son rattachement.

- [`DATEDEPOT`](#mot-cle-datedepot)
- [`TYPEDEPOT`](#mot-cle-typedepot)
- [`OFFREDEMPLOI`](#mot-cle-offredemploi)
- [`DISPONIBILITES`](#mot-cle-disponibilites)
- [`FONCTIONS`](#mot-cle-fonctions)
- [`AFFECTATIONS`](#mot-cle-affectations)
- [`DECISION`](#mot-cle-decision)
- [`DATEREPONSE`](#mot-cle-datereponse)
- [`TYPEREPONSE`](#mot-cle-typereponse)

## Champs personnalisés

Les champs personnalisés sont enregistrés dans `publipostage_champs` et rattachés à une catégorie.

Règles actuellement imposées par l'éditeur :

- mot-clé obligatoire ;
- majuscules ;
- uniquement lettres `A-Z` et chiffres `0-9` ;
- aucun espace, accent ou symbole ;
- unicité dans la catégorie ;
- interdiction d'entrer en collision avec un mot-clé de base proposé au même endroit.

Comme ces champs dépendent de la base utilisée, ils ne peuvent pas être énumérés statiquement dans ce document.

## Mots-clés canoniques modernes

Le domaine documentaire moderne construit aussi un contexte avec préfixes :

- `STRUCTURE_*` ;
- `SALARIE_*` ;
- `CONTRAT_*`.

Le catalogue RH actuel garantit au minimum les clés requises suivantes :

- [`STRUCTURE_RAISON_SOCIALE`](#structure-raison-sociale) ;
- [`STRUCTURE_ADRESSE`](#structure-adresse) ;
- [`SALARIE_NOM`](#salarie-nom) ;
- [`SALARIE_PRENOM`](#salarie-prenom) ;
- [`CONTRAT_DATE_DEBUT`](#contrat-date-debut).

<a id="structure-raison-sociale"></a>
### `STRUCTURE_RAISON_SOCIALE`

Raison sociale de la structure employeur.

<a id="structure-adresse"></a>
### `STRUCTURE_ADRESSE`

Adresse de la structure employeur.

<a id="salarie-nom"></a>
### `SALARIE_NOM`

Nom du salarié dans le nouveau contexte canonique.

<a id="salarie-prenom"></a>
### `SALARIE_PRENOM`

Prénom du salarié dans le nouveau contexte canonique.

<a id="contrat-date-debut"></a>
### `CONTRAT_DATE_DEBUT`

Date de début du contrat dans le nouveau contexte canonique.

Le constructeur `build_merge_context()` peut générer d'autres clés préfixées à partir des données fournies par les adaptateurs. Elles ne doivent être documentées comme garanties que lorsqu'un adaptateur stable les alimente effectivement.

## Comportement cible en cas de valeur absente

La décision fonctionnelle conservée dans [Documents RH, Structure et publipostage](../09_DOCUMENTS_RH_STRUCTURE_PUBLIPOSTAGE.md) fixe la règle cible :

- clé connue mais donnée absente → valeur vide ;
- clé inconnue → jeton conservé ou signalé lors de la prévisualisation.

Cette règle cible doit rester testable et ne doit pas masquer une faute de frappe dans un modèle.
