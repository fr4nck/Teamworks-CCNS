# Diagnostic et rapports de crash

Ce mécanisme est l'un des plus fiables et des mieux vérifiés de l'application : chemins, formats de fichiers, contenu du rapport et règles de confidentialité correspondent précisément au code (`teamworks/Utils/UTILS_Crash.py`, `UTILS_Blackbox.py`, `UTILS_Rapport_bugs.py`, `UTILS_Envoi_rapport_bug.py`).

## Où sont les logs ?

Le gestionnaire de crash choisit le dossier dans cet ordre :

1. variable technique `TEAMWORKS_LOG_DIR` si elle est définie ;
2. installation portable : `Portable/Logs` à côté de l'application ;
3. Windows : `%APPDATA%/teamworks/Logs` ;
4. autres systèmes : `$XDG_CONFIG_HOME/teamworks/Logs` ou `~/.config/teamworks/Logs`.

Le dialogue de crash possède un bouton **Ouvrir le dossier Logs**.

## Format du rapport

Un crash Python produit un fichier `crash-AAAAMMJJ-HHMMSS-...-PID.txt`. Les erreurs fatales capturées nativement (`faulthandler`) peuvent produire `native-crash-....log`.

Le rapport texte peut contenir :

- date et contexte ;
- version de l'application (lue en priorité depuis `VERSION`) ;
- PID ;
- indication portable/PyInstaller ;
- versions Python et wxPython ;
- système et architecture ;
- chemin de l'exécutable/répertoire courant, avec le dossier utilisateur masqué ;
- `BUILD.txt` et/ou `VERSION` **s'ils existent** à l'emplacement attendu ;
- chronologie technique de la « boîte noire » ;
- pile Python.

Le rapport est plafonné à une taille maximale avant envoi (2 Mo).

## Version, SHA et build

`VERSION` est la source canonique utilisée par la Vanilla wx actuelle. `BUILD.txt` n'est ajouté au rapport que s'il existe dans le paquet. Un SHA Git n'est donc pas garanti dans chaque rapport : joignez-le seulement s'il est affiché ou fourni avec le build. Voir [Mises à jour](../demarrage/mise-a-jour.md).

## Chronologie technique (« boîte noire »)

La boîte noire enregistre jusqu'à 200 événements techniques wx (changement de page, clic de bouton/menu, création/destruction de fenêtre), et surveille les gels applicatifs (seuil d'alerte ~8 secondes). Elle vise à montrer **la chronologie technique**, pas le contenu métier saisi.

## Confidentialité

Le formateur de rapport est conçu pour **ne pas sérialiser** :

- variables locales ;
- valeurs de champs ;
- identifiants métier ;
- montants ;
- requêtes SQL ;
- contenu de la base ;
- message libre de l'exception.

Il masque aussi le chemin du dossier personnel lorsque cela est possible.

!!! warning
    Le système est conçu pour éviter les données métier sensibles. Avant tout partage, relisez néanmoins le fichier et n'ajoutez pas de capture, sauvegarde ou donnée personnelle inutile.

## Que joindre à un signalement ?

- fichier de rapport correspondant au crash ;
- version Teamworks ;
- SHA/build uniquement s'il est disponible ;
- local ou réseau/MySQL ;
- action juste avant le problème ;
- étapes minimales de reproduction ;
- résultat attendu/obtenu.

Le dialogue sait ouvrir, copier et, selon la configuration de messagerie (adresse configurable dans **Préférences > Maintenance/Diagnostic**), envoyer le rapport technique. Pour le canal de support, voir [Aide et signalement de bugs](../reference/aide.md).

## Points d'attention

- Un rapport n'explique pas forcément à lui seul la cause fonctionnelle ; la reproduction reste importante.
- Les rapports natifs peuvent être moins structurés qu'un rapport Python.
- En cas de gel sans crash, la chronologie/watchdog peut aider, mais l'analyse complète reste **à confirmer en recette fonctionnelle** selon le cas.

## Voir aussi

[Problèmes fréquents](../reference/problemes-frequents.md) · [Aide et signalement de bugs](../reference/aide.md) · [Mises à jour](../demarrage/mise-a-jour.md) · [Paramétrage](parametrage.md)
