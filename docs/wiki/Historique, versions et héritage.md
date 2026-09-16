# Historique, versions et héritage

Teamworks-CCNS descend d’un socle historique Teamworks/Noethys mais le fork actuel a ses propres corrections et évolutions. Ce wiki documente **Teamworks-CCNS actuel**, pas un manuel ancien recopié.

## Deux rails du projet

- **wx / Vanilla wx** : référence historique et de production du logiciel actuel ;
- **Qt** : migration progressive sur une branche séparée.

Les deux rails ne doivent pas être confondus. Une procédure wx n’est pas annoncée comme disponible en Qt sans validation du portage.

## Version documentée

Le fichier `VERSION` de la branche auditée contient `0.9.2-rc3`. Une RC est une candidate à la publication : elle peut être qualifiée pour test/validation mais n’est pas décrite comme « stable finale » par simple déduction.

## Compatibilités historiques conservées

Le code actuel maintient volontairement certaines compatibilités :

- `BRUTMENS` dans les anciens modèles de contrats ;
- `CLASSIFICATION` et `VALEURPOINT` pour les contrats historiques ;
- le libellé « OpenOffice Writer » dans l’interface alors que la voie technique passe par UNO/soffice ;
- différents écrans/aides portant encore des formulations anciennes.

Ces éléments sont documentés comme historiques lorsqu’ils fonctionnent encore, et non supprimés du manuel par souci de modernisation visuelle.

## Ce qui n’est pas une fonctionnalité actuelle

Une classe, un commentaire, une roadmap ou une ancienne page d’aide ne suffit pas à prouver un parcours utilisateur. Le wiki marque **À documenter après validation fonctionnelle** les zones dont le code existe mais dont le parcours exact n’a pas encore été confirmé par recette interactive.
