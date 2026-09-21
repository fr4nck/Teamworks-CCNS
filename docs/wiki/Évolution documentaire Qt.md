# Évolution documentaire Qt

> **Statut : conception / expérimentation.** Cette page décrit la cible envisagée pour la future interface Qt. Elle ne décrit pas une fonction disponible dans la Vanilla wx actuelle.

## Pourquoi faire évoluer l'éditeur ?

La Vanilla wx dispose aujourd'hui de **Teamword**, fondé sur `wx.richtext.RichTextCtrl`. Il permet la rédaction, la mise en forme, les images, les liens, le publipostage, l'aperçu et l'impression.

L'audit du code historique montre cependant que le document est fortement lié au widget wx : le buffer RichText sert à la fois d'état du document, de format de sauvegarde et de base de l'impression.

La future version Qt doit éviter de reproduire ce couplage.

## Deux héritages complémentaires

### Teamword

Teamword apporte principalement l'expérience de **rédaction fluide** :

- texte continu ;
- paragraphes ;
- police, taille et couleur ;
- gras, italique, souligné ;
- alignements et retraits ;
- recherche/remplacement ;
- insertion d'images et de liens ;
- insertion simple des mots-clés de publipostage.

### NoeDoc

Le moteur historique **NoeDoc** de Noethys apporte une autre idée : un document peut être composé d'objets identifiés et rendu indépendamment de l'éditeur.

Les concepts intéressants observés sont notamment :

- objets documentaires identifiés ;
- champs métier associés à des objets ;
- positionnement X/Y en millimètres ;
- ordre de rendu explicite ;
- images et objets spéciaux ;
- modèle de fond réutilisable (`IDfond`) ;
- rendu PDF via ReportLab sans passer directement par le widget d'édition.

NoeDoc ne doit pas être porté tel quel vers Qt : son modèle reste fortement couplé à wx, FloatCanvas et aux tables Noethys.

## Cible : un modèle documentaire indépendant

La cible étudiée est un `DocumentModel` sérialisable et versionné, indépendant de wx et de Qt.

```text
DocumentModel
     │
     ├── éditeur Qt
     ├── rendu PDF / impression
     ├── rendu email
     └── importeurs legacy
```

Qt doit être le premier client moderne du moteur documentaire, pas le moteur lui-même.

## Contenu fluide et mise en page avancée

Le mode normal reste la rédaction d'un document :

```text
Paragraphe
Paragraphe
Tableau
Paragraphe
Saut de page
Paragraphe
```

Une couche de positionnement précis peut être utilisée lorsque le document le nécessite :

```text
logo
bloc adresse
zone de signature
image
cadre
QR / code-barres éventuel
```

Le positionnement libre doit rester une fonction avancée, pas le mode normal de rédaction.

## Sections et pagination

Les concepts suivants sont nouveaux et n'existent pas explicitement dans Teamword :

- saut de page manuel ;
- sections ;
- changement d'orientation ;
- marges par section ;
- en-têtes et pieds de page ;
- pagination contrôlée.

La pagination automatique d'un flux long existe déjà historiquement via `RichTextPrintout`, mais le futur modèle doit la rendre indépendante de wx.

Exemple de cible :

```text
Section 1 : A4 portrait

Saut de section

Section 2 : A4 paysage
Tableau large

Saut de section

Section 3 : A4 portrait
Signatures
```

## Tableaux

Les tableaux constituent une fonction nouvelle du futur moteur. Ni Teamword ni NoeDoc ne fournissent aujourd'hui un véritable modèle de tableau adapté à ce besoin.

La cible doit permettre progressivement :

- lignes et colonnes ;
- largeur des colonnes ;
- bordures et alignements ;
- fusion de cellules ;
- texte riche ;
- mots-clés de publipostage dans les cellules ;
- continuation sur plusieurs pages ;
- répétition éventuelle de la ligne d'en-tête.

## Mots-clés et publipostage

La syntaxe historique `{CLE}` doit rester reconnue pour la compatibilité.

Dans le futur moteur, une variable doit cependant devenir un élément atomique (`MergeField`) plutôt qu'un simple texte modifiable caractère par caractère.

L'objectif est :

```text
DocumentModel
+
MergeContext
=
Document rendu
```

Le moteur documentaire ne doit pas aller chercher directement les données dans la base Teamworks.

## Images et ressources

Les images doivent devenir des ressources adressables (`AssetRef`) plutôt que des chemins locaux ou des bitmaps directement attachés au widget.

Cela doit permettre notamment :

- réutilisation d'un logo ;
- portabilité du document ;
- rendu PDF cohérent ;
- absence de chemins absolus dépendant du poste de travail.

## PageMaster

Le principe de `IDfond` de NoeDoc inspire un futur `PageMaster` pour mutualiser :

- logo ;
- en-tête ;
- pied de page ;
- coordonnées de la structure ;
- mentions récurrentes ;
- pagination.

Les valeurs métier restent fournies au rendu par le contexte de fusion ; le gabarit ne doit pas devenir une nouvelle source de vérité.

## Migration depuis Teamword

Les fichiers `.twd` existants doivent être considérés comme du **legacy à importer**, jamais comme le nouveau format documentaire.

Règle de migration prévue :

- conserver les paragraphes et lignes vides existants ;
- ne pas inventer de saut de page à partir de lignes vides ;
- ne pas inventer de saut de section ;
- laisser le nouveau renderer paginer automatiquement le flux importé ;
- préserver l'original tant que la migration n'est pas validée.

## Points encore à valider par prototype

Les décisions suivantes doivent être testées avant d'être figées :

- éditeur Qt natif ou éditeur HTML/JavaScript embarqué ;
- comportement réellement atomique des `MergeField` ;
- round-trip du contenu riche ;
- moteur PDF et tableaux multi-pages ;
- gestion des polices ;
- fidélité de l'import `.twd` ;
- collage depuis Word et LibreOffice.

## Liens associés

[[Éditeur interne et documents]] · [[Publipostage et documents]] · [[Mots-clés de publipostage]] · [[Architecture fonctionnelle]]
