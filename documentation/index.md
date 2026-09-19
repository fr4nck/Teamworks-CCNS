# Teamworks-CCNS — Documentation

Ce site décrit **Teamworks-CCNS Vanilla wx** tel qu'il existe réellement dans le code, vérifié section par section plutôt que supposé. La trajectoire **Qt** suit un rail séparé, à l'étude et sans code livré à ce jour : une fonction décrite ici n'est pas disponible en Qt sans portage et validation dédiés — voir [Trajectoire Qt](architecture/qt.md).

!!! info "Niveau de preuve"
    Les procédures de ce site sont reliées au code wx réel. Lorsqu'un comportement nécessite encore une vraie recette (Windows notamment), le site emploie explicitement **« à confirmer en recette fonctionnelle »** au lieu de compléter par déduction.

## Commencer

1. [Installation](demarrage/installation.md)
2. [Premier démarrage](demarrage/premier-demarrage.md)
3. [Configuration initiale](demarrage/configuration.md)

## Travailler avec les personnes et l'activité

- [Individus et fiches](utilisation/individus.md) — liste, recherche, colonnes et les huit onglets de la fiche.
- [Présences et planning](utilisation/presences-planning.md)
- [Contrats, CCNS et CEE](utilisation/contrats-ccns-cee.md) — contrats, rémunération et contrôles calculés.
- [DPAE et DUE](utilisation/dpae-due.md) — édition du formulaire PDF, sans télétransmission.
- [Recrutement](utilisation/recrutement.md) — candidats, candidatures, entretiens et offres d'emploi.
- [Frais et déplacements](utilisation/frais-deplacements.md)

## Produire des documents

- [Documents et publipostage](utilisation/documents.md) — parcours complet de fusion.
- [Éditeur interne (Teamword)](utilisation/editeur.md)
- [Référence des mots-clés](publipostage/mots-cles.md) — les 47 mots-clés standard, reconstruits depuis le code.
- [Contextes d'utilisation](publipostage/contextes.md) — quel mot-clé, dans quel document.

## Configurer et protéger les données

- [Paramétrage](administration/parametrage.md)
- [Utilisateurs et habilitations](administration/utilisateurs.md)
- [Données, sauvegardes et MySQL](administration/donnees-sauvegardes.md)
- [Mises à jour](demarrage/mise-a-jour.md)

## Se dépanner

- [Problèmes fréquents](reference/problemes-frequents.md)
- [Diagnostic et rapports de crash](administration/diagnostic.md)
- [Aide et signalement de bugs](reference/aide.md)
- [Glossaire](reference/glossaire.md)

## Pour les développeurs et contributeurs

- [Architecture — vue d'ensemble](architecture/vue-ensemble.md)
- [Organisation du dépôt](developpement/organisation-depot.md)
- [Contribuer et documenter](developpement/contribuer.md)

## Origine et migration

- [Historique du projet et migration depuis le Wiki](historique/origine-et-wiki.md)
