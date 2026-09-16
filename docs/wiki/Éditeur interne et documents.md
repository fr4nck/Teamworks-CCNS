# Éditeur interne et documents

**Teamword** est le traitement de texte intégré à Teamworks-CCNS wx. Il est implémenté dans `DLG_Teamword.py` avec `wx.richtext.RichTextCtrl` et est utilisé directement par l’assistant de publipostage.

## Comment l’ouvrir ?

Le parcours confirmé passe par l’assistant **Édition de documents** :

1. lancez un publipostage depuis un contexte pris en charge (par exemple Individus) ;
2. vérifiez les données ;
3. choisissez **Traitement de texte intégré** ;
4. à l’étape du modèle, cliquez sur **Ajouter** pour créer un `.twd` ou sélectionnez un modèle puis **Modifier**.

L’assistant peut aussi ouvrir Teamword en mode **Éditeur d’Email**.

## Créer et ouvrir des documents

Teamword sait créer un nouveau document, ouvrir un fichier, sauvegarder, sauvegarder sous un autre nom et fermer un document. Plusieurs documents peuvent être ouverts dans les onglets de son notebook. Lorsqu’un document modifié est fermé sans avoir été sauvegardé, Teamword demande s’il faut enregistrer les changements.

Dans le publipostage, les modèles Teamword sont filtrés sur l’extension `.twd`.

## Mise en forme disponible

Les commandes présentes dans l’éditeur couvrent :

- police et couleur de police ;
- gras, italique et souligné ;
- alignement gauche, centré et droit ;
- retraits gauche/droit ;
- réglages d’espacement de paragraphe ;
- interligne simple, intermédiaire et double ;
- URL ;
- image ;
- recherche et remplacement.

Le moteur peut aussi convertir le contenu RichText en HTML, notamment pour l’email.

## Insérer un mot-clé

Lorsqu’un contexte de publipostage fournit des variables, Teamword affiche un panneau **Liste des mots-clés**. Double-cliquez sur une entrée pour l’insérer à la position du curseur.

Exemples :

- [`{CIVILITE}`](Mots-clés-de-publipostage#publipostage-civilite)
- [`{NOM}`](Mots-clés-de-publipostage#publipostage-nom)
- [`{PRENOM}`](Mots-clés-de-publipostage#publipostage-prenom)
- [`{DATENAISS}`](Mots-clés-de-publipostage#publipostage-datenaiss)
- [`{ADRESSERESID}`](Mots-clés-de-publipostage#publipostage-adresseresid)
- [`{CPRESID}`](Mots-clés-de-publipostage#publipostage-cpresid)
- [`{VILLERESID}`](Mots-clés-de-publipostage#publipostage-villeresid)
- [`{TELEPHONES}`](Mots-clés-de-publipostage#publipostage-telephones)
- [`{EMAILS}`](Mots-clés-de-publipostage#publipostage-emails)

L’insertion automatique évite les erreurs d’accolades. Référence exhaustive : [[Mots-clés de publipostage]].

## Aperçu et impression

Teamword possède un **Aperçu avant impression** basé sur `wx.PrintPreview` et une impression via la boîte de dialogue système. Dans l’assistant de publipostage, l’impression peut aussi être lancée automatiquement avec le nombre d’exemplaires et l’imprimante choisis.

## Publipostage

Pour chaque document, l’assistant :

1. ouvre le modèle `.twd` ;
2. fournit la liste des valeurs du contexte ;
3. remplace les balises connues ;
4. sauvegarde et/ou imprime selon les options ;
5. ouvre éventuellement l’aperçu avant de continuer.

Une balise connue dont la valeur est vide devient vide. Une balise inconnue n’est pas dans la liste de remplacement et n’est pas corrigée automatiquement.

## Email intégré

Teamword peut convertir son contenu en HTML, intégrer les images dans le HTML et envoyer via les paramètres SMTP fournis par Teamworks. Le mode Email de l’assistant utilise l’adresse `{EMAILS}` du document comme destinataire et peut proposer un aperçu avant envoi.

## Limites actuelles

- L’aide interne de Teamword affiche explicitement que l’aide de ce module est **en cours de rédaction** ; ce wiki constitue donc la documentation utilisateur détaillée.
- Teamword est un éditeur RichText intégré, pas un clone complet de Word/Writer. Pour des modèles nécessitant des fonctions bureautiques externes spécifiques, utilisez le moteur correspondant.
- Les noms de champs personnalisés dépendent du dossier ; utilisez la grille de vérification plutôt qu’une ancienne liste papier.

## Teamword, Word ou Writer : quand choisir quoi ?

| Besoin | Teamword | Word | Writer |
|---|---|---|---|
| Rester dans Teamworks | **oui** | non | non |
| Insérer les mots-clés par double-clic | **oui** | non, liste fournie dans le modèle d’exemple | non, liste fournie dans le modèle d’exemple |
| Modèle géré par l’assistant | `.twd` | `.doc` | `.odt` |
| Dépendance externe | aucune suite bureautique pour l’édition Teamword | Microsoft Word | UNO/soffice compatible |
| Email HTML intégré | **oui** | non dans cette voie | non dans cette voie |

Voir [[Publipostage et documents]] pour le parcours de fusion complet.
