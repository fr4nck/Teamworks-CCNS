# Diagnostic performance wx — navigation Présences

Date : 2026-09-07  
PR parente : `perf-wx-personnes-latency` (#408)  
Branche : `perf-wx-presences-latency`

## Baseline réelle Windows

La recette vidéo `2026-09-07_12-06-03.mp4` a été exécutée avec :

- branche Git : `perf-wx-personnes-latency` ;
- SHA : `17c3edd` ;
- `TEAMWORKS_PERF_DIAG=1` ;
- Windows, capture OBS.

Le watchdog et la vidéo concordent :

- `12:06:55.668` : clic de navigation vers Présences ;
- `12:07:03.107` : `FREEZE_DETECTED` ;
- transition visuelle vers Présences vers `12:07:03.5` ;
- blocage réel de la boucle wx : environ 8 secondes.

Ce gel existe donc avec les optimisations Individus/fiches de #408 actives. Il
est traité comme un chantier distinct.

Le premier affichage complet d'Individus reste par ailleurs visuellement de
l'ordre de 5 à 6 secondes sur cette recette. Les navigations ultérieures ne
constituent pas une comparaison valide du premier chargement car les pages sont
déjà construites et plusieurs données sont déjà en mémoire.

## Limite du premier enregistrement

Au SHA `17c3edd`, les mesures `TEAMWORKS_PERF_DIAG` étaient conservées en mémoire.
Le rapport watchdog prouve donc le freeze, mais il ne permet pas de reconstruire
rétroactivement des valeurs `sql_ms`, `connexion_ms`, `io_ms` et `python_wx_ms`.
Aucun chiffre n'est inventé à partir de la vidéo.

Cette branche ajoute une persistance explicitement opt-in des seuls résumés
d'actions via `TEAMWORKS_PERF_LOG`.

## Chemin de premier chargement

`CTRL_Navigation_principale.NavigationPrincipale.SetSelection()` appelle le
`MAJpanel()` de la page cible avant de masquer l'ancienne page. Un `MAJpanel()`
Présences lent laisse donc visuellement Individus affiché et figé pendant le
chargement.

`CTRL_Presences.PanelPresences.MAJpanel()` effectue, lors du premier accès :

1. construction de la page (`InitPage`) ;
2. préparation/rechargement du planning ;
3. recalcul du planning ;
4. rechargement de la liste des individus ;
5. reconstruction de la légende ;
6. rafraîchissement du calendrier.

Tous ces appels restent synchrones dans le thread wx.

## Redondances structurelles déjà identifiées

Ces constats sont des pistes de correction, pas encore des optimisations dans
cette première passe d'instrumentation.

### 1. Planning déclenché pendant `InitPage`, puis recalculé juste après

`InitPage()` positionne `self.init = True` puis appelle
`panelCalendrier.MAJselectionDates(...)`. Ce dernier appelle
`PanelPresences.MAJpanelPlanning()` dès que la page est marquée initialisée.

À son retour dans `MAJpanel()`, le bloc `planning` exécute ensuite à nouveau la
préparation du planning puis `MAJpanelPlanning(reinitSelectionPersonnes=True)`.

Le premier accès contient donc au moins deux passages de planning.

### 2. Recherche des présents répétée dans le même recalcul

`PanelPresences.MAJpanelPlanning(reinitSelectionPersonnes=True)` appelle
`PanelPlanning.RecherchePresents(selectionDates)` pour reconstruire la sélection.

`PanelPlanning.ReInitPlanning(...)` rappelle ensuite
`self.RecherchePresents(listeDates)` pour renseigner `self.listePresents`.

La même lecture logique est donc effectuée deux fois dans ce chemin.

### 3. Liste des individus chargée à la construction puis rechargée

`CTRL_Presences_personnes.PanelPersonnes.__init__()` initialise
`dictPersonnes` via `Import_Personnes()`. La requête agrège
`personnes LEFT JOIN presences` avec `MAX(presences.date)`.

Lors du même premier `MAJpanel()`, `panelPersonnes.MAJpanel()` rappelle
`Import_Personnes()`.

### 4. Catégories du planning rechargées

`CTRL_Planning.PanelPlanning.__init__()` initialise déjà
`self.dictCategories = self.ImportCategories()`. Le premier `MAJpanel()` appelle
ensuite `RechargeDictCategories()`, qui relit `cat_presences`.

Ces répétitions peuvent amplifier fortement la latence lorsque chaque ouverture
de connexion et chaque round-trip MySQL est distant.

## Instrumentation ajoutée

Le `MAJpanel()` Présences installe l'instrumentation SQL avant toute construction
lourde puis mesure les actions suivantes :

- `wx.presences.majpanel` ;
- `wx.presences.initialisation` ;
- `wx.presences.planning.preparation` ;
- `wx.presences.planning.maj` ;
- `wx.presences.planning.recherche_presents` ;
- `wx.presences.planning.reinit` ;
- `wx.presences.planning.categories` ;
- `wx.presences.planning.affichage` ;
- `wx.presences.personnes.maj` ;
- `wx.presences.legendes.maj` ;
- `wx.presences.calendrier.maj`.

Chaque résumé d'action expose :

- `nb_requetes` ;
- `sql_ms` ;
- `connexion_ms` ;
- `io_ms` ;
- `python_wx_ms` ;
- `total_ms`.

Les actions étant imbriquées, `wx.presences.majpanel` donne le coût total et les
sous-actions servent à attribuer ce coût. Les temps SQL des sous-actions sont
également inclus dans l'action parente : il ne faut pas additionner les lignes
entre elles pour recalculer le total.

## Corrélation avec la boîte noire

Quand `TEAMWORKS_PERF_DIAG=1`, le diagnostic envoie à la mémoire circulaire de la
boîte noire des breadcrumbs strictement techniques :

- `PERF_ACTION_START` / `PERF_ACTION_END` avec le nom d'action wx ;
- `PERF_SQL_START` / `PERF_SQL_END` avec uniquement `operation + table`.

Exemple de composant sûr : `app:sql.select.presences`.

Aucune requête complète, clause `WHERE`, valeur, identifiant de personne ou
contenu de base n'est envoyé au rapport de freeze.

## Journal JSONL opt-in

Pour conserver les métriques d'une recette normale, définir un chemin explicite :

```powershell
$env:TEAMWORKS_PERF_DIAG="1"
$env:TEAMWORKS_PERF_LOG="$PWD\perf-presences.jsonl"
python teamworks\Teamworks.py
```

Le fichier JSONL ne contient que : date, nom d'action et métriques agrégées. Les
détails métier éventuellement présents en mémoire ne sont pas écrits.

## Recette demandée

Sur un démarrage neuf de l'application :

1. vérifier le SHA Git ;
2. activer `TEAMWORKS_PERF_DIAG=1` et `TEAMWORKS_PERF_LOG` ;
3. ouvrir Individus une première fois et attendre l'affichage complet ;
4. cliquer une seule fois sur Présences ;
5. attendre l'affichage complet sans effectuer d'autre navigation ;
6. conserver le MP4, le `perf-presences.jsonl` et tout `freeze-*.txt` produit ;
7. seulement ensuite effectuer des navigations de second passage, clairement
   identifiées comme « page déjà construite ».

Le rapprochement à effectuer est :

- horodatage `BUTTON_CLICK` de Présences ;
- dernier `PERF_ACTION_START` / `PERF_SQL_START` avant `FREEZE_DETECTED` ;
- métriques JSONL de `wx.presences.majpanel` et de ses sous-actions ;
- horodatage de récupération de la boucle wx.

## Décision après mesure

La première correction devra cibler la composante dominante :

- `connexion_ms` élevé : réduire le nombre d'ouvertures DB / round-trips ;
- `sql_ms` élevé : identifier la ou les signatures de requêtes dominantes,
  puis mesurer la requête réelle côté recette (`EXPLAIN` si nécessaire) ;
- `python_wx_ms` élevé dans `planning.reinit` ou `planning.affichage` : profiler
  le recalcul/dessin et éviter les reconstructions redondantes ;
- coûts comparables : supprimer d'abord les passages structurellement dupliqués
  décrits ci-dessus avant d'envisager du threading.

Aucune migration générale vers des workers, aucun cache global et aucun index ne
sont introduits avant cette mesure réelle.
