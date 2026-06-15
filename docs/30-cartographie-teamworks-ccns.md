# Cartographie fonctionnelle et technique de Teamworks-CCNS

## Objet

Ce document décrit l’architecture actuellement posée pour le fork **Teamworks-CCNS** :
- ce qui relève du **cœur métier CCNS** ;
- ce qui relève des **contrôles** ;
- ce qui relève des **points d’entrée Teamworks** ;
- ce qui est déjà branché ou préparé dans le dépôt.

Il ne s’agit pas d’une notice utilisateur complète, mais d’une **vue d’ensemble projet** destinée au dépôt GitHub.

---

## Vision d’ensemble

Le fork Teamworks-CCNS repose sur quatre niveaux :

1. **Cœur métier**
2. **Moteur de contrôle**
3. **Intégration Teamworks**
4. **Écrans et points d’entrée**

### Schéma simple

```text
Accueil Teamworks
 └─ Gadget CCNS
      └─ alertes prioritaires / ouverture contrat

Dossiers incomplets
 └─ synthèse CCNS par individu
      ├─ bloquants
      ├─ à revoir
      └─ état global

Fiche individuelle
 └─ onglet Synthèse CCNS
      └─ détail des contrats et anomalies de la personne

Audit contrats
 └─ lecture transverse
      ├─ filtres
      ├─ tri par individu puis gravité
      ├─ export CSV
      └─ ouverture contrat
```

---

## 1. Cœur métier

Le cœur métier CCNS a été introduit comme une couche dédiée, distincte de l’historique Teamworks.

### Domaines couverts

#### Personnes et cadre juridique
- personne
- profil juridique

#### Contrats
- type de contrat
- régime d’emploi
- organisation du temps
- contrat

#### Convention collective
- classification CCNS
- grille salariale
- ligne de grille
- types de minima

#### Activité et affectations
- saison
- période
- activité
- lieu
- créneau
- affectation
- nature de temps

#### Contrôle et calcul
- règle de calcul
- résultat de calcul
- anomalie
- compteur individuel

#### Sécurité
- permissions
- rôles
- utilisateurs
- périmètres d’accès
- événements sensibles

---

## 2. Contrôles CCNS déjà posés

Le moteur n’est pas une paie complète. En revanche, plusieurs contrôles métier sont déjà préparés.

### Contrôles disponibles
- présence de la classification sur le contrat
- présence d’une grille salariale
- calcul du minimum conventionnel depuis la grille
- comparaison salaire saisi / minimum théorique
- temps partiel court :
  - jusqu’à 10 h
  - plus de 10 h et moins de 24 h
- ancienneté standard :
  - groupes 1 à 6
  - paliers de 2 ans
  - plafond à 15 %
  - base SMC groupe 3
- plafond CEE
- premiers cas apprentissage

### Types d’anomalies déjà utilisés
- contrat sans classification
- contrat sans grille
- minimum CCNS non atteint
- ancienneté oubliée
- ancienneté inférieure au théorique
- ancienneté appliquée à tort
- dépassement CEE
- règle introuvable

---

## 3. Persistance et bootstrap

Le fork dispose d’une première persistance minimale et d’un bootstrap de référence.

### Ce qui existe déjà
- repositories en mémoire
- conteneur runtime
- seed de données de référence
- règles CCNS par défaut
- classifications de base
- grille salariale initiale
- rôles par défaut

### Dans le dépôt Teamworks
Le raccord au dépôt historique a été préparé autour de :
- tables `tw_*`
- upgrade de base
- bridge CCNS
- script de seed Teamworks

---

## 4. Points d’entrée Teamworks

L’intégration a été pensée en réutilisant les écrans existants autant que possible.

### A. Accueil
**Gadget CCNS**
- compteurs synthétiques
- alertes prioritaires
- ouverture directe de contrat

### B. Dossiers incomplets
**Extension CCNS par individu**
- alertes bloquantes
- contrats à revoir
- contrats sans anomalie détectée
- synthèse globale de l’état CCNS d’une personne

### C. Fiche individuelle
**Onglet Synthèse CCNS**
- statut global de la personne
- nombre de contrats
- nombre d’anomalies
- détail par contrat
- ouverture directe du contrat

### D. Audit contrats
**Écran transverse d’analyse**
- lecture de contrats existants
- filtres
- tri par individu puis gravité
- export CSV
- ouverture directe du contrat
- marquage visuel des anomalies

### E. Registre du personnel
Le registre unique du personnel existe déjà dans Teamworks.
La stratégie retenue est de **ne pas le dupliquer** :
- l’écran historique reste la référence ;
- les enrichissements éventuels doivent se faire dans cet écran existant.

---

## 5. Répartition des rôles des écrans

### Vue globale
- **Accueil** : alerte rapide
- **Dossiers incomplets** : supervision par individu
- **Audit contrats** : contrôle transverse et export

### Vue détaillée
- **Fiche individuelle / Synthèse CCNS** : lecture complète par personne
- **Fiche contrat** : correction et vérification fine

---

## 6. Logique fonctionnelle retenue

Le fork Teamworks-CCNS ne vise pas à empiler des écrans parallèles.
La logique retenue est :

- **réutiliser Teamworks là où il a déjà un bon point d’entrée**
- **ajouter une couche CCNS spécialisée**
- **faire remonter les alertes au bon niveau**
- **laisser la correction se faire depuis les écrans contrats existants**

En pratique :
- l’accueil appelle l’attention ;
- dossiers incomplets organise la supervision ;
- la fiche individuelle donne une synthèse par personne ;
- l’audit donne une vue transverse ;
- la fiche contrat reste le point de correction.

---

## 7. État du projet

### Déjà posé
- socle domaine
- moteur de contrôle
- anomalies
- calcul des minima depuis grilles
- calcul d’ancienneté standard
- audit contrats
- synthèse par individu
- gadget accueil
- extension dossiers incomplets
- raccord initial au dépôt Teamworks
- seed de référence

### À consolider
- branchements effectifs dans tous les menus et écrans
- validation des imports et points d’entrée réels
- vérification des noms exacts de classes Teamworks
- tests manuels complets sur le dépôt réel
- ajustement final des tables et colonnes réellement utiles

### À venir ensuite
- consolidation des écrans existants plutôt que création de nouveaux écrans
- approfondissement des cas apprentissage
- enrichissement raisonné du registre unique du personnel existant
- fiabilisation du pont entre données historiques Teamworks et tables `tw_*`

---

## 8. Principe de conception

Le projet suit un principe simple :

> **pas de surcouche décorative ; une surcouche métier CCNS utile, lisible et branchée sur les écrans réellement utilisés.**

---

## 9. Résumé

Teamworks-CCNS est désormais structuré comme :
- un **cœur métier CCNS**
- un **moteur de contrôle**
- une **intégration progressive dans Teamworks**
- plusieurs **portes d’entrée complémentaires** :
  - accueil
  - dossiers incomplets
  - fiche individuelle
  - audit contrats

Le projet est donc déjà au-delà d’un simple cadrage : il constitue une base d’implémentation cohérente pour une extension CCNS de Teamworks.
