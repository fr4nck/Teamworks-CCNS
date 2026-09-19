# Trajectoire Qt

!!! danger "Prévu, sans aucun code à ce jour"
    Recherche exhaustive dans le dépôt (`PyQt5`, `PyQt6`, `PySide2`, `PySide6`, `QtWidgets`, `QtCore`) : les seules occurrences sont des **exclusions de build** cx_Freeze (`setup.py`, `setup_rc1.py`), pas du code Qt. **Il n'existe aucun import, widget, fenêtre ou module Qt fonctionnel dans ce dépôt** — ni prototype isolé, ni spike technique. Cette page décrit une **vision de conception**, pas un chantier en cours. Ne présentez jamais une fonction comme « disponible en Qt » ou même « expérimentale côté Qt » sur la seule base de cette page.

## Pourquoi une évolution est envisagée

La Vanilla wx dispose aujourd'hui de [Teamword](../utilisation/editeur.md), fondé sur `wx.richtext.RichTextCtrl`. Le document y est fortement lié au widget : le buffer RichText sert à la fois d'état du document, de format de sauvegarde et de base de l'impression. Une éventuelle évolution viserait à découpler le modèle de document du widget d'édition.

## Deux héritages qui inspirent la réflexion

- **Teamword** apporte l'expérience de rédaction fluide (texte continu, mise en forme, images, liens, insertion de mots-clés).
- **NoeDoc** (moteur historique de Noethys) apporte l'idée d'un document composé d'objets identifiés, positionnés en X/Y, rendus indépendamment de l'éditeur — mais son modèle reste fortement couplé à wx et ne serait pas porté tel quel.

## Cible envisagée : un modèle documentaire indépendant

```text
DocumentModel
     │
     ├── éditeur Qt (hypothétique)
     ├── rendu PDF / impression
     ├── rendu email
     └── importeurs legacy (.twd)
```

Idées associées, non implémentées :

- variables de publipostage comme éléments atomiques (`MergeField`) plutôt que du texte modifiable caractère par caractère (`{CLE}` resterait la syntaxe visible) ;
- images comme ressources adressables (`AssetRef`) plutôt que bitmaps attachés au document ;
- un `PageMaster` pour mutualiser logo, en-tête, pied de page et pagination entre documents ;
- des fonctions absentes de Teamword aujourd'hui : tableaux, sections, sauts de page/section manuels, en-têtes/pieds de page par section.

## Principe de migration envisagé

Si ce chantier démarrait un jour, les fichiers `.twd` existants seraient traités comme du contenu legacy à importer (jamais comme le nouveau format), sans réinventer de saut de page/section à partir de lignes vides, et en préservant l'original tant que la migration ne serait pas validée.

## Points explicitement non tranchés

Avant tout début d'implémentation, resteraient à décider : éditeur Qt natif ou éditeur web embarqué, comportement réellement atomique des `MergeField`, moteur PDF et tableaux multi-pages, fidélité de l'import `.twd`, collage depuis Word/LibreOffice.

## Principe pour tout nouveau composant métier

Indépendamment de Qt, la ligne directrice du projet est que les nouveaux composants métier ne dépendent pas directement de wx ou Qt lorsque ce n'est pas nécessaire — l'interface consomme un moteur testable séparément. C'est déjà le principe suivi par la couche `domain/`/`application/` décrite dans [Architecture — vue d'ensemble](vue-ensemble.md). Cela ne signifie pas une réécriture immédiate de la Vanilla wx.

## Voir aussi

[Éditeur interne (Teamword)](../utilisation/editeur.md) · [Architecture — vue d'ensemble](vue-ensemble.md) · [FormEngine et questionnaires](formengine-questionnaires.md) · [Référence des mots-clés](../publipostage/mots-cles.md)
