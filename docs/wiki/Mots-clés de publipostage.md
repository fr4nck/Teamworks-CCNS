# Mots-clés de publipostage

Cette page référence les **47 mots-clés standard distincts** exposés par le moteur wx actuel. La syntaxe est exactement `{MOTCLE}`. Les champs personnalisés sont traités séparément, car leurs noms dépendent du dossier.

<a id="index-alphabetique"></a>
## Index alphabétique

[`{ADRESSERESID}`](#publipostage-adresseresid) · [`{AFFECTATIONS}`](#publipostage-affectations) · [`{AGE}`](#publipostage-age) · [`{BAREMECEE}`](#publipostage-baremecee) · [`{BRUTMENS}`](#publipostage-brutmens) · [`{CIVILITE}`](#publipostage-civilite) · [`{CLASSIFICATION}`](#publipostage-classification) · [`{CONFORMITEREMUNERATION}`](#publipostage-conformiteremuneration) · [`{CONVENTION}`](#publipostage-convention) · [`{CPNAISS}`](#publipostage-cpnaiss) · [`{CPRESID}`](#publipostage-cpresid) · [`{DATEDEBUT}`](#publipostage-datedebut) · [`{DATEDEPOT}`](#publipostage-datedepot) · [`{DATEFIN}`](#publipostage-datefin) · [`{DATENAISS}`](#publipostage-datenaiss) · [`{DATEREPONSE}`](#publipostage-datereponse) · [`{DECISION}`](#publipostage-decision) · [`{DISPONIBILITES}`](#publipostage-disponibilites) · [`{DUREEHEBDO}`](#publipostage-dureehebdo) · [`{EMAILS}`](#publipostage-emails) · [`{ESSAI}`](#publipostage-essai) · [`{FAX}`](#publipostage-fax) · [`{FONCTIONS}`](#publipostage-fonctions) · [`{GROUPECCNS}`](#publipostage-groupeccns) · [`{MEMO}`](#publipostage-memo) · [`{MINIMUMCCNS}`](#publipostage-minimumccns) · [`{MINIMUMCEE}`](#publipostage-minimumcee) · [`{MINIMUMRETENU}`](#publipostage-minimumretenu) · [`{MINIMUMSMIC}`](#publipostage-minimumsmic) · [`{NATIONALITE}`](#publipostage-nationalite) · [`{NOM}`](#publipostage-nom) · [`{NOMJFILLE}`](#publipostage-nomjfille) · [`{NUMSECU}`](#publipostage-numsecu) · [`{OFFREDEMPLOI}`](#publipostage-offredemploi) · [`{PAYSNAISS}`](#publipostage-paysnaiss) · [`{PRENOM}`](#publipostage-prenom) · [`{QUALIFICATIONCEE}`](#publipostage-qualificationcee) · [`{QUALIFICATIONS}`](#publipostage-qualifications) · [`{SALAIREBRUTMENSUEL}`](#publipostage-salairebrutmensuel) · [`{SITUATION}`](#publipostage-situation) · [`{TELEPHONES}`](#publipostage-telephones) · [`{TYPECONTRAT}`](#publipostage-typecontrat) · [`{TYPEDEPOT}`](#publipostage-typedepot) · [`{TYPEREPONSE}`](#publipostage-typereponse) · [`{VALEURPOINT}`](#publipostage-valeurpoint) · [`{VILLENAISS}`](#publipostage-villenaiss) · [`{VILLERESID}`](#publipostage-villeresid)

## Index par contexte

<a id="index-contexte-individu"></a>
### Individu

`CIVILITE`, `NOM`, `NOMJFILLE`, `PRENOM`, `DATENAISS`, `AGE`, `CPNAISS`, `VILLENAISS`, `PAYSNAISS`, `NATIONALITE`, `NUMSECU`, `ADRESSERESID`, `CPRESID`, `VILLERESID`, `SITUATION`, `TELEPHONES`, `EMAILS`, `FAX`.

<a id="index-contexte-candidat"></a>
### Candidat

`CIVILITE`, `NOM`, `PRENOM`, `DATENAISS`, `AGE`, `ADRESSERESID`, `CPRESID`, `VILLERESID`, `QUALIFICATIONS`, `TELEPHONES`, `FAX`, `EMAILS`, `MEMO`.

<a id="index-contexte-candidature"></a>
### Candidature

Une candidature charge d’abord la **Personne** si elle est liée ; sinon le **Candidat**. Elle ajoute ensuite : `DATEDEPOT`, `TYPEDEPOT`, `OFFREDEMPLOI`, `DISPONIBILITES`, `FONCTIONS`, `AFFECTATIONS`, `DECISION`, `DATEREPONSE`, `TYPEREPONSE`.

<a id="index-contexte-contrat"></a>
### Contrat

Le contexte Contrat hérite d’abord des 18 mots-clés **Individu**, puis ajoute : `DATEDEBUT`, `DATEFIN`, `CLASSIFICATION`, `TYPECONTRAT`, `VALEURPOINT`, `ESSAI`, `CONVENTION`, `GROUPECCNS`, `QUALIFICATIONCEE`, `DUREEHEBDO`, `SALAIREBRUTMENSUEL`, `BRUTMENS`, `MINIMUMCCNS`, `MINIMUMSMIC`, `MINIMUMRETENU`, `CONFORMITEREMUNERATION`, `BAREMECEE`, `MINIMUMCEE`.

## Index par usage

<a id="index-usage-identite"></a>
### Identité
`CIVILITE`, `NOM`, `NOMJFILLE`, `PRENOM`, `DATENAISS`, `AGE`, `CPNAISS`, `VILLENAISS`, `PAYSNAISS`, `NATIONALITE`, `NUMSECU`, `SITUATION`.

<a id="index-usage-coordonnees"></a>
### Coordonnées
`ADRESSERESID`, `CPRESID`, `VILLERESID`, `TELEPHONES`, `EMAILS`, `FAX`.

<a id="index-usage-recrutement"></a>
### Recrutement
`QUALIFICATIONS`, `MEMO`, `DATEDEPOT`, `TYPEDEPOT`, `OFFREDEMPLOI`, `DISPONIBILITES`, `FONCTIONS`, `AFFECTATIONS`, `DECISION`, `DATEREPONSE`, `TYPEREPONSE`.

<a id="index-usage-contrat"></a>
### Contrat
`DATEDEBUT`, `DATEFIN`, `CLASSIFICATION`, `TYPECONTRAT`, `VALEURPOINT`, `ESSAI`, `CONVENTION`, `DUREEHEBDO`.

<a id="index-usage-remuneration"></a>
### Rémunération
`SALAIREBRUTMENSUEL`, `BRUTMENS`, `MINIMUMRETENU`, `CONFORMITEREMUNERATION`.

<a id="index-usage-ccns"></a>
### CCNS
`GROUPECCNS`, `MINIMUMCCNS`, `MINIMUMSMIC`, `MINIMUMRETENU`, `CONFORMITEREMUNERATION`.

<a id="index-usage-cee"></a>
### CEE
`QUALIFICATIONCEE`, `BAREMECEE`, `MINIMUMCEE`.

<a id="exemples-modeles"></a>
## Exemples de modèles

Exemple Individu :

```text
Bonjour {CIVILITE} {NOM},
```

Exemple Contrat :

```text
Votre contrat débute le {DATEDEBUT}.
Salaire brut mensuel : {SALAIREBRUTMENSUEL}
```

Ces exemples sont fictifs et ne contiennent aucune donnée personnelle réelle.

<a id="champs-personnalises"></a>
## Champs personnalisés

Un champ personnalisé est défini dans le dossier et peut être ajouté aux données du publipostage selon sa catégorie. Les contrats disposent en plus de champs configurables dont le mot-clé est stocké dans les données du dossier.

Tous les noms ne peuvent pas être listés ici : ils ne sont pas codés en dur. Pour connaître le mot-clé exact, ouvrez **Vérification des données du document** ou, pour un champ de contrat, **Paramétrage > Contrats > Les champs de contrats**. Ne fabriquez pas une balise à partir du libellé. Voir [Champs personnalisés du guide](Publipostage-et-documents#champs-personnalises-publipostage).

## Compatibilité et comportement

- **Teamword**, **Microsoft Word** et **LibreOffice Writer** reçoivent la même convention `{MOTCLE}` lorsque le contexte expose la valeur.
- La voie Writer audité effectue une recherche/remplacement sensible à la casse.
- Une valeur connue mais absente devient généralement vide.
- Une balise inconnue n’est pas ajoutée à la liste de remplacement et peut rester visible.
- Les clés internes commençant par `_` servent aux liaisons et ne sont pas des mots-clés de modèle.
- Il n’existe pas de contexte générique `presence`, `frais` ou `dpae` dans le moteur audité.

## Compatibilité historique

`{BRUTMENS}` est un alias de compatibilité de `{SALAIREBRUTMENSUEL}`. `{CLASSIFICATION}` et `{VALEURPOINT}` restent disponibles pour les anciens contrats/modèles. Les identifiants DPAE/DUE tels que `NUM_SIRET` ne deviennent pas pour autant des balises de publipostage.

## Référence détaillée

<a id="publipostage-civilite"></a>
### `{CIVILITE}`
Civilité enregistrée. Contextes : Individu, Contrat via Individu, Candidat, Candidature.

<a id="publipostage-nom"></a>
### `{NOM}`
Nom de famille. Contextes : Individu, Contrat, Candidat, Candidature.

<a id="publipostage-nomjfille"></a>
### `{NOMJFILLE}`
Nom de naissance/jeune fille. Individu, Contrat et Candidature si une Personne est liée ; absent du contexte Candidat.

<a id="publipostage-prenom"></a>
### `{PRENOM}`
Prénom. Individu, Contrat, Candidat, Candidature.

<a id="publipostage-datenaiss"></a>
### `{DATENAISS}`
Date de naissance formatée par le moteur. Individu, Contrat, Candidat, Candidature.

<a id="publipostage-age"></a>
### `{AGE}`
Âge calculé ou enregistré selon la source. Individu, Contrat, Candidat, Candidature.

<a id="publipostage-cpnaiss"></a>
### `{CPNAISS}`
Code postal du lieu de naissance. Individu, Contrat, Candidature si Personne liée.

<a id="publipostage-villenaiss"></a>
### `{VILLENAISS}`
Ville de naissance. Individu, Contrat, Candidature si Personne liée.

<a id="publipostage-paysnaiss"></a>
### `{PAYSNAISS}`
Pays de naissance. Individu, Contrat, Candidature si Personne liée.

<a id="publipostage-nationalite"></a>
### `{NATIONALITE}`
Nationalité enregistrée. Individu, Contrat, Candidature si Personne liée.

<a id="publipostage-numsecu"></a>
### `{NUMSECU}`
Numéro de sécurité sociale enregistré. Individu, Contrat, Candidature si Personne liée. Donnée sensible à ne pas utiliser dans un exemple public.

<a id="publipostage-adresseresid"></a>
### `{ADRESSERESID}`
Adresse de résidence. Individu, Contrat, Candidat, Candidature.

<a id="publipostage-cpresid"></a>
### `{CPRESID}`
Code postal de résidence. Individu, Contrat, Candidat, Candidature.

<a id="publipostage-villeresid"></a>
### `{VILLERESID}`
Ville de résidence. Individu, Contrat, Candidat, Candidature.

<a id="publipostage-situation"></a>
### `{SITUATION}`
Situation enregistrée dans la fiche. Individu, Contrat, Candidature si Personne liée.

<a id="publipostage-telephones"></a>
### `{TELEPHONES}`
Téléphones regroupés par le moteur. Individu, Contrat, Candidat, Candidature.

<a id="publipostage-emails"></a>
### `{EMAILS}`
Adresses email regroupées. Individu, Contrat, Candidat, Candidature ; utilisé aussi comme destinataire par la voie Email lorsque disponible.

<a id="publipostage-fax"></a>
### `{FAX}`
Numéros de fax enregistrés. Individu, Contrat, Candidat, Candidature.

<a id="publipostage-qualifications"></a>
### `{QUALIFICATIONS}`
Qualifications/diplômes du Candidat. Candidat et Candidature tant que celle-ci repose sur le Candidat non converti.

<a id="publipostage-memo"></a>
### `{MEMO}`
Mémo du Candidat. Candidat et Candidature tant que celle-ci repose sur le Candidat non converti.

<a id="publipostage-datedepot"></a>
### `{DATEDEPOT}`
Date de dépôt de la candidature. Contexte Candidature.

<a id="publipostage-typedepot"></a>
### `{TYPEDEPOT}`
Canal/type de dépôt de la candidature. Contexte Candidature.

<a id="publipostage-offredemploi"></a>
### `{OFFREDEMPLOI}`
Intitulé de l’offre liée ou libellé de candidature spontanée. Contexte Candidature.

<a id="publipostage-disponibilites"></a>
### `{DISPONIBILITES}`
Périodes de disponibilité assemblées par le moteur. Contexte Candidature.

<a id="publipostage-fonctions"></a>
### `{FONCTIONS}`
Fonctions souhaitées de la candidature. Contexte Candidature.

<a id="publipostage-affectations"></a>
### `{AFFECTATIONS}`
Affectations souhaitées de la candidature. Contexte Candidature.

<a id="publipostage-decision"></a>
### `{DECISION}`
Décision de candidature, convertie en libellé utilisateur. Contexte Candidature.

<a id="publipostage-datereponse"></a>
### `{DATEREPONSE}`
Date de réponse communiquée lorsqu’elle est enregistrée. Contexte Candidature.

<a id="publipostage-typereponse"></a>
### `{TYPEREPONSE}`
Canal/type de réponse lorsqu’il est enregistré. Contexte Candidature.

<a id="publipostage-datedebut"></a>
### `{DATEDEBUT}`
Date de début du contrat. Contexte Contrat.

<a id="publipostage-datefin"></a>
### `{DATEFIN}`
Date de fin du contrat lorsqu’elle existe. Contexte Contrat.

<a id="publipostage-classification"></a>
### `{CLASSIFICATION}`
Compatibilité historique : classification enregistrée ou valeur de repli prévue par le moteur pour les modèles anciens. Contexte Contrat.

<a id="publipostage-typecontrat"></a>
### `{TYPECONTRAT}`
Type/intitulé du contrat. Contexte Contrat.

<a id="publipostage-valeurpoint"></a>
### `{VALEURPOINT}`
Valeur du point historique lorsqu’elle est disponible. Contexte Contrat.

<a id="publipostage-essai"></a>
### `{ESSAI}`
Information de période d’essai formatée par le moteur. Contexte Contrat.

<a id="publipostage-convention"></a>
### `{CONVENTION}`
Code/libellé de convention ou régime enregistré. Contexte Contrat.

<a id="publipostage-groupeccns"></a>
### `{GROUPECCNS}`
Groupe CCNS du contrat lorsqu’il est renseigné. Contexte Contrat.

<a id="publipostage-qualificationcee"></a>
### `{QUALIFICATIONCEE}`
Qualification/statut CEE enregistré. Contexte Contrat.

<a id="publipostage-dureehebdo"></a>
### `{DUREEHEBDO}`
Durée hebdomadaire du contrat formatée par le moteur. Contexte Contrat.

<a id="publipostage-salairebrutmensuel"></a>
### `{SALAIREBRUTMENSUEL}`
Salaire brut mensuel utilisé par le contrôle de rémunération lorsqu’il est applicable. Contexte Contrat.

<a id="publipostage-brutmens"></a>
### `{BRUTMENS}`
Alias historique de `{SALAIREBRUTMENSUEL}` ; même valeur. Contexte Contrat.

<a id="publipostage-minimumccns"></a>
### `{MINIMUMCCNS}`
Minimum CCNS calculé lorsque groupe, date et barème permettent le calcul. Contexte Contrat.

<a id="publipostage-minimumsmic"></a>
### `{MINIMUMSMIC}`
Minimum SMIC calculé par le moteur lorsqu’il dispose du barème applicable. Contexte Contrat.

<a id="publipostage-minimumretenu"></a>
### `{MINIMUMRETENU}`
Seuil finalement retenu par le moteur parmi les minima disponibles. Contexte Contrat.

<a id="publipostage-conformiteremuneration"></a>
### `{CONFORMITEREMUNERATION}`
Résultat textuel du contrôle de rémunération lorsque le calcul est possible. Contexte Contrat ; ce n’est pas une certification juridique.

<a id="publipostage-baremecee"></a>
### `{BAREMECEE}`
Référence/libellé du barème CEE applicable lorsque déterminable. Contexte Contrat.

<a id="publipostage-minimumcee"></a>
### `{MINIMUMCEE}`
Minimum CEE calculé lorsque qualification, date et barème sont exploitables. Contexte Contrat.

## Liens associés

[[Publipostage et documents]] · [[Éditeur interne et documents]] · [[Individus et fiches]] · [[Contrats, CCNS et CEE]] · [[Recrutement]]
