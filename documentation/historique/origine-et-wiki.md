# Origine du projet et migration du Wiki

## Deux rails d'interface

Teamworks-CCNS descend du logiciel **Teamworks/Noethys** et conserve volontairement certaines compatibilités historiques.

- **Vanilla wx** : rail wxPython historique et de production, seul rail réellement disponible aujourd'hui — c'est ce que documente l'ensemble de ce site.
- **Qt** : trajectoire d'interface à l'étude, sans code livré à ce jour. Voir [Trajectoire Qt](../architecture/qt.md). Une fonction wx n'est jamais annoncée comme disponible en Qt sans portage et validation dédiés.

## Compatibilités historiques conservées

Exemples confirmés dans le code :

- le champ de contrat historique `BRUTMENS` (avec `HEBDO`/`ANNUEL`) reste utilisable, mais l'assistant de création de contrat le masque automatiquement dès que la convention **CCNS** est sélectionnée, au profit du calcul natif — ce n'est pas un simple synonyme recopié automatiquement, voir [Référence des mots-clés](../publipostage/mots-cles.md) ;
- `CLASSIFICATION` et `VALEURPOINT` restent disponibles pour les anciens contrats/modèles ;
- le libellé historique **OpenOffice Writer** est encore utilisé dans l'interface, alors que le pilote technique passe par UNO/`soffice` (LibreOffice) ;
- le module D.U.E. historique pour l'édition PDF DPAE/DUE (voir [DPAE et DUE](../utilisation/dpae-due.md)) ;
- l'adresse `https://www.teamworks.ovh` reste présente dans le cœur historique du logiciel et comme site/forum d'archive, même si l'interface actuelle a retiré l'ancienne entrée de menu correspondante.

## Forum historique et support actuel

Le **forum historique Teamworks** reste une ressource d'archive. L'entraide du fork est orientée vers **Discussions GitHub** ; les bugs reproductibles relèvent des **Issues GitHub** lorsque cet espace est activé. Voir [Aide et signalement de bugs](../reference/aide.md).

## Ce que cette documentation refuse de déduire

Une classe, un commentaire, une ancienne aide ou un menu historique ne suffit pas à prouver un parcours actuellement fonctionnel. Lorsqu'un écran existe dans le code mais que son comportement complet n'a pas été vérifié par une recette réelle, cette documentation dit **à confirmer en recette fonctionnelle** plutôt que de l'affirmer.

## Migration depuis le Wiki GitHub

Avant cette documentation MkDocs, Teamworks-CCNS disposait :

1. d'un **Wiki GitHub** publié (`https://github.com/fr4nck/Teamworks-CCNS/wiki`), avec un contenu partiel et en partie daté ;
2. d'une **branche documentaire préparée mais jamais publiée dans le Wiki** (`docs/wiki-teamworks-ccns-ready`, dossier `docs/wiki/`, PR #432), plus complète (26 pages) et déjà relue une première fois contre le code.

Cette documentation MkDocs reprend la base de la branche `docs/wiki-teamworks-ccns-ready`, la corrige et l'enrichit à partir d'une nouvelle relecture complète du code (voir les avertissements de statut sur chaque page concernée), et l'organise selon la structure de navigation de ce site plutôt que la structure plate du Wiki.

### Tableau de correspondance

| Ancienne page (`docs/wiki/`) | Nouvelle page MkDocs |
|---|---|
| `Home.md` | [Accueil](../index.md) |
| `_Sidebar.md` | remplacé par la navigation MkDocs (`mkdocs.yml`) |
| `Installer Teamworks-CCNS wx.md` | [Installation](../demarrage/installation.md) |
| `Démarrage rapide.md` | [Premier démarrage](../demarrage/premier-demarrage.md) |
| `Paramétrage.md` | [Paramétrage](../administration/parametrage.md) (+ [Configuration initiale](../demarrage/configuration.md)) |
| `Versions et mises à jour wx.md` | [Mises à jour](../demarrage/mise-a-jour.md) |
| `Individus et fiches.md` | [Individus et fiches](../utilisation/individus.md) |
| `Contrats, CCNS et CEE.md` | [Contrats, CCNS et CEE](../utilisation/contrats-ccns-cee.md) |
| `Présences et planning.md` | [Présences et planning](../utilisation/presences-planning.md) |
| `Recrutement.md` | [Recrutement](../utilisation/recrutement.md) |
| `DPAE et DUE.md` | [DPAE et DUE](../utilisation/dpae-due.md) |
| `Frais et déplacements.md` | [Frais et déplacements](../utilisation/frais-deplacements.md) |
| `Publipostage et documents.md` | [Documents et publipostage](../utilisation/documents.md) |
| `Éditeur interne et documents.md` | [Éditeur interne (Teamword)](../utilisation/editeur.md) |
| `Mots-clés de publipostage.md` | [Référence des mots-clés](../publipostage/mots-cles.md) + [Contextes](../publipostage/contextes.md) (reconstruites depuis le code) |
| `Données, sauvegardes et MySQL.md` | [Données, sauvegardes et MySQL](../administration/donnees-sauvegardes.md) |
| `Sauvegardes et restauration.md` | fusionné dans [Données, sauvegardes et MySQL](../administration/donnees-sauvegardes.md) |
| `Diagnostic et rapports de crash.md` | [Diagnostic et rapports de crash](../administration/diagnostic.md) |
| `Problèmes fréquents.md` | [Problèmes fréquents](../reference/problemes-frequents.md) |
| `Aide, discussions et signalement de bugs.md` | [Aide et signalement de bugs](../reference/aide.md) |
| `Glossaire.md` | [Glossaire](../reference/glossaire.md) |
| `Architecture fonctionnelle.md` | [Architecture — vue d'ensemble](../architecture/vue-ensemble.md) |
| `Évolution documentaire Qt.md` | [Trajectoire Qt](../architecture/qt.md) |
| `Prototype FormEngine - synthèse.md` | [FormEngine et questionnaires](../architecture/formengine-questionnaires.md) |
| `Questionnaires et formulaires conditionnels.md` | fusionné dans [FormEngine et questionnaires](../architecture/formengine-questionnaires.md) |
| `Historique, versions et héritage.md` | cette page |

Pages **sans équivalent dans l'ancien Wiki**, ajoutées à partir de la lecture du code pour cette documentation : [Utilisateurs et habilitations](../administration/utilisateurs.md), l'ensemble de la section [Développement](../developpement/organisation-depot.md), et [Exemples de publipostage](../publipostage/exemples.md).

### État du Wiki GitHub publié

Le Wiki GitHub publié (`fr4nck/Teamworks-CCNS.wiki`) contenait, avant cette migration, une version plus ancienne et partielle de plusieurs pages ci-dessus, ainsi que deux pages sans équivalent dans `docs/wiki/` :

- `Accueil.md` — page d'accueil alternative, non issue de `docs/wiki/` ;
- `Publipostage-et-documents.md` (nom avec tirets) — doublon d'une version antérieure de la page publipostage, distinct du fichier `Publipostage et documents.md`.

Ces deux pages n'ont pas été supprimées lors des tentatives de synchronisation précédentes : elles restent à examiner (conserver, fusionner ou retirer) par un mainteneur disposant des droits d'écriture sur le dépôt Wiki. Voir la section « Ce qu'il reste à faire avant remplacement du Wiki » de la pull request de cette documentation.

## Voir aussi

[Mises à jour](../demarrage/mise-a-jour.md) · [Architecture — vue d'ensemble](../architecture/vue-ensemble.md) · [Aide et signalement de bugs](../reference/aide.md)
