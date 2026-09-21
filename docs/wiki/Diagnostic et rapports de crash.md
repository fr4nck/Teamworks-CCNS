# Diagnostic et rapports de crash

<a id="dossier-logs"></a>
## Où sont les logs ?

Le gestionnaire de crash choisit le dossier dans cet ordre :

1. variable technique `TEAMWORKS_LOG_DIR` si elle est définie ;
2. installation portable : `Portable/Logs` à côté de l’application ;
3. Windows : `%APPDATA%/teamworks/Logs` ;
4. autres systèmes : `$XDG_CONFIG_HOME/teamworks/Logs` ou `~/.config/teamworks/Logs`.

Le dialogue de crash possède un bouton **Ouvrir le dossier Logs**.

<a id="format-rapport"></a>
## Format du rapport

Un crash Python produit un fichier du type `crash-AAAAMMJJ-HHMMSS-...-PID.txt`. Les erreurs fatales capturées par `faulthandler` peuvent produire `native-crash-....log`.

Le rapport texte peut contenir :

- date et contexte ;
- version de l’application ;
- PID ;
- indication portable/PyInstaller ;
- versions Python et wxPython ;
- système et architecture ;
- chemin de l’exécutable/répertoire courant avec le dossier utilisateur masqué ;
- `BUILD.txt` et/ou `VERSION` **s’ils existent** à l’emplacement attendu ;
- chronologie technique de la « boîte noire » ;
- pile Python sécurisée.

<a id="version-build-crash"></a>
## Version, SHA et build

`VERSION` est la source canonique utilisée par la Vanilla wx actuelle. `BUILD.txt` n’est ajouté au rapport que s’il existe dans le paquet. Un SHA Git n’est donc pas garanti dans chaque rapport : joignez-le seulement s’il est affiché ou fourni avec le build.

Voir [[Versions et mises à jour wx]].

<a id="chronologie-technique"></a>
## Chronologie technique

La boîte noire enregistre des catégories d’actions wx utiles au diagnostic, par exemple changement de page, clic de bouton/menu ou création/destruction de fenêtre. Elle vise à montrer **la chronologie technique**, pas le contenu métier saisi.

<a id="confidentialite-crash"></a>
## Confidentialité

Le formateur de rapport est conçu pour **ne pas sérialiser** :

- variables locales ;
- valeurs de champs ;
- identifiants métier ;
- montants ;
- requêtes SQL ;
- contenu de la base ;
- message libre de l’exception.

Il masque aussi le chemin du dossier personnel lorsque cela est possible.

> Le système est conçu pour éviter les données métier sensibles. Avant tout partage, relisez néanmoins le fichier et n’ajoutez pas de capture, sauvegarde ou donnée personnelle inutile.

<a id="joindre-issue"></a>
## Que joindre à un signalement ?

- fichier de rapport correspondant au crash ;
- version Teamworks ;
- SHA/build uniquement s’il est disponible ;
- local ou réseau/MySQL ;
- action juste avant le problème ;
- étapes minimales de reproduction ;
- résultat attendu/obtenu.

Le dialogue sait ouvrir, copier et, selon la configuration de messagerie, envoyer le rapport technique. Pour le canal de support, voir [[Aide, discussions et signalement de bugs]].

## Points d’attention

- Un rapport n’explique pas forcément à lui seul la cause fonctionnelle ; la reproduction reste importante.
- Les rapports natifs peuvent être moins structurés qu’un rapport Python.
- En cas de gel sans crash, la chronologie/watchdog peut aider, mais l’analyse complète reste **À confirmer en recette fonctionnelle** selon le cas.

## Liens associés

[[Problèmes fréquents]] · [[Aide, discussions et signalement de bugs]] · [[Versions et mises à jour wx]]
