# Teamworks-CCNS 0.9.1b — Validation Windows sur copie de base réelle

**Build de référence :** `4a226af71facf4fe201e022086e6dd00a46ecbf0`  
**CI de référence :** `#789`  
**Version :** `0.9.1b`

Ce document consigne la validation manuelle exigée avant toute qualification bêta ou RC. Il doit être exécuté sur une **copie autorisée de base réelle**, jamais sur l’unique base de production.

## 1. Préconditions

- [ ] utiliser le portable ou l’installateur issu de l’artefact Windows de la CI #789 ;
- [ ] vérifier l’empreinte SHA-256 du fichier utilisé ;
- [ ] conserver une copie intacte de la base avant le test ;
- [ ] fermer l’instance Teamworks de production et éviter toute écriture concurrente sur la copie de test ;
- [ ] noter la version de Windows et l’architecture du poste ;
- [ ] démarrer depuis un dossier fraîchement installé ou décompressé, sans dépendance à l’environnement développeur.

Empreintes de référence :

- portable ZIP : `b53aad8bda071165b6696e120f17f86001445057b7f6be931a5053fe218fe65f` ;
- installateur : `98917d083cb5cda827e4a8bb1b00985a8146d325a62e2030a53be53b8d2380ec`.

## 2. Informations de recette

| Champ | Valeur |
| --- | --- |
| Date | |
| Testeur | |
| Poste / Windows | |
| Mode utilisé | Portable / Installateur |
| Base de test | Copie réelle / autre |
| SHA du build | `4a226af71facf4fe201e022086e6dd00a46ecbf0` |
| Résultat global | À valider |

Statuts à utiliser : `OK`, `ANOMALIE`, `BLOQUANT`, `NON TESTÉ`, `NON APPLICABLE`.

## 3. Parcours minimal obligatoire

| # | Contrôle | Statut | Observation / anomalie |
| ---: | --- | --- | --- |
| 1 | Lancement de `Teamworks-CCNS.exe` | NON TESTÉ | |
| 2 | Ouverture de la copie de base réelle | NON TESTÉ | |
| 3 | Affichage de l’accueil | NON TESTÉ | |
| 4 | Affichage de la liste des salariés | NON TESTÉ | |
| 5 | Ouverture d’une fiche salarié | NON TESTÉ | |
| 6 | Ouverture de chaque onglet de la fiche salarié | NON TESTÉ | |
| 7 | Modification d’une donnée de test | NON TESTÉ | |
| 8 | Enregistrement de la modification | NON TESTÉ | |
| 9 | Fermeture puis redémarrage de Teamworks | NON TESTÉ | |
| 10 | Persistance de la donnée modifiée après redémarrage | NON TESTÉ | |
| 11 | Création d’une sauvegarde | NON TESTÉ | |
| 12 | Restauration d’une copie | NON TESTÉ | |
| 13 | Ouverture du parcours contrats / DUE | NON TESTÉ | |
| 14 | Création d’un contrat CCNS moderne | NON TESTÉ | |
| 15 | Création d’un contrat CEE | NON TESTÉ | |
| 16 | Renouvellement CDD, si le jeu de données le permet | NON TESTÉ | |
| 17 | Transformation CDD vers CDI, si le jeu de données le permet | NON TESTÉ | |
| 18 | Modèle de contrat | NON TESTÉ | |
| 19 | Publipostage / impression d’un contrat | NON TESTÉ | |
| 20 | Présences | NON TESTÉ | |
| 21 | Recrutement | NON TESTÉ | |
| 22 | Frais | NON TESTÉ | |
| 23 | Paramètres | NON TESTÉ | |
| 24 | Structure / organisation | NON TESTÉ | |
| 25 | Références administratives RH | NON TESTÉ | |
| 26 | Rapports | NON TESTÉ | |
| 27 | Publipostage général | NON TESTÉ | |
| 28 | Impression PDF | NON TESTÉ | |
| 29 | Fermeture normale de l’application | NON TESTÉ | |
| 30 | Absence de processus Teamworks résiduel après fermeture | NON TESTÉ | |

## 4. Contrôles UI prioritaires

Ces contrôles ne remplacent pas le parcours fonctionnel ci-dessus.

| Contrôle | Statut | Observation |
| --- | --- | --- |
| Aucun texte critique tronqué à l’échelle utilisée | NON TESTÉ | |
| Aucun grand espace ou panneau incohérent réapparu | NON TESTÉ | |
| Pas de doubles checkboxes | NON TESTÉ | |
| Mode Système cohérent avec Windows | NON TESTÉ | |
| Mode Clair | NON TESTÉ | |
| Mode Sombre | NON TESTÉ | |
| Sélections et contrôles désactivés lisibles | NON TESTÉ | |
| Logo / branding de l’organisation correct | NON TESTÉ | |
| Échelle d’interface persistante après redémarrage | NON TESTÉ | |

## 5. Anomalies constatées

Créer une ligne par anomalie réelle. Ne pas mélanger dette historique et défaut observé pendant la recette.

| Réf. | Écran / action | Gravité | Description reproductible | Données concernées | Correction requise avant pré-release |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

Gravité recommandée :

- `BLOQUANT` : empêche le parcours ou menace l’intégrité des données ;
- `MAJEUR` : fonction critique inutilisable ou résultat incorrect ;
- `MINEUR` : défaut réel sans blocage du parcours ;
- `COSMÉTIQUE` : présentation uniquement.

## 6. Critère de sortie

La recette est **réussie** uniquement si :

- tous les contrôles obligatoires applicables sont `OK` ;
- aucune perte ni altération non prévue de données n’est constatée ;
- sauvegarde et restauration fonctionnent ;
- aucune anomalie `BLOQUANT` ou `MAJEUR` non corrigée ne subsiste sur le parcours minimal ;
- les éventuels `NON APPLICABLE` sont justifiés ;
- les anomalies conservées sont documentées explicitement.

## 7. Décision

- [ ] recette réussie ;
- [ ] recette à reprendre après correction ;
- [ ] build rejeté.

**Décision / commentaire :**


**Validé par :**  
**Date :**

## 8. Suite après validation

Si la recette est réussie sans modification de code, le même build peut être examiné pour une qualification bêta interne. Si une correction de code est nécessaire, la validation machine et la recette doivent être rejouées sur le nouveau commit et son nouvel artefact ; le build `4a226af...` ne doit alors plus être présenté comme candidat courant.
