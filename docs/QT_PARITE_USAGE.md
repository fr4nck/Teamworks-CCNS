# Qt : matrice de parité d'usage (première recette)

La capacité à lancer le portable Qt ne suffit pas à déclarer la parité avec la
Vanilla wx. Cette matrice est volontairement prudente ; les parcours ci-dessous
restent à confirmer sur une copie des données d'exploitation PMSL.

| Parcours Qt | État technique | Ce qui reste à qualifier |
| --- | --- | --- |
| Ouvrir l'application et rechercher un salarié | Tests Qt + démarrage Windows | Liste réelle et usage quotidien |
| Sélectionner une fiche et consulter Généralités | Lecteur dédié + chargement différé | Données historiques représentatives |
| Modifier nom/prénom/adresse/CP/ville/mémo | Écriture SQL paramétrée, conflit détecté, commit + relecture | Recette Windows sur copie, droits et concurrence |
| Contrats : créer, modifier, supprimer | Services transactionnels et tests Qt existants | Champs métiers, modèles de documents et parcours complets |
| Présences et frais | Services Qt d'écriture présents | Recette fonctionnelle avec données métier |
| Qualifications, questionnaire, recrutement, scénarios | Parcours en partie en consultation ou aperçu | CRUD et intégration à compléter |
| Créer une fiche minimale (nom, prénom, adresse, CP, ville, mémo) | Formulaire Qt, insertion SQLite/MySQL, commit et relecture, test Qt de bout en bout | Recette Windows sur copie des données ; autres champs restent à compléter |
| Suppression salarié, NIR et référentiels | Non implémentés dans le nouveau parcours | Conception métier et tests renforcés |

## Règles de la première modification salarié

Seuls les six champs ci-dessus sont modifiables : pas de num_secu, date de
naissance, nationalité, codes de pays, situation sociale ou coordonnées liées.
L'éditeur ouvre une connexion spécifique sur le thread de l'interface, séparée
des connexions SQLite utilisées par les workers. La mise à jour compare la
version lue lors de l'ouverture ; en cas de conflit, aucune écriture n'est validée.

Une fois le commit réalisé, la relecture confirme les données persistées.
Si cette relecture échoue, le résultat indique explicitement qu'un commit a déjà
eu lieu ; aucun faux rollback n'est annoncé. La liste et la fiche sont mises à
jour sur succès, puis rechargées par un worker.

Cette première verticalité ne constitue pas une parité fonctionnelle.
La Vanilla wx reste la version de référence ; aucun changement n'est apporté
à wx/master. PostgreSQL reste différé conformément à PMSL-Arch ADR-010.


## Extension : création de fiche minimale

Le bouton « Ajouter » ouvre désormais le même formulaire Qt en mode création.
Seuls les six champs déjà qualifiés sont insérés ; aucune valeur fictive n'est
affectée au NIR, à la naissance, aux contrats ou aux référentiels sociaux.
L'identifiant attribué par la base est vérifié après commit. La nouvelle fiche
apparaît dans la liste et devient sélectionnée. L'annulation ne démarre aucune
connexion d'écriture. Une erreur de relecture après commit n'est pas annoncée
comme une annulation : l'utilisateur est invité à vérifier la liste plutôt que
créer un doublon.

La CI vérifie les imports wx statiques des modules d'interface Qt et la
suppression de wxPython dans le paquet. Cela ne démontre PAS encore la parité
fonctionnelle de Teamworks avec la version Vanilla wx.
