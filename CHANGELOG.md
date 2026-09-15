# Teamworks-CCNS 0.9.2

## Performance

- réduction des connexions MySQL répétées au premier affichage **Individus** ;
- calcul batché de l'arbre **État des dossiers** avec une connexion bornée par rafraîchissement ;
- optimisation des écrans Individus, fiches et Présences déjà intégrée au socle 0.9.2 ;
- instrumentation de performance opt-in conservée pour la recette Windows/MySQL réelle.

## Interface

- persistance de l'ordre, de la visibilité, du tri et des largeurs des colonnes Individus ;
- suppression du redimensionnement automatique qui réimposait notamment une largeur excessive à **Téléphones** ;
- affichage Individus préparé sous gel wx puis publié en une fois ;
- corrections de géométrie wx et de zones de travail déjà intégrées au socle ;
- identité affichée alignée sur la version Teamworks-CCNS distribuée.

## Stabilité

- corrections des questionnaires et de leur ordre d'initialisation ;
- correction de `AttributeError: flush` à la fermeture journalisée ;
- durcissement du parcours DPAE/DUE et de ses transactions ;
- corrections des valeurs `NULL` dans les champs de publipostage ;
- protections du cycle de vie du publipostage Word/Writer ;
- corrections de plusieurs crashs et incompatibilités wxPython Phoenix présents dans la branche 0.9.2.

## Documents

- publipostage Individus indépendant de la première colonne visible ;
- corrections des mappings de mots-clés de contrats, notamment `CLASSIFICATION`, `CPNAISS` et `ADRESSERESID` ;
- fiabilisation de la fermeture et de la relance des traitements de documents.

## Nettoyage du produit

- suppression du parcours utilisateur des sollicitations commerciales historiques ;
- retrait des liens visibles vers l'ancien forum et les anciens services promotionnels ;
- remplacement de l'aide payante historique par une information Teamworks-CCNS neutre ;
- archivage séparé de l'historique upstream ancien.

## Héritage

Teamworks-CCNS dérive du projet historique Teamworks/Noethys. L'historique upstream est conservé séparément dans `docs/legacy/`.

> Cette liste décrit uniquement les changements présents dans la branche candidate 0.9.2. Les performances finales et les parcours Word/LibreOffice restent à confirmer sur le poste Windows/MySQL réel avant gel de la Vanilla.
