# Contextes d'utilisation

Cette page répond à deux questions symétriques : « je rédige tel type de document, quels mots-clés puis-je utiliser ? » et « ce mot-clé, dans quels contextes fonctionne-t-il ? ». Elle est construite depuis le même code que la [référence des mots-clés](mots-cles.md) — voir cette page pour le détail de chaque balise.

Il n'existe **aucun contexte** « présences », « planning », « frais » ou « DPAE » dans le moteur de publipostage actuel : ne proposez jamais un mot-clé de ces domaines, il ne sera pas reconnu.

## Contexte → mots-clés disponibles

### Individu (Personne)

Ouvert depuis **Individus > sélection > Courrier**.

`{CIVILITE}` `{NOM}` `{NOMJFILLE}` `{PRENOM}` `{DATENAISS}` `{AGE}` `{CPNAISS}` `{VILLENAISS}` `{PAYSNAISS}` `{NATIONALITE}` `{NUMSECU}` `{ADRESSERESID}` `{CPRESID}` `{VILLERESID}` `{SITUATION}` `{TELEPHONES}` `{EMAILS}` `{FAX}`

+ les [champs personnalisés de publipostage](mots-cles.md#champs-personnalises) configurés dans votre dossier.

### Candidat

Ouvert depuis **Recrutement > Candidats > sélection > Courrier**.

`{CIVILITE}` `{NOM}` `{PRENOM}` `{DATENAISS}` `{AGE}` `{ADRESSERESID}` `{CPRESID}` `{VILLERESID}` `{TELEPHONES}` `{FAX}` `{EMAILS}` `{QUALIFICATIONS}` `{MEMO}`

+ les champs personnalisés de publipostage.

### Candidature

Ouvert depuis **Recrutement > Candidatures > sélection > Courrier**.

Charge d'abord soit les mots-clés **Individu** complets (18, si un `IDpersonne` est lié), soit ceux du **Candidat** (13, sinon), puis ajoute toujours :

`{DATEDEPOT}` `{TYPEDEPOT}` `{OFFREDEMPLOI}` `{DISPONIBILITES}` `{FONCTIONS}` `{AFFECTATIONS}` `{DECISION}` `{DATEREPONSE}` `{TYPEREPONSE}`

+ les champs personnalisés de publipostage.

### Contrat

Ouvert depuis **Individus > fiche > onglet Contrats > Courrier / Imprimer un document**, ou depuis le Registre unique du personnel.

Hérite toujours des 18 mots-clés **Individu** du titulaire, puis ajoute :

`{DATEDEBUT}` `{DATEFIN}` `{CLASSIFICATION}` `{TYPECONTRAT}` `{VALEURPOINT}` `{ESSAI}` `{CONVENTION}` `{GROUPECCNS}` `{QUALIFICATIONCEE}` `{DUREEHEBDO}` `{SALAIREBRUTMENSUEL}` `{MINIMUMCCNS}` `{MINIMUMSMIC}` `{MINIMUMRETENU}` `{CONFORMITEREMUNERATION}` `{BAREMECEE}` `{MINIMUMCEE}`

+ les [champs de contrat](mots-cles.md#champs-personnalises) (stockés par contrat) et les champs personnalisés de publipostage.

!!! warning "Uniquement depuis la fiche contrat : `{BRUTJOUR}` et la couche RH"
    Le bouton **Imprimer un document** de l'onglet Contrats (et lui seul) ajoute en plus l'alias `{BRUTJOUR}` (si `QUALIFICATIONCEE`/`BAREMECEE` sont renseignés) et les clés `STRUCTURE_*`/`SALARIE_*`/`CONTRAT_*` de la [couche moderne RH](mots-cles.md#couche-moderne-rh). Le sélecteur générique de publipostage ne les propose pas.

## Mot-clé → contextes compatibles

| Mot-clé | Individu | Candidat | Candidature | Contrat |
|---|:---:|:---:|:---:|:---:|
| `CIVILITE` | ✓ | ✓ | ✓ | ✓ |
| `NOM` | ✓ | ✓ | ✓ | ✓ |
| `NOMJFILLE` | ✓ | — | ✓ (si Personne liée) | ✓ |
| `PRENOM` | ✓ | ✓ | ✓ | ✓ |
| `DATENAISS` | ✓ | ✓ | ✓ | ✓ |
| `AGE` | ✓ | ✓ | ✓ | ✓ |
| `CPNAISS` | ✓ | — | ✓ (si Personne liée) | ✓ |
| `VILLENAISS` | ✓ | — | ✓ (si Personne liée) | ✓ |
| `PAYSNAISS` | ✓ | — | ✓ (si Personne liée) | ✓ |
| `NATIONALITE` | ✓ | — | ✓ (si Personne liée) | ✓ |
| `NUMSECU` | ✓ | — | ✓ (si Personne liée) | ✓ |
| `ADRESSERESID` | ✓ | ✓ | ✓ | ✓ |
| `CPRESID` | ✓ | ✓ | ✓ | ✓ |
| `VILLERESID` | ✓ | ✓ | ✓ | ✓ |
| `SITUATION` | ✓ | — | ✓ (si Personne liée) | ✓ |
| `TELEPHONES` | ✓ | ✓ | ✓ | ✓ |
| `EMAILS` | ✓ | ✓ | ✓ | ✓ |
| `FAX` | ✓ | ✓ | ✓ | ✓ |
| `QUALIFICATIONS` | — | ✓ | ✓ (si Candidat non converti) | — |
| `MEMO` | — | ✓ | ✓ (si Candidat non converti) | — |
| `DATEDEPOT`, `TYPEDEPOT`, `OFFREDEMPLOI`, `DISPONIBILITES`, `FONCTIONS`, `AFFECTATIONS`, `DECISION`, `DATEREPONSE`, `TYPEREPONSE` | — | — | ✓ | — |
| `DATEDEBUT`, `DATEFIN`, `CLASSIFICATION`, `TYPECONTRAT`, `VALEURPOINT`, `ESSAI`, `CONVENTION`, `GROUPECCNS`, `QUALIFICATIONCEE`, `DUREEHEBDO`, `SALAIREBRUTMENSUEL`, `MINIMUMCCNS`, `MINIMUMSMIC`, `MINIMUMRETENU`, `CONFORMITEREMUNERATION`, `BAREMECEE`, `MINIMUMCEE` | — | — | — | ✓ |
| `BRUTJOUR` | — | — | — | ✓ (fiche contrat uniquement) |

## Voir aussi

[Référence des mots-clés](mots-cles.md) · [Exemples](exemples.md) · [Documents et publipostage](../utilisation/documents.md)
