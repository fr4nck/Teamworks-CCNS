# Teamworks-CCNS

Fork de **Teamworks** orienté **CCNS** pour la gestion d’équipes, de contrats, de classifications et de contrôles métier dans le sport associatif.

Projet d’origine : Teamworks  
Cible du fork : **structurer une surcouche CCNS utile, lisible et progressive**, branchée sur les écrans réellement utilisés dans Teamworks.

---

## Positionnement du fork

Teamworks-CCNS n’a pas vocation à être une réécriture complète de Teamworks.

Le projet vise à :

- conserver les usages utiles déjà présents dans Teamworks ;
- ajouter un **cœur métier CCNS** dédié ;
- introduire des **contrôles métier** exploitables ;
- faire remonter les alertes aux bons endroits de l’interface ;
- éviter la multiplication d’écrans parallèles quand un point d’entrée pertinent existe déjà.

En pratique :

- l’**accueil** sert d’appel rapide ;
- la fenêtre **Dossiers incomplets** sert de supervision globale par individu ;
- la **fiche individuelle** sert de point de lecture détaillé ;
- les **écrans contrats** restent le point naturel de correction ;
- l’**audit CCNS** sert de vue transverse et exportable.

---

## Ce que le fork introduit

### 1. Un cœur métier CCNS
Le fork prépare une couche dédiée pour gérer notamment :

- personnes ;
- profils juridiques ;
- contrats ;
- classifications CCNS ;
- grilles salariales ;
- affectations ;
- règles métier ;
- résultats de contrôle ;
- anomalies ;
- compteurs individuels.

### 2. Des contrôles CCNS
Le moteur posé dans le fork couvre déjà la logique de base autour de :

- classification présente ou absente ;
- grille salariale présente ou absente ;
- calcul du minimum conventionnel depuis une grille ;
- comparaison entre salaire saisi et minimum théorique ;
- temps partiel court ;
- ancienneté standard ;
- premiers cas CEE ;
- premiers cas apprentissage.

### 3. Une intégration progressive dans Teamworks
L’intégration est pensée autour des écrans existants, notamment :

- gadget d’accueil CCNS ;
- extension CCNS de la fenêtre **Dossiers incomplets** ;
- synthèse CCNS par individu dans la **fiche individuelle** ;
- audit CCNS des contrats ;
- listes exportables ;
- points d’ouverture directe des contrats.

---

## Architecture projet

Le fork s’organise autour de quatre niveaux :

1. **cœur métier**
2. **moteur de contrôle**
3. **raccord Teamworks**
4. **points d’entrée interface**

### Vue simple

```text
Accueil Teamworks
 └─ Gadget CCNS
      └─ alertes prioritaires / ouverture contrat

Dossiers incomplets
 └─ supervision CCNS par individu
      ├─ alertes bloquantes
      ├─ contrats à revoir
      └─ synthèse globale

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

## État d’avancement

### Déjà posé
- socle domaine ;
- moteur de contrôle ;
- anomalies ;
- calcul des minima depuis grilles ;
- calcul d’ancienneté standard ;
- bootstrap de données de référence ;
- seed Teamworks ;
- audit CCNS des contrats ;
- liste d’audit exportable ;
- filtres ;
- marquage visuel ;
- tri par individu puis gravité ;
- synthèse CCNS par individu ;
- extension de la fenêtre **Dossiers incomplets** ;
- gadgets d’accueil CCNS ;
- premiers raccords au dépôt Teamworks.

### À consolider
- branchements effectifs dans les menus et écrans réels ;
- validation des imports et noms exacts de classes Teamworks ;
- tests manuels complets dans le dépôt réel ;
- consolidation des tables et colonnes réellement utiles ;
- durcissement progressif des cas métier spécifiques.

---

## Documents utiles

Le dépôt a vocation à contenir une documentation projet simple et lisible, notamment :

- cartographie fonctionnelle et technique ;
- ordre de migration ;
- objets conventionnels ;
- activité et affectations ;
- moteur et anomalies ;
- contrôles CCNS détaillés ;
- synthèse d’intégration dans Teamworks ;
- règles de développement relatives aux performances ;
- règles de pérennité technique, de compatibilité multiplateforme et de gestion des dépendances ;
- guide opérationnel des agents et contributeurs (`AGENTS.md`) ;
- matrice de compatibilité réelle (`docs/MATRICE_COMPATIBILITE.md`) ;
- feuille de route de maintenance (`docs/FEUILLE_ROUTE_MAINTENANCE.md`).

---

## Principe de conception

Le principe directeur du fork est le suivant :

> **pas de surcouche décorative ; une surcouche métier CCNS utile, progressive et branchée sur les écrans réellement utilisés.**

---

## Installation

Les modalités d’installation restent proches de Teamworks tant que le fork poursuit son intégration progressive.

### Linux

1. Installer Python 3.7 ou plus.
2. Ouvrir un terminal.
3. Se placer dans le répertoire du projet.
4. Installer les dépendances :

```bash
pip install -r requirements.txt
```

### Windows

1. Installer Python 3.7 ou plus.
2. Cocher l’option d’ajout au `PATH` lors de l’installation.
3. Ouvrir l’invite de commandes.
4. Se placer dans le répertoire du projet.
5. Installer les dépendances :

```bash
pip install -r requirements.txt
```

---

## Lancement

Depuis le répertoire `teamworks/` :

```bash
python Teamworks.py
```

---

## Objectif du projet

L’objectif n’est pas seulement de stocker davantage d’informations RH.

L’objectif est de permettre à Teamworks de mieux couvrir :

- les contrats et cadres d’emploi ;
- les classifications CCNS ;
- les minima conventionnels ;
- la lecture des anomalies ;
- les points de contrôle utiles au quotidien ;
- la supervision par individu et par contrat.

---

## Statut

Le projet est en cours de structuration active.

Le fork est déjà au-delà d’un simple cadrage :
il constitue une **base d’implémentation cohérente** pour une extension CCNS de Teamworks, mais demande encore de la consolidation côté intégration réelle.
