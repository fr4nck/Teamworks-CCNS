# Teamworks-CCNS — Roadmap officielle et unique

Mise à jour : 29 juillet 2026

Ce fichier est l'unique roadmap de référence du projet. Toute autre roadmap doit être supprimée. Les tickets, PR, notes de version et décisions techniques doivent rester cohérents avec ce document.

## 1. État réel du projet

Teamworks-CCNS est actuellement un prototype de migration Windows non validé en usage réel.

La désignation `v0.9.0-rc1` est annulée comme indicateur de maturité. Le build a été produit, mais le parcours élémentaire démarrer → ouvrir une base → ouvrir un dossier salarié n'avait pas été validé sur le poste utilisateur.

Aucune version ne doit être qualifiée de bêta, RC ou stable sur la seule base d'une CI verte ou d'un ZIP généré.

## 2. Règles de vérité

Chaque annonce doit distinguer explicitement :

- code modifié ;
- tests automatisés réussis ;
- exécutable construit ;
- parcours Windows réellement exécuté ;
- validation utilisateur obtenue.

Les pourcentages d'avancement, les formulations « presque fini » et les dates de sortie non démontrées sont interdits.

## 3. Priorité immédiate — gel fonctionnel

Aucune nouvelle fonction métier, nouvelle convention collective ou refonte visuelle importante tant que le socle n'est pas fiable.

Ordre obligatoire :

1. démarrage de l'exécutable portable ;
2. présence de toutes les dépendances et ressources ;
3. ouverture d'une base existante ;
4. affichage de la liste des salariés ;
5. ouverture d'une fiche individuelle ;
6. chargement de tous les onglets ;
7. modification, enregistrement et relecture ;
8. sauvegarde et restauration sur copie ;
9. fermeture propre ;
10. journalisation exploitable des erreurs.

## 4. Parcours minimal de validation Windows

Un build n'est publiable que si le parcours suivant est entièrement validé sur Windows depuis un dossier fraîchement décompressé, sans Python installé :

- lancement de `Teamworks.exe` ;
- ouverture d'une copie de base réelle ;
- affichage de l'accueil ;
- affichage de la liste des salariés ;
- ouverture d'une fiche salarié ;
- ouverture de chaque onglet ;
- modification d'une donnée non sensible ;
- enregistrement ;
- fermeture et redémarrage ;
- vérification de la persistance ;
- création d'une sauvegarde ;
- restauration d'une copie ;
- fermeture sans processus résiduel.

Chaque étape doit avoir un résultat daté : automatique, CI Windows, test manuel développeur, validation utilisateur.

## 5. Packaging Windows

Le packaging doit :

- inclure les paquets chargés dynamiquement ;
- inclure ressources, traductions, icônes, licences et fichiers de version ;
- échouer si un module ou fichier obligatoire manque ;
- produire un manifeste de contenu ;
- produire une somme SHA-256 ;
- conserver la liste figée des dépendances ;
- être testé depuis un chemin contenant espaces et caractères accentués ;
- ne contenir aucun chemin absolu du poste de développement.

Les modules chargés via `importlib`, `__getattr__`, plugins ou imports conditionnels doivent être inventoriés et contrôlés automatiquement.

## 6. Thèmes et affichage

Le mode `Système` doit reprendre le thème natif de Windows, Linux ou macOS.

Le thème doit s'appliquer à l'ensemble de l'interface wxPython : fenêtres, panneaux, boîtes de dialogue, listes, arbres, notebooks, champs, boutons, menus et zones de texte.

Les modes `Clair` et `Sombre` sont des surcharges explicites. Un thème partiel n'est pas considéré comme livré.

La validation comprend au minimum :

- Windows 11 clair ;
- Windows 11 sombre ;
- changement de thème puis redémarrage ;
- lisibilité de tous les textes ;
- absence de panneaux blancs isolés en mode sombre ;
- contraste suffisant des éléments sélectionnés, désactivés et en erreur.

## 7. Inventaire technique obligatoire

Avant toute nouvelle extension métier, documenter :

- écrans existants ;
- tables et fichiers de données utilisés ;
- imports dynamiques ;
- dépendances externes ;
- fonctions opérationnelles ;
- fonctions partielles ;
- fonctions mortes ;
- règles historiques héritées ;
- règles ajoutées pour PMSL ;
- zones sans tests.

## 8. Socle RH neutre

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

Chaque bloc doit être utilisable indépendamment des conventions collectives.

## 9. Moteur réglementaire

Les règles ne doivent pas être dispersées dans les écrans.

Chaque règle doit comporter :

- identifiant stable ;
- domaine : légal, conventionnel, accord PMSL ou paramétrage interne ;
- source ;
- date d'effet ;
- population concernée ;
- paramètres ;
- méthode de calcul ;
- message utilisateur ;
- cas limites ;
- tests associés ;
- historique de version.

Une règle n'est jamais déclarée prise en charge sans cas de tests démontrés.

## 10. Périmètre CCNS PMSL

Ordre de traitement :

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

Chaque contrôle doit afficher la règle, les données utilisées, le résultat et les données manquantes.

## 11. Intégrations après stabilisation

- imports CSV ou Excel ;
- rapprochement Noethys ;
- exports paie et comptabilité ;
- Dolibarr ;
- rapports PDF ;
- tableau de bord ;
- interface web ;
- autres conventions collectives.

Aucune intégration ne doit fragiliser le socle local.

## 12. Versionnement réaliste

- `0.1.x` : démarrage et écrans essentiels réparés ;
- `0.2.x` : parcours salarié complet validé ;
- `0.3.x` : contrats, absences, congés et sauvegardes fiables ;
- `0.4.x` : planning et pointage ;
- `0.5.x` : moteur de règles isolé et testé ;
- `0.6.x` : premier périmètre CCNS validé ;
- `0.7.x` : exports et contrôles consolidés ;
- `0.8.x` : bêta interne PMSL ;
- `0.9.x` : préproduction sur copie réelle ;
- `1.0.0` : usage réel possible avec procédure de sauvegarde, restauration et retour arrière validée.

## 13. Critères de passage

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
- validation explicite de l'utilisateur.

### Version stable

- période d'utilisation réelle sans anomalie bloquante ;
- procédure de secours documentée ;
- données récupérables ;
- règles métier critiques sourcées et testées ;
- limites connues publiées.

## 14. Mode de développement

- un seul fichier de roadmap : `ROADMAP.md` ;
- pas de ZIP à chaque PR ;
- PR regroupées par objectif testable ;
- aucune fusion sans critère de sortie explicite ;
- aucun ticket fermé sur simple présence de code ;
- changelog fondé sur des fonctions vérifiées ;
- priorité aux parcours complets plutôt qu'au nombre de commits.

## 15. Prochain jalon

Le prochain jalon est la stabilisation du parcours Windows minimal et du thème système natif. Aucun numéro de RC ne sera utilisé avant validation complète de ce jalon.