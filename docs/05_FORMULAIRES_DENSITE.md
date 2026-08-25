# Teamworks — formulaires métier et densité informationnelle

**Statut : norme applicative dérivée de PMSL-Arch ADR-005.**

## Objectif

Teamworks doit converger vers une interface desktop productive : compacte sans être tassée, structurée sans être rigide, et chaque contrôle doit occuper la place correspondant à la donnée qu'il représente.

Cette norme s'applique transversalement. Elle ne doit pas être implémentée fenêtre par fenêtre.

## Principes obligatoires

### Champs dimensionnés par la sémantique

La largeur attendue dépend du type de donnée :

- code, département, groupe : très compact ;
- code postal, heure : compact ;
- date, durée, taux, montant : compact à moyen ;
- téléphone, NIR, SIRET : largeur calibrée sur leur format ;
- nom, prénom, ville : largeur moyenne ;
- email, adresse, intitulé : largeur moyenne à longue ;
- commentaire/mémo : zone multiligne réellement extensible.

Les métriques doivent être centralisées dans les primitives de style et calculées en tenant compte de la police et de l'échelle DPI. Les écrans métier ne doivent pas coder leurs propres largeurs arbitraires.

### `wx.EXPAND` avec intention

`wx.EXPAND` ne doit plus être le comportement automatique des champs courts. Il reste adapté aux listes, tableaux, zones de recherche longues, adresses, mémos et espaces de travail réellement fluides.

Un sizer organise le formulaire ; il ne transforme pas chaque champ en pleine largeur.

### Groupes métier

Les couples naturels peuvent partager une ligne : code postal/ville, date début/date fin, heure début/heure fin, téléphone/portable, montant/unité.

On ne rapproche jamais des champs sans relation métier uniquement pour remplir l'espace disponible.

### Densité productive

- supprimer les grands espaces morts ;
- éviter les cartes ou encarts géants pour peu de contenu ;
- conserver des marges et espacements issus de `UTILS_Styles.py` ;
- utiliser l'espace supplémentaire pour afficher de l'information utile ;
- préserver une navigation clavier rapide et un ordre de tabulation logique.

### Labels, aide et validation

- label persistant ;
- placeholder jamais utilisé comme seul libellé ;
- labels au-dessus par défaut pour les formulaires hétérogènes ;
- labels à gauche admis pour les petites grilles administratives très régulières ;
- aide de format uniquement lorsqu'elle réduit réellement le risque d'erreur ;
- erreur affichée près du champ, explicite et actionnable ;
- couleur jamais utilisée comme seul signal ;
- aucune exception Python ne doit devenir un message métier.

## Architecture cible Teamworks

La cible est une famille de rôles de champs consommée par les contrôles communs, par exemple :

```text
FIELD_XS
FIELD_CODE
FIELD_POSTAL_CODE
FIELD_DATE
FIELD_TIME
FIELD_NUMBER
FIELD_PERCENT
FIELD_MONEY
FIELD_PHONE
FIELD_NIR
FIELD_SIRET
FIELD_IBAN
FIELD_NAME
FIELD_CITY
FIELD_EMAIL
FIELD_ADDRESS
FIELD_TEXT
FIELD_LONG_TEXT
```

Ces rôles doivent progressivement porter : largeur, hauteur, alignement, expansion, validation, formatage et aide éventuelle.

La logique recherchée est :

`donnée métier -> rôle de champ -> métrique commune -> widget`

et non :

`fenêtre -> SetMinSize local -> exception de sizer`.

## Frontière dashboard

Les gadgets appartiennent à l'accueil/dashboard. Ils ne doivent pas être enfants du layout global ni rester visibles au-dessus des écrans Personnes, Contrats, Coordonnées ou autres écrans métier.

La correction doit porter sur le conteneur propriétaire des gadgets, pas sur une série de `Hide()` ajoutés écran par écran.

## Priorités de correction

1. P0 — fenêtres qui plantent ou ne s'ouvrent pas ;
2. P1 — primitives communes, rôles de champs, sizers et frontière dashboard ;
3. P2 — migration progressive des formulaires historiques ;
4. P3 — finitions visuelles locales.

## Garde-fous

Lorsqu'un défaut apparaît sur plusieurs fenêtres, la correction doit être recherchée dans `UTILS_Styles.py`, les contrôles communs, les helpers de layout ou le conteneur partagé avant toute modification locale.

Les tests et smokes doivent couvrir les primitives transversales lorsque c'est possible. La recette Windows doit inclure plusieurs échelles d'interface et vérifier troncatures, grands vides, ordre clavier et densité.

## Implémentation dans Teamworks CCNS

- les rôles `FIELD_*`, leur longueur attendue, leur expansion et leur calcul à
  partir de la police/DPI sont centralisés dans `teamworks/Utils/UTILS_Styles.py` ;
- `ApplyFieldRole()` et `GetFieldSizerFlag()` portent la première migration
  transversale des champs administratifs courts (Structure et Références RH) ;
- l'hôte AUI des gadgets interdit les fenêtres flottantes : leur propriétaire
  reste le panneau Accueil, y compris après restauration d'une perspective ;
- les migrations suivantes doivent consommer ces primitives, sans ajouter de
  largeurs pixel ni de `Hide()` locaux par écran.

## Références

- [PMSL-Arch PR #3 — ADR-005 et raccordement au design system](https://github.com/fr4nck/PMSL-Arch/pull/3)
- [Teamworks-CCNS PR #274 — adoption de la norme applicative](https://github.com/fr4nck/Teamworks-CCNS/pull/274)
- `docs/CHARTE_GRAPHIQUE_TEAMWORKS.md`
- `docs/03_UI_UX_MODERNISATION.md`
- Bastien & Scapin
- Fluent 2
- Carbon Design System
- RGAA / pratiques DSFR / GOV.UK / USWDS
