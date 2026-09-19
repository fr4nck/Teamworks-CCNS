# Documents et publipostage

## À quoi ça sert ?

Le publipostage produit un ou plusieurs documents à partir d'un modèle et des données Teamworks. Le même assistant peut piloter **Teamword** (éditeur interne), **Microsoft Word** ou **LibreOffice Writer**, avec une voie Email Teamword distincte.

## Où le trouver ?

Parcours confirmés dans le code :

- **Individus > sélection > Courrier** pour une ou plusieurs personnes ;
- **Recrutement > Candidats/Candidatures > sélection > Courrier** ;
- l'onglet **Contrats** de la fiche individuelle, bouton **Imprimer un document** — seul point d'entrée qui ajoute l'alias `{BRUTJOUR}` et la [couche moderne RH](../publipostage/mots-cles.md#couche-moderne-rh) ;
- le **Registre unique du personnel** (liste de tous les contrats) ;
- **Outils > Créer des courriers ou des emails par publipostage** pour le sélecteur généraliste multi-catégories.

## Guide de bout en bout {#publipostage-parcours}

### 1. Choisir le contexte

Le moteur générique connaît quatre contextes : **Individu**, **Candidat**, **Candidature**, **Contrat**. Le point d'entrée détermine les mots-clés réellement disponibles — voir [Contextes d'utilisation](../publipostage/contextes.md).

### 2. Choisir les personnes ou données

Sélectionnez les lignes ou le contrat concernés. L'assistant construit un jeu de données par destinataire/élément.

### 3. Vérifier les données

L'étape **Vérification des données du document** affiche les mots-clés et leurs valeurs. C'est le meilleur endroit pour repérer une donnée vide avant fusion. Les cellules peuvent être corrigées pour le document courant ; l'écran permet aussi de gérer les champs personnalisés et d'imprimer la liste en PDF.

### 4. Choisir l'éditeur

L'assistant propose quatre voies :

1. **Microsoft Word** (automatisation COM) ;
2. **LibreOffice Writer** — libellé historique « OpenOffice Writer » dans l'interface, pilote technique UNO/`soffice` ;
3. **Traitement de texte intégré Teamword** — voir [Éditeur interne](editeur.md) ;
4. **Éditeur Email Teamword** — même fenêtre que 3, ouverte pour composer un email.

### 5. Choisir, créer ou importer le modèle

| Éditeur | Extension de modèle |
|---|---|
| Teamword | `.twd` |
| Microsoft Word | `.doc` |
| LibreOffice Writer | `.odt` |

La page des modèles expose **Importer**, actualiser la liste, **Ajouter**, **Modifier** et **Supprimer**.

### 6. Insérer les mots-clés

La syntaxe commune est `{MOTCLE}`. Utilisez uniquement un mot-clé présent dans votre contexte — voir la [référence des mots-clés](../publipostage/mots-cles.md) et les [exemples](../publipostage/exemples.md).

### 7. Lancer la fusion et vérifier

L'assistant remplace les balises connues pour chaque document et affiche la progression. Une donnée connue mais absente est généralement remplacée par une chaîne vide (avec quelques exceptions non normalisées — voir la [référence des mots-clés](../publipostage/mots-cles.md#compatibilite-et-comportement)). Une balise inconnue du contexte n'est jamais recherchée et peut rester visible : relisez toujours le résultat.

### 8. Enregistrer, imprimer ou prévisualiser

Selon la voie choisie, les options proposent sauvegarde, répertoire/nom de fichier, impression, nombre d'exemplaires, imprimante et aperçu. La voie Email possède ses propres paramètres d'expédition, sujet et pièces jointes.

## Microsoft Word

La voie Word automatise Microsoft Word via COM (`win32com`) et utilise `.doc`. Word doit être installé et accessible à l'automatisation sur le poste Windows.

!!! warning "À confirmer en recette fonctionnelle"
    Compatibilité avec chaque version moderne de Microsoft Office utilisée sur les postes réels.

## LibreOffice Writer

L'interface conserve le nom historique « OpenOffice Writer ». Le pilote technique utilise UNO/`soffice` et des modèles `.odt` ; cette documentation emploie **LibreOffice Writer** comme terme actuel tout en signalant cette compatibilité historique. La recherche/remplacement Writer est sensible à la casse.

!!! warning "À confirmer en recette fonctionnelle"
    Versions exactes de LibreOffice/OpenOffice supportées sur chaque plateforme livrée.

## Teamword

Teamword reste dans Teamworks, utilise des modèles `.twd` et affiche la liste des mots-clés du contexte ; un double-clic insère la balise. Il sait prévisualiser, imprimer et convertir le document en HTML pour l'envoi par email. Voir [Éditeur interne (Teamword)](editeur.md) pour le détail complet de ses fonctionnalités.

## Résultat attendu

Chaque élément sélectionné produit un document fusionné selon le modèle choisi et les options de sortie. Le document final doit être relu avant tout usage officiel.

## Problèmes fréquents

- **Balise visible :** vérifier orthographe, accolades, casse et contexte.
- **Valeur vide :** vérifier l'étape « Vérification des données » et la donnée source.
- **Word ne s'ouvre pas :** contrôler installation/automatisation Word.
- **Writer ne s'ouvre pas :** contrôler UNO/`soffice`.
- **Modèle absent :** vérifier extension et répertoire des modèles.
- **Un jeton comme `{NBREJOURS}` ou `{REPARTITION}` reste visible :** ce ne sont pas des mots-clés du moteur — voir l'avertissement dans la [référence des mots-clés](../publipostage/mots-cles.md).

Voir [Problèmes fréquents](../reference/problemes-frequents.md) pour la liste complète.

## Voir aussi

[Éditeur interne (Teamword)](editeur.md) · [Référence des mots-clés](../publipostage/mots-cles.md) · [Contextes d'utilisation](../publipostage/contextes.md) · [Individus et fiches](individus.md) · [Recrutement](recrutement.md) · [Contrats, CCNS et CEE](contrats-ccns-cee.md)
