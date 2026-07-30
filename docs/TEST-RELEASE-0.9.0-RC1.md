# Recette Teamworks-CCNS 0.9.0-rc.1

Cette version est une **release candidate** destinée aux essais réels sous Windows. Elle ne doit pas être présentée comme une version stable avant validation des scénarios ci-dessous.

## Installation et démarrage

- Décompresser l’archive dans un dossier local non synchronisé.
- Lancer `Teamworks-CCNS.exe`.
- Vérifier l’absence de blocage, de fenêtre console parasite et d’erreur au démarrage.
- Vérifier que `VERSION`, `BUILD.txt`, `Versions.txt` et `PACKAGE-SHA256SUMS.txt` sont présents.

## Base de données

- Ouvrir une copie de base de données de test, jamais l’original de production.
- Vérifier l’ouverture sans erreur de module manquant.
- Vérifier la navigation dans les principaux écrans.
- Fermer puis rouvrir l’application et contrôler la persistance de la configuration.

## Interface

- Tester les icônes, boutons, liens et menus principaux.
- Vérifier qu’aucun clic ne provoque de gel de l’interface.
- Vérifier les boîtes de dialogue sur un écran Windows standard et avec mise à l’échelle élevée.

## Fonctions métier prioritaires

- Ouvrir un dossier salarié.
- Consulter les éléments contractuels et CCNS.
- Tester un contrôle ou calcul sans modifier les données de production.
- Tester les exports disponibles vers un dossier temporaire.
- Vérifier la journalisation et les messages d’erreur.

## Intégrité du paquet

- Comparer l’archive au fichier `SHA256SUMS.txt` publié avec la release.
- Conserver les journaux et une copie d’écran en cas d’anomalie.

## Critères de passage en 0.9.0 stable

La version stable pourra être publiée lorsque :

1. le démarrage est confirmé sur au moins un poste Windows réel ;
2. l’ouverture d’une base de test ne produit aucune erreur bloquante ;
3. les principaux écrans sont navigables sans gel ;
4. aucun module nécessaire n’est absent ;
5. aucun défaut critique de sauvegarde, de configuration ou d’intégrité n’est constaté.
