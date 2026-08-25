# Teamworks — suivi UI/UX / thème graphique

## Objectif

Ce fichier suit la **modernisation graphique et ergonomique** de Teamworks-CCNS indépendamment de la migration Python 3 et des fonctions métier CCNS.

## Périmètre

Entrent notamment ici :

- design system et tokens sémantiques ;
- thème clair/sombre ;
- typographie et échelle UI ;
- icônes ;
- boutons et composants communs ;
- listes, tableaux, formulaires et dialogues ;
- layouts adaptatifs, DPI et zoom ;
- suppression des dimensions figées problématiques ;
- cohérence visuelle et accessibilité ;
- régressions causées par la refonte graphique.

## Règle de classement

Un défaut historique déjà présent dans Teamworks Vanilla appartient à `01_VANILLA_BUGFIX.md`.

Une incompatibilité imposée par Python 3/wxPython Phoenix appartient à `02_PYTHON3_PHOENIX.md`.

Une anomalie créée par le nouveau thème, le zoom, les tokens, les nouvelles dimensions ou les nouveaux composants appartient ici.

## Références

- `docs/CHARTE_GRAPHIQUE_TEAMWORKS.md`
- `docs/33-modernisation-optimisation-sobriete-teamworks-ccns.md`
- `DESIGN_SYSTEM_UI_UX.md` lorsqu'il est utilisé comme référentiel de travail
- chantier TW-189 et garde-fous associés

## État initial

Le chantier est déjà largement engagé : design system, échelle d'interface, tokens, composants communs et nombreux garde-fous existent. L'inventaire détaillé doit être consolidé écran par écran et composant par composant avant de figer un pourcentage fiable.

## Pourcentage

**À recalculer après inventaire détaillé.**

La progression devra tenir compte de la couverture des composants communs et des écrans métier réellement migrés, pas uniquement du nombre de commits UI.
