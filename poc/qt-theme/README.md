# POC isolé — moteur de thème Qt

Objectif : tester une nouvelle couche UI sans toucher au code wxPython de Teamworks.

Le POC est désormais un vrai stress-test métier :

- navigation Accueil / Individus / Présences / Planning / Recrutement / Documents RH ;
- tableau de bord avec alertes et accès rapides ;
- fiche salarié maître/détail avec 8 onglets ;
- formulaires denses, combobox, checkboxes, scroll, statuts ;
- tableau de contrats multi-colonnes avec sélection, filtres et actions ;
- dialogue de création de contrat ;
- tableau temps de travail sur plusieurs semaines ;
- documents RH et contrôles associés ;
- thème clair/sombre à chaud.

Le prototype n'importe aucun module de production et n'accède à aucune base Teamworks. Il peut être supprimé intégralement sans impact sur l'application.

## Architecture testée

```text
launcher.py
  ├─ ThemeEngine          -> thème central et tokens sémantiques
  ├─ TeamworksReadAdapter -> frontière vers le métier
  └─ app.py               -> stress-test UI jetable
```

`theme_engine.py` porte les rôles de couleur et de surface (`primary`, `surface`, `surface_container`, `outline`, `warning`, `danger`, `selection`, etc.). Qt Material ne sert plus que de couche QSS de base interchangeable.

`data_adapter.py` définit la frontière de lecture que devra respecter une future UI de production. Aucun objet wxPython, SQL brut ou widget ne doit la franchir. Le `DemoAdapter` alimente le POC ; le `ProductionAdapterStub` reste volontairement désactivé.

Cette organisation sert à tester la stratégie de migration progressive : conserver le domaine et les services Teamworks, remplacer la présentation sans injecter de logique métier dans Qt.

## Lancer le POC sous Windows

Double-cliquer sur :

```text
poc\qt-theme\run_windows.cmd
```

Le lanceur :

1. crée un environnement virtuel isolé si nécessaire ;
2. installe les seules dépendances du POC ;
3. compile les quatre modules Python pour détecter les erreurs de syntaxe ;
4. lance `launcher.py`.

## Critères GO / NO-GO

Le verdict porte sur :

1. qualité des tableaux, formulaires, onglets, boutons et dialogues ;
2. densité d'information desktop ;
3. thème sombre sans zones blanches résiduelles ;
4. changement global de thème sans retouche écran par écran ;
5. HiDPI et redimensionnement ;
6. facilité de migration progressive depuis wxPython ;
7. possibilité de brancher les services métier existants derrière un adaptateur stable.

### GO

Préparer un adaptateur de lecture réel vers les services/repositories Teamworks existants, sans dépendance à wxPython, puis migrer un seul écran de production pilote.

### NO-GO

Fermer la PR et supprimer `poc/qt-theme/`. Aucun autre code n'est affecté.
