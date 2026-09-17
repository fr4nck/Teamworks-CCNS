# Diagnostic performance wx — Individus et fiche individuelle

Date : 2026-09-07  
Branche de base : `wx/master`

## Périmètre

Ce chantier cible uniquement la réactivité de la Vanilla wx autour de la liste
Individus et des fiches individuelles. Il ne modifie ni le modèle métier, ni
les règles CCNS, ni Qt.

## Diagnostic factuel

### 1. Ouverture de la liste Individus

Chemin : `Ctrl/CTRL_Personnes.py::PanelPersonnes.MAJpanel()` →
`Ol/OL_personnes.py::ListView` / `Ol/OL_personnes_core.py::ListView`.

Au premier affichage, `InitPage()` construit `ListView`. Le constructeur charge
déjà :

1. `pays` ;
2. `Situations` ;
3. toute la table `Coordonnees` ;
4. toute la table `diplomes` ;
5. `types_diplomes` ;
6. `personnes`.

`MAJpanel()` appelait ensuite immédiatement `listCtrl_personnes.MAJ()` sans
paramètre, ce qui relançait les cinq dernières lectures. Le premier affichage
exécutait donc **11 requêtes** pour la liste, dont cinq strictement redondantes.
Toutes ces lectures sont synchrones dans le thread wx.

Correction : `Ol/OL_personnes.py::ListView.MAJ()` ignore uniquement ce tout
premier `MAJ()` sans paramètre. Les rafraîchissements ultérieurs restent
inchangés.

**Avant : 11 requêtes. Après : 6 requêtes.**

### 2. Arbre « Problèmes des fiches »

Chemin : `Ctrl/CTRL_Gadget_pb_personnes.py::TreeCtrl.MAJ_treeCtrl()` →
`FonctionsPerso.Creation_liste_pb_personnes()` / `Recherche_problemes_personnes()`.

Pour `N` personnes possédant un contrat actif ou à venir, le code historique
faisait :

- 1 requête pour trouver les personnes concernées ;
- 1 requête globale sur `personnes` ;
- puis, **pour chaque personne** :
  - 1 requête `coordonnees` ;
  - 1 requête pièces spécifiques ;
  - 1 requête pièces basiques, identique pour toutes les personnes ;
  - 1 requête pièces possédées ;
  - 1 requête `contrats`.

Soit **`5 × N + 2` requêtes**, exécutées en série dans le thread UI. Les IDs
pouvaient en outre être dupliqués lorsque plusieurs contrats actifs/à venir
appartenaient à la même personne.

Correction : `Utils/UTILS_Personnes_performance.py` conserve les mêmes règles
et regroupe ces lectures par `IDpersonne IN (...)`. Les pièces basiques ne sont
lues qu'une fois et les IDs sont dédupliqués en conservant leur ordre.

**Avant : `5N + 2` requêtes. Après : 7 requêtes fixes.**

Exemples structurels :

| Personnes concernées (N) | Avant | Après | Réduction |
| ---: | ---: | ---: | ---: |
| 1 | 7 | 7 | 0 % |
| 10 | 52 | 7 | 86,5 % |
| 25 | 127 | 7 | 94,5 % |
| 50 | 252 | 7 | 97,2 % |

### 3. Ouverture de la fiche individuelle

Chemin : `Dlg/DLG_Fiche_individuelle_core.py::Notebook.__init__()`.

Le notebook historique instancie les huit pages avant l'affichage du dialogue,
y compris Qualifications, Contrats, Présences, Scénarios, Frais et Recrutement.
Les constructeurs de ces pages peuvent eux-mêmes effectuer des accès SQL et des
reconstructions de contrôles, bien que l'utilisateur reste sur Généralités.

Correction dans le wrapper `Dlg/DLG_Fiche_individuelle.py` :

- Généralités reste chargée immédiatement ;
- Questionnaire reste chargé immédiatement, car la fermeture historique le
  sauvegarde systématiquement ;
- les six autres pages sont remplacées par des placeholders légers et ne sont
  construites qu'à leur premier affichage ;
- ordre, libellés, images et classes des pages restent identiques.

Cela retire du chemin d'ouverture les constructeurs et accès I/O des six pages
secondaires, sans changer les règles de sauvegarde Généralités/Questionnaire.

### 4. Changement d'onglet

Le code historique appelle `page.Refresh()` à chaque changement d'onglet et,
quand l'utilisateur quitte Généralités, sauvegarde cette page de manière
synchrone. Ce comportement métier est conservé.

Le premier accès à un onglet différé est désormais mesuré séparément sous
`wx.personnes.fiche.onglet.chargement`, puis les changements sous
`wx.personnes.fiche.onglet.changement`.

### 5. Fermeture de fiche / retour liste

Chemin : `Dlg/DLG_Fiche_individuelle_core.py::Dialog.Fermer()`.

Après sauvegarde, la fermeture rafraîchit synchronement :

1. la liste Individus (`ListView.MAJ`) : 5 lectures SQL ;
2. l'arbre des problèmes : auparavant `5N + 2` lectures SQL.

Il n'y a pas de second rafraîchissement dans `OL_personnes.Modifier()` après
`ShowModal()` : le coût est bien celui du rafraîchissement déclenché par
`Fermer()`.

**Avant : `5N + 7` requêtes. Après : 12 requêtes**, indépendamment de N.

### 6. Thread UI et I/O

Les accès MySQL inspectés restent synchrones et sont exécutés depuis les
constructeurs/handlers wx. Le chantier ne déplace pas les écritures ou les
lectures vers un thread de fond : une telle modification serait plus risquée
pour `wx/master` (connexion DB, cycle de vie wx, erreurs et transactions).

Le gain retenu consiste d'abord à supprimer les attentes réseau évitables :
requêtes dupliquées, N+1 et chargement des pages non visibles. Une migration
asynchrone pourra être évaluée ensuite uniquement si les mesures réelles montrent
encore une attente longue après cette réduction.

## Instrumentation

`Utils/UTILS_Diagnostic_performance.py` reste désactivé par défaut et s'active
avec :

```bash
TEAMWORKS_PERF_DIAG=1
```

Nouvelles mesures :

- chaque `GestionDB.ExecuterReq` et `ResultatReq` : durée, phase, réseau/local,
  aperçu de la requête ;
- `wx.personnes.liste.ouverture` ;
- `wx.personnes.liste.rafraichissement` ;
- `wx.personnes.dossiers.rafraichissement` ;
- `wx.personnes.fiche.ouverture` ;
- `wx.personnes.fiche.onglet.chargement` ;
- `wx.personnes.fiche.onglet.changement` ;
- `wx.personnes.fiche.fermeture`.

Chaque mesure d'action contient :

- `nb_requetes` ;
- `sql_ms` ;
- `connexion_ms` ;
- `io_ms` ;
- `python_wx_ms` ;
- `total_ms`.

Les valeurs sont accessibles par
`Utils.UTILS_Diagnostic_performance.obtenir_mesures()`.

## Avant / après

Les millisecondes réelles dépendent du poste client et du serveur MySQL de
recette. Cette branche GitHub n'a pas accès à cette base distante : **aucun
chiffre de latence réseau n'est inventé**. Les mesures reproductibles disponibles
ici sont les nombres de requêtes et le travail différé ; les colonnes de temps
ci-dessous doivent être remplies avec une exécution avant/après sur le même
poste, la même base et la même fiche.

| Action | Requêtes avant | Requêtes après | Temps avant | Temps après |
| --- | ---: | ---: | ---: | ---: |
| Premier affichage liste, hors arbre | 11 | 6 | à relever sur recette | à relever sur recette |
| Arbre problèmes | `5N + 2` | 7 | à relever sur recette | à relever sur recette |
| Premier affichage liste + arbre | `5N + 13` | 13 | à relever sur recette | à relever sur recette |
| Fermeture fiche + retour liste | `5N + 7` | 12 | à relever sur recette | à relever sur recette |
| Ouverture fiche | 8 pages construites | 2 pages construites, 6 différées | à relever sur recette | à relever sur recette |

Exemple de réduction de requêtes pour `N=25` : premier affichage complet
`138 → 13` (-90,6 %) ; fermeture/retour `132 → 12` (-90,9 %).

## Index et SELECT *

Le chemin critique corrigé n'ajoute aucun `SELECT *`. Les nouvelles lectures
sélectionnent explicitement les colonnes nécessaires.

Aucun index n'est ajouté dans ce chantier. Sans `EXPLAIN` sur la base MySQL de
recette et sans connaître la volumétrie réelle, forcer une migration d'index
serait contraire aux règles du dépôt. Après réduction du nombre de round-trips,
si une requête batch reste lente, les candidats à vérifier avec `EXPLAIN` sont
notamment les clés étrangères/colonnes de filtre `IDpersonne` sur
`coordonnees`, `diplomes`, `pieces` et `contrats`, ainsi que les colonnes de
jointure des tables de pièces.

## Fichiers modifiés

- `teamworks/Utils/UTILS_Diagnostic_performance.py`
- `teamworks/Utils/UTILS_Personnes_performance.py` (nouveau)
- `teamworks/Ol/OL_personnes.py`
- `teamworks/Ctrl/CTRL_Gadget_pb_personnes.py`
- `teamworks/Dlg/DLG_Fiche_individuelle.py`
- `tests/test_wx_personnes_performance.py` (nouveau)
- `docs/PERF_WX_PERSONNES_2026-09-07.md` (ce document)

## Risques laissés volontairement hors patch

- passage général des accès MySQL hors thread wx : risque supérieur pour la
  branche stable, à mesurer après cette passe ;
- cache global de villes/pays/situations : invalidation à définir avant de
  l'introduire ;
- mise à jour partielle de `DICT_COORDONNEES` / `DICT_QUALIFICATIONS` au retour
  d'une fiche : possible gain supplémentaire, mais plus exposé aux incohérences ;
- ajout d'index : uniquement après `EXPLAIN` sur la base réelle.
