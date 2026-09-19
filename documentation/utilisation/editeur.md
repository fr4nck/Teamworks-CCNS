# Éditeur interne (Teamword)

**Teamword** est l'éditeur de texte enrichi intégré à Teamworks-CCNS wx (`teamworks/Dlg/DLG_Teamword.py`), basé sur le composant natif `wx.richtext.RichTextCtrl`. Ce n'est ni du HTML pur ni du RTF Microsoft : c'est le moteur RichText propre à wxWidgets, avec sa propre représentation XML.

!!! info "Éditeur actuel de la Vanilla wx"
    Cette page décrit l'éditeur réellement disponible aujourd'hui. Le chantier d'un futur moteur documentaire pour la trajectoire Qt est une vision non commencée — voir [Trajectoire Qt](../architecture/qt.md).

## Où le trouver ?

- **Outils > Teamword, l'éditeur de texte** : ouvre l'éditeur vide, sans mots-clés de publipostage.
- Depuis le [publipostage](documents.md), en choisissant **Traitement de texte intégré** (création/modification de modèle) ou **Éditeur Email Teamword** — ces deux choix ouvrent en réalité la même fenêtre Teamword, avec le panneau de mots-clés activé.

Un composant frère mais distinct, `teamworks/Ctrl/CTRL_Editeur_email.py`, gère les modèles d'email indépendants du publipostage (accessible via `DLG_Saisie_modele_email.py`). Il partage la même technologie RichText et les mêmes commandes de mise en forme, mais utilise son propre format XML « Noetext » (`.ntx`), distinct de `.twd`.

## Créer, ouvrir et enregistrer

Teamword sait créer, ouvrir, enregistrer (« Enregistrer sous » compris), fermer, et gérer plusieurs documents dans des onglets (`wx.aui.AuiNotebook`). Il demande confirmation avant de fermer un document modifié non enregistré.

### Format `.twd`

`.twd` est le format natif de Teamword : une variante du XML natif de `wx.richtext`, enregistrée sous une extension et un nom de handler personnalisés (`RichTextXMLHandler(name="Teamword", ext="twd")`). Ce n'est **pas** un format Word (`.doc`/`.docx`) ni OpenDocument (`.odt`) : dans le [publipostage](documents.md), Word utilise `.doc` et Writer utilise `.odt`, chacun via son propre pilote d'automatisation (COM / UNO) — Teamword ne lit et n'écrit que `.twd` (et les formats génériques `wx.richtext` : texte brut, XML natif, HTML).

Les images insérées sont stockées en bitmap brut dans le XML : un document `.twd` avec plusieurs images peut devenir volumineux.

## Mise en forme

Commandes confirmées dans le code (menu Format et barre d'outils) :

- police et couleur de police ;
- gras, italique, souligné ;
- alignement gauche/centré/droit ;
- retraits (augmenter/diminuer) ;
- espacement des paragraphes ;
- interligne simple/1,5/double ;
- insertion de lien (URL) ;
- insertion d'image (JPEG/PNG/GIF, avec recadrage) ;
- rechercher / rechercher-remplacer (y compris remplacement global).

### Fonctions absentes de Teamword

Aucune trace dans le code de : tableaux, en-têtes/pieds de page, styles nommés, puces/numérotation, vérificateur orthographique, saut de page/section manuel. Pour un modèle nécessitant ces fonctions bureautiques, choisissez Word ou Writer dans l'assistant de publipostage.

## Mots-clés de publipostage

Lorsqu'il est ouvert depuis un contexte de publipostage, Teamword affiche un panneau **Liste des mots-clés** ancré à gauche. Un **double-clic** sur un mot-clé l'insère en texte brut `{MOTCLE}` à la position du curseur — il n'existe pas de raccourci clavier ni de menu contextuel dédié pour cette insertion. Ce panneau n'apparaît pas dans l'éditeur ouvert depuis **Outils > Teamword** (sans contexte).

Au moment de la fusion, `RemplaceMotscles()` recherche chaque `{MOTCLE}` (tolérant aux variations d'accolades) et remplace le texte trouvé par la valeur, en conservant le style du document.

Voir la [référence des mots-clés](../publipostage/mots-cles.md) et les [contextes d'utilisation](../publipostage/contextes.md).

## Aperçu, impression et export

- **Aperçu avant impression** : rendu standard `wx.PrintPreview`/`wx.PreviewFrame` via `wx.richtext.RichTextPrintout`.
- **Impression** : boîte de dialogue d'impression système standard, ou impression silencieuse (sans dialogue) pendant un lot de publipostage.
- **Aucun export PDF direct du document** n'est codé dans Teamword. Le seul export PDF du publipostage sert à imprimer la *liste des mots-clés disponibles*, pas le document produit. Un « export PDF » du document dépend donc uniquement d'un pilote d'imprimante virtuelle PDF installé sur le poste — **à confirmer en recette selon l'environnement**.
- Une fonction d'affichage HTML existe dans le code (`OnFileViewHTML`) mais ne semble reliée à aucun menu ou bouton actif — **à confirmer en recette**.

## HTML et email

Le moteur sait convertir le RichText en HTML (avec images encodées en base64) pour la voie Email : le panneau **Envoyer par Email** permet de configurer l'envoi, avec remplacement des mots-clés effectué directement dans le HTML avant envoi SMTP. `{EMAILS}` peut servir de destinataire du document courant.

!!! warning "À confirmer en recette fonctionnelle"
    Rendu HTML final dans les différents clients de messagerie, et comportement des images/encodages complexes.

## Aide intégrée

Le menu Aide de Teamword affiche actuellement le message « L'aide pour ce nouveau module est en cours de rédaction » — cette page en tient lieu en attendant.

## Héritage et évolution

Teamword reste l'éditeur de la Vanilla wx ; il n'est pas prévu de le remplacer brutalement. La trajectoire Qt, si elle aboutit un jour, étudierait un moteur documentaire distinct — voir [Trajectoire Qt](../architecture/qt.md). Les objectifs de conception qui y sont décrits ne sont **pas** des fonctions disponibles dans Teamword aujourd'hui.

## Résultat attendu

Un document `.twd` peut être réouvert, modifié, fusionné, prévisualisé ou imprimé. En publipostage, seules les balises connues du contexte sont remplacées automatiquement.

## Points d'attention

- Une balise inconnue peut rester affichée dans le résultat.
- Pour un modèle nécessitant des fonctions bureautiques externes (tableaux, en-têtes/pieds de page...), choisissez Word ou Writer.

## Voir aussi

[Documents et publipostage](documents.md) · [Référence des mots-clés](../publipostage/mots-cles.md) · [Trajectoire Qt](../architecture/qt.md) · [Problèmes fréquents](../reference/problemes-frequents.md)
