# Charte graphique Teamworks

Cette charte est la référence visuelle du logiciel. Elle doit permettre de faire évoluer l'apparence de Teamworks sans reprendre écran par écran des tailles, couleurs ou espacements codés en dur.

## Principe général

Les écrans métier expriment une intention visuelle, jamais une valeur locale.

Exemples :

- un titre de page demande `H1`, pas `16 pt gras` ;
- un état bloquant demande `danger`, pas `rouge` ;
- un espace entre deux champs demande `field_gap`, pas `8 px` ;
- une icône standard demande `medium`, pas `20 x 20` ;
- un bouton demande `button_min_height`, pas `36 px` ;
- une grande fenêtre métier demande le profil `wide`, pas `890 x 600`.

Les sources de vérité sont :

- `teamworks/Utils/UTILS_Interface.py` pour les couleurs ;
- `teamworks/Utils/UTILS_Styles.py` pour la typographie, les espacements, les icônes, les contrôles et les dimensions ;
- `teamworks/Ctrl/CTRL_Texte.py` pour les composants texte sémantiques ;
- `teamworks/Ctrl/CTRL_Section.py` pour les sections visuelles réutilisables.

## Couleurs : cinq familles maximum

Teamworks utilise au maximum cinq familles visuelles :

1. **Neutre** : fonds, surfaces, texte, contours, séparateurs, état désactivé.
2. **Primaire** : identité visuelle, sélection, focus, information, action principale.
3. **Succès** : validation et état conforme.
4. **Avertissement** : attention, échéance, état à surveiller.
5. **Danger** : blocage, erreur, suppression ou état critique.

Le mode clair et le mode sombre utilisent des nuances différentes de ces mêmes familles. Une nuance n'est pas une nouvelle couleur métier.

`info`, `selection` et `focus` ne doivent jamais créer une nouvelle teinte : ils réutilisent la famille primaire.

Aucun écran métier ne doit introduire directement `wx.Colour(...)`, `RED`, `PINK`, `BLUE`, une valeur RGB ou une couleur hexadécimale pour son rendu normal.

## Hiérarchie typographique

La gamme sémantique est :

- `Display`
- `H1`
- `H2`
- `H3`
- `H4`
- `H5`
- `H6`
- `Lead`
- `BodyLarge`
- `Body`
- `BodySecondary`
- `BodySmall`
- `Label`
- `Caption`
- `Micro`
- `DataLarge`

Les tailles suivent la police native du système et l'échelle d'interface. Les écrans ne doivent pas appeler directement `SetPointSize()` ou construire leurs propres `wx.Font()` sauf contrainte technique documentée.

## Espacements

L'échelle de base est limitée à :

- `none` = 0
- `xs` = 4
- `sm` = 8
- `md` = 12
- `lg` = 16
- `xl` = 24
- `2xl` = 32

Les écrans préfèrent les rôles :

- `control_gap`
- `field_gap`
- `section_gap`
- `content_padding`
- `dialog_padding`
- `toolbar_gap`
- `page_gap`

## Icônes et contrôles

Les tailles d'icônes appartiennent à une gamme unique :

- `micro`
- `small`
- `medium`
- `large`
- `hero`

Les écrans métier ne fixent pas eux-mêmes la taille d'une icône. `CTRL_Bouton_image` consomme cette gamme et l'échelle d'interface.

Les dimensions communes des contrôles sont également centralisées : hauteur minimale des boutons, marge d'icône, hauteur de toolbar, hauteur de footer, etc. Une évolution de densité doit donc être possible depuis `UTILS_Styles.py`.

## Dimensions de fenêtres

Les fenêtres ne doivent plus être conçues autour d'une résolution historique précise.

Profils disponibles :

- `compact` : petite saisie ou confirmation enrichie ;
- `standard` : formulaire courant ;
- `wide` : écran métier riche ;
- `workspace` : planning, tableau dense ou grand écran de travail.

Chaque profil est calculé selon la taille d'écran, avec un minimum et un maximum. Sur un écran 4K, l'interface doit afficher davantage d'information utile, pas seulement davantage de vide.

## Densité et lecture

Un écran doit faire apparaître immédiatement :

1. le contexte ou titre principal ;
2. les sections ;
3. les données et actions principales ;
4. les informations secondaires ;
5. les métadonnées ou aides discrètes.

La hiérarchie est obtenue d'abord par la typographie, l'espacement et la structure. La couleur ne doit jamais servir à compenser une mauvaise hiérarchie de lecture.

## Règles de maintenance

Dans les écrans `Ctrl` et `Dlg`, éviter toute nouvelle occurrence de :

- `wx.Font(...)` ou `SetPointSize(...)` ;
- `wx.Colour(...)` pour le rendu normal ;
- couleurs nommées comme `RED`, `PINK`, `BLUE` ;
- tailles d'icônes codées localement ;
- `SetSize((...))` ou `SetMinSize((...))` arbitraire pour une fenêtre ;
- colonnes figées qui pourraient absorber l'espace disponible ;
- `Fit(self)` comme stratégie de dimensionnement d'un dialogue métier ;
- boutons-image minuscules sans libellé.

Les exceptions techniques doivent rester rares, localisées et commentées.

## Gel graphique avant recette

Quand les principaux parcours visibles sont raccordés à la charte, la priorité passe à la stabilité : compilation, tests, parcours critiques Windows et paquet installable. Les retouches purement cosmétiques qui exigeraient une chirurgie importante sont reportées après la recette. Les corrections faciles et transversales restent acceptables si elles consomment les composants centraux sans modifier la logique métier.

## Objectif de durabilité

Une future évolution de la charte — nouvelle couleur primaire, nouvelle densité, typographie plus grande, nouvelles tailles d'icônes, nouvelle proportion des fenêtres — doit être réalisable principalement dans les modules centraux, sans campagne de retouche manuelle sur l'ensemble du logiciel.
