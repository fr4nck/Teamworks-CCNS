# Architecture fonctionnelle

Cette page donne seulement des repères aux utilisateurs avancés et contributeurs. Ce n’est pas une documentation développeur complète.

## Les grandes briques

| Brique | Rôle pratique |
|---|---|
| **wx** | interface actuelle de la Vanilla wx : fenêtres, panneaux, boutons, listes et événements |
| **Data** | données/fichiers utilisés par l’application et stockage local du dossier |
| **Utils** | utilitaires et une partie de la logique métier transverse : sauvegardes, publipostage, diagnostics, calculs, etc. |
| **Dlg** | dialogues/fenêtres de saisie et assistants : contrat, candidature, DPAE/DUE, Teamword… |
| **Ctrl** | contrôleurs/panneaux qui composent les pages principales et les onglets de fiches |
| **Ol** | listes basées historiquement sur ObjectListView : individus, candidats, contrats, etc. |
| **Teamword** | éditeur intégré implémenté comme dialogue wx RichText et utilisé par le publipostage |

## Exemple de parcours

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

La structure ci-dessus décrit surtout le rail **wx**. La migration **Qt** est séparée ; elle ne doit pas recevoir automatiquement les correctifs ou comportements spécifiques wx.

## Liens associés

[[Glossaire]] · [[Diagnostic et rapports de crash]] · [[Historique, versions et héritage]]
