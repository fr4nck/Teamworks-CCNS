# POC isolé — moteur de thème Qt

Objectif : tester sérieusement une nouvelle couche UI sans toucher au code wxPython de Teamworks.

Le POC est volontairement plus gros qu'une simple maquette : il doit mettre Qt sous contrainte avec les composants qui posent problème dans une vraie application RH dense.

## Ce que le stress-test contient maintenant

### Coquille principale

- navigation Accueil / Individus / Présences / Planning / Recrutement / Documents RH ;
- barre d'état ;
- panneau latéral dense ;
- changement clair/sombre à chaud ;
- redimensionnement à partir de 1100×720 jusqu'aux grands écrans ;
- préférences d'affichage factices pour tester les dialogues.

### Tableau de bord

- cartes de synthèse ;
- alertes métier ;
- accès rapides ;
- panneaux juxtaposés et splitter redimensionnable.

### Individus / fiche salarié

- liste filtrable ;
- navigation maître/détail ;
- résumé du salarié sélectionné ;
- formulaire dense ;
- combobox ;
- checkboxes ;
- statut visuel ;
- scroll ;
- huit onglets : Généralités, Qualifications, Contrats, Présences/temps, Scénarios, Frais, Documents RH et Recrutement.

### Contrats

- barre de commandes ;
- tableau dense multi-colonnes ;
- sélection de lignes par checkbox ;
- filtre Actifs uniquement ;
- états de contrôle ;
- sélection multiple ;
- dialogue Nouveau contrat ;
- champs, listes, spinbox, texte multiligne et contrôles de conformité.

### Temps de travail

- tableau de 18 semaines ;
- volumes prévus/réalisés ;
- écarts ;
- repos, pauses, amplitudes et états ;
- filtre de période et commandes.

### Documents RH

- tableau de documents ;
- cases à cocher ;
- états ;
- boutons d'action intégrés aux lignes.

Tout cela utilise exclusivement des données factices. Le POC n'importe **aucun module de production** et n'accède à **aucune base Teamworks**.

## Stack testée

- PySide6 : bindings Qt officiels pour Python ;
- qt-material : moteur QSS open source utilisé comme moteur de thème interchangeable.

Material n'est pas la direction graphique finale. Le but est de vérifier le principe : une couche Qt peut-elle recevoir un thème global et rester cohérente sur les tableaux, dialogues, formulaires et widgets complexes ? Si oui, le moteur pourra être remplacé ou complété par une couche Fluent/tokens propre à Teamworks.

## Lancer sous Windows

Double-cliquer sur :

```text
poc\qt-theme\run_windows.cmd
```

Le lanceur :

1. crée un environnement virtuel local au POC ;
2. installe ses dépendances ;
3. compile `app.py` pour détecter une erreur de syntaxe ;
4. lance l'interface.

Rien n'est installé globalement dans Teamworks.

## Critères Go / No-Go

Après essai, regarder surtout :

1. **Densité** — peut-on afficher beaucoup d'informations sans fabriquer des cartes géantes ?
2. **Tableaux** — sélection, colonnes, scroll, lignes, alternance, checkboxes : est-ce propre et rapide ?
3. **Formulaires** — alignement, focus, clavier, lisibilité et ergonomie.
4. **Dark mode** — reste-t-il des zones blanches ou des widgets incohérents ?
5. **Dialogues** — donnent-ils immédiatement un résultat plus propre que les dialogues wx historiques ?
6. **HiDPI / redimensionnement** — comportement sur écran Windows réel.
7. **Cohérence globale** — le thème agit-il sur l'application entière sans retouche écran par écran ?
8. **Performance perçue** — démarrage, navigation entre onglets, scroll et rafraîchissement.

## Règle de décision

- **GO** si le gain visuel et ergonomique est net tout en conservant la densité métier : prochaine étape = adaptateur en lecture seule vers les services métier existants.
- **NO-GO** si Qt ne fait qu'embellir sans résoudre les problèmes de cohérence, densité et thème global : suppression de `poc/qt-theme` sans impact sur le produit.

Aucune fusion dans `master` ne doit être faite avant ce verdict.
