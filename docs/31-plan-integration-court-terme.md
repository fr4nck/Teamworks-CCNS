# Plan d’intégration court terme — Teamworks-CCNS

## Objet

Ce document décrit le **prochain cycle de travail utile** pour Teamworks-CCNS.

L’objectif n’est plus d’ajouter des briques isolées, mais de :
- **brancher** ce qui a déjà été préparé ;
- **stabiliser** les points d’entrée dans Teamworks ;
- **vérifier** les usages réels ;
- **consolider** les données et les parcours.

Ce plan est volontairement court terme, concret et exécutable.

---

## Principe directeur

Le fork a déjà posé :
- un cœur métier CCNS ;
- un moteur de contrôle ;
- plusieurs écrans ou points d’entrée ;
- un premier raccord au dépôt Teamworks.

La priorité n’est donc plus la multiplication des modules.

La priorité devient :

> **intégrer, tester, simplifier, consolider.**

---

## Lot 1 — Brancher les points d’entrée existants

### Objectif
Rendre visibles dans Teamworks les points d’entrée déjà préparés.

### À faire
- brancher le **gadget d’accueil CCNS** dans l’accueil ;
- brancher la logique CCNS dans la fenêtre **Dossiers incomplets** ;
- brancher l’onglet **Synthèse CCNS** dans la **fiche individuelle** ;
- brancher les entrées de menu utiles :
  - seed CCNS ;
  - audit CCNS ;
  - registre du personnel si retenu dans sa forme finale ;
- vérifier les points d’ouverture de contrat depuis :
  - l’audit ;
  - la synthèse individuelle ;
  - les gadgets ;
  - dossiers incomplets.

### Résultat attendu
Un utilisateur peut atteindre la logique CCNS depuis les écrans naturels de Teamworks sans passer par des scripts.

---

## Lot 2 — Stabiliser l’audit CCNS

### Objectif
Transformer l’audit en outil réellement exploitable sur des données du dépôt.

### À faire
- vérifier que l’audit lit correctement les contrats historiques ;
- valider les correspondances :
  - type de contrat ;
  - classification ;
  - salaire de base ;
  - temps hebdomadaire ;
  - prime d’ancienneté ;
- tester les filtres ;
- tester le tri par individu puis gravité ;
- tester l’export CSV ;
- vérifier l’ouverture du contrat depuis la liste ;
- corriger les éventuels décalages entre données réelles et hypothèses du moteur.

### Résultat attendu
L’audit devient un outil de lecture fiable pour relire les contrats existants.

---

## Lot 3 — Consolider la supervision par individu

### Objectif
Faire de la logique “individu” le vrai point de lecture opérationnel.

### À faire
- vérifier l’intégration de la **Synthèse CCNS** dans la fiche individuelle ;
- vérifier le calcul du statut global d’un individu :
  - bloquant ;
  - à revoir ;
  - ok ;
  - aucun contrat ;
- vérifier la cohérence entre :
  - Dossiers incomplets ;
  - Synthèse CCNS ;
  - Audit transverse ;
- vérifier que les mêmes anomalies remontent partout de manière cohérente ;
- éviter les doublons de libellés ou de navigation.

### Résultat attendu
La supervision par individu devient cohérente quel que soit le point d’entrée.

---

## Lot 4 — Consolider les données de référence

### Objectif
Réduire l’écart entre bootstrap de travail et base réellement exploitable.

### À faire
- relire les classifications injectées ;
- relire la grille salariale de référence ;
- vérifier les lignes de minima déjà saisies ;
- vérifier les règles de seed dans les tables :
  - historiques ;
  - `tw_*` ;
- confirmer les valeurs encore provisoires ;
- distinguer clairement :
  - données de démonstration ;
  - données de travail ;
  - données prêtes à être stabilisées.

### Résultat attendu
Le dépôt ne repose plus sur des valeurs ambiguës ou insuffisamment relues.

---

## Lot 5 — Vérifier le registre et les écrans RH existants

### Objectif
S’assurer que les écrans RH existants restent la référence là où ils doivent l’être.

### À faire
- relire le **registre unique du personnel existant** dans Teamworks ;
- éviter toute duplication inutile ;
- n’ajouter que les enrichissements réellement justifiés ;
- vérifier la cohérence avec :
  - la fiche individuelle ;
  - les contrats ;
  - les données d’entrée/sortie ;
- décider explicitement ce qui reste dans l’écran historique et ce qui relève des écrans CCNS.

### Résultat attendu
Les usages RH historiques restent lisibles et ne sont pas brouillés par une surcouche inutile.

---

## Lot 6 — Consolider le raccord technique au dépôt réel

### Objectif
Passer de “briques préparées” à “intégration techniquement robuste”.

### À faire
- vérifier les imports réels ;
- vérifier les noms exacts des classes Teamworks ;
- vérifier les chemins de modules ;
- vérifier les ouvertures de dialogues ;
- vérifier les points de montage dans les menus et notebooks ;
- vérifier la montée de version de base ;
- vérifier la création effective des tables `tw_*`.

### Résultat attendu
Le fork devient techniquement plus stable dans le vrai dépôt Teamworks.

---

## Lot 7 — Premier cycle de tests manuels

### Objectif
Faire un vrai tour d’horizon fonctionnel avant d’ajouter de nouvelles briques.

### Parcours minimal recommandé
1. lancer Teamworks ;
2. exécuter le seed CCNS ;
3. vérifier les tables et données injectées ;
4. ouvrir l’audit CCNS ;
5. tester filtres, tri et export ;
6. ouvrir un contrat depuis l’audit ;
7. ouvrir une fiche individuelle ;
8. vérifier la Synthèse CCNS ;
9. ouvrir la fenêtre Dossiers incomplets ;
10. vérifier les nœuds CCNS ;
11. vérifier le gadget d’accueil.

### Résultat attendu
Une liste claire :
- de ce qui fonctionne ;
- de ce qui casse ;
- de ce qui est redondant ;
- de ce qui doit être simplifié.

---

## Ordre conseillé d’exécution

### Priorité immédiate
1. **Lot 1 — Brancher les points d’entrée**
2. **Lot 2 — Stabiliser l’audit**
3. **Lot 3 — Consolider la supervision par individu**

### Ensuite
4. **Lot 6 — Consolider le raccord technique**
5. **Lot 4 — Consolider les données de référence**
6. **Lot 5 — Vérifier les écrans RH existants**
7. **Lot 7 — Cycle de tests manuels**

---

## Ce qu’il ne faut pas faire tout de suite

Pour garder le projet lisible, il vaut mieux éviter à court terme :

- créer de nouveaux écrans concurrents à ceux qui existent déjà ;
- multiplier les variantes de registre ;
- élargir le moteur CCNS à trop de cas spéciaux avant stabilisation ;
- ajouter de nouvelles couches de reporting tant que les points d’entrée actuels ne sont pas propres ;
- complexifier l’accueil au-delà d’un rôle de tableau d’appel.

---

## Critère de réussite du cycle court terme

Le cycle sera considéré comme réussi si :

- la logique CCNS est visible depuis les bons écrans ;
- l’utilisateur comprend où regarder selon son besoin ;
- l’audit est fiable et exploitable ;
- la supervision par individu est cohérente ;
- les ouvertures de contrats fonctionnent ;
- les données de base ne sont plus purement théoriques ;
- le dépôt devient plus démontrable et plus testable.

---

## Résumé

Le prochain objectif n’est pas d’inventer davantage.

Le prochain objectif est de faire en sorte que **ce qui existe déjà prenne vraiment forme dans Teamworks** :

- **accueil**
- **dossiers incomplets**
- **fiche individuelle**
- **audit**
- **raccord dépôt réel**

C’est cette phase qui transformera Teamworks-CCNS d’un ensemble de briques prometteuses en un fork réellement manipulable.
