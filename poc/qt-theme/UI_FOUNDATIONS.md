# Socle UI Qt Teamworks

Ce document fige les choix retenus pour la transposition Qt du logiciel historique.

## Principe directeur

La première phase transpose fidèlement l'organisation fonctionnelle et la disposition des écrans wxPython historiques. La modernisation visuelle plus ambitieuse viendra ensuite. Le code wx reste donc la référence de composition, tandis que Qt fournit la géométrie responsive, les composants communs et le moteur de thème.

Aucune règle métier ne doit être dupliquée dans les widgets Qt. Les widgets émettent des intentions ; contrôleurs, presenters, services et repositories restent responsables des validations, autorisations et écritures.

## Décisions consolidées après recette Windows

La recette du 3 septembre 2026 a validé les points suivants :

- le premier affichage Qt ne doit jamais attendre la connexion réseau historique ; la liste initiale des personnes est chargée sur un worker Qt avec son propre reader/sa propre connexion puis injectée dans le modèle sur le thread principal ;
- les contrats restent chargés à la demande après sélection d'une personne ;
- la couche Qt reste strictement en lecture seule pendant le POC ;
- le chemin MySQL historique reste la source des données : aucune nouvelle pile SQL n'est introduite dans l'UI ;
- la page Généralités utilise une densité `compact` fournie par les composants communs et par le thème, pas des hauteurs locales dispersées ;
- Généralités reprend le comportement responsive du wrapper wx actuel : deux colonnes 3/5 + 2/5 sur largeur desktop, puis une colonne scrollable dans l'ordre Identité, Situation sociale, Adresse, Coordonnées, Mémo lorsque la largeur devient insuffisante ;
- le NIR conserve sa place historique mais n'est volontairement pas chargé dans le POC Qt.

Mesure de référence observée sous Windows après chargement différé : premier affichage 1,31 s, données des 96 personnes prêtes à 1,79 s, RSS 130 Mo, deux dépendances UI directes. Ces valeurs sont des points de recette et non des garanties de production.

## Rails de transposition en cours

Le travail visuel avance désormais sur deux rails qui partagent exactement le même socle Qt :

1. **Généralités et ses satellites** : Identité, Situation sociale, Adresse, Coordonnées, Mémo, puis Coordonnées/Villes/Pays/Situations sociales.
2. **Pages secondaires de la fiche individuelle** : Questionnaire, Qualifications, Présences et Recrutement. Ces pages reprennent la géométrie du source wx courant et utilisent `TwFormSection`, `TwActionBar` et `TwDataTable`. Les actions d'écriture restent désactivées ; les boutons Ajouter peuvent uniquement ouvrir les aperçus Qt locaux déjà transposés.

Pour ce second rail, les invariants source sont notamment :
- Qualifications : Pièces à fournir + Qualifications en deux colonnes, puis Pièces reçues ; actions sous les listes ;
- Présences : actions horizontales, recherche, résumé, puis liste ;
- Recrutement de la fiche individuelle : Candidatures puis Entretiens, avec leurs actions au-dessus de chaque liste ;
- Questionnaire : tableau Question / Réponse sans données fictives.

## Ordre de transposition des satellites de Généralités

1. Coordonnées : fixe/mobile/fax/email, champs conditionnels, intitulé, validation et pied de dialogue.
2. Villes : recherche, modes de recherche, résultats tabulaires, sélection et saisie manuelle.
3. Pays / Nationalités : référentiel CRUD puis petit dialogue d'édition.
4. Situations sociales : validation du patron CRUD générique avec règles d'utilisation pilotées hors UI.

Le critère de réussite du quatrième lot est que Situations sociales soit principalement un assemblage de composants déjà existants.

## Composants communs

### `TwDialogShell`
Squelette de dialogue : titre, marges, zone centrale, profil de taille, pied Aide / Valider / Annuler ou Fermer.

Interface cible :
- `TwDialogShell(title, parent=None, profile="compact")`
- `set_content(widget)`
- `set_primary_label(text)`
- signaux `validateRequested`, `cancelRequested`, `helpRequested`

### `TwActionBar`
Barre d'actions homogène : Ajouter, Modifier, Supprimer, Rechercher, Imprimer, etc. Elle gère uniquement ordre, icônes, tooltips, rôle visuel et état enabled/visible.

Interface cible :
- `TwActionBar(actions, orientation=Qt.Horizontal)`
- `set_enabled(action_id, enabled)`
- `set_visible(action_id, visible)`
- signal `triggered(action_id)`

### `TwFormSection`
Bloc nommé d'un formulaire, avec titre, description facultative et contenu. Le paramètre `compact=True` réduit uniquement la géométrie commune ; il ne change ni les états, ni les couleurs, ni la logique métier.

Interface cible :
- `TwFormSection(title, description=None, compact=False)`
- `add_row(row)`
- `add_widget(widget)`

### `TwFieldRow`
Géométrie standard d'un champ : label, editor, suffixe/unité, aide ou action annexe. La densité compacte est propagée à l'éditeur et à son action via la propriété dynamique Qt `twDensity="compact"`.

Interface cible :
- `TwFieldRow(label, editor, suffix=None, action=None, help_text=None, compact=False)`
- `set_validation(state, message="")`

### `TwDataTable`
Tableau Teamworks : sélection de ligne entière, tri, alternance, hauteur commune, état vide et activation par double-clic.

Interface cible :
- `TwDataTable(model=None)`
- `set_model(model)`
- `selected_key()` / `select_key(key)` lorsque le modèle expose une clé
- signaux `selectionChanged`, `activated`

### `TwCrudPanel`
Patron de référentiel : titre, introduction facultative, `TwActionBar` et `TwDataTable`.

Interface cible :
- `TwCrudPanel(title, model=None, description=None)`
- signaux `addRequested`, `editRequested`, `deleteRequested`

### `TwSearchPicker`
Patron rechercher -> résultats -> choisir : champ de recherche, mode facultatif, actions, tableau et sélection.

Interface cible :
- `TwSearchPicker(model=None, modes=())`
- `query()`, `search_mode()`, `selected_key()`
- signaux `searchRequested`, `showAllRequested`, `selectionAccepted`

### `TwChoiceStrip`
Choix exclusifs compacts, premier usage : Fixe / Mobile / Fax / Email.

Interface cible :
- `TwChoiceStrip(choices)`
- `value()` / `set_value(key)`
- signal `valueChanged(key)`

## Tokens géométriques

Les écrans ne doivent pas embarquer de pixels arbitraires. Toute exception locale doit être justifiée.

### Espacements
- XS = 4 px
- SM = 8 px
- MD = 12 px
- LG = 16 px
- XL = 24 px
- XXL = 32 px

Rôles usuels : marge de dialogue 16 px, champ à champ 8 px, label vers contrôle 4 px, section à section 16 px, groupes majeurs 24 px, boutons voisins 8 px.

### Hauteurs
- contrôle compact = 28 px
- contrôle standard = 32 px
- toolbar = 36 px
- recherche = 38 px
- ligne de tableau dense = 26 px
- en-tête de tableau = 32 px

Le thème applique ces hauteurs via les rôles et propriétés dynamiques (`twDensity`) afin qu'une fiche dense n'ait pas à imposer elle-même des `setFixedHeight()` arbitraires.

### Rayons
- champ = 4 px
- bouton = 4 px
- panneau / section = 8 px
- rond = 999 px

### Icônes
- XS = 12 px
- SM = 16 px
- MD = 20 px
- LG = 24 px

Les icônes historiques peuvent être utilisées pendant la transposition derrière un catalogue sémantique. La cible est Fluent System Icons pour le vocabulaire visuel commun.

### Typographie
Famille Windows : Segoe UI Variable avec repli Segoe UI.
- body = 10 pt / normal
- label = 9.5 pt / normal
- secondary = 9 pt / normal
- section = 10.5 pt / semibold
- dialog title = 14 pt / semibold
- page title = 17 pt / semibold

Le DPI scaling reste celui de Qt ; ces valeurs sont des dimensions logiques de référence.

## États visuels

Deux dimensions doivent rester indépendantes : état d'interaction et état sémantique. Un champ peut donc être `focus + error`, une ligne `selected + warning`, etc.

- normal : surface sobre, bordure `outline_variant` 1 px.
- hover : légère élévation de surface, aucune variation de géométrie.
- pressed : contraste un peu plus marqué que hover, sans déplacement.
- focus : anneau `focus` 2 px clairement visible, sans masquer error/warning/success.
- selected : fond `selection`, texte `selection_text`, en particulier sur lignes entières de tableau.
- disabled : surface et texte atténués mais lisibles ; aucun hover. `readonly` reste distinct de `disabled`.
- error : bordure/icone/message `danger`; jamais couleur seule.
- warning : bordure/icone/message `warning`; n'implique pas nécessairement un blocage.
- success : confirmation ponctuelle `success`; ne pas peindre en vert tous les champs normaux.

Les états métier sont portés par des propriétés dynamiques Qt (`validationState`, rôles sémantiques) et rendus centralement par le thème. Les fiches ne décident pas elles-mêmes du style d'une erreur ou d'un focus.

## Priorité de mise en œuvre

Pour obtenir rapidement une cohérence visible :

1. tokens ;
2. `TwDialogShell` ;
3. `TwActionBar` ;
4. `TwFormSection` / `TwFieldRow` ;
5. `TwDataTable` ;
6. `TwCrudPanel` ;
7. `TwSearchPicker` ;
8. `TwChoiceStrip` et états de validation.

Le premier écran d'application de ce socle est désormais la vraie page Généralités, avec ses quatre familles de satellites comme terrain de validation du kit commun.
