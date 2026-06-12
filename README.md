# Teamworks-CCNS

Fork de Teamworks orienté CCNS pour la gestion d’équipes et des cadres d’emploi dans le sport associatif.

Pour Windows, macOS et Linux.

Projet d’origine : https://github.com/Noethys/Teamworks

Ce dépôt vise à faire évoluer Teamworks afin d’intégrer progressivement les spécificités de la convention collective nationale du sport (CCNS), notamment autour :

* des cadres d’emploi ;
* des contrats ;
* du temps de travail ;
* des contrôles métier.

## Télécharger Teamworks-CCNS

Cliquez sur le bouton **Code** ci-dessus, puis sélectionnez **Download ZIP** pour télécharger l’intégralité du code source.

Décompressez ensuite l’archive dans le répertoire de votre choix.

## Installer Teamworks-CCNS sous Linux ou macOS

1. Installez Python 3.7 ou plus depuis le site https://www.python.org.

2. Ouvrez votre terminal.

3. Placez-vous dans le répertoire d’installation de Teamworks-CCNS. Exemple :

```bash
cd Teamworks-CCNS/
```

Si le dossier obtenu porte un autre nom après décompression de l’archive ZIP, adaptez simplement la commande `cd` au nom réel du dossier.

4. Créez un environnement virtuel Python dédié :

```bash
python3 -m venv .venv
```

5. Activez l’environnement virtuel :

```bash
source .venv/bin/activate
```

6. Installez les dépendances avec la commande suivante :

```bash
python3 -m pip install -r requirements.txt
```

## Installer Teamworks-CCNS sous Windows

1. Installez Python 3.7 ou plus depuis le site https://www.python.org.

   Durant l’installation, cochez bien l’option **Add Python 3.x to PATH**.

2. Ouvrez l’invite de commandes Windows.

3. Placez-vous dans le répertoire d’installation de Teamworks-CCNS. Exemple :

```bash
cd Teamworks-CCNS
```

Si le dossier obtenu porte un autre nom après décompression de l’archive ZIP, adaptez simplement la commande `cd` au nom réel du dossier.

4. Créez un environnement virtuel Python dédié :

```bash
python -m venv .venv
```

5. Activez l’environnement virtuel :

```bash
.venv\Scripts\activate
```

6. Installez les dépendances avec la commande suivante :

```bash
python -m pip install -r requirements.txt
```

## Lancer Teamworks-CCNS

Depuis le répertoire du projet, activez d’abord l’environnement virtuel si ce n’est pas déjà fait.

Sous Linux ou macOS :

```bash
source .venv/bin/activate
python3 Teamworks.py
```

Sous Windows :

```bash
.venv\Scripts\activate
python Teamworks.py
```

Le fichier principal de lancement reste pour le moment `Teamworks.py`.

## Cohabitation avec Teamworks d’origine

Teamworks-CCNS peut cohabiter avec le projet Teamworks d’origine, à condition de conserver deux répertoires séparés, par exemple :

```text
Teamworks/
Teamworks-CCNS/
```

L’utilisation d’un environnement virtuel Python propre à chaque projet est recommandée afin d’éviter les conflits de dépendances.
