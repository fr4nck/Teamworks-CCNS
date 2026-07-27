# Recette fonctionnelle Teamworks-CCNS 0.9.0

## Objectif

Valider une version Windows exploitable sur une copie de base réelle avant publication de la version 0.9.0.

## Règles de recette

- Ne jamais tester sur la base de production.
- Créer une copie datée de la base et des fichiers associés.
- Noter chaque anomalie avec l’action, le résultat attendu, le résultat obtenu et une capture si utile.
- Toute anomalie bloquante empêche la publication de la version 0.9.0.

## Environnement cible

- Windows 10 ou Windows 11
- Python 3.11
- wxPython et dépendances du projet installées
- Copie récente de la base Teamworks-CCNS

## Parcours critiques

### 1. Démarrage et fermeture

- [ ] L’application démarre sans trace d’erreur bloquante.
- [ ] La fenêtre principale s’affiche correctement.
- [ ] La fermeture normale ne provoque ni blocage ni perte de données.
- [ ] Un second démarrage après fermeture fonctionne.

### 2. Salariés et contrats

- [ ] La liste des salariés s’ouvre.
- [ ] Une fiche salarié existante s’affiche.
- [ ] La création d’un salarié de test fonctionne.
- [ ] La modification puis l’annulation d’une fiche ne modifie pas les données.
- [ ] La création d’un contrat de test fonctionne.
- [ ] La modification d’un contrat existant fonctionne.
- [ ] Les dates, durées, groupes CCNS et rémunérations sont conservés après réouverture.

### 3. Contrôle salarial CCNS

- [ ] La consultation du contrôle salarial s’exécute.
- [ ] Les anomalies attendues sont affichées.
- [ ] Un contrat conforme n’est pas signalé à tort.
- [ ] L’export CSV fonctionne et s’ouvre dans un tableur.
- [ ] L’export JSON est valide et lisible.

### 4. Présences, plannings et absences

- [ ] Les plannings existants s’affichent.
- [ ] Une présence de test peut être créée puis supprimée.
- [ ] Une absence ou indisponibilité peut être enregistrée.
- [ ] Les contrôles de cohérence ne bloquent pas un cas valide.

### 5. Impression et publipostage

- [ ] Une prévisualisation d’impression s’ouvre.
- [ ] Un PDF est généré sans erreur.
- [ ] Les caractères accentués sont corrects.
- [ ] Un publipostage simple remplace correctement les mots-clés.
- [ ] Les listes de destinataires et pièces jointes ne sont pas réutilisées entre deux envois.

### 6. Sauvegarde et restauration

- [ ] Une sauvegarde manuelle est créée.
- [ ] Le fichier de sauvegarde est lisible et non vide.
- [ ] Une restauration est testée sur un environnement isolé.
- [ ] Les données restaurées correspondent à la sauvegarde.

### 7. Compatibilité des données historiques

- [ ] Les anciennes fiches contenant des accents s’ouvrent correctement.
- [ ] Les anciens fichiers ISO-8859-15 ou CP1252 ne provoquent pas d’erreur.
- [ ] Les exports historiques restent accessibles.

## Critères de publication 0.9.0

La version est publiable lorsque :

- tous les parcours critiques sont exécutés ;
- aucune anomalie bloquante ou critique n’est ouverte ;
- les tests automatisés GitHub Actions sont verts ;
- un paquet Windows reproductible est généré ;
- le numéro de version 0.9.0 est affiché dans l’application ou dans les métadonnées du paquet ;
- une note de version décrit les limites connues.

## Rapport de recette

| Date | Testeur | Environnement | Résultat | Anomalies |
|---|---|---|---|---|
|  |  |  |  |  |
