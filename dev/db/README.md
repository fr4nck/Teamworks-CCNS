# Base de développement / recette Teamworks-CCNS

Ce dossier fournit un serveur **MySQL 5.5.62 isolé dans Docker** afin de reproduire l'environnement SQL historique sans installer MySQL 5.5 directement sur Windows et sans utiliser la production comme bac à sable.

L'application Teamworks reste exécutée **nativement sous Windows**. Seule la base de développement/recette est conteneurisée.

## Pré-requis

- Windows x64 ;
- Docker Desktop avec backend WSL2 ;
- PowerShell ;
- un dump SQL de test ou de production utilisé uniquement comme source transitoire locale.

L'image MySQL 5.5.62 est volontairement ancienne et épinglée. Le port est publié uniquement sur `127.0.0.1` : le serveur n'est pas exposé au réseau local ni à Internet.

## Première utilisation

```powershell
Copy-Item dev\db\.env.example dev\db\.env
notepad dev\db\.env
powershell -ExecutionPolicy Bypass -File dev\db\start.ps1
```

Choisir deux mots de passe longs et aléatoires dans `.env`. Le fichier `.env` n'est jamais versionné.

Connexion Teamworks :

- hôte : `127.0.0.1` ;
- port : `3307` par défaut ;
- base : valeur `TEAMWORKS_DB_NAME` ;
- utilisateur : valeur `TEAMWORKS_DB_USER` ;
- mot de passe : valeur `TEAMWORKS_DB_PASSWORD`.

## Importer une copie de base

Le dump doit rester **hors du dépôt Git**.

```powershell
powershell -ExecutionPolicy Bypass -File dev\db\import.ps1 -DumpPath "C:\Sauvegardes\teamworks.sql"
```

Le script copie temporairement le dump dans le conteneur, l'importe dans la base configurée puis supprime la copie temporaire du conteneur.

Pour repartir d'une base totalement vide :

```powershell
powershell -ExecutionPolicy Bypass -File dev\db\reset.ps1 -Force
```

Cette commande détruit uniquement le volume Docker `teamworks_mysql55_data`. Elle ne touche pas au serveur PMSL ni aux dumps externes.

## Anonymisation

Après import d'une copie réelle :

```powershell
powershell -ExecutionPolicy Bypass -File dev\db\anonymize.ps1 -Force
```

L'outil anonymise les tables historiques connues lorsqu'elles existent, neutralise les coordonnées et mots de passe applicatifs repérés et conserve les identifiants/relations nécessaires aux tests.

**Limite volontaire :** une base n'est pas considérée partageable uniquement parce que ce script a terminé. Tout nouveau champ ou module susceptible de contenir des données personnelles doit être ajouté à l'audit d'anonymisation. Les commentaires libres et pièces jointes nécessitent une vigilance particulière.

## Arrêter sans supprimer les données

```powershell
docker compose --env-file dev\db\.env -f dev\db\compose.yml stop
```

Pour redémarrer :

```powershell
powershell -ExecutionPolicy Bypass -File dev\db\start.ps1
```

## Niveaux de preuve

Ce conteneur améliore la reproductibilité, mais ne remplace pas :

1. les tests automatisés ;
2. le démarrage du portable Windows exact ;
3. la recette sur une copie représentative ;
4. la décision explicite de qualification bêta/RC/stable.
