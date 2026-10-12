# Politique CI Teamworks-CCNS

## Principe

La CI doit apporter une preuve utile sans multiplier les exécutions coûteuses.

## Tests automatiques

Les contrôles rapides de compilation, tests unitaires et audits statiques peuvent s'exécuter sur les pull requests lorsqu'ils couvrent directement les fichiers modifiés.

## Build Windows

Le build Windows complet n'est jamais déclenché automatiquement sur chaque pull request ou chaque push.

Il est lancé uniquement :

- manuellement lorsqu'un lot cohérent doit être testé sur Windows ;
- automatiquement lors de la création d'un tag de version.

Un seul workflow Windows produit l'exécutable, exécute le smoke test et crée le ZIP portable.

## Ressources

- aucun workflow redondant pour une même preuve ;
- annulation d'une exécution précédente du même build lorsqu'une nouvelle démarre ;
- conservation courte des artefacts intermédiaires ;
- aucun build pour une modification documentaire seule ;
- aucun statut bêta, RC ou stable sans validation Windows réelle.

## Qualification portable : consolidation du 12 octobre 2026

Le tri de la PR historique #391 conserve un seul harnais portable maintenu :
`scripts/test_windows_portable_isolated.ps1`. L'ancien nom
`test_windows_portable_isolation.ps1` reste un point d'entrée compatible et
lui transmet les paramètres. Il n'exécute plus sa propre sonde ni le nettoyage
récursif d'un dossier temporaire partagé. Le rapport `qualification-portable.json`
et la copie du paquet sont conservés dans un dossier temporaire unique, dont
le chemin est affiché ; l'ancien rapport `windows-release-portable.json` à la
racine du dépôt n'est plus produit par ce point d'entrée.

Le harnais exige deux ouvertures de fenêtre, le marqueur d'import Email et
deux fermetures avec code de sortie zéro. Un `BUILD.txt` vide est refusé avant
lancement ; la même garde est ajoutée au test installateur. Le SHA attendu
reste une option : sans `ExpectedCommit`, la cohérence avec un commit donné
n'est pas vérifiée. Le manifeste est alors une provenance déclarée, sans
preuve que le paquet correspond à la tête de la branche.

Les dossiers source ne sont ni masqués ni renommés. L'isolation du paquet,
du répertoire courant et de l'environnement Python ne prouve donc pas à elle
seule qu'un paquet ne pourrait jamais lire le checkout par un chemin absolu.
La garantie de masquage de #391 n'est pas réimportée, et la PR reste ouverte.

Validation locale : 25 tests ciblés réussis et syntaxe PowerShell des trois
scripts vérifiée. Les nouveaux tests reproduisent le faux succès sur un code
de sortie 7 avec un processus doublé, exécutent le refus du manifeste vide
sur un paquet factice et vérifient la transmission des paramètres historiques.
Ils ne constituent ni une exécution réelle de l'application packagée, ni une
recette graphique Windows, ni une installation/désinstallation qualifiée.
Pas de build ou CI lourde lancé dans ce lot.
