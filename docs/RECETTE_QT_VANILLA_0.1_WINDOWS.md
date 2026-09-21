# Recette Windows — Qt Vanilla 0.1

Cette recette qualifie le candidat `qt-v0.1.0` sur un poste Windows réel et une copie de données représentative.

## Préconditions

- Windows 10 ou Windows 11 x64 ;
- compte utilisateur standard, avec élévation uniquement pour installer/désinstaller ;
- Vanilla wx conservée sur le poste pour vérifier la coexistence ;
- copie de la base de travail ou base de recette dédiée ;
- version MySQL identique à celle réellement déployée si l'exploitation est en réseau ;
- ZIP portable, setup EXE et `SHA256SUMS.txt` issus du même run de release.

Ne jamais réaliser la première recette sur l'unique base de production.

## 1. Intégrité des artefacts

1. calculer le SHA-256 du ZIP et du setup ;
2. vérifier les valeurs dans `SHA256SUMS.txt` ;
3. vérifier que le nom de version est `0.1.0`.

Critère : aucune différence de hash.

## 2. Portable isolé

1. extraire le ZIP dans un dossier temporaire ;
2. vérifier la présence de `Portable/` ;
3. vérifier l'absence de répertoire `wx` ou `wxPython` ;
4. lancer `Teamworks-CCNS-Qt.exe` ;
5. configurer uniquement la copie de base de recette ;
6. fermer puis relancer.

Critères :

- lancement sans Python installé ;
- aucune dépendance wx demandée ;
- aucune écriture dans le profil Teamworks habituel ;
- fermeture sans avertissement QThread.

## 3. Installation côte à côte

1. laisser la Vanilla wx installée ;
2. lancer le setup Qt ;
3. conserver le dossier proposé `Program Files\Teamworks-CCNS-Qt` ;
4. vérifier que la wx n'est ni remplacée ni désinstallée ;
5. lancer la Qt depuis le menu Démarrer.

Critères :

- deux applications coexistent ;
- aucun dossier `Portable/` sous l'installation Qt ;
- aucun fichier de base copié sous Program Files.

## 4. Individus et Généralités

1. charger la liste réelle de personnes ;
2. rechercher une personne par nom ;
3. sélectionner successivement trois personnes ;
4. contrôler identité, naissance, adresse et coordonnées ;
5. changer rapidement de personne pendant les chargements.

Critères :

- aucune donnée de la personne précédente ne reste affichée ;
- accents et caractères français corrects ;
- aucun blocage de fenêtre ;
- aucune exception visible.

## 5. Contrats

Sur un salarié de recette :

1. consulter les contrats ;
2. créer un CDI ou CDD CCNS valide ;
3. tenter une création avec rémunération invalide ;
4. modifier date, groupe/durée/rémunération dans le périmètre autorisé ;
5. basculer Signature ;
6. basculer DUE ;
7. annuler une suppression ;
8. confirmer une suppression sur un contrat de test ;
9. fermer et relancer l'application.

Critères :

- aucune écriture avant validation ;
- cas invalide : 0 commit ;
- cas valide : commit unique puis relecture ;
- annulation : aucune modification ;
- après redémarrage, la base et l'écran concordent.

## 6. Présences

1. consulter plusieurs jours et plusieurs personnes ;
2. vérifier un cas connu de durée ;
3. vérifier une personne sans présence.

Critères :

- lecture correcte ;
- état vide distinct d'une erreur ;
- aucun bouton d'écriture Présences revendiqué dans la 0.1.

## 7. Scénarios

1. consulter les scénarios d'une personne avec plusieurs scénarios ;
2. consulter une personne sans scénario.

Critère : lecture correcte, aucun CRUD Scénarios revendiqué dans la 0.1.

## 8. Frais

1. créer un déplacement ;
2. modifier ce déplacement ;
3. créer un remboursement ;
4. rattacher le déplacement ;
5. vérifier le refus de voler un déplacement déjà rattaché ;
6. détacher/supprimer selon le parcours qualifié ;
7. fermer et relancer.

Critères :

- transactions multi-tables cohérentes ;
- rollback sur cas refusé ;
- rattachement persistant après redémarrage ;
- aucun SQL visible dans l'UI.

## 9. Documents RH

Depuis un contrat :

1. ouvrir Documents RH ;
2. parcourir les types de document ;
3. vérifier les modèles compatibles ;
4. vérifier l'état prêt/bloqué/préparation externe ;
5. tester un dossier incomplet.

Critères :

- les anomalies sont explicites ;
- aucune fenêtre Word ou LibreOffice ne s'ouvre ;
- aucun fichier n'est prétendu généré ;
- aucune mutation de schéma due à la consultation.

## 10. MySQL réel

Répéter au minimum :

- chargement Individus ;
- création/modification/suppression d'un contrat de test ;
- cycle Déplacement/Remboursement ;
- ouverture Documents RH.

Critères :

- serveur réellement déployé accepté ;
- placeholders et transactions corrects ;
- aucune différence de résultat métier avec la recette SQLite de référence.

## 11. Fermeture et redémarrage

1. fermer après plusieurs changements rapides de personne ;
2. vérifier l'absence de `QThread destroyed while running` ;
3. relancer ;
4. vérifier la persistance des écritures validées.

## 12. Désinstallation

1. fermer Qt ;
2. désinstaller Qt Vanilla ;
3. vérifier que la wx démarre toujours ;
4. vérifier que les données/configurations utilisateur existent toujours ;
5. vérifier que la base de recette n'a pas été supprimée ou déplacée.

## Verdict

La recette est **PASS** uniquement si tous les critères obligatoires ci-dessus sont satisfaits.

Tout défaut de transaction, perte de données, dépendance wx du package, crash de fermeture, échec MySQL réel ou atteinte aux données utilisateur est bloquant pour le tag stable.
