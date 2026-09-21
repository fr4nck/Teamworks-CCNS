# Architecture fonctionnelle

Cette page donne seulement des repères aux utilisateurs avancés et contributeurs. Ce n’est pas une documentation développeur complète.

## Les grandes briques actuelles

| Brique | Rôle pratique |
|---|---|
| **wx** | interface actuelle de la Vanilla wx : fenêtres, panneaux, boutons, listes et événements |
| **Data** | données/fichiers utilisés par l’application et stockage local du dossier |
| **Utils** | utilitaires et une partie de la logique métier transverse : sauvegardes, publipostage, diagnostics, calculs, etc. |
| **Dlg** | dialogues/fenêtres de saisie et assistants : contrat, candidature, DPAE/DUE, Teamword… |
| **Ctrl** | contrôleurs/panneaux qui composent les pages principales et les onglets de fiches |
| **Ol** | listes basées historiquement sur ObjectListView : individus, candidats, contrats, etc. |
| **Teamword** | éditeur intégré implémenté comme dialogue wx RichText et utilisé par le publipostage |

## Exemple de parcours actuel

Une action utilisateur traverse souvent plusieurs briques :

```text
Page wx / Ctrl
   ↓
Dialogue Dlg
   ↓
Liste Ol ou logique Utils
   ↓
Données du dossier
```

Par exemple, **Individus > fiche > Contrats > Imprimer > D.U.E.** part d’un contrôleur de fiche, ouvre un dialogue DPAE/DUE et lit les données du contrat/personne avant de produire un PDF.

## Pourquoi ces repères sont utiles ?

- retrouver la zone à mentionner dans une Issue technique ;
- comprendre qu’une présence d’un ancien module dans le dépôt ne prouve pas qu’il est encore accessible dans l’interface actuelle ;
- distinguer interface, données et logique lorsqu’un comportement doit être vérifié.

## Vanilla wx et Qt

La structure ci-dessus décrit surtout le rail **wx**.

La stratégie actuelle est de conserver la Vanilla wx comme outil stable en maintenance légère, tandis que les évolutions structurelles sont étudiées côté Qt.

Deux chantiers illustrent cette séparation.

### Futur moteur documentaire

L'objectif est de sortir progressivement le modèle documentaire du widget d'édition :

```text
DocumentModel
     ↓
éditeur Qt / PDF / email
```

Teamword reste en place dans la Vanilla wx ; le nouveau moteur est étudié séparément.

Voir [[Évolution documentaire Qt]].

### Formulaires métier conditionnels

L'étude du moteur de questionnaires Noethys inspire un moteur de formulaires indépendant de l'UI :

```text
FormDefinition + réponses + contexte
                 ↓
              FormEngine
                 ↓
état des champs + validations
```

Le premier cas d'usage étudié est la demande de congé/absence.

Voir [[Questionnaires et formulaires conditionnels]].

## Principe commun aux nouveaux moteurs

Les nouveaux composants métier ne doivent pas dépendre directement de wx ou Qt lorsque cette dépendance n'est pas nécessaire.

L'interface doit consommer un moteur testable séparément, plutôt que devenir elle-même la source de vérité métier.

Cette orientation concerne les nouveaux développements ; elle ne signifie pas une réécriture immédiate de la Vanilla wx.

## Liens associés

[[Glossaire]] · [[Évolution documentaire Qt]] · [[Questionnaires et formulaires conditionnels]] · [[Diagnostic et rapports de crash]] · [[Historique, versions et héritage]]
