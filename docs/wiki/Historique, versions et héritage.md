# Historique, versions et héritage

Teamworks-CCNS descend du logiciel Teamworks/Noethys et conserve volontairement certaines compatibilités. Le wiki documente le fork actuel sans effacer les traces utiles de son histoire.

## Deux rails distincts

- **Vanilla wx** : référence historique/fonctionnelle documentée ici ;
- **Qt** : migration progressive sur un rail séparé.

Une fonction wx n’est pas annoncée comme disponible en Qt sans portage et validation dédiés.

## Version et état de publication

La branche documentaire auditée porte `0.9.2-rc3`. Une RC n’est pas une stable finale par simple déduction. Voir [[Versions et mises à jour wx]] pour distinguer `VERSION`, release, commit et build.

## Compatibilités historiques conservées

Exemples confirmés :

- `{BRUTMENS}` comme alias de `{SALAIREBRUTMENSUEL}` ;
- `CLASSIFICATION` et `VALEURPOINT` dans les anciens contrats/modèles ;
- libellé historique **OpenOffice Writer** alors que le pilote passe par UNO/`soffice` ;
- module D.U.E. historique pour l’édition PDF DPAE/DUE ;
- adresse `https://www.teamworks.ovh` conservée dans le cœur historique et comme site/forum historique, même si la coque actuelle masque l’ancienne entrée de menu.

## Forum historique et support actuel

Le **Forum historique Teamworks** reste une ressource d’archive. L’entraide du fork est orientée vers **Discussions GitHub** ; les bugs reproductibles relèvent des **Issues GitHub** lorsque cet espace est activé. Voir [[Aide, discussions et signalement de bugs]].

## Ce que le wiki refuse de déduire

Une classe, un commentaire, une ancienne aide ou un menu historique ne suffit pas à prouver un parcours actuel. Lorsqu’un écran existe dans le code mais que son comportement complet n’est pas qualifié, la documentation dit **À confirmer en recette fonctionnelle**.

## Liens associés

[[Versions et mises à jour wx]] · [[Architecture fonctionnelle]] · [[Aide, discussions et signalement de bugs]]
