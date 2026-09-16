# Éditeur interne et documents

**Teamword** est l’éditeur RichText intégré de Teamworks-CCNS wx. Il peut être utilisé directement ou comme moteur de modèles du publipostage.

<a id="teamword-ouvrir"></a>
## Où le trouver ?

- **Outils > Teamword, l’éditeur de texte** pour ouvrir l’éditeur ;
- **Outils > Éditeur d’Emails** pour la voie email ;
- dans le publipostage, choisir **Traitement de texte intégré** ou **Éditeur Email Teamword**.

<a id="teamword-fichiers"></a>
## Créer, ouvrir et enregistrer

Teamword sait :

- créer un nouveau document ;
- ouvrir un document ;
- enregistrer ;
- **Enregistrer sous** ;
- fermer un document ;
- travailler avec plusieurs documents dans des onglets.

Lors de la fermeture d’un document modifié non enregistré, l’éditeur demande si les changements doivent être sauvegardés. Les modèles de publipostage Teamword utilisent `.twd`.

<a id="teamword-formatage"></a>
## Mise en forme

Les commandes auditées couvrent :

- choix de police et couleur ;
- gras, italique, souligné ;
- alignement gauche, centré, droit ;
- retraits ;
- espacement des paragraphes ;
- interligne ;
- liens/URL ;
- images.

Teamword est un éditeur intégré et ne prétend pas reproduire toutes les fonctions de Word ou Writer.

<a id="teamword-recherche"></a>
## Recherche et remplacement

L’éditeur possède des commandes de recherche et de remplacement dans le document courant. Vérifiez le résultat lorsqu’un même texte apparaît plusieurs fois ou dans un document complexe.

<a id="teamword-mots-cles"></a>
## Mots-clés de publipostage

Lorsqu’il est ouvert avec un contexte de publipostage, Teamword affiche **Liste des mots-clés**. Un double-clic sur un mot-clé l’insère à la position du curseur.

Accès direct à la référence :

- [index alphabétique](Mots-clés-de-publipostage#index-alphabetique) ;
- [index Individu](Mots-clés-de-publipostage#index-contexte-individu) ;
- [index Contrat](Mots-clés-de-publipostage#index-contexte-contrat) ;
- [index Recrutement](Mots-clés-de-publipostage#index-usage-recrutement).

Exemples fréquents : [`{NOM}`](Mots-clés-de-publipostage#publipostage-nom), [`{PRENOM}`](Mots-clés-de-publipostage#publipostage-prenom), [`{DATEDEBUT}`](Mots-clés-de-publipostage#publipostage-datedebut).

<a id="teamword-apercu-impression"></a>
## Aperçu et impression

Teamword utilise `wx.PrintPreview` pour l’aperçu avant impression et la boîte d’impression système pour imprimer. Le publipostage peut aussi enchaîner automatiquement sauvegarde, aperçu et impression selon les options choisies.

<a id="teamword-html-email"></a>
## HTML et Email

Le moteur sait convertir le RichText en HTML et intégrer les images nécessaires au contenu HTML. La voie Email du publipostage utilise Teamword comme éditeur et peut prendre `{EMAILS}` comme destinataire du document courant, avec sujet et pièces jointes configurés dans l’assistant.

**À confirmer en recette fonctionnelle :** rendu HTML final dans les différents clients de messagerie et comportement des images/encodages complexes.

## Résultat attendu

Un document `.twd` peut être réouvert, modifié, fusionné, prévisualisé ou imprimé. En publipostage, seules les balises connues du contexte sont remplacées automatiquement.

## Points d’attention

- L’aide historique interne de Teamword indique qu’elle est incomplète ; ce wiki décrit les fonctions observées dans le code actuel.
- Une balise inconnue peut rester affichée dans le résultat.
- Pour un modèle nécessitant des fonctions bureautiques externes, choisissez Word ou Writer dans l’assistant.

## Problèmes fréquents

Pour un document qui ne s’ouvre pas, une balise vide ou un problème de modèle, voir [[Problèmes fréquents]].

## Liens associés

[[Publipostage et documents]] · [[Mots-clés de publipostage]] · [[Problèmes fréquents]]
