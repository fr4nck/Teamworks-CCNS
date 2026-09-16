# Mots-clés de publipostage

Cette page est la référence des **mots-clés standard réellement exposés par le moteur de publipostage actuel** de Teamworks-CCNS wx.

La syntaxe à saisir dans un modèle est **exactement** `{MOTCLE}` : accolades comprises. L’inventaire ci-dessous provient des listes retournées par `UTILS_Publipostage_donnees.py`. Il contient **47 mots-clés standard distincts**. Les champs personnalisés, dont le nom est défini dans la base de chaque dossier, sont traités séparément plus bas.

> L’assistant construit d’abord les données du contexte (`personne`, `contrat`, `candidat` ou `candidature`), puis remet ces mêmes données à Teamword, Word ou Writer. Un mot-clé n’est donc disponible que si le contexte l’expose.

## Trouver un mot-clé par usage

- [Individus et identité](#usage-individus)
- [Adresse et coordonnées](#usage-coordonnees)
- [Contrats, CCNS, CEE et rémunération](#usage-contrats)
- [Recrutement](#usage-recrutement)
- [Disponibilité par contexte](#disponibilite-par-contexte)
- [Champs personnalisés](#champs-personnalises)
- [Valeurs vides et balises inconnues](#valeurs-vides-et-balises-inconnues)

Voir aussi [[Publipostage et documents]] et [[Éditeur interne et documents]].

<a id="usage-individus"></a>
## Individus et identité

[`{CIVILITE}`](#publipostage-civilite) · [`{NOM}`](#publipostage-nom) · [`{NOMJFILLE}`](#publipostage-nomjfille) · [`{PRENOM}`](#publipostage-prenom) · [`{DATENAISS}`](#publipostage-datenaiss) · [`{AGE}`](#publipostage-age) · [`{CPNAISS}`](#publipostage-cpnaiss) · [`{VILLENAISS}`](#publipostage-villenaiss) · [`{PAYSNAISS}`](#publipostage-paysnaiss) · [`{NATIONALITE}`](#publipostage-nationalite) · [`{NUMSECU}`](#publipostage-numsecu) · [`{SITUATION}`](#publipostage-situation)

<a id="usage-coordonnees"></a>
## Adresse et coordonnées

[`{ADRESSERESID}`](#publipostage-adresseresid) · [`{CPRESID}`](#publipostage-cpresid) · [`{VILLERESID}`](#publipostage-villeresid) · [`{TELEPHONES}`](#publipostage-telephones) · [`{EMAILS}`](#publipostage-emails) · [`{FAX}`](#publipostage-fax)

<a id="usage-contrats"></a>
## Contrats, CCNS, CEE et rémunération

[`{DATEDEBUT}`](#publipostage-datedebut) · [`{DATEFIN}`](#publipostage-datefin) · [`{CLASSIFICATION}`](#publipostage-classification) · [`{TYPECONTRAT}`](#publipostage-typecontrat) · [`{VALEURPOINT}`](#publipostage-valeurpoint) · [`{ESSAI}`](#publipostage-essai) · [`{CONVENTION}`](#publipostage-convention) · [`{GROUPECCNS}`](#publipostage-groupeccns) · [`{QUALIFICATIONCEE}`](#publipostage-qualificationcee) · [`{DUREEHEBDO}`](#publipostage-dureehebdo) · [`{SALAIREBRUTMENSUEL}`](#publipostage-salairebrutmensuel) · [`{BRUTMENS}`](#publipostage-brutmens) · [`{MINIMUMCCNS}`](#publipostage-minimumccns) · [`{MINIMUMSMIC}`](#publipostage-minimumsmic) · [`{MINIMUMRETENU}`](#publipostage-minimumretenu) · [`{CONFORMITEREMUNERATION}`](#publipostage-conformiteremuneration) · [`{BAREMECEE}`](#publipostage-baremecee) · [`{MINIMUMCEE}`](#publipostage-minimumcee)

<a id="usage-recrutement"></a>
## Recrutement

**Candidat :** [`{CIVILITE}`](#publipostage-civilite), [`{NOM}`](#publipostage-nom), [`{PRENOM}`](#publipostage-prenom), [`{DATENAISS}`](#publipostage-datenaiss), [`{AGE}`](#publipostage-age), [`{ADRESSERESID}`](#publipostage-adresseresid), [`{CPRESID}`](#publipostage-cpresid), [`{VILLERESID}`](#publipostage-villeresid), [`{QUALIFICATIONS}`](#publipostage-qualifications), [`{TELEPHONES}`](#publipostage-telephones), [`{FAX}`](#publipostage-fax), [`{EMAILS}`](#publipostage-emails), [`{MEMO}`](#publipostage-memo).

**Candidature :** [`{DATEDEPOT}`](#publipostage-datedepot), [`{TYPEDEPOT}`](#publipostage-typedepot), [`{OFFREDEMPLOI}`](#publipostage-offredemploi), [`{DISPONIBILITES}`](#publipostage-disponibilites), [`{FONCTIONS}`](#publipostage-fonctions), [`{AFFECTATIONS}`](#publipostage-affectations), [`{DECISION}`](#publipostage-decision), [`{DATEREPONSE}`](#publipostage-datereponse), [`{TYPEREPONSE}`](#publipostage-typereponse).

<a id="disponibilite-par-contexte"></a>
## Disponibilité par contexte

`✓` = disponible. `—` = non exposé par ce contexte. `Personne liée` et `Candidat non converti` sont des conditions réelles du moteur Candidature.

### Données personne / candidat

| Mot-clé | Individus | Contrats | Candidats | Candidatures |
|---|---:|---:|---:|---:|
| [`{CIVILITE}`](#publipostage-civilite) | ✓ | ✓ | ✓ | ✓ |
| [`{NOM}`](#publipostage-nom) | ✓ | ✓ | ✓ | ✓ |
| [`{NOMJFILLE}`](#publipostage-nomjfille) | ✓ | ✓ | — | Personne liée |
| [`{PRENOM}`](#publipostage-prenom) | ✓ | ✓ | ✓ | ✓ |
| [`{DATENAISS}`](#publipostage-datenaiss) | ✓ | ✓ | ✓ | ✓ |
| [`{AGE}`](#publipostage-age) | ✓ | ✓ | ✓ | ✓ |
| [`{CPNAISS}`](#publipostage-cpnaiss) | ✓ | ✓ | — | Personne liée |
| [`{VILLENAISS}`](#publipostage-villenaiss) | ✓ | ✓ | — | Personne liée |
| [`{PAYSNAISS}`](#publipostage-paysnaiss) | ✓ | ✓ | — | Personne liée |
| [`{NATIONALITE}`](#publipostage-nationalite) | ✓ | ✓ | — | Personne liée |
| [`{NUMSECU}`](#publipostage-numsecu) | ✓ | ✓ | — | Personne liée |
| [`{ADRESSERESID}`](#publipostage-adresseresid) | ✓ | ✓ | ✓ | ✓ |
| [`{CPRESID}`](#publipostage-cpresid) | ✓ | ✓ | ✓ | ✓ |
| [`{VILLERESID}`](#publipostage-villeresid) | ✓ | ✓ | ✓ | ✓ |
| [`{SITUATION}`](#publipostage-situation) | ✓ | ✓ | — | Personne liée |
| [`{TELEPHONES}`](#publipostage-telephones) | ✓ | ✓ | ✓ | ✓ |
| [`{EMAILS}`](#publipostage-emails) | ✓ | ✓ | ✓ | ✓ |
| [`{FAX}`](#publipostage-fax) | ✓ | ✓ | ✓ | ✓ |
| [`{QUALIFICATIONS}`](#publipostage-qualifications) | — | — | ✓ | Candidat non converti |
| [`{MEMO}`](#publipostage-memo) | — | — | ✓ | Candidat non converti |

### Données candidature

| Mot-clé | Individus | Contrats | Candidats | Candidatures |
|---|---:|---:|---:|---:|
| [`{DATEDEPOT}`](#publipostage-datedepot) | — | — | — | ✓ |
| [`{TYPEDEPOT}`](#publipostage-typedepot) | — | — | — | ✓ |
| [`{OFFREDEMPLOI}`](#publipostage-offredemploi) | — | — | — | ✓ |
| [`{DISPONIBILITES}`](#publipostage-disponibilites) | — | — | — | ✓ |
| [`{FONCTIONS}`](#publipostage-fonctions) | — | — | — | ✓ |
| [`{AFFECTATIONS}`](#publipostage-affectations) | — | — | — | ✓ |
| [`{DECISION}`](#publipostage-decision) | — | — | — | ✓ |
| [`{DATEREPONSE}`](#publipostage-datereponse) | — | — | — | ✓ |
| [`{TYPEREPONSE}`](#publipostage-typereponse) | — | — | — | ✓ |

### Données contrat

| Mot-clé | Individus | Contrats | Candidats | Candidatures |
|---|---:|---:|---:|---:|
| [`{DATEDEBUT}`](#publipostage-datedebut) | — | ✓ | — | — |
| [`{DATEFIN}`](#publipostage-datefin) | — | ✓ | — | — |
| [`{CLASSIFICATION}`](#publipostage-classification) | — | ✓ | — | — |
| [`{TYPECONTRAT}`](#publipostage-typecontrat) | — | ✓ | — | — |
| [`{VALEURPOINT}`](#publipostage-valeurpoint) | — | ✓ | — | — |
| [`{ESSAI}`](#publipostage-essai) | — | ✓ | — | — |
| [`{CONVENTION}`](#publipostage-convention) | — | ✓ | — | — |
| [`{GROUPECCNS}`](#publipostage-groupeccns) | — | ✓ | — | — |
| [`{QUALIFICATIONCEE}`](#publipostage-qualificationcee) | — | ✓ | — | — |
| [`{DUREEHEBDO}`](#publipostage-dureehebdo) | — | ✓ | — | — |
| [`{SALAIREBRUTMENSUEL}`](#publipostage-salairebrutmensuel) | — | ✓ | — | — |
| [`{BRUTMENS}`](#publipostage-brutmens) | — | ✓ | — | — |
| [`{MINIMUMCCNS}`](#publipostage-minimumccns) | — | ✓ | — | — |
| [`{MINIMUMSMIC}`](#publipostage-minimumsmic) | — | ✓ | — | — |
| [`{MINIMUMRETENU}`](#publipostage-minimumretenu) | — | ✓ | — | — |
| [`{CONFORMITEREMUNERATION}`](#publipostage-conformiteremuneration) | — | ✓ | — | — |
| [`{BAREMECEE}`](#publipostage-baremecee) | — | ✓ | — | — |
| [`{MINIMUMCEE}`](#publipostage-minimumcee) | — | ✓ | — | — |

Le moteur générique ne déclare actuellement **aucun contexte `presence`, `frais` ou `dpae`**.

## Héritage entre contextes

- **Contrat → Individu :** un document de contrat reçoit les 18 mots-clés Personne, puis les mots-clés Contrat. C’est pourquoi `{NOM}` ou `{ADRESSERESID}` fonctionnent dans un modèle de contrat.
- **Candidature → Personne ou Candidat :** si la candidature référence une personne, Teamworks charge les données Personne ; sinon il charge les données Candidat. Les 9 mots-clés propres à la candidature sont ensuite ajoutés.
- Les clés techniques commençant par `_` servent aux liaisons et ne sont pas proposées dans les modèles.

## Compatibilité des éditeurs

Les 47 mots-clés standard suivent la même convention dans les trois voies documentaires :

| Voie | Syntaxe | Condition |
|---|---|---|
| Teamword, éditeur interne | `{MOTCLE}` | le contexte doit exposer le mot-clé |
| Microsoft Word | `{MOTCLE}` | le contexte doit exposer le mot-clé |
| Writer via UNO/soffice | `{MOTCLE}` | le contexte doit exposer le mot-clé |

L’interface historique appelle la troisième voie « OpenOffice Writer ». Le pilote utilise UNO/`soffice`; le wiki la désigne « Writer (LibreOffice/OpenOffice selon l’installation) » sans inventer une intégration LibreOffice distincte.

## Référence détaillée

### Règle de lecture

Dans toutes les fiches ci-dessous, **Compatibilité : Teamword / Word / Writer** signifie que le moteur de l’éditeur sait recevoir la valeur lorsque le contexte indiqué l’expose. Les liens « Voir aussi » permettent de revenir à la fonction métier.

## Identité et individu

<a id="publipostage-civilite"></a>
### `{CIVILITE}`
**Description :** civilité enregistrée. **Exemple :** `Mme`. **Contextes :** Individus ; Contrats via l’individu ; Candidats ; Candidatures. **Source :** personne/candidat. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** valeur stockée telle quelle. **Voir aussi :** [[Individus et fiches]], [[Contrats, CCNS et CEE]], [[Recrutement]].

<a id="publipostage-nom"></a>
### `{NOM}`
**Description :** nom de famille. **Exemple :** `DUPONT`. **Contextes :** Individus ; Contrats via l’individu ; Candidats ; Candidatures. **Source :** personne/candidat. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** le moteur ne force pas les majuscules. **Voir aussi :** [[Individus et fiches]], [[Contrats, CCNS et CEE]], [[Recrutement]].

<a id="publipostage-nomjfille"></a>
### `{NOMJFILLE}`
**Description :** nom de naissance / jeune fille de la personne. **Exemple :** `MARTIN`. **Contextes :** Individus ; Contrats ; Candidature si une personne est liée. **Source :** personne. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** absent du contexte Candidat. **Voir aussi :** [[Individus et fiches]], [[Contrats, CCNS et CEE]], [[Recrutement]].

<a id="publipostage-prenom"></a>
### `{PRENOM}`
**Description :** prénom. **Exemple :** `Camille`. **Contextes :** Individus ; Contrats ; Candidats ; Candidatures. **Source :** personne/candidat. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** valeur stockée telle quelle. **Voir aussi :** [[Individus et fiches]], [[Contrats, CCNS et CEE]], [[Recrutement]].

<a id="publipostage-datenaiss"></a>
### `{DATENAISS}`
**Description :** date de naissance. **Exemple :** `17/04/1992`. **Contextes :** Individus ; Contrats ; Candidats ; Candidatures. **Source :** personne/candidat. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** format français `jj/mm/aaaa` lorsqu’une date existe. **Voir aussi :** [[Individus et fiches]], [[Recrutement]].

<a id="publipostage-age"></a>
### `{AGE}`
**Description :** âge en années. **Exemple :** `34`. **Contextes :** Individus ; Contrats ; Candidats ; Candidatures. **Source :** donnée calculée. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** personne : calcul depuis la naissance ; candidat : valeur enregistrée si présente, sinon recalcul. **Voir aussi :** [[Individus et fiches]], [[Recrutement]].

<a id="publipostage-cpnaiss"></a>
### `{CPNAISS}`
**Description :** code postal de naissance. **Exemple :** `69003`. **Contextes :** Individus ; Contrats ; Candidature si personne liée. **Source :** personne. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** numérique → 5 chiffres ; texte non numérique conservé. **Voir aussi :** [[Individus et fiches]].

<a id="publipostage-villenaiss"></a>
### `{VILLENAISS}`
**Description :** ville de naissance. **Exemple :** `Lyon`. **Contextes :** Individus ; Contrats ; Candidature si personne liée. **Source :** personne. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** non exposé par Candidat. **Voir aussi :** [[Individus et fiches]].

<a id="publipostage-paysnaiss"></a>
### `{PAYSNAISS}`
**Description :** nom du pays de naissance. **Exemple :** `France`. **Contextes :** Individus ; Contrats ; Candidature si personne liée. **Source :** personne + référentiel pays. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** vide si aucune référence exploitable. **Voir aussi :** [[Individus et fiches]].

<a id="publipostage-nationalite"></a>
### `{NATIONALITE}`
**Description :** libellé de nationalité. **Exemple :** `Française`. **Contextes :** Individus ; Contrats ; Candidature si personne liée. **Source :** personne + référentiel pays. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** vide si aucune référence exploitable. **Voir aussi :** [[Individus et fiches]].

<a id="publipostage-numsecu"></a>
### `{NUMSECU}`
**Description :** numéro de sécurité sociale enregistré. **Exemple :** `2 92 04 69 …`. **Contextes :** Individus ; Contrats ; Candidature si personne liée. **Source :** personne. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** pas de transformation métier supplémentaire dans le moteur de publipostage. **Voir aussi :** [[Individus et fiches]], [[Contrats, CCNS et CEE]].

<a id="publipostage-situation"></a>
### `{SITUATION}`
**Description :** libellé de situation de la personne. **Exemple :** `Salarié`. **Contextes :** Individus ; Contrats ; Candidature si personne liée. **Source :** personne + table situations. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** vide si aucune ligne ne correspond. **Voir aussi :** [[Individus et fiches]].

## Adresse et coordonnées

<a id="publipostage-adresseresid"></a>
### `{ADRESSERESID}`
**Description :** adresse de résidence. **Exemple :** `12 rue des Lilas`. **Contextes :** Individus ; Contrats ; Candidats ; Candidatures. **Source :** personne/candidat. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** texte tel qu’enregistré. **Voir aussi :** [[Individus et fiches]], [[Recrutement]].

<a id="publipostage-cpresid"></a>
### `{CPRESID}`
**Description :** code postal de résidence. **Exemple :** `69140`. **Contextes :** Individus ; Contrats ; Candidats ; Candidatures. **Source :** personne/candidat. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** numérique → 5 chiffres ; texte non numérique conservé. **Voir aussi :** [[Individus et fiches]], [[Recrutement]].

<a id="publipostage-villeresid"></a>
### `{VILLERESID}`
**Description :** ville de résidence. **Exemple :** `Rillieux-la-Pape`. **Contextes :** Individus ; Contrats ; Candidats ; Candidatures. **Source :** personne/candidat. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** valeur stockée telle quelle. **Voir aussi :** [[Individus et fiches]], [[Recrutement]].

<a id="publipostage-telephones"></a>
### `{TELEPHONES}`
**Description :** coordonnées Fixe/Mobile. **Exemple :** `04 72 00 00 00, 06 00 00 00 00`. **Contextes :** Individus ; Contrats ; Candidats ; Candidatures. **Source :** coordonnées. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** plusieurs numéros sont joints par `, `. **Voir aussi :** [[Individus et fiches]], [[Recrutement]].

<a id="publipostage-emails"></a>
### `{EMAILS}`
**Description :** adresses email. **Exemple :** `camille@example.org`. **Contextes :** Individus ; Contrats ; Candidats ; Candidatures. **Source :** coordonnées. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** plusieurs adresses sont jointes par `, ` ; le mode Email utilise cette valeur comme destinataire. **Voir aussi :** [[Individus et fiches]], [[Éditeur interne et documents]].

<a id="publipostage-fax"></a>
### `{FAX}`
**Description :** coordonnées de type Fax. **Exemple :** `04 72 00 00 01`. **Contextes :** Individus ; Contrats ; Candidats ; Candidatures. **Source :** coordonnées. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** plusieurs fax sont joints par `, `. **Voir aussi :** [[Individus et fiches]], [[Recrutement]].

## Recrutement

<a id="publipostage-qualifications"></a>
### `{QUALIFICATIONS}`
**Description :** diplômes/qualifications du candidat. **Exemple :** `BAFA; PSC1`. **Contextes :** Candidats ; Candidature seulement si les données viennent encore du candidat. **Source :** candidat/diplômes. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** libellés joints par `; ` ; absent après bascule vers une personne liée. **Voir aussi :** [[Recrutement]].

<a id="publipostage-memo"></a>
### `{MEMO}`
**Description :** mémo du candidat. **Exemple :** `Disponible les week-ends`. **Contextes :** Candidats ; Candidature si candidat non converti. **Source :** candidat. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** non exposé par `Importation_personne`. **Voir aussi :** [[Recrutement]].

<a id="publipostage-datedepot"></a>
### `{DATEDEPOT}`
**Description :** date de dépôt de la candidature. **Exemple :** `03/09/2026`. **Contextes :** Candidatures. **Source :** candidature. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** format français. **Voir aussi :** [[Recrutement]].

<a id="publipostage-typedepot"></a>
### `{TYPEDEPOT}`
**Description :** mode de dépôt. **Exemple :** `Email`. **Contextes :** Candidatures. **Source :** candidature. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** libellé issu du choix enregistré (vive voix, courrier, téléphone, main à main, email, Pôle Emploi, organisateur, fédération ou autre). **Voir aussi :** [[Recrutement]].

<a id="publipostage-offredemploi"></a>
### `{OFFREDEMPLOI}`
**Description :** intitulé de l’offre associée. **Exemple :** `Animateur sportif`. **Contextes :** Candidatures. **Source :** candidature/offre. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** sans offre : `Candidature spontanée`. **Voir aussi :** [[Recrutement]].

<a id="publipostage-disponibilites"></a>
### `{DISPONIBILITES}`
**Description :** périodes de disponibilité. **Exemple :** `du 01/07/2027 au 31/08/2027`. **Contextes :** Candidatures. **Source :** candidature. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** périodes jointes par `; `. **Voir aussi :** [[Recrutement]].

<a id="publipostage-fonctions"></a>
### `{FONCTIONS}`
**Description :** fonctions souhaitées/associées. **Exemple :** `Animateur; Coordinateur`. **Contextes :** Candidatures. **Source :** candidature. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** plusieurs valeurs jointes par `; `. **Voir aussi :** [[Recrutement]].

<a id="publipostage-affectations"></a>
### `{AFFECTATIONS}`
**Description :** affectations souhaitées/associées. **Exemple :** `Accueil de loisirs`. **Contextes :** Candidatures. **Source :** candidature. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** plusieurs valeurs jointes par `; `. **Voir aussi :** [[Recrutement]].

<a id="publipostage-decision"></a>
### `{DECISION}`
**Description :** décision enregistrée. **Exemple :** `Oui`. **Contextes :** Candidatures. **Source :** candidature. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** `Décision non prise`, `Oui` ou `Non`. **Voir aussi :** [[Recrutement]].

<a id="publipostage-datereponse"></a>
### `{DATEREPONSE}`
**Description :** date de réponse. **Exemple :** `12/09/2026`. **Contextes :** Candidatures. **Source :** candidature. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** renseigné seulement si une réponse est enregistrée. **Voir aussi :** [[Recrutement]].

<a id="publipostage-typereponse"></a>
### `{TYPEREPONSE}`
**Description :** mode de réponse. **Exemple :** `Téléphone`. **Contextes :** Candidatures. **Source :** candidature. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** renseigné seulement si une réponse est enregistrée. **Voir aussi :** [[Recrutement]].

## Contrat, classification et CCNS

<a id="publipostage-datedebut"></a>
### `{DATEDEBUT}`
**Description :** date de début du contrat. **Exemple :** `01/10/2026`. **Contextes :** Contrats. **Source :** contrat. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** format français. **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="publipostage-datefin"></a>
### `{DATEFIN}`
**Description :** date de fin du contrat. **Exemple :** `30/06/2027`. **Contextes :** Contrats. **Source :** contrat. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** vide si aucune date n’est enregistrée. **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="publipostage-classification"></a>
### `{CLASSIFICATION}`
**Description :** classification historique du contrat. **Exemple :** `Groupe 3`. **Contextes :** Contrats. **Source :** contrat/classification. **Compatibilité :** Teamword / Word / Writer. **Statut :** historique / compatibilité. **Remarque :** si l’ancienne classification est vide, le moteur reprend `GROUPECCNS`, puis `QUALIFICATIONCEE`. **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="publipostage-typecontrat"></a>
### `{TYPECONTRAT}`
**Description :** libellé du type de contrat. **Exemple :** `Contrat d'engagement éducatif`. **Contextes :** Contrats. **Source :** contrat/type. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** libellé de la table des types. **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="publipostage-valeurpoint"></a>
### `{VALEURPOINT}`
**Description :** valeur du point associée au contrat historique. **Exemple :** `7.21 €`. **Contextes :** Contrats. **Source :** contrat/valeurs du point. **Compatibilité :** Teamword / Word / Writer. **Statut :** historique / compatibilité. **Remarque :** vide sans référence historique. **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="publipostage-essai"></a>
### `{ESSAI}`
**Description :** valeur du champ `essai` du contrat. **Exemple :** `0`. **Contextes :** Contrats. **Source :** contrat. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** converti en texte ; `0` si vide. Le moteur n’explicite pas ici une unité, le wiki n’en invente donc pas. **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="publipostage-convention"></a>
### `{CONVENTION}`
**Description :** code de convention du contrat. **Exemple :** `CCNS`. **Contextes :** Contrats. **Source :** contrat. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** valeur issue du contrat. **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="publipostage-groupeccns"></a>
### `{GROUPECCNS}`
**Description :** code du groupe CCNS. **Exemple :** `3`. **Contextes :** Contrats. **Source :** contrat. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** utilisé par le contrôle CCNS lorsque la convention vaut `CCNS`. **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="publipostage-qualificationcee"></a>
### `{QUALIFICATIONCEE}`
**Description :** libellé de qualification CEE. **Exemple :** `BAFA titulaire`. **Contextes :** Contrats. **Source :** contrat. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** les codes BAFA/BAFD, stagiaire, non diplômé et équivalent sont traduits en libellés. **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="publipostage-dureehebdo"></a>
### `{DUREEHEBDO}`
**Description :** durée hebdomadaire. **Exemple :** `35 h`. **Contextes :** Contrats. **Source :** contrat. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** zéros décimaux finaux supprimés. **Voir aussi :** [[Contrats, CCNS et CEE]].

## Rémunération et contrôles

<a id="publipostage-salairebrutmensuel"></a>
### `{SALAIREBRUTMENSUEL}`
**Description :** salaire brut mensuel enregistré. **Exemple :** `2145.00 €`. **Contextes :** Contrats. **Source :** contrat/rémunération. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** deux décimales ; balise à privilégier pour les nouveaux modèles. **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="publipostage-brutmens"></a>
### `{BRUTMENS}`
**Description :** alias historique du salaire brut mensuel. **Exemple :** `2145.00 €`. **Contextes :** Contrats. **Source :** contrat/rémunération. **Compatibilité :** Teamword / Word / Writer. **Statut :** historique / alias. **Remarque :** valeur exactement copiée depuis `{SALAIREBRUTMENSUEL}`. Préférer [`{SALAIREBRUTMENSUEL}`](#publipostage-salairebrutmensuel). **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="publipostage-minimumccns"></a>
### `{MINIMUMCCNS}`
**Description :** minimum CCNS calculé. **Exemple :** `1986.40 €`. **Contextes :** Contrats. **Source :** contrôle CCNS calculé à la date de début. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** vide si le contrat ne fournit pas le contexte CCNS nécessaire. **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="publipostage-minimumsmic"></a>
### `{MINIMUMSMIC}`
**Description :** minimum SMIC utilisé par le contrôle. **Exemple :** `1900.00 €`. **Contextes :** Contrats. **Source :** contrôle de rémunération. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** renseigné dans le contrôle mensuel CCNS lorsqu’il peut être évalué. **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="publipostage-minimumretenu"></a>
### `{MINIMUMRETENU}`
**Description :** minimum retenu par le contrôle. **Exemple :** `1986.40 €`. **Contextes :** Contrats. **Source :** contrôle de rémunération. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** un minimum annuel peut être annoté `annuel`. **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="publipostage-conformiteremuneration"></a>
### `{CONFORMITEREMUNERATION}`
**Description :** résultat textuel du contrôle. **Exemple :** `Conforme`. **Contextes :** Contrats. **Source :** contrôle CCNS/CEE. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** peut valoir `Conforme`, `Non conforme` ou `Contrôle annuel requis`, sinon vide. **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="publipostage-baremecee"></a>
### `{BAREMECEE}`
**Description :** montant journalier CEE applicable trouvé par Teamworks. **Exemple :** `52.00 €`. **Contextes :** Contrats CEE. **Source :** barème CEE. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** renseigné lorsqu’un barème correspond à la qualification et à la date. **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="publipostage-minimumcee"></a>
### `{MINIMUMCEE}`
**Description :** minimum journalier légal CEE utilisé par le contrôle. **Exemple :** `26.00 €`. **Contextes :** Contrats reconnus comme CEE avec qualification. **Source :** donnée calculée. **Compatibilité :** Teamword / Word / Writer. **Statut :** recommandé. **Remarque :** formaté sur deux décimales. **Voir aussi :** [[Contrats, CCNS et CEE]].

<a id="champs-personnalises"></a>
## Champs personnalisés

Deux mécanismes rendent impossible une liste statique finie de tous les noms créés par les utilisateurs :

1. **Champs personnalisés de publipostage par catégorie** : l’assistant lit `publipostage_champs` pour la catégorie courante. Le nom et la valeur par défaut sont définis dans le dossier ; l’étape de vérification permet d’ajouter, modifier ou supprimer ces champs.
2. **Champs personnalisés de contrat** : `contrats_champs.mot_cle` fournit les noms et `contrats_valchamps` la valeur du contrat. Les noms vides ou non textuels sont ignorés.

Si un champ personnalisé porte le nom `MONCHAMP`, la syntaxe du modèle est `{MONCHAMP}`. Les champs de `publipostage_champs` sont signalés par `*` dans la grille/PDF de l’assistant. Pour connaître ceux d’un dossier précis, lancez le publipostage et utilisez **Vérification des données du document** ; le bouton **Imprimer** génère la liste des mots-clés et valeurs du contexte courant.

## Alias, historiques et noms à ne pas confondre

- `{BRUTMENS}` est une compatibilité historique de `{SALAIREBRUTMENSUEL}`.
- `{CLASSIFICATION}` reste accepté pour les anciens modèles ; sans classification ancienne, il reprend le groupe CCNS ou à défaut la qualification CEE.
- `{VALEURPOINT}` reste disponible pour les contrats historiques qui référencent une valeur du point.
- `NOM_PRENOM*1` et `NOM_PRENOM*1_DATEDEBUT_DATEFIN` sont des **règles internes de nommage des fichiers**, pas des balises de document.
- `OFFRE_INTITULE`, `OFFRE_DETAIL`, `OFFRE_DATEDEBUT`, `OFFRE_DATEFIN` et `OFFRE_REFERENCE_ANPE` sont construits par une fonction auxiliaire, mais ne sont pas ajoutés aux quatre contextes génériques actuels ; ils ne sont pas documentés comme mots-clés disponibles.
- `NUM_SIRET`, `CIVILITE_SALARIE` et les autres identifiants du module DPAE/DUE pilotent son formulaire/PDF ; ils ne sont pas des mots-clés du moteur générique.

<a id="valeurs-vides-et-balises-inconnues"></a>
## Valeurs vides et balises inconnues

- De nombreux champs sont initialisés à `""` lorsque la donnée manque ; une balise connue est alors remplacée par du texte vide.
- Un champ personnalisé de contrat déclaré sans valeur apparaît dans la liste des mots-clés mais reste vide dans la grille.
- Si l’objet métier demandé n’existe pas, la fonction d’import peut renvoyer un jeu de données vide ; contrôlez la grille avant validation.
- Le remplacement parcourt uniquement les mots-clés connus du contexte. Une balise inconnue n’est pas ajoutée à la liste et reste donc visible dans le modèle/résultat des moteurs inspectés.
- Utilisez les formes exactes documentées. Le pilote Writer effectue une recherche sensible à la casse.

## Exemples de modèles

### Courrier simple

```text
Bonjour {CIVILITE} {PRENOM} {NOM},

Nous vous écrivons à l'adresse suivante :
{ADRESSERESID}
{CPRESID} {VILLERESID}
```

**Mots-clés utilisés :** [`{CIVILITE}`](#publipostage-civilite), [`{PRENOM}`](#publipostage-prenom), [`{NOM}`](#publipostage-nom), [`{ADRESSERESID}`](#publipostage-adresseresid), [`{CPRESID}`](#publipostage-cpresid), [`{VILLERESID}`](#publipostage-villeresid).

### Attestation

```text
Je soussigné atteste que {PRENOM} {NOM}, né(e) le {DATENAISS},
est enregistré(e) dans Teamworks-CCNS.
```

**Mots-clés utilisés :** [`{PRENOM}`](#publipostage-prenom), [`{NOM}`](#publipostage-nom), [`{DATENAISS}`](#publipostage-datenaiss).

### Document contractuel

```text
Contrat de {PRENOM} {NOM}
Type : {TYPECONTRAT}
Période : du {DATEDEBUT} au {DATEFIN}
Convention : {CONVENTION}
Groupe CCNS : {GROUPECCNS}
Durée hebdomadaire : {DUREEHEBDO}
Salaire brut mensuel : {SALAIREBRUTMENSUEL}
Minimum retenu : {MINIMUMRETENU}
Contrôle : {CONFORMITEREMUNERATION}
```

### Courrier de candidature

```text
Bonjour {PRENOM} {NOM},

Votre candidature déposée le {DATEDEPOT} pour {OFFREDEMPLOI}
a été enregistrée. Décision actuelle : {DECISION}.
```

**Mots-clés utilisés :** [`{DATEDEPOT}`](#publipostage-datedepot), [`{OFFREDEMPLOI}`](#publipostage-offredemploi), [`{DECISION}`](#publipostage-decision).

## Provenance et exhaustivité

Inventaire vérifié dans `teamworks/Utils/UTILS_Publipostage_donnees.py` : `GetDonneesDocument`, `Importation_personne`, `Importation_candidat`, `Importation_candidature` et `Importation_contrat`. Syntaxe/remplacement vérifiés dans `DLG_Publiposteur.py`, `DLG_Teamword.py` et `UTILS_Pilotageooo.py`.

Le script `tools/validate_wiki_publipostage.py` compare les listes statiques de ces quatre fonctions avec les 47 fiches/ancres de cette page et contrôle les liens wiki vers les ancres. Les noms issus des tables personnalisables en base ne peuvent pas être déterminés exhaustivement sans ouvrir un dossier utilisateur ; cette limite est documentée plutôt que remplacée par une liste inventée.
