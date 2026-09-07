# Pilote de recette Windows wx

Ce pilote complète les tests existants par de vraies interactions sur le bureau Windows. Il ne charge ni n'appelle directement les handlers Python de Teamworks.

## Exécution locale — une seule commande

Ouvrir PowerShell à la racine du dépôt, dans votre session Windows normale et déverrouillée, puis lancer :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\recette_windows\run_local.ps1
```

C'est tout. Le lanceur :

- vérifie Windows, la session utilisateur interactive et le bureau d'entrée déverrouillé ;
- trouve automatiquement la racine du dépôt et Python 3.11 ;
- vérifie le lanceur `run_teamworks.py` et le runtime wx existant sans modifier les dépendances normales de Teamworks ;
- installe uniquement `requirements\recette-windows.txt` si nécessaire ;
- crée un dossier d'artefacts horodaté ;
- lance `individus-smoke` avec le backend UI Automation (`uia`) ;
- conserve stdout, stderr, traceback éventuel, screenshot d'échec, dump UIA, logs Teamworks, focus clavier et informations Windows ;
- crée un ZIP du dossier ;
- termine par `RECETTE OK`, `RECETTE KO — ...` ou `ENVIRONNEMENT NON PRÊT — ...`.

Résultats :

```text
artifacts\recette-windows\local-YYYYMMDD-HHMMSS-individus-smoke\
artifacts\recette-windows\local-YYYYMMDD-HHMMSS-individus-smoke.zip
```

Le fichier `environment.json` contient les informations Windows utiles. Le DPI et le pourcentage de scaling ne sont renseignés que si Windows fournit une valeur exploitable au processus ; sinon ils restent `null`. Une valeur de scaling système n'est pas présentée comme une mesure DPI par moniteur.

## Parcours actuel

Le scénario lance réellement `run_teamworks.py`, attend la fenêtre `Teamworks v...`, puis effectue les interactions Windows suivantes :

1. teste `TAB`, `Shift+TAB` et `Entrée` sur la navigation `Individus`, en enregistrant le contrôle avant, le contrôle après, l'attendu, l'obtenu et le verdict dans `keyboard-focus.json` ;
2. effectue ensuite un vrai clic souris sur `Individus` ;
3. cherche la liste wx `OL_personnes` avec repli sur une List/ListView native visible si son nom n'est pas exposé par UIA ;
4. si une ligne UIA est exploitable, sélectionne et double-clique réellement la première ligne ;
5. sinon, effectue un vrai clic droit puis choisit réellement `Options`, action non destructive ;
6. vérifie que le dialogue obtenu répond ;
7. envoie réellement `Echap`, vérifie que le dialogue s'est fermé par cette touche et enregistre le focus revenu dans la fenêtre principale.

Si `Echap` ne ferme pas le dialogue, le pilote peut utiliser `WM_CLOSE` uniquement pour remettre l'application dans un état propre, mais la recette reste **KO** : ce fallback ne masque pas l'échec clavier.

## Artefacts

Le dossier local contient selon le résultat :

- `result.json` — toujours présent, y compris en cas de KO ou d'environnement non prêt ;
- `keyboard-focus.json` — résultats TAB / Shift+TAB / Entrée / Echap, écrits au fil du scénario ;
- `environment.json` — Windows, session, Python, écran et DPI/scaling réellement détectés ;
- `windows.txt` — dump des fenêtres/contrôles UIA lorsque Teamworks a été lancé ;
- `stdout.log` / `stderr.log` — sortie du processus Teamworks ;
- `runner-stdout.log` / `runner-stderr.log` — sortie du pilote ;
- `failure.txt` et `failure.png` en cas de KO lorsque la capture est possible ;
- `app-logs\` — logs Teamworks récents trouvés dans le dépôt et les emplacements Windows usuels ;
- `process.json` — PID, code retour du processus et backend ;
- `pip-stdout.log` / `pip-stderr.log` — installation des seules dépendances de recette ;
- `local-run.json` — verdict synthétique et chemins du dossier/ZIP.

## Garde destructive

Avant `Entrée`, avant un clic générique nommé et à l'ouverture d'un nouveau dialogue, le texte accessible est analysé. Un dialogue de confirmation comportant un marqueur de suppression, effacement ou destruction interrompt le scénario avec le code 3 sans envoyer de validation.

Le backend par défaut est Microsoft UI Automation (`uia`). `win32` reste disponible pour diagnostic avec :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\recette_windows\run_local.ps1 -Backend win32
```

Aucune exécution GitHub Actions ni aucun runner self-hosted n'est nécessaire pour la recette locale.
