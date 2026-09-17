# Recrutement

<a id="recrutement-vues"></a>
## À quoi ça sert ?

L’espace **Recrutement** suit les candidats avant et pendant leur candidature, puis permet de convertir un candidat en fiche **Individu** lorsque son dossier doit rejoindre le suivi courant.

## Où le trouver ?

Onglet principal **Recrutement**. La fiche individuelle contient aussi un onglet **Recrutement** pour les candidatures et entretiens déjà rattachés à cette personne.

## Les quatre vues réelles

La barre de navigation du module propose :

- **Candidats** ;
- **Candidatures** ;
- **Entretiens** ;
- **Offres d’emploi**.

Les actions générales sont ajouter, modifier, supprimer, filtres/tout afficher, colonnes, imprimer, export texte, export Excel et aide. **Courrier** n’est affiché que pour **Candidats** et **Candidatures**. L’export Excel est désactivé sous Linux dans le contrôleur wx actuel.

<a id="candidat"></a>
## Candidat

La fiche candidat regroupe : identité, adresse, coordonnées, qualifications, candidatures, entretiens et mémo. Les coordonnées peuvent être ajoutées/modifiées/supprimées ; une adresse email peut être utilisée pour lancer un email depuis son menu contextuel.

Un candidat possède ses propres coordonnées et qualifications tant qu’il n’a pas été converti en personne Teamworks.

<a id="candidature"></a>
## Candidature

Le dialogue de candidature comprend des sections vérifiées :

- **Dépôt de candidature** : date, canal de dépôt, remarques ;
- **Offre d’emploi** : offre liée ou candidature spontanée ;
- **Disponibilités** : périodes ajoutables, modifiables et supprimables ;
- **Poste souhaité** : fonctions et affectations ;
- **Réponse** : décision et suivi de la réponse communiquée.

Choisir une offre peut préremplir ses périodes de disponibilité, fonctions et affectations dans la candidature.

<a id="conversion-candidat"></a>
## Passer d’un candidat à un individu

Le code contient une action réelle de **conversion de fiche**. Elle :

1. crée une fiche Personne/Individu à partir de l’identité, de l’adresse et du mémo du candidat ;
2. transfère ses coordonnées et qualifications ;
3. rattache ses candidatures et entretiens à la nouvelle personne ;
4. retire les enregistrements propres au candidat converti ;
5. propose d’ouvrir la nouvelle fiche individuelle.

Schéma fonctionnel simplifié :

```text
Candidat
   ↓
Candidature
   ↓
Personne / Individu
   ↓
Contrat
```

Le dernier passage n’est pas automatique : un **Contrat** est ensuite créé depuis la fiche de l’Individu.

<a id="publipostage-recrutement"></a>
## Publipostage depuis le recrutement

Deux contextes sont directement utilisables depuis le bouton **Courrier** :

- **Candidat** : identité, coordonnées, qualifications et mémo ;
- **Candidature** : identité provenant du candidat ou de la personne liée, plus dépôt, offre, disponibilités, fonctions, affectations, décision et réponse.

Les quatre contextes génériques du moteur sont :

| Contexte | Point d’usage |
|---|---|
| **Individu / Personne** | liste/fiches Individus |
| **Candidat** | Recrutement > Candidats |
| **Candidature** | Recrutement > Candidatures |
| **Contrat** | documents d’un contrat |

Voir l’[index Candidat](Mots-clés-de-publipostage#index-contexte-candidat) et l’[index Candidature](Mots-clés-de-publipostage#index-contexte-candidature).

## Résultat attendu

Les listes et le panneau de résumé reflètent le type de vue choisi. Une conversion réussie déplace le suivi vers une fiche Individu tout en conservant les liaisons de candidatures/entretiens prévues par le code.

## Points d’attention

- Après conversion, une candidature utilise les données de la **Personne** liée plutôt que les anciennes données Candidat.
- `{QUALIFICATIONS}` et `{MEMO}` appartiennent au contexte Candidat ; ils ne deviennent pas automatiquement des champs Personne.
- Les scénarios complets entretien → décision → embauche restent **À confirmer en recette fonctionnelle**.

## Liens associés

[[Individus et fiches]] · [[Mots-clés de publipostage]] · [[Publipostage et documents]] · [[Contrats, CCNS et CEE]]
