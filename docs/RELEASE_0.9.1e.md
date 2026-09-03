# Teamworks-CCNS 0.9.1e

## Nature de la version

`0.9.1e` est une corrective de stabilisation de `0.9.1d`, centrée sur la fiche individuelle, la saisie des coordonnées, l'adaptation à wxPython Phoenix et la cohérence UI sous zoom/DPI.

## Correctifs et durcissements inclus

- Généralités : prise en charge du lieu de naissance à l'étranger sans validation bloquante contre la base française des communes ;
- NIR : contrôle du département `99` pour une naissance à l'étranger ;
- adresse et lieu de naissance : comportement de saisie plus permissif hors contexte français ;
- Généralités : disposition responsive en une ou deux colonnes selon la largeur réellement disponible et l'échelle d'interface, compatible avec les Snap Layouts Windows 11 ;
- Coordonnées : conservation du correctif Phoenix sur les boutons `Fixe`, `Mobile`, `Fax`, `Email` et intégration cohérente dans la fiche Généralités ;
- boutons d'action : migration de plusieurs familles historiques vers le contrat commun `CTRL_Bouton_image`, avec rôles sémantiques et choix de ressources d'icônes multi-résolution ;
- dialogues compacts : recalcul de la géométrie après thème/zoom afin d'éviter les fenêtres étirées ou rognées ;
- recrutement, personnes, CCNS, publipostage et configurations exposées : garde-fous anti-régression sur les boutons et la géométrie.

## Compatibilité et données

- aucun changement volontaire de schéma de données ;
- conservation des parcours métier existants ;
- compatibilité Windows / wxPython Phoenix vérifiée par les parcours critiques de CI.

## Validation

La PR #364 est validée par la CI Windows avant fusion. Le paquet Windows `0.9.1e` ne doit être publié qu'après validation de `master`, afin que les binaires installable et portable correspondent exactement à la version publiée.

La publication Windows de cette corrective est explicitement déclenchée après validation verte de `master`. Une première tentative a été annulée automatiquement par un push de maintenance concurrent sur `master`; la relance est effectuée depuis le dernier état validé de `master`.
