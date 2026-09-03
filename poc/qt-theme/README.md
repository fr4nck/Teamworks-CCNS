# POC isolé — moteur de thème Qt

Objectif : tester en parallèle une nouvelle couche UI **exploitable, jolie et frugale**, sans toucher au code wxPython de Teamworks.

Le POC est un stress-test métier :

- navigation Accueil / Individus / Présences / Planning / Recrutement / Documents RH ;
- tableau de bord avec alertes et accès rapides ;
- fiche salarié maître/détail avec 8 onglets ;
- formulaires denses, combobox, checkboxes, scroll, statuts ;
- tableau de contrats multi-colonnes avec sélection, filtres et actions ;
- dialogue de création de contrat ;
- tableau temps de travail sur plusieurs semaines ;
- documents RH et contrôles associés ;
- thème clair/sombre à chaud ;
- mesure de démarrage, mémoire RSS et nombre de dépendances directes.

Le prototype n'accède à aucune base Teamworks et ne modifie aucune donnée de production. Il peut être supprimé intégralement sans impact sur l'application.

## Architecture testée

```text
launcher.py
  ├─ ThemeEngine               -> thème central et tokens sémantiques
  ├─ DemoAdapter               -> données factices du stress-test visuel
  ├─ DomainPeopleReadAdapter   -> lecture seule des vraies classes domaine/repository
  ├─ FrugalityProbe            -> démarrage / mémoire / dépendances, sans psutil
  └─ app.py                    -> stress-test UI jetable
```

`theme_engine.py` porte les rôles de couleur et de surface (`primary`, `surface`, `surface_container`, `outline`, `warning`, `danger`, `selection`, etc.). Qt Material n'est qu'une couche QSS de base interchangeable.

`data_adapter.py` définit la frontière de lecture attendue par l'UI. Aucun objet wxPython, SQL brut ou widget ne doit la franchir.

`domain_read_adapter.py` constitue la première connexion concrète avec l'architecture actuelle : il consomme `domain.people.Person` et `infrastructure.repositories.PeopleRepository` en lecture seule. Les informations qui n'existent pas encore dans le domaine restent vides au lieu d'être inventées.

`frugality.py` fixe des budgets initiaux et les mesure sans nouvelle dépendance :

- premier affichage : cible <= 3 s ;
- mémoire RSS : cible <= 220 Mo ;
- dépendances UI directes : cible <= 4 ;
- dépendances actuelles du POC : PySide6 + qt-material.

Ces seuils servent de garde-fou et seront ajustés après mesure réelle sur les postes Windows de l'association.

## Lancer le POC sous Windows

Double-cliquer sur :

```text
poc\qt-theme\run_windows.cmd
```

Le lanceur crée son environnement virtuel, installe les seules dépendances du POC, compile tous les modules du POC puis lance le stress-test. Après le premier affichage, la barre d'état et la console indiquent le temps de démarrage, la mémoire RSS et le statut du budget de frugalité.

## Critères GO / NO-GO

Le verdict porte sur trois axes indissociables :

### Exploitable
- écrans métier denses ;
- navigation et raccourcis cohérents ;
- adaptateurs stables vers les services/repositories existants ;
- aucune logique métier dupliquée dans Qt.

### Joli
- Fluent 2 comme référence desktop ;
- hiérarchie visuelle nette ;
- thèmes clair/sombre complets ;
- pas d'effets décoratifs lourds.

### Frugal
- démarrage et mémoire mesurés ;
- dépendances limitées ;
- pas de moteur web embarqué ;
- chargement progressif des écrans lourds ;
- mesures répétables sur Windows.

### GO
Brancher un adaptateur réel vers la persistance/services existants en lecture seule, puis migrer un écran pilote complet.

### NO-GO
Fermer la PR et supprimer `poc/qt-theme/`. Aucun autre code n'est affecté.
