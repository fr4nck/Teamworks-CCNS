# Publipostage et documents

<a id="publipostage-parcours"></a>
## À quoi ça sert ?

Le publipostage produit plusieurs documents à partir d’un modèle et des données Teamworks. Le même assistant peut piloter **Teamword**, **Microsoft Word** ou **Writer**, avec une voie Email Teamword distincte.

## Où le trouver ?

Parcours confirmés :

- **Individus > Courrier** pour une ou plusieurs personnes ;
- **Recrutement > Candidats/Candidatures > Courrier** ;
- les documents de **Contrat** depuis l’onglet Contrats lorsque le parcours appelle le contexte contrat ;
- **Outils > Créer des courriers ou des emails par publipostage** pour l’assistant général.

## Guide de bout en bout

### 1. Choisir le contexte

Le moteur générique connaît quatre contextes : **Individu/Personne**, **Candidat**, **Candidature**, **Contrat**. Le point d’entrée détermine les mots-clés réellement disponibles.

### 2. Choisir les personnes ou données

Sélectionnez les lignes ou le contrat concernés. L’assistant construit un document de données par destinataire/élément.

### 3. Vérifier les données

L’étape **Vérification des données du document** affiche les mots-clés et leurs valeurs. C’est le meilleur endroit pour repérer une donnée vide avant fusion. Les cellules peuvent être corrigées pour le document courant ; l’écran permet aussi de gérer les champs personnalisés et d’imprimer la liste en PDF.

### 4. Choisir l’éditeur

L’assistant propose quatre voies :

1. **Microsoft Word** ;
2. **Writer** — libellé historique « OpenOffice Writer » ;
3. **Traitement de texte intégré Teamword** ;
4. **Éditeur Email Teamword**.

### 5. Choisir, créer ou importer le modèle

Extensions utilisées :

| Éditeur | Modèle |
|---|---|
| Teamword | `.twd` |
| Microsoft Word | `.doc` |
| Writer | `.odt` |

La page des modèles expose **Importer**, actualiser la liste, **Ajouter**, **Modifier** et **Supprimer**.

### 6. Insérer les mots-clés

La syntaxe commune est `{MOTCLE}`. Exemple fictif :

```text
Bonjour {CIVILITE} {NOM},

Votre contrat débute le {DATEDEBUT}.
Salaire brut mensuel : {SALAIREBRUTMENSUEL}
```

Utilisez uniquement un mot-clé présent dans votre contexte : [[Mots-clés de publipostage]].

### 7. Lancer la fusion et vérifier

L’assistant remplace les balises connues pour chaque document et affiche la progression. Une donnée connue mais absente est généralement remplacée par une chaîne vide. Une balise inconnue du contexte n’est pas devinée et peut rester visible : relisez le résultat.

### 8. Enregistrer, imprimer ou prévisualiser

Selon la voie choisie, les options proposent sauvegarde, répertoire/nom de fichier, impression, nombre d’exemplaires, imprimante et aperçu. La voie Email possède ses paramètres d’expédition, sujet et pièces jointes.

<a id="publipostage-teamword"></a>
## Teamword

Teamword reste dans Teamworks, utilise des modèles `.twd` et affiche la liste des mots-clés ; un double-clic insère la balise. Il sait prévisualiser, imprimer et convertir le document en HTML. Voir [[Éditeur interne et documents]].

<a id="publipostage-word"></a>
## Microsoft Word

La voie Word automatise Microsoft Word et utilise `.doc`. Word doit être installé et accessible à l’automatisation du poste Windows. La création d’un modèle peut ouvrir Word avec un texte d’exemple et la liste des mots-clés.

**À confirmer en recette fonctionnelle :** compatibilité avec chaque version moderne de Microsoft Office utilisée sur les postes réels.

<a id="publipostage-writer"></a>
## LibreOffice Writer

L’interface conserve le nom historique « OpenOffice Writer ». Le pilote technique utilise UNO/`soffice` et des modèles `.odt`; la documentation emploie **LibreOffice Writer** comme terme utilisateur actuel tout en signalant cette compatibilité historique.

La recherche/remplacement Writer audité est sensible à la casse. Le fonctionnement dépend d’une installation UNO/`soffice` compatible.

**À confirmer en recette fonctionnelle :** versions exactes de LibreOffice/OpenOffice supportées sur chaque plateforme livrée.

<a id="champs-personnalises-publipostage"></a>
## Champs personnalisés

Un champ personnalisé est une valeur définie dans votre dossier qui rejoint les données du publipostage pour une catégorie donnée. Son nom de balise dépend de la base ; il ne peut donc pas être listé universellement dans ce wiki.

Pour retrouver son mot-clé exact :

1. ouvrez le publipostage dans le bon contexte ;
2. allez à **Vérification des données du document** ;
3. relevez le nom affiché dans la grille ou dans la gestion des champs ;
4. pour les champs de contrat, contrôlez aussi **Paramétrage > Contrats > Les champs de contrats**.

N’inventez jamais une balise à partir du libellé d’un champ.

## Résultat attendu

Chaque élément sélectionné produit un document fusionné selon le modèle choisi et les options de sortie. Le document final doit être relu avant usage officiel.

## Problèmes fréquents

- **Balise visible :** vérifier orthographe, accolades, casse et contexte.
- **Valeur vide :** vérifier l’étape 2 et la donnée source.
- **Word ne s’ouvre pas :** contrôler installation/automatisation Word.
- **Writer ne s’ouvre pas :** contrôler UNO/`soffice`.
- **Modèle absent :** vérifier extension et répertoire des modèles.

Voir [[Problèmes fréquents]].

## Liens associés

[[Éditeur interne et documents]] · [[Mots-clés de publipostage]] · [[Individus et fiches]] · [[Recrutement]] · [[Contrats, CCNS et CEE]]
