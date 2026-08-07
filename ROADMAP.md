# Teamworks-CCNS — Roadmap officielle et unique

**Mise à jour : 7 août 2026**

Ce fichier est l’unique roadmap de référence du projet. Toute autre documentation peut détailler un domaine, mais ne doit pas porter une roadmap concurrente ni annoncer un niveau de maturité différent.

## 1. État réel du projet

Teamworks-CCNS est actuellement en **`0.9.0-dev`**.

Le socle Python 3 / wxPython Phoenix, la CI et le packaging Windows ont fortement progressé. Le dépôt sait désormais construire un portable Windows reproductible, exécuter des parcours critiques Windows automatisés et publier une Release sur tag conforme.

En revanche, la qualification **bêta / RC / stable reste volontairement refusée** tant que le parcours Windows minimal n’a pas été validé manuellement sur une copie de base réelle par l’utilisateur.

Aucune CI verte, aucun pourcentage d’avancement et aucun ZIP généré ne suffisent à qualifier une version.

## 2. Règles de vérité

Chaque annonce doit distinguer explicitement :

- code modifié ;
- tests automatisés réussis ;
- exécutable construit ;
- parcours Windows réellement exécuté ;
- validation utilisateur obtenue.

Les formulations « presque fini » et les dates de sortie non démontrées sont interdites.

## 3. Historique consolidé des lots récents

Les références ci-dessous décrivent ce qui est réellement intégré à `master`.

| Lot | Objet | Référence | État réel |
| --- | --- | --- | --- |
| TW-121 | Validation des préférences d’affichage Windows | PR #189 | Fusionné ; validation visuelle réelle à compléter |
| TW-122 | Restauration sûre des profils d’affichage Windows | PR #190 | Fusionné |
| TW-123 | Roadmap de livraison RC1 Windows | PR #191 | Fusionné puis supersédé par TW-126 / `ROADMAP.md` |
| TW-123 | Compatibilité Windows des profils d’affichage | PR #192 | Fusionné |
| TW-124 | Réparer le build Windows avec NumPy 2 | PR #193 | Fusionné |
| TW-125 | Verrouiller le contenu du ZIP Windows | PR #194 | Fusionné |
| TW-126 | Stabiliser les parcours runtime Windows | PR #195 | Fusionné |
| TW-126 | Établir une roadmap unique | PR #196 | Fusionné ; `ROADMAP.md` devient la seule roadmap |
| TW-127 | Utiliser réellement le thème système natif | PR #197 | Fusionné ; validation visuelle réelle à compléter |
| TW-128 | Consolider la CI et supprimer les builds Windows redondants | PR #198 | Fusionné |
| TW-129 | Consolider les contrôles légers dans un seul workflow | PR #199 | Fusionné |
| TW-130 | Préflight SQLite strictement en lecture seule | PR #200 | Fusionné |
| TW-131 | Workflow Tests reproductible et frugal | PR #201 | Fusionné |
| TW-132 | Build Windows reproductible et vérifiable | PR #202 | Fusionné |
| TW-133 | Vérifier réellement le manifeste du portable Windows | PR #203 | Fusionné |
| TW-134 | Publier automatiquement les builds Windows dans les Releases | PR #204 | Fusionné |
| TW-136 | Centraliser et fiabiliser toutes les dates | PR #205 | Fusionné |
| TW-137 | Corriger les libellés Unicode du calendrier | PR #206 | Fusionné |
| TW-138 | Migrer le socle historique en UTF-8 | PR #207 | Fusionné |
| TW-138 | Regrouper GitHub Actions dans un workflow unique | PR #208 | Fusionné |
| TW-139 | Auditer et stabiliser les parcours runtime | PR #209 | **Brouillon ouvert ; recette Windows réelle requise** |
| TW-139 | Supprimer définitivement les découpages manuels de dates | PR #210 | Fusionné |
| TW-140 | Fiabiliser les champs masqués de dates | PR #211 | Fusionné |
| TW-141 | Fiabiliser les listes du filtre recrutement | PR #212 | Fusionné |
| TW-142 | Fiabiliser la sélection multiple native | PR #213 | Fusionné |
| TW-143 | Corriger les filtres des boîtes d’export | PR #214 | Fusionné |

### Collisions historiques d’identifiants TW

Les identifiants `TW-123`, `TW-126`, `TW-138` et `TW-139` ont été réutilisés dans l’historique avant la consolidation de la gouvernance documentaire. Ces collisions sont conservées comme faits historiques et ne doivent pas être réécrites artificiellement.

**À compter de cette consolidation, un identifiant `TW-*` déjà présent dans une branche, un commit, une issue ou une PR ne doit plus être réattribué.**

## 4. Priorité immédiate — stabilisation avant pré-release

Aucune nouvelle fonction métier, convention collective ou refonte visuelle importante ne doit passer devant les validations suivantes :

1. terminer la recette Windows réelle du lot d’audit runtime ouvert en PR #209 ;
2. produire un portable Windows depuis `master` avec le workflow unique ;
3. exécuter le parcours minimal sur une copie de base réelle ;
4. corriger uniquement les anomalies bloquantes constatées ;
5. documenter les résultats ;
6. seulement ensuite décider si la version mérite une qualification bêta ou RC.

## 5. Parcours minimal de validation Windows

Un build n’est qualifiable en pré-release que si le parcours suivant est entièrement validé depuis un dossier fraîchement décompressé, sans dépendre d’un environnement développeur :

- lancement de `Teamworks-CCNS.exe` ;
- ouverture d’une copie de base réelle ;
- affichage de l’accueil ;
- affichage de la liste des salariés ;
- ouverture d’une fiche salarié ;
- ouverture de chaque onglet ;
- modification d’une donnée de test ;
- enregistrement ;
- fermeture et redémarrage ;
- vérification de la persistance ;
- création d’une sauvegarde ;
- restauration d’une copie ;
- fermeture sans processus résiduel.

Chaque étape doit avoir un résultat daté et préciser sa nature : automatique, CI Windows, test manuel développeur ou validation utilisateur.

## 6. Packaging Windows — état actuel

Le workflow unique `.github/workflows/ci.yml` construit le paquet Windows uniquement :

- sur déclenchement manuel explicite avec l’option de build ;
- sur tag `v*`.

Le packaging est actuellement fondé sur **Python 3.11**, **Windows Server 2022** et **PyInstaller 6.16.0**.

Le build :

- inventorie les modules internes ;
- inclut les paquets chargés dynamiquement ;
- inclut ressources et fichiers de version essentiels ;
- exécute un smoke test de démarrage ;
- produit un manifeste UTF-8 ;
- vérifie les empreintes SHA-256 des fichiers ;
- produit la somme SHA-256 du ZIP ;
- conserve la liste des dépendances réellement utilisées ;
- publie une GitHub Release uniquement lorsqu’un tag correspond exactement à `VERSION`.

Ce niveau de packaging est une condition nécessaire mais non suffisante pour une RC.

## 7. CI — état actuel

La CI doit rester **unique, lisible et frugale**.

Le seul workflow autorisé est `.github/workflows/ci.yml`.

Il regroupe :

- compilation et audits sur Ubuntu 24.04 / Python 3.11 ;
- politique UTF-8 ;
- tests automatisés ;
- parcours critiques Windows sur Windows Server 2022 ;
- build portable uniquement sur demande explicite ou tag.

Aucun deuxième workflow ne doit être ajouté pour contourner ou dupliquer ces contrôles.

## 8. Thèmes et affichage

Le mode `Système` doit reprendre les couleurs natives exposées par wxWidgets. Les modes `Clair` et `Sombre` restent des surcharges explicites.

Le code de préférences, de persistance, de restauration et de thème natif est intégré. La validation manuelle doit encore confirmer sur les écrans prioritaires :

- lisibilité complète ;
- absence de panneaux incohérents ;
- absence de texte tronqué avec l’échelle choisie ;
- persistance après redémarrage ;
- comportement correct des sélections et états désactivés.

## 9. Données, encodages et dates

État consolidé :

- sources et ressources textuelles suivies migrées vers UTF-8 ;
- compatibilité avec certains anciens encodages conservée aux frontières d’import ;
- normalisation centrale des dates historiques ;
- suppression des découpages manuels de dates recensés ;
- champs masqués de dates fiabilisés ;
- aucune migration destructive de la base réalisée dans ces lots.

Toute future migration de données devra rester séparée, sauvegardée et réversible.

## 10. Audit runtime en cours

La PR #209 reste la référence du chantier de recette runtime globale. Elle couvre notamment :

- Individus ;
- Présences ;
- Recrutement ;
- Contrats / DUE ;
- Frais ;
- Paramètres ;
- Rapports ;
- Impression / publipostage.

Son audit automatisable est avancé, mais **sa fusion reste conditionnée à la recette Windows manuelle sur base réelle**. Aucun document ne doit la présenter comme terminée avant cette validation.

## 11. Socle RH neutre après stabilisation

Après validation du parcours minimal :

- personnes ;
- contrats ;
- classifications ;
- absences ;
- congés ;
- plannings ;
- pointage ;
- documents ;
- droits ;
- historique ;
- sauvegardes ;
- exports.

Chaque bloc doit rester utilisable indépendamment des conventions collectives.

## 12. Moteur réglementaire

Les règles ne doivent pas être dispersées dans les écrans. Chaque règle doit comporter au minimum :

- identifiant stable ;
- domaine ;
- source ;
- date d’effet ;
- population concernée ;
- paramètres ;
- méthode de calcul ;
- message utilisateur ;
- cas limites ;
- tests associés ;
- historique de version.

Une règle n’est jamais déclarée prise en charge sans cas de tests démontrés.

## 13. Périmètre CCNS PMSL

Ordre de consolidation métier après stabilisation :

1. groupes et classifications ;
2. minima conventionnels et historique des grilles ;
3. temps partiels ;
4. ancienneté ;
5. préparation et trajets ;
6. durée du travail et dépassements ;
7. congés et absences ;
8. arrêts maladie et accidents du travail ;
9. apprentis et alternants ;
10. CEE ;
11. stagiaires ;
12. services civiques ;
13. salariés mineurs.

## 14. Intégrations après stabilisation

- imports CSV ou Excel ;
- rapprochement Noethys ;
- exports paie et comptabilité ;
- Dolibarr ;
- rapports PDF ;
- tableau de bord ;
- interface web ;
- autres conventions collectives.

Aucune intégration ne doit fragiliser le socle local.

## 15. Critères de maturité

### Bêta interne

- parcours minimal Windows validé ;
- aucune perte de données connue ;
- sauvegarde et restauration validées ;
- erreurs bloquantes journalisées ;
- fonctions annoncées réellement accessibles.

### Release candidate

- bêta utilisée sur copie réelle ;
- anomalies bloquantes corrigées ;
- tests de non-régression exécutés ;
- packaging reproductible ;
- validation explicite de l’utilisateur.

### Version stable

- période d’utilisation réelle sans anomalie bloquante ;
- procédure de secours documentée ;
- données récupérables ;
- règles métier critiques sourcées et testées ;
- limites connues publiées.

## 16. Mode de développement

- un seul fichier de roadmap : `ROADMAP.md` ;
- pas de ZIP à chaque PR ;
- workflow GitHub Actions unique ;
- PR regroupées par objectif testable ;
- aucune fusion sans critère de sortie explicite ;
- changelog fondé sur des fonctions vérifiées ;
- priorité aux parcours complets plutôt qu’au nombre de commits ;
- aucun nouvel identifiant TW sans vérification préalable de son absence dans l’historique.

## 17. Prochain jalon

Le prochain jalon est **la validation Windows réelle du socle actuel**, pas l’ajout de nouvelles fonctionnalités.

La séquence est :

**PR #209 / recette runtime → build portable `master` → parcours minimal sur copie réelle → correction des seuls blocages → décision de qualification pré-release.**
