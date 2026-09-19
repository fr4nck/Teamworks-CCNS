# Installation

Cette page concerne la **Vanilla wx**, seule interface disponible aujourd'hui. La trajectoire Qt est une vision à l'étude, sans code livré — voir [Trajectoire Qt](../architecture/qt.md).

## Éditions disponibles

Le projet peut livrer un **installateur Windows** et une **archive portable**. L'installateur place l'application dans un emplacement Windows ; le portable fonctionne depuis son dossier décompressé et facilite les essais isolés.

Avant de remplacer une installation utilisée, suivez [Sauvegardes et restauration — avant une mise à jour](../administration/donnees-sauvegardes.md#avant-mise-a-jour).

## Vérifier la version

La Vanilla wx lit le fichier `VERSION` comme source canonique. Un `BUILD.txt` peut exister dans certains paquets et rapports, mais il n'est pas garanti dans l'arbre source. Une version au suffixe `-rc` (release candidate) est une version candidate à la publication, pas une version stable finale par simple déduction. Voir [Mises à jour](mise-a-jour.md).

## Installation Windows

1. Fermez Teamworks-CCNS.
2. Sauvegardez le dossier métier/base concerné.
3. Lancez l'installateur de la version que vous avez décidé de déployer.
4. Conservez l'ancien paquet/installateur pour un retour arrière tant que la nouvelle version n'est pas validée.
5. Lancez Teamworks et vérifiez la version affichée avant d'ouvrir un dossier important.
6. Après ouverture, contrôlez quelques parcours représentatifs.

## Version portable

1. Décompressez l'archive dans un nouveau dossier où vous pouvez écrire.
2. Ne lancez pas l'exécutable directement depuis l'archive ZIP.
3. Ne mélangez pas les fichiers de deux versions dans le même répertoire.
4. Vérifiez la version puis ouvrez un dossier de test avant un dossier de production.

## Premier lancement

Teamworks peut afficher l'**Assistant Démarrage**. Le menu **Fichier** permet aussi **Créer un nouveau fichier** ou **Ouvrir un fichier**. L'application mémorise les dossiers récents.

Un dossier local s'appuie notamment sur `<nom>_TDATA.dat`. Un dossier réseau/MySQL utilise le mode `[RESEAU]`. Ne renommez pas manuellement ces éléments pour tenter de réparer un dossier.

## Mise à jour

Le menu wx contient une recherche de mise à jour, mais son fonctionnement complet sur les paquets actuels reste **à confirmer en recette fonctionnelle**. Pour une version publiée, contrôlez l'espace **Releases GitHub** décrit dans [Mises à jour](mise-a-jour.md).

Ce mécanisme concerne **la Vanilla wx uniquement**, pas une trajectoire Qt (inexistante à ce jour).

## Résultat attendu

Teamworks démarre, affiche la version attendue et permet d'ouvrir/créer un dossier sans message de migration inattendu. Après une mise à jour, contrôlez Individus, contrats, présences et un publipostage représentatif avant de considérer la migration validée.

## Points d'attention

- Désinstaller l'application n'est pas une sauvegarde des données.
- Une migration de schéma peut modifier le dossier ; conservez une sauvegarde antérieure.
- N'utilisez pas une RC comme « stable » simplement parce qu'elle démarre.

## Problèmes fréquents

Pour un démarrage impossible ou une mise à jour indisponible, voir [Problèmes fréquents](../reference/problemes-frequents.md). Pour un rapport de crash, voir [Diagnostic et rapports de crash](../administration/diagnostic.md).

## Voir aussi

[Premier démarrage](premier-demarrage.md) · [Sauvegardes et restauration](../administration/donnees-sauvegardes.md) · [Mises à jour](mise-a-jour.md) · [Diagnostic et rapports de crash](../administration/diagnostic.md)
