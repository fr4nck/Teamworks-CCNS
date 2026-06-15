# Modernisation, optimisation et sobriété technique — Teamworks-CCNS

## Objet

Ce document formalise un axe de travail complémentaire pour Teamworks-CCNS :

- **moderniser** les points techniques vieillissants ;
- **optimiser** les lectures et calculs ;
- **réduire** les accès inutiles à la base de données ;
- **préparer** une exécution plus sobre et plus robuste.

Il ne remplace pas le plan d’intégration court terme.  
Il le complète, en donnant une direction claire pour la phase suivante.

---

## Constats

Le fork Teamworks-CCNS s’appuie sur un code historique Teamworks auquel s’ajoute une surcouche CCNS.

Cette situation crée naturellement plusieurs risques :

- dépendances anciennes ou API obsolètes ;
- répétition de lectures de contrats ;
- recalculs redondants entre plusieurs écrans ;
- appels SQL multipliés pour un même besoin ;
- chemins de lecture différents pour une même information.

En l’état, plusieurs points d’entrée peuvent relire les mêmes données :

- gadget d’accueil CCNS ;
- audit CCNS ;
- synthèse individuelle ;
- Dossiers incomplets ;
- potentiellement d’autres écrans liés aux contrats.

Si chacun recharge et recalcule seul, on obtient :
- plus de latence ;
- plus d’appels base ;
- plus de duplication de code ;
- plus de fragilité ;
- plus de consommation de ressources.

---

## Objectif général

Le but n’est pas de “faire moderne” pour faire moderne.

Le but est de tendre vers un code :

- **compatible** avec des versions Python et bibliothèques plus récentes ;
- **plus lisible** ;
- **moins bavard avec la base de données** ;
- **plus sobre** techniquement ;
- **plus simple à maintenir**.

---

## Axe 1 — Modernisation technique

### 1. Compatibilité Python et dépendances
Exemples déjà visibles :
- usages vieillissants de Pillow ;
- warnings de syntaxe historiques ;
- anciens patterns wx / Python à relire.

### 2. API obsolètes à remplacer progressivement
Exemples typiques :
- appels Pillow anciens ;
- comparaisons Python peu sûres ;
- chaînes regex non raw ;
- traitements hérités pouvant générer des warnings ou futures incompatibilités.

### 3. Principe retenu
La modernisation doit être **progressive** :
- d’abord garantir le fonctionnement ;
- ensuite remplacer proprement les appels obsolètes ;
- enfin remonter vers des versions de bibliothèques plus récentes.

---

## Axe 2 — Optimisation des lectures CCNS

### Constat
Les mêmes informations peuvent être relues plusieurs fois :
- liste des contrats ;
- classification ;
- type de contrat ;
- salaire de base ;
- temps hebdomadaire ;
- anomalies ;
- statut global.

### Risque
Faire :
- un audit complet pour l’accueil ;
- un audit complet pour Dossiers incomplets ;
- un audit complet pour la fiche individuelle ;
- un audit complet pour l’audit transverse,

revient à multiplier inutilement les lectures et calculs.

### Direction souhaitée
Passer d’une logique :
- **écran par écran**
- **requête par requête**

à une logique :
- **service partagé**
- **calcul une fois, réutilisation plusieurs fois**

---

## Axe 3 — Sobriété des accès base

### Principe
Tout ce qui peut être :
- lu une fois,
- enrichi une fois,
- réutilisé plusieurs fois,

ne doit pas être recalculé ou relu sans nécessité.

### Pistes concrètes
- regrouper les lectures liées aux contrats ;
- éviter les requêtes répétées par individu ;
- limiter les relectures de grilles salariales ;
- éviter les recalculs complets quand seul un individu est concerné ;
- distinguer les cas :
  - lecture globale ;
  - lecture ciblée ;
  - lecture de détail.

### Bénéfices
- moins d’appels SQL ;
- moins de charge ;
- moins de temps de réponse ;
- moins de duplication de logique ;
- moins d’énergie consommée pour une même tâche.

---

## Architecture cible à viser

### Aujourd’hui
Plusieurs points d’entrée peuvent refaire chacun leurs propres lectures et calculs.

### Demain
On vise une architecture plus simple :

```text
Base Teamworks / tables tw_*
        │
        ▼
Service central de lecture CCNS
        │
        ├─ contrats enrichis
        ├─ statuts CCNS
        ├─ anomalies
        ├─ synthèses par individu
        └─ indicateurs globaux
        │
        ▼
Écrans consommateurs
    ├─ accueil
    ├─ dossiers incomplets
    ├─ fiche individuelle
    └─ audit transverse
```

---

## Service central de lecture CCNS

### Rôle attendu
Un service central devra progressivement fournir :

- les contrats utiles ;
- les données enrichies par contrat ;
- les anomalies calculées ;
- les statuts individuels ;
- les indicateurs globaux d’accueil.

### Ce qu’il évite
Il évite que chaque écran :
- refasse ses requêtes ;
- refasse ses mappages ;
- refasse ses calculs.

### Ce qu’il permet
Il permet :
- une logique commune ;
- des résultats cohérents entre écrans ;
- une baisse du nombre de requêtes ;
- un futur cache léger si nécessaire.

---

## Cache léger raisonné

Le mot “cache” ne doit pas faire peur.  
Il ne s’agit pas ici de construire une usine.

### Idée simple
Sur une même session ou un même écran :
- garder en mémoire un résultat calculé ;
- invalider ce résultat quand une donnée contrat change ;
- éviter de recalculer tant qu’aucune modification n’est intervenue.

### Cas d’usage
- rafraîchir l’accueil sans relire toute la base à chaque clic ;
- réouvrir la synthèse individuelle sans refaire l’audit complet de tous les contrats ;
- alimenter Dossiers incomplets à partir d’un service déjà chargé.

---

## Ce qu’il faut éviter

Pour rester propre, il vaut mieux éviter :

- un cache opaque ou impossible à invalider ;
- une couche d’optimisation prématurée partout ;
- des lectures partielles incohérentes entre les écrans ;
- des micro-optimisations locales sans architecture commune.

---

## Chantiers concrets à prévoir

### Lot A — Compatibilité technique
- recenser les appels obsolètes ;
- corriger Pillow ;
- corriger les warnings de syntaxe bloquants ou bruyants ;
- fiabiliser le lancement sur une version Python raisonnable.

### Lot B — Cartographie des lectures
- identifier quels écrans lisent quoi ;
- lister les requêtes redondantes ;
- identifier les recalculs complets inutiles.

### Lot C — Service partagé CCNS
- créer une couche centrale de lecture ;
- factoriser les lectures contrats / classifications / grilles ;
- produire des objets ou dictionnaires réutilisables par plusieurs écrans.

### Lot D — Première sobriété réelle
- remplacer les audits complets inutiles ;
- limiter les recalculs au périmètre concerné ;
- préparer un cache local léger.

### Lot E — Validation
- comparer avant / après ;
- vérifier que les résultats affichés restent cohérents ;
- mesurer la baisse des requêtes ou des recalculs.

---

## Critères de réussite

Le chantier sera considéré comme utile si :

- le code devient plus lisible ;
- les écrans CCNS partagent la même logique ;
- le nombre de lectures répétées diminue ;
- le lancement devient plus robuste ;
- les résultats affichés restent cohérents ;
- l’intégration est plus simple à maintenir.

---

## Positionnement dans le projet

Ce chantier vient **après** :
- le branchement des points d’entrée ;
- les premiers tests réels ;
- l’identification des zones qui cassent ou doublonnent.

Autrement dit :
- **d’abord on branche**
- **ensuite on teste**
- **ensuite on modernise et on optimise utilement**

---

## Résumé

La modernisation utile de Teamworks-CCNS ne se résume pas à mettre à jour des bibliothèques.

Elle doit viser en même temps :

- la **compatibilité technique** ;
- la **réduction des appels base** ;
- la **mutualisation des lectures** ;
- la **sobriété de calcul** ;
- la **cohérence des écrans**.

La bonne trajectoire est donc :

> **faire tourner, brancher, tester, puis moderniser intelligemment en réduisant les accès et les recalculs inutiles.**
