# Architecture — vue d'ensemble

Cette page donne des repères aux utilisateurs avancés, contributeurs et agents IA travaillant sur le dépôt. Ce n'est pas un dump du code — pour le détail, voir [Organisation du dépôt](../developpement/organisation-depot.md).

## Les grandes briques de l'application wx (`teamworks/`)

| Brique | Rôle pratique |
|---|---|
| **wx** (`Teamworks.py`, `Teamworks_core.py`) | interface actuelle : fenêtres, panneaux, boutons, listes et événements. Points d'entrée confirmés : `Teamworks.py` (`app.MainLoop()`), `Teamworks_core.py` (`class MyApp(wx.App)`, `class MyFrame(wx.Frame)`, `class Toolbook(wx.Toolbook)` pour la navigation par onglets) |
| **Data** | données/fichiers statiques utilisés par l'application |
| **Utils** | utilitaires et logique métier transverse : sauvegardes, publipostage, diagnostics, calculs, thème |
| **Dlg** | dialogues/fenêtres de saisie et assistants : contrat, candidature, DPAE/DUE, Teamword… |
| **Ctrl** | contrôleurs/panneaux qui composent les pages principales et les onglets de fiches |
| **Ol** | listes basées sur ObjectListView : individus, candidats, contrats, etc. |
| **CcnsCore** | moteur métier CCNS ajouté par le fork (audit de contrats en lot, contrôles salariaux) |

## Exemple de parcours actuel

```text
Page wx / Ctrl
   ↓
Dialogue Dlg
   ↓
Liste Ol ou logique Utils
   ↓
Données du dossier (GestionDB)
```

Par exemple, **Individus > fiche > Contrats > Imprimer > D.U.E.** part d'un contrôleur de fiche, ouvre un dialogue DPAE/DUE et lit les données du contrat/personne avant de produire un PDF — voir [DPAE et DUE](../utilisation/dpae-due.md).

## Une seconde couche moderne, en construction

En parallèle du socle wx historique, le dépôt développe une couche métier moderne, indépendante de wx et testable séparément :

- **`domain/`** : modèle métier pur (contrats, convention/CCNS/CEE, planning, missions, personnes, sécurité/accès…), sans dépendance wx ni base de données ;
- **`application/`** : cas d'usage et services qui orchestrent ce modèle (contrôle salarial, bootstrap, sécurité) ;
- **`infrastructure/`** : implémentations concrètes (lecture SQL) des interfaces définies côté `domain/`, encore appuyées sur `GestionDB`.

Cette couche alimente réellement certains calculs affichés dans l'application (contrôle CCNS/CEE de l'assistant de contrat — voir [Contrats, CCNS et CEE](../utilisation/contrats-ccns-cee.md)), mais une partie (planning/missions, habilitations) est **encore un modèle de domaine non branché à une interface** — voir les avertissements sur les pages concernées ([Présences et planning](../utilisation/presences-planning.md), [Utilisateurs et habilitations](../administration/utilisateurs.md)).

## Un module wx réellement disponible : les questionnaires

Teamworks-CCNS embarque un module de questionnaires configurables par fiche individuelle (onglet **Questionnaire**), hérité de Noethys : questions, types de contrôle (texte, entier, listes, case à cocher, date, réglette, document), réponses stockées en base. Ce module est **fonctionnel et testé**, mais c'est un formulaire **statique** : il n'a pas de logique conditionnelle (afficher/masquer/rendre obligatoire un champ selon la réponse à un autre). Voir [FormEngine et questionnaires](formengine-questionnaires.md) pour le chantier visant à ajouter cette logique conditionnelle.

## Pourquoi ces repères sont utiles

- retrouver la zone à mentionner dans une Issue technique ;
- comprendre qu'une présence d'un ancien module dans le dépôt ne prouve pas qu'il est encore accessible dans l'interface actuelle ;
- distinguer interface, données et logique lorsqu'un comportement doit être vérifié ;
- ne pas confondre un modèle de domaine moderne « prêt sur le papier » avec une fonctionnalité utilisateur disponible.

## Vanilla wx et Qt

Toute la structure ci-dessus décrit le rail **wx**, seul rail réellement en production. Une trajectoire Qt est à l'étude, **sans code livré à ce jour** — voir [Trajectoire Qt](qt.md).

## Voir aussi

[Organisation du dépôt](../developpement/organisation-depot.md) · [Trajectoire Qt](qt.md) · [FormEngine et questionnaires](formengine-questionnaires.md) · [Historique du projet](../historique/origine-et-wiki.md) · [Glossaire](../reference/glossaire.md)
