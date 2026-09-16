# Recette Présences après corrections #410

## Baseline mesurée le 2026-09-07

Premier `Individus -> Présences` :

- `wx.presences.majpanel` : 7 494,60 ms ;
- 53 requêtes ;
- connexion : 6 209,45 ms (82,9 %) ;
- SQL/fetch : 1 072,52 ms ;
- Python/wx : 212,64 ms.

## Corrections de cette passe

1. Le premier `InitPage()` ne déclenche plus un calcul complet du planning via
   `MAJselectionDates()` avant le calcul effectué par `MAJpanel()`.
2. Le résultat de `RecherchePresents()` calculé pour réinitialiser la sélection
   est réutilisé par `ReInitPlanning()` au lieu de relire immédiatement les mêmes
   dates.
3. Les connexions MySQL sont réutilisées uniquement pendant un `MAJpanel()`
   Présences. La portée est thread-local et action-scoped ; les bases SQLite ne
   passent pas par ce mécanisme. Un `DB.Close()` logique rend la connexion au
   scope après rollback de sécurité et la connexion physique est fermée en
   sortie du scope, y compris sur exception.
4. La navigation mesure désormais `wx.personnes.panel.majpanel`, qui englobe le
   vrai premier `PanelPersonnes.MAJpanel()` et donc son éventuel `InitPage()`.

## Recette Windows à refaire à l'identique

```powershell
cd "$HOME\Documents\GitHub\Teamworks-CCNS"
git fetch origin
git switch perf-wx-presences-latency
git pull
Remove-Item ".\perf-presences.jsonl" -ErrorAction SilentlyContinue
$env:PYTHONPATH="$PWD;$PWD\teamworks"
$env:TEAMWORKS_PERF_DIAG="1"
$env:TEAMWORKS_PERF_LOG="$PWD\perf-presences.jsonl"
py teamworks\Teamworks.py
```

Parcours : démarrage neuf -> Individus -> attendre le chargement complet -> un
seul clic Présences -> attendre l'affichage complet -> arrêter la capture.

Conserver : MP4, `perf-presences.jsonl`, et tout `freeze-*.txt` produit.

## Critères de comparaison

Comparer exactement :

- `wx.personnes.panel.majpanel` ;
- `wx.personnes.liste.ouverture` ;
- `wx.personnes.dossiers.rafraichissement` ;
- `wx.presences.majpanel` ;
- `wx.presences.initialisation` ;
- `wx.presences.planning.*` ;
- `wx.presences.personnes.maj` ;
- `wx.presences.calendrier.maj` ;
- `connexion_ms`, `sql_ms`, `python_wx_ms`, `nb_requetes`.

Aucun objectif en millisecondes n'est inventé avant la nouvelle recette réelle.
